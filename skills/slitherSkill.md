# Skill: Running Slither Static Analyzer

## Overview
Slither is a static analysis framework for Solidity smart contracts developed by 
Trail of Bits. It detects vulnerabilities, code quality issues, and optimization 
opportunities using a suite of built-in detectors.

---

## Execution Environment Requirements

- `slither-analyzer` must be installed via pip: `pip install slither-analyzer`
- A Solidity compiler (`solc`) must be available. Use `py-solc-x` to manage versions.
- The target is a single `.sol` file (standalone analysis mode).
- Slither should be invoked with `--solc-solcs-bin` pointing to the installed solc binary.

---

## Command Format

```bash
slither <CONTRACT_PATH> \
  --solc-solcs-bin <SOLC_BIN_PATH> \
  --json <OUTPUT_JSON_PATH> \
  --disable-color \
  --exclude-dependencies
```

### Parameters

| Parameter | Value | Purpose |
|---|---|---|
| `<CONTRACT_PATH>` | `/tmp/contract_<uuid>.sol` | Path to the temp Solidity file |
| `--solc-solcs-bin` | Path from `solcx.get_executable()` | Tell Slither which solc to use |
| `--json` | `/tmp/slither_<uuid>.json` | Write structured output to JSON |
| `--disable-color` | (flag) | Prevents ANSI escape codes in output |
| `--exclude-dependencies` | (flag) | Skip analysis of imported libraries |

---

## Python Invocation Pattern

```python
import subprocess
import json
import os

def runSlither(contractPath, solcBinPath, outputJsonPath):
    command = [
        "slither", contractPath,
        "--solc-solcs-bin", solcBinPath,
        "--json", outputJsonPath,
        "--disable-color",
        "--exclude-dependencies"
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=120
    )
    # NOTE: Slither exits with code 1 when it finds issues (NOT an error).
    # Exit code 255 means compilation failed. Handle both.
    return result
```

---

## Exit Code Handling

| Exit Code | Meaning | Action |
|---|---|---|
| `0` | No vulnerabilities found | Parse the JSON (may still have informational items) |
| `1` | Vulnerabilities found | Parse the JSON normally — this is the expected success path |
| `255` | Compilation error | Surface the error to the user; abort |
| Any other | Unexpected failure | Log stderr and surface generic error |

---

## JSON Output Structure

The output JSON file has this structure:

```json
{
  "success": true,
  "error": null,
  "results": {
    "detectors": [
      {
        "check": "reentrancy-eth",
        "impact": "High",
        "confidence": "Medium",
        "description": "Reentrancy in ...",
        "elements": [
          {
            "type": "function",
            "name": "withdraw",
            "source_mapping": { "filename_short": "contract.sol", "lines": [12, 15] }
          }
        ]
      }
    ]
  }
}
```

### Key Fields to Extract

- `results.detectors[].check` → Detector identifier (e.g., `"reentrancy-eth"`)
- `results.detectors[].impact` → `"High"` | `"Medium"` | `"Low"` | `"Informational"`  
- `results.detectors[].confidence` → `"High"` | `"Medium"` | `"Low"`
- `results.detectors[].description` → Human-readable description of the finding
- `results.detectors[].elements[].name` → Name of the affected function/variable

---

## Filtering Rules for LLM Context

When passing Slither output to the Groq API, apply these filters to reduce noise:

1. **Include always**: Impact = `High` or `Medium`
2. **Include if confidence >= Medium**: Impact = `Low`  
3. **Exclude always**: Checks prefixed with `naming-convention` (stylistic only)
4. **Exclude always**: Checks prefixed with `solc-version` unless it's an old version  
5. **Cap at 20 findings** for the LLM prompt to avoid token overflow

---

## Common False Positives to Note

| Detector | Common FP Scenario |
|---|---|
| `reentrancy-no-eth` | Flagging functions that call audited ERC-20 tokens |
| `calls-loop` | Legitimate batch operations in safe context |
| `unused-return` | Intentional ignored return values for gas efficiency |
| `tautology` | Solidity version-specific safe math patterns |

---

## Error Messages to Surface to User

- **Compilation failure**: "Slither could not compile the contract. Please check your Solidity version pragma and syntax."
- **Timeout**: "Slither analysis timed out after 120 seconds. The contract may be too complex."
- **Binary not found**: "Slither is not installed. Please check the deployment environment."
