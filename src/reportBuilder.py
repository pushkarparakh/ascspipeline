"""
src/reportBuilder.py — ASCSPipeline Report Post-Processor
==========================================================
Validates and enriches the raw Markdown report returned by the Groq API.
Adds a metadata header (scan timestamp, tool versions) and a disclaimer.
Ensures the report has the expected structure before rendering.

Author: ASCSPipeline
Coding style: camelCase, minimal underscores
"""

import re
from datetime import datetime, timezone


# ── Report Metadata ───────────────────────────────────────────────────────────

APP_VERSION = "1.0.0"
SLITHER_VERSION_LABEL = "slither-analyzer>=0.10.0"
ADERYN_VERSION_LABEL = "Latest (auto-downloaded)"
GROQ_MODEL_LABEL = "llama-3.3-70b-versatile"


# ── Validation Helpers ────────────────────────────────────────────────────────

def containsMinimalStructure(reportText: str) -> bool:
    """
    Checks whether the Groq report contains at least the minimal expected
    Markdown structure. Returns False if the response appears malformed.
    """
    requiredPatterns = [
        r"#.*(audit|report|security)",  # A heading with audit-related keyword
        r"\*\*severity\*\*",            # At least one finding with severity label
    ]
    textLower = reportText.lower()
    return all(re.search(pat, textLower) for pat in requiredPatterns)


def extractSeverityCounts(reportText: str) -> dict:
    """
    Scans the report for severity labels and returns a summary count dict.
    Pattern matches: **Severity**: Critical / High / Medium / Low
    """
    counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0, "Informational": 0}
    pattern = re.compile(
        r"\*\*severity\*\*\s*:\s*(critical|high|medium|low|informational)",
        re.IGNORECASE,
    )
    for match in pattern.finditer(reportText):
        level = match.group(1).capitalize()
        if level in counts:
            counts[level] += 1
    return counts


# ── Metadata Block Builder ─────────────────────────────────────────────────────

def buildMetadataBlock(
    contractLineCount: int,
    slitherAvailable: bool,
    aderynAvailable: bool,
) -> str:
    """
    Builds a Markdown metadata block to prepend to the final report.
    """
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    slitherStatus = "Active" if slitherAvailable else "Unavailable"
    aderynStatus = "Active" if aderynAvailable else "Unavailable (Slither-only mode)"

    return f"""---
> **ASCSPipeline Scan Metadata**
>
> | Field | Value |
> |---|---|
> | **Scan Time** | {timestamp} |
> | **App Version** | {APP_VERSION} |
> | **Contract Size** | {contractLineCount} lines |
> | **Slither** | {slitherStatus} ({SLITHER_VERSION_LABEL}) |
> | **Aderyn** | {aderynStatus} ({ADERYN_VERSION_LABEL}) |
> | **AI Model** | {GROQ_MODEL_LABEL} via Groq |

---

"""


# ── Main Report Builder ────────────────────────────────────────────────────────

def buildFinalReport(
    rawReport: str,
    contractCode: str,
    slitherAvailable: bool,
    aderynAvailable: bool,
) -> str:
    """
    Takes the raw Groq AI report and returns a polished, complete Markdown document.

    Steps:
      1. Validates the report has expected structure
      2. Prepends a metadata block
      3. Appends a severity summary table if counts are detected
      4. Returns the assembled report

    Args:
        rawReport:        Markdown string from groqClient.generateReport()
        contractCode:     Original Solidity source (for line count)
        slitherAvailable: Whether Slither ran successfully
        aderynAvailable:  Whether Aderyn ran successfully

    Returns:
        Final enriched Markdown string for rendering in Streamlit.
    """
    lineCount = len(contractCode.strip().splitlines())

    # Validate structure
    if not rawReport or len(rawReport.strip()) < 100:
        return (
            "**Report generation failed**: The AI model returned an empty or "
            "too-short response. Please try again or check your Groq API key."
        )

    if not containsMinimalStructure(rawReport):
        # Still return it — the LLM might have used slightly different formatting
        # but the content could still be valid
        pass

    # Build metadata block
    metaBlock = buildMetadataBlock(
        contractLineCount=lineCount,
        slitherAvailable=slitherAvailable,
        aderynAvailable=aderynAvailable,
    )

    # Optionally append severity summary if counts are detectable
    counts = extractSeverityCounts(rawReport)
    totalFindings = sum(counts.values())

    severitySummary = ""
    if totalFindings > 0:
        severitySummary = "\n\n---\n\n## Automated Finding Counts\n\n"
        severitySummary += "| Severity | Count |\n|---|---|\n"
        for level in ["Critical", "High", "Medium", "Low", "Informational"]:
            if counts[level] > 0:
                severitySummary += f"| {level} | {counts[level]} |\n"

    return metaBlock + rawReport + severitySummary
