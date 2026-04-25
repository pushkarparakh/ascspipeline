"""
setupTools.py — ASCSPipeline Environment Provisioner
=====================================================
Runs automatically on Streamlit app startup (via @st.cache_resource).
Responsibilities:
  - Installs the correct solc version via py-solc-x
  - Downloads the Aderyn Linux binary from GitHub Releases into /tmp/
  - Returns a config dict consumed by other modules

Author: ASCSPipeline
Coding style: camelCase, minimal underscore usage
"""

import io
import os
import stat
import tarfile
import zipfile
import requests
import streamlit as st
from typing import Optional


# ── Constants ─────────────────────────────────────────────────────────────────

SOLC_VERSION = "0.8.20"
ADERYN_BIN_PATH = "/tmp/aderyn"
ADERYN_RELEASES_API = "https://api.github.com/repos/Cyfrin/aderyn/releases/latest"

# ELF magic bytes — the first 4 bytes of any valid Linux binary
ELF_MAGIC = b"\x7fELF"


# ── Solidity Compiler Setup ───────────────────────────────────────────────────

def installSolc(version: str = SOLC_VERSION) -> str:
    """
    Ensures the requested solc version is installed via py-solc-x.
    solcx.install_solc() is idempotent — if the version is already present it
    skips the download and returns the path immediately.
    Returns the absolute path to the solc executable.
    """
    try:
        import solcx
        executablePath = solcx.install_solc(version)
        return str(executablePath)

    except Exception as err:
        raise RuntimeError(f"Failed to install solc v{version}: {err}") from err


# ── Aderyn Binary Setup ───────────────────────────────────────────────────────

def isElfBinary(data: bytes) -> bool:
    """Returns True if the bytes represent a valid ELF executable."""
    return data[:4] == ELF_MAGIC


def selectAderynAsset(assets: list) -> Optional[dict]:
    """
    Picks the most appropriate Aderyn asset for the current Linux x86_64 host.
    Explicitly excludes macOS (darwin/apple), Windows, and ARM builds.
    Priority order:
      1. x86_64 musl static Linux .tar.gz
      2. x86_64 Linux .tar.gz
      3. Any Linux x86_64 asset
    """
    # Hard exclusions — never pick these on a Linux x86_64 host
    EXCLUDED_KEYWORDS = {"darwin", "apple", "windows", "win32", "aarch64", "arm64", "arm"}

    def isExcluded(name: str) -> bool:
        return any(kw in name for kw in EXCLUDED_KEYWORDS)

    linuxCandidates = []
    for asset in assets:
        name = asset.get("name", "").lower()
        if isExcluded(name):
            continue
        if "linux" in name or "x86_64" in name or "amd64" in name:
            linuxCandidates.append(asset)

    # Prefer musl static build
    for asset in linuxCandidates:
        name = asset.get("name", "").lower()
        if "musl" in name and ("x86_64" in name or "amd64" in name):
            return asset

    # Any x86_64 Linux asset
    for asset in linuxCandidates:
        name = asset.get("name", "").lower()
        if "x86_64" in name or "amd64" in name:
            return asset

    return linuxCandidates[0] if linuxCandidates else None


def extractBinaryFromArchive(archiveData: bytes, assetName: str) -> Optional[bytes]:
    """
    Extracts the 'aderyn' binary from a .tar.gz or .zip archive.
    Returns the raw binary bytes, or None if extraction fails.
    """
    try:
        if assetName.endswith(".tar.gz") or assetName.endswith(".tgz"):
            with tarfile.open(fileobj=io.BytesIO(archiveData), mode="r:gz") as tar:
                for member in tar.getmembers():
                    # Find a member whose name is exactly 'aderyn' or ends with '/aderyn'
                    memberBasename = os.path.basename(member.name)
                    if memberBasename == "aderyn" and member.isfile():
                        extracted = tar.extractfile(member)
                        if extracted:
                            return extracted.read()

        elif assetName.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(archiveData)) as zf:
                for entry in zf.namelist():
                    if os.path.basename(entry) == "aderyn":
                        return zf.read(entry)

    except Exception as err:
        st.warning(f"Archive extraction failed: {err}")

    return None


def downloadAderyn() -> Optional[str]:
    """
    Downloads the Aderyn binary to ADERYN_BIN_PATH if not already present.

    Handles both raw binaries and .tar.gz / .zip archives correctly.
    Validates the resulting file is a genuine ELF executable before accepting it.
    Returns the path to the binary on success, or None if any step fails.
    """
    # Already have a valid binary cached
    if os.path.exists(ADERYN_BIN_PATH) and os.access(ADERYN_BIN_PATH, os.X_OK):
        with open(ADERYN_BIN_PATH, "rb") as f:
            header = f.read(4)
        if isElfBinary(header):
            return ADERYN_BIN_PATH
        # Cached file is corrupt — remove and re-download
        os.remove(ADERYN_BIN_PATH)

    st.info("Downloading Aderyn security analyzer...")

    try:
        response = requests.get(ADERYN_RELEASES_API, timeout=30)
        response.raise_for_status()
        releaseData = response.json()
    except requests.RequestException as err:
        st.warning(f"Could not reach GitHub API for Aderyn: {err}")
        return None

    assets = releaseData.get("assets", [])
    chosenAsset = selectAderynAsset(assets)

    if not chosenAsset:
        st.warning("No compatible Aderyn Linux binary found in the latest release. Aderyn analysis will be skipped.")
        return None

    assetName = chosenAsset.get("name", "")
    downloadUrl = chosenAsset["browser_download_url"]

    try:
        archiveResponse = requests.get(downloadUrl, timeout=120, stream=True)
        archiveResponse.raise_for_status()
        rawData = archiveResponse.content

    except Exception as err:
        st.warning(f"Aderyn download failed: {err}. Continuing without it.")
        return None

    # Determine if the downloaded file is an archive or a raw binary
    isArchive = assetName.endswith(".tar.gz") or assetName.endswith(".tgz") or assetName.endswith(".zip")

    if isArchive:
        binaryData = extractBinaryFromArchive(rawData, assetName)
        if not binaryData:
            st.warning("Could not extract Aderyn binary from archive. Aderyn analysis will be skipped.")
            return None
    else:
        binaryData = rawData

    # Validate it is a real ELF binary
    if not isElfBinary(binaryData):
        st.warning(
            f"Downloaded file '{assetName}' is not a valid Linux binary "
            "(ELF header not found). Aderyn analysis will be skipped."
        )
        return None

    # Write and mark executable
    try:
        with open(ADERYN_BIN_PATH, "wb") as binFile:
            binFile.write(binaryData)

        currentMode = os.stat(ADERYN_BIN_PATH).st_mode
        os.chmod(ADERYN_BIN_PATH, currentMode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        return ADERYN_BIN_PATH

    except Exception as err:
        st.warning(f"Failed to write Aderyn binary: {err}. Continuing without it.")
        if os.path.exists(ADERYN_BIN_PATH):
            os.remove(ADERYN_BIN_PATH)
        return None


# ── Master Setup Entrypoint ───────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def setupEnvironment() -> dict:
    """
    Master entrypoint called once per Streamlit session via @st.cache_resource.
    Provisions all required binaries and returns a config dict.

    Returns:
        dict with keys:
            - 'solcPath'   : str path to solc executable
            - 'aderynPath' : str path to aderyn binary, or None
            - 'ready'      : bool, True if at minimum solc is available
    """
    config = {
        "solcPath": None,
        "aderynPath": None,
        "ready": False,
    }

    with st.status("Initializing ASCSPipeline environment...", expanded=True) as statusBox:

        statusBox.write(f"Installing Solidity compiler (solc v{SOLC_VERSION})...")
        try:
            config["solcPath"] = installSolc(SOLC_VERSION)
            statusBox.write(f"solc ready: {config['solcPath']}")
        except RuntimeError as err:
            statusBox.write(f"solc installation failed: {err}")
            st.error("Critical: Could not install the Solidity compiler. Analysis will not work.")
            return config

        statusBox.write("Fetching Aderyn binary from GitHub Releases...")
        config["aderynPath"] = downloadAderyn()
        if config["aderynPath"]:
            statusBox.write(f"Aderyn ready: {config['aderynPath']}")
        else:
            statusBox.write("Aderyn unavailable. Running in Slither-only mode.")

        config["ready"] = True
        statusBox.update(label="Environment ready", state="complete", expanded=False)

    return config
