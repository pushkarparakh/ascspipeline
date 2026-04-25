# Skill: Running Aderyn Static Analyzer

## Overview
Aderyn is a Rust-based static analysis tool for Solidity developed by Cyfrin.
It analyzes Foundry and Hardhat projects and produces structured Markdown or JSON
security reports. It is designed to complement Slither with different detection patterns.

---

## Binary Provisioning (Serverless/Cloud Environments)

Aderyn is a compiled Rust binary. In cloud environments (like Streamlit Community Cloud)
where `cargo`, `rustup`, or `cyfrinup` are unavailable, the binary must be downloaded
directly from the GitHub Releases API.

### Download Logic

```python
import requests
import os
import stat

ADERYN_INSTALL_PATH = "/tmp/aderyn"
ADERYN_RELEASES_URL = "https://api.github.com/repos/Cyfrin/aderyn/releases/latest"
ADERYN_ASSET_PATTERN = "aderyn-x86_64-unknown-linux-musl"  # Static musl binary

def downloadAderyn():
    if os.path.exists(ADERYN_INSTALL_PATH):
        return ADERYN_INSTALL_PATH
    
    response = requests.get(ADERYN_RELEASES_URL, timeout=30)
    releaseData = response.json()
    
    downloadUrl = None
    for asset in releaseData.get("assets", []):
        if ADERYN_ASSET_PATTERN in asset["name"]:
            downloadUrl = asset["browser_download_url"]
            break
    
    if not downloadUrl:
        raise RuntimeError("Could not find Aderyn Linux binary in latest release.")
    
    binaryData = requests.get(downloadUrl, timeout=120)
    with open(ADERYN_INSTALL_PATH, "wb") as f:
        f.write(binaryData.content)
    
    os.chmod(ADERYN_INSTALL_PATH, os.stat(ADERYN_INSTALL_PATH).st_mode | stat.S_IEXEC)
    return ADERYN_INSTALL_PATH
```

---

## Project Scaffold Requirement

Aderyn requires a project directory structure (Foundry-compatible). For single-file
analysis, a minimal scaffold is created at runtime:

```
/tmp/aderyn_project_<uuid>/
├── foundry.toml          ← Minimal Foundry config
└── src/
    └── Contract.sol      ← The pasted contract code
```

### Minimal `foundry.toml` Content

```toml
[profile.default]
src = "src"
out = "out"
libs = ["lib"]
solc_version = "0.8.20"
```

---

## Command Format

```bash
/tmp/aderyn /tmp/aderyn_project_<uuid>/ \
  --output /tmp/aderyn_report_<uuid>.json
```

### Parameters

| Parameter | Value | Purpose |
|---|---|---|
| First positional arg | `/tmp/aderyn_project_<uuid>/` | Path to the Foundry project root |
| `--output` | `/tmp/aderyn_report_<uuid>.json` | Write JSON report |

> **Note**: Older Aderyn versions may produce a `report.md` by default. If `--output`
> with `.json` extension is not supported, use `--output report.md` and parse Markdown.

---

## Python Invocation Pattern

```python
import subprocess
import os
import uuid
import shutil

def runAderyn(contractCode, aderynBinPath):
    projectId = str(uuid.uuid4())[:8]
    projectDir = f"/tmp/aderynProject{projectId}"
    srcDir = os.path.join(projectDir, "src")
    os.makedirs(srcDir, exist_ok=True)
    
    # Write foundry.toml
    foundryConfig = '[profile.default]\nsrc = "src"\nout = "out"\nlibs = ["lib"]\n'
    with open(os.path.join(projectDir, "foundry.toml"), "w") as f:
        f.write(foundryConfig)
    
    # Write contract
    contractFile = os.path.join(srcDir, "Contract.sol")
    with open(contractFile, "w") as f:
        f.write(contractCode)
    
    reportPath = f"/tmp/aderynReport{projectId}.json"
    
    command = [aderynBinPath, projectDir, "--output", reportPath]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=120,
        cwd=projectDir
    )
    
    # Read report if it exists
    reportContent = ""
    if os.path.exists(reportPath):
        with open(reportPath, "r") as f:
            reportContent = f.read()
    
    # Cleanup
    shutil.rmtree(projectDir, ignore_errors=True)
    if os.path.exists(reportPath):
        os.remove(reportPath)
    
    return result, reportContent
```

---

## JSON Output Structure (Aderyn >= 0.3.x)

```json
{
  "files_summary": { ... },
  "issue_count": { "high": 2, "low": 3 },
  "high_issues": {
    "issues": [
      {
        "title": "Reentrancy vulnerabilities",
        "description": "...",
        "detector_name": "reentrancy",
        "instances": [
          {
            "contract_path": "src/Contract.sol",
            "line_no": 42,
            "src": "...",
            "src_char": "..."
          }
        ]
      }
    ]
  },
  "low_issues": {
    "issues": [ ... ]
  }
}
```

### Key Fields to Extract

- `high_issues.issues[].title` → Finding title
- `high_issues.issues[].description` → Description text
- `high_issues.issues[].instances[].line_no` → Line number in source
- `issue_count.high` + `issue_count.low` → Summary counts

---

## Exit Code Handling

| Exit Code | Meaning | Action |
|---|---|---|
| `0` | Analysis completed | Parse the report file |
| Non-zero | Analysis failed or no Foundry project detected | Log stderr; use Slither output only |

---

## Fallback Behavior

If Aderyn fails (binary download fails, or the tool errors on the contract):
1. Log the error to `stderr`
2. Surface a warning in the Streamlit UI: "Aderyn analysis unavailable. Proceeding with Slither output only."
3. Pass `aderynOutput = "Aderyn analysis was not available for this scan."` to the Groq prompt
4. Do NOT abort the entire scan — Slither + RAG context alone is sufficient for a report

---

## Error Messages to Surface to User

- **Download failure**: "Could not download the Aderyn binary. Check internet connectivity."
- **Timeout**: "Aderyn analysis timed out after 120 seconds."
- **No report generated**: "Aderyn did not generate a report. Proceeding without it."
