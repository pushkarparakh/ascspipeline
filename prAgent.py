import os
import sys
import json
import requests

from src.ragEngine import RagEngine
from src.groqClient import generateReport
from src.reportBuilder import buildFinalReport

SCAN_MARKER = "<!-- ascs-pr-scan -->"
GITHUB_API = "https://api.github.com"


def loadEnv() -> dict:
    keys = ["GROQ_API_KEY", "GITHUB_TOKEN", "GITHUB_REPO", "PR_NUMBER"]
    env = {k: os.environ.get(k, "").strip() for k in keys}
    missing = [k for k in keys if not env[k]]
    if missing:
        print(f"[prAgent] Missing env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)
    return env


def githubHeaders(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def fetchChangedSolFiles(repo: str, prNumber: str, token: str) -> list:
    headers = githubHeaders(token)
    url = f"{GITHUB_API}/repos/{repo}/pulls/{prNumber}/files"
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    solFiles = []
    for fileInfo in resp.json():
        name = fileInfo.get("filename", "")
        if not name.endswith(".sol") or fileInfo.get("status") == "removed":
            continue
        rawUrl = fileInfo.get("raw_url")
        if not rawUrl:
            continue
        rawResp = requests.get(rawUrl, headers=headers, timeout=30)
        if rawResp.ok:
            solFiles.append((name, rawResp.text))

    return solFiles


def readSlitherOutput() -> str:
    if not os.path.exists("slither-report.json"):
        return "Slither report not available."
    try:
        with open("slither-report.json") as f:
            data = json.load(f)
        detectors = data.get("results", {}).get("detectors", [])
        if not detectors:
            return "Slither: No findings."

        # Strip informational noise before sending to LLM
        noiseChecks = {"naming-convention", "solc-version", "pragma"}
        filtered = [d for d in detectors if d.get("check") not in noiseChecks]

        lines = []
        for d in filtered[:20]:
            impact = d.get("impact", "?")
            check = d.get("check", "?")
            desc = d.get("description", "").strip().replace("\n", " ")
            lines.append(f"[{impact}] {check}: {desc[:200]}")

        return "\n".join(lines) if lines else "Slither: No actionable findings after noise filtering."
    except Exception as e:
        return f"Slither: Parse error — {e}"


def readAderynOutput() -> str:
    if not os.path.exists("aderyn-report.json"):
        return "Aderyn report not available."
    try:
        with open("aderyn-report.json") as f:
            data = json.load(f)

        lines = []
        for severity in ("high_issues", "medium_issues", "low_issues"):
            section = data.get(severity) or {}
            issues = section.get("issues", []) if isinstance(section, dict) else []
            label = severity.replace("_issues", "").capitalize()
            for issue in issues[:10]:
                title = issue.get("title", "?")
                desc = issue.get("description", "").strip().replace("\n", " ")
                lines.append(f"[{label}] {title}: {desc[:200]}")

        return "\n".join(lines) if lines else "Aderyn: No findings."
    except Exception as e:
        return f"Aderyn: Parse error — {e}"


def findExistingComment(repo: str, prNumber: str, token: str) -> int | None:
    headers = githubHeaders(token)
    page = 1
    while True:
        url = f"{GITHUB_API}/repos/{repo}/issues/{prNumber}/comments"
        resp = requests.get(url, headers=headers, params={"per_page": 100, "page": page}, timeout=30)
        resp.raise_for_status()
        comments = resp.json()
        if not comments:
            break
        for comment in comments:
            if SCAN_MARKER in comment.get("body", ""):
                return comment["id"]
        if len(comments) < 100:
            break
        page += 1
    return None


def postOrUpdateComment(repo: str, prNumber: str, token: str, body: str) -> None:
    headers = githubHeaders(token)
    existingId = findExistingComment(repo, prNumber, token)

    if existingId:
        url = f"{GITHUB_API}/repos/{repo}/issues/comments/{existingId}"
        resp = requests.patch(url, headers=headers, json={"body": body}, timeout=30)
        action = "updated"
    else:
        url = f"{GITHUB_API}/repos/{repo}/issues/{prNumber}/comments"
        resp = requests.post(url, headers=headers, json={"body": body}, timeout=30)
        action = "posted"

    resp.raise_for_status()
    print(f"[prAgent] Comment {action}.")


def buildScanHeader(solFiles: list) -> str:
    fileList = "\n".join(f"- `{name}`" for name, _ in solFiles)
    count = len(solFiles)
    noun = "file" if count == 1 else "files"
    return (
        f"{SCAN_MARKER}\n\n"
        f"<details>\n"
        f"<summary><b>ASCSPipeline Security Scan</b> &mdash; "
        f"{count} Solidity {noun} analysed (click to expand)</summary>\n\n"
        f"{fileList}\n\n"
        f"</details>\n\n"
    )


def main() -> None:
    env = loadEnv()

    print("[prAgent] Fetching changed Solidity files...")
    solFiles = fetchChangedSolFiles(env["GITHUB_REPO"], env["PR_NUMBER"], env["GITHUB_TOKEN"])

    if not solFiles:
        print("[prAgent] No Solidity files changed. Nothing to audit.")
        sys.exit(0)

    print(f"[prAgent] Scanning {len(solFiles)} file(s): {[f for f, _ in solFiles]}")

    # Concat all changed .sol files with clear separators for the LLM
    contractCode = "\n\n".join(
        f"// ===== {name} =====\n{content}"
        for name, content in solFiles
    )

    slitherOut = readSlitherOutput()
    aderynOut  = readAderynOutput()

    print("[prAgent] Querying RAG knowledge base...")
    ragQuery = f"{contractCode[:500]}\n{slitherOut[:300]}"
    ragContext = ragEngine.retrieveContext(ragQuery, topK=4)

    print("[prAgent] Calling Groq for AI audit synthesis...")
    rawReport = generateReport(
        apiKey=env["GROQ_API_KEY"],
        contractCode=contractCode,
        slitherOutput=slitherOut,
        aderynOutput=aderynOut,
        ragContext=ragContext,
    )

    finalReport = buildFinalReport(
        rawReport=rawReport,
        contractCode=contractCode,
        slitherAvailable="not available" not in slitherOut.lower(),
        aderynAvailable="not available" not in aderynOut.lower(),
    )

    commentBody = buildScanHeader(solFiles) + finalReport

    print("[prAgent] Posting to PR...")
    postOrUpdateComment(env["GITHUB_REPO"], env["PR_NUMBER"], env["GITHUB_TOKEN"], commentBody)


if __name__ == "__main__":
    ragEngine = RagEngine()
    main()
