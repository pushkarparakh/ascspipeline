"""
src/analyzerEngine.py — ASCSPipeline Static Analysis Runner
============================================================
Runs Slither and Aderyn as subprocesses against a target Solidity file.
Parses their outputs and returns structured data for the Groq prompt.

Behavioral guarantees:
  - All temp files are cleaned up after reading
  - Timeouts are enforced (120s per tool)
  - Non-zero exit codes from Slither that indicate findings are handled correctly
  - Aderyn failure is non-fatal; Slither alone is sufficient

Author: ASCSPipeline
Coding style: camelCase, minimal underscores
"""

import os
import json
import uuid
import shutil
import subprocess
import tempfile
from typing import Optional


# ── Constants ─────────────────────────────────────────────────────────────────

ANALYSIS_TIMEOUT = 120  # seconds
FOUNDRY_TOML_CONTENT = """[profile.default]
src = "src"
out = "out"
libs = ["lib"]
solc_version = "0.8.20"
"""


# ── Slither Runner ────────────────────────────────────────────────────────────

def buildSlitherSummary(detectors: list) -> str:
    """
    Converts a list of Slither detector dicts into a concise text summary
    ready for injection into a Groq prompt.
    """
    SEVERITY_ORDER = {"High": 0, "Medium": 1, "Low": 2, "Informational": 3, "Optimization": 4}
    EXCLUDED_CHECKS = {"naming-convention", "solc-version", "pragma"}

    filtered = [
        d for d in detectors
        if d.get("check", "") not in EXCLUDED_CHECKS
    ]
    filtered.sort(key=lambda d: SEVERITY_ORDER.get(d.get("impact", "Low"), 3))

    # Cap at 20 findings to stay within token budget
    filtered = filtered[:20]

    lines = []
    for item in filtered:
        check = item.get("check", "unknown")
        impact = item.get("impact", "Unknown")
        confidence = item.get("confidence", "Unknown")
        description = item.get("description", "").strip().replace("\n", " ")[:300]
        lines.append(
            f"- [{impact}/{confidence}] {check}: {description}"
        )

    return "\n".join(lines) if lines else "No significant findings from Slither."


def runSlither(contractPath: str, solcBinPath: str) -> str:
    """
    Runs Slither against a single Solidity file and returns a structured
    text summary of findings.

    Args:
        contractPath: Absolute path to the .sol file.
        solcBinPath:  Path to the solc binary from py-solc-x.

    Returns:
        A human-readable string summary of Slither findings.
    """
    sessionId = uuid.uuid4().hex[:8]
    outputJsonPath = os.path.join(tempfile.gettempdir(), f"slitherOut{sessionId}.json")

    command = [
        "slither", contractPath,
        "--solc", solcBinPath,
        "--json", outputJsonPath,
        "--disable-color",
        "--exclude-dependencies",
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=ANALYSIS_TIMEOUT,
        )
        # Exit codes:  0 = no findings,  1 = findings found,  255 = compilation error
        if result.returncode == 255:
            return (
                f"Slither compilation error:\n{result.stderr[:800]}\n"
                "Tip: Check your Solidity pragma version and syntax."
            )

        # Parse the JSON output file
        if os.path.exists(outputJsonPath):
            try:
                with open(outputJsonPath, "r") as jsonFile:
                    data = json.load(jsonFile)
                detectors = data.get("results", {}).get("detectors", [])
                return buildSlitherSummary(detectors)
            except (json.JSONDecodeError, KeyError) as parseErr:
                return f"Slither output parse error: {parseErr}\nRaw stderr:\n{result.stderr[:600]}"
        else:
            # Fallback: attempt to parse stderr directly (some Slither versions write JSON to stderr)
            try:
                stderrData = json.loads(result.stderr)
                detectors = stderrData.get("results", {}).get("detectors", [])
                return buildSlitherSummary(detectors)
            except (json.JSONDecodeError, KeyError):
                return f"Slither produced no JSON output.\nStdout: {result.stdout[:400]}\nStderr: {result.stderr[:400]}"

    except subprocess.TimeoutExpired:
        return f"Slither timed out after {ANALYSIS_TIMEOUT} seconds."
    except FileNotFoundError:
        return "Slither binary not found. Ensure slither-analyzer is installed."
    finally:
        if os.path.exists(outputJsonPath):
            os.remove(outputJsonPath)


# ── Aderyn Runner ─────────────────────────────────────────────────────────────

def buildFoundryProject(contractCode: str) -> str:
    """
    Creates a minimal Foundry-compatible project directory in /tmp/.
    Returns the path to the project root.
    """
    sessionId = uuid.uuid4().hex[:8]
    projectRoot = os.path.join(tempfile.gettempdir(), f"aderynProject{sessionId}")
    srcDir = os.path.join(projectRoot, "src")
    os.makedirs(srcDir, exist_ok=True)

    with open(os.path.join(projectRoot, "foundry.toml"), "w") as configFile:
        configFile.write(FOUNDRY_TOML_CONTENT)

    contractDest = os.path.join(srcDir, "Contract.sol")
    with open(contractDest, "w") as solidityFile:
        solidityFile.write(contractCode)

    return projectRoot


def parseAderynReport(reportContent: str) -> str:
    """
    Parses Aderyn JSON report content into a readable summary string.
    Falls back to raw text if JSON parsing fails (e.g., Markdown output).
    """
    try:
        data = json.loads(reportContent)
        lines = []
        issueCount = data.get("issue_count", {})
        highCount = issueCount.get("high", 0)
        lowCount = issueCount.get("low", 0)
        lines.append(f"Aderyn found {highCount} high-severity and {lowCount} low-severity issues.")

        for issue in data.get("high_issues", {}).get("issues", []):
            title = issue.get("title", "Unknown")
            description = issue.get("description", "")[:200]
            instances = issue.get("instances", [])
            lineNos = ", ".join(str(i.get("line_no", "?")) for i in instances[:3])
            lines.append(f"- [HIGH] {title} (lines: {lineNos}): {description}")

        for issue in data.get("low_issues", {}).get("issues", []):
            title = issue.get("title", "Unknown")
            description = issue.get("description", "")[:150]
            lines.append(f"- [LOW] {title}: {description}")

        return "\n".join(lines) if lines else "Aderyn found no issues."

    except (json.JSONDecodeError, TypeError):
        # Markdown or plain text output — return raw (truncated)
        return reportContent[:2000]


def runAderyn(contractCode: str, aderynBinPath: Optional[str]) -> str:
    """
    Scaffolds a temporary Foundry project, runs Aderyn against it,
    and returns a text summary of findings.

    Args:
        contractCode:   Raw Solidity source code string.
        aderynBinPath:  Path to the aderyn binary, or None if unavailable.

    Returns:
        A human-readable string summary of Aderyn findings.
    """
    if not aderynBinPath or not os.path.exists(aderynBinPath):
        return "Aderyn binary not available. Skipping Aderyn analysis."

    projectRoot = buildFoundryProject(contractCode)
    sessionId = os.path.basename(projectRoot).replace("aderynProject", "")
    reportPath = os.path.join(tempfile.gettempdir(), f"aderynReport{sessionId}.json")

    command = [aderynBinPath, projectRoot, "--output", reportPath]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=ANALYSIS_TIMEOUT,
            cwd=projectRoot,
        )

        if os.path.exists(reportPath):
            with open(reportPath, "r") as reportFile:
                rawContent = reportFile.read()
            return parseAderynReport(rawContent)
        else:
            # Check for default report.md
            defaultReport = os.path.join(projectRoot, "report.md")
            if os.path.exists(defaultReport):
                with open(defaultReport, "r") as mdFile:
                    return mdFile.read()[:2000]
            return (
                f"Aderyn completed but produced no report.\n"
                f"Stderr: {result.stderr[:400]}"
            )

    except subprocess.TimeoutExpired:
        return f"Aderyn timed out after {ANALYSIS_TIMEOUT} seconds."
    except FileNotFoundError:
        return "Aderyn binary not executable or not found."
    finally:
        shutil.rmtree(projectRoot, ignore_errors=True)
        if os.path.exists(reportPath):
            try:
                os.remove(reportPath)
            except OSError:
                pass
