import os
import uuid
import tempfile
import streamlit as st

st.set_page_config(
    page_title="ASCSPipeline — Scanner",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "ASCSPipeline v1.0 — Smart Contract Security Platform"},
)

import setupTools
from src.theme import applyTheme, renderNav
from src.ragEngine import RagEngine
from src.analyzerEngine import runSlither, runAderyn
from src.groqClient import generateReport
from src.reportBuilder import buildFinalReport

applyTheme()


SAMPLE_CONTRACT = """\
// SPDX-License-Identifier: MIT
pragma solidity ^0.7.6;

/// @title VulnerableVault — DO NOT DEPLOY. Demonstration contract only.
contract VulnerableVault {
    mapping(address => uint256) public balances;

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        (bool sent, ) = msg.sender.call{value: amount}("");
        require(sent, "Transfer failed");
        balances[msg.sender] -= amount;  // SWC-107: state after external call
    }

    function adminWithdrawAll(address payable recipient) external {
        require(tx.origin == recipient, "Not authorized");  // SWC-115
        recipient.transfer(address(this).balance);
    }

    function destroy() external {
        selfdestruct(payable(msg.sender));  // SWC-106
    }
}
"""


@st.cache_resource(show_spinner=False)
def loadRagEngine() -> RagEngine:
    return RagEngine()


def renderSidebar(envConfig: dict) -> str:
    renderNav("scanner")

    with st.sidebar:
        st.markdown("<div class='label' style='padding:0 0.5rem'>Configuration</div>", unsafe_allow_html=True)

        groqApiKey = st.text_input(
            "Groq API Key",
            type="password",
            placeholder="gsk_...",
            help="Get a free key at console.groq.com. Never stored.",
            key="groqApiKeyInput",
        )

        if groqApiKey:
            st.success("API key configured")
        else:
            st.warning("Enter your Groq API key to enable AI analysis")

        st.markdown("<div class='sidebarDivider'></div>", unsafe_allow_html=True)
        st.markdown("<div class='navLabel'>Tool Status</div>", unsafe_allow_html=True)

        statusItems = [
            ("Slither",      envConfig.get("ready", False),          "Trail of Bits — static analysis"),
            ("Aderyn",       envConfig.get("aderynPath") is not None, "Cyfrin — Rust-native analysis"),
            ("RAG Corpus",   True,                                    "SWC + DeFi knowledge base"),
            ("Groq AI",      bool(groqApiKey),                       "llama-3.3-70b-versatile"),
        ]

        for label, ready, desc in statusItems:
            dotState = "on" if ready else "off"
            st.markdown(
                f"<div class='statusRow'>"
                f"  <span class='dot {dotState}'></span>"
                f"  <div>"
                f"    <div class='statusRowLabel'>{label}</div>"
                f"    <div class='statusRowSub'>{desc}</div>"
                f"  </div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            "<div style='padding:1.5rem 1.2rem 0.5rem;font-size:0.67rem;color:#3d444d;"
            "font-family:\"JetBrains Mono\",monospace;line-height:1.7'>"
            "v1.0.0 &middot; Streamlit Cloud<br>"
            "Slither &middot; Aderyn &middot; Groq &middot; scikit-learn"
            "</div>",
            unsafe_allow_html=True,
        )

    return groqApiKey


def renderHero() -> None:
    st.markdown(
        """
        <div class="hero">
            <div class="heroTitle">ASCSPipeline</div>
            <p class="heroSub">
                Agentic Smart Contract Security Pipeline &mdash;
                deterministic static analysis augmented by AI reasoning.
            </p>
            <div class="tagRow">
                <span class="tag g">Slither</span>
                <span class="tag b">Aderyn</span>
                <span class="tag o">Groq AI</span>
                <span class="tag p">RAG Corpus</span>
                <span class="tag">Solidity 0.8.x</span>
                <span class="tag">Streamlit Cloud</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def runScan(contractCode: str, groqApiKey: str, envConfig: dict, ragEngine: RagEngine) -> None:
    sessionId = uuid.uuid4().hex[:8]
    solFilePath = os.path.join(tempfile.gettempdir(), f"contract{sessionId}.sol")

    slitherOut = "Slither not run."
    aderynOut  = "Aderyn not run."
    ragContext = ""

    try:
        with open(solFilePath, "w") as f:
            f.write(contractCode)

        with st.status("Running security analysis pipeline...", expanded=True) as progress:
            progress.write("Step 1 / 4 — Slither static analysis...")
            slitherOut = runSlither(solFilePath, envConfig["solcPath"]) if envConfig.get("solcPath") \
                else "Slither unavailable: solc not installed."
            progress.write("Slither complete.")

            progress.write("Step 2 / 4 — Aderyn static analysis...")
            aderynOut = runAderyn(contractCode, envConfig.get("aderynPath"))
            progress.write("Aderyn complete.")

            progress.write("Step 3 / 4 — Querying RAG knowledge base...")
            ragContext = ragEngine.retrieveContext(f"{contractCode[:500]}\n{slitherOut[:300]}", topK=4)
            progress.write("Context retrieved.")

            progress.write("Step 4 / 4 — Groq AI audit synthesis...")
            rawReport = generateReport(
                apiKey=groqApiKey,
                contractCode=contractCode,
                slitherOutput=slitherOut,
                aderynOutput=aderynOut,
                ragContext=ragContext,
            )
            progress.update(label="Analysis complete", state="complete", expanded=False)

        finalReport = buildFinalReport(
            rawReport=rawReport,
            contractCode=contractCode,
            slitherAvailable=bool(envConfig.get("solcPath")),
            aderynAvailable=bool(envConfig.get("aderynPath")),
        )

        st.markdown("---")

        colA, colB = st.columns([8, 2])
        with colA:
            st.markdown(
                "<div style='font-size:1rem;font-weight:700;color:#e8edf5;"
                "letter-spacing:-0.2px'>Security Audit Report</div>",
                unsafe_allow_html=True,
            )
        with colB:
            st.download_button(
                label="Download .md",
                data=finalReport,
                file_name=f"ascspipeline_{sessionId}.md",
                mime="text/markdown",
                key=f"dl{sessionId}",
            )

        st.markdown("<div class='report'>", unsafe_allow_html=True)
        st.markdown(finalReport)
        st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("Raw Tool Outputs", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Slither**")
                st.code(slitherOut, language="text")
            with c2:
                st.markdown("**Aderyn**")
                st.code(aderynOut, language="text")
            st.markdown("**RAG Context**")
            st.code(ragContext, language="text")

    except (ValueError, RuntimeError) as e:
        st.error(str(e))
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        raise
    finally:
        if os.path.exists(solFilePath):
            os.remove(solFilePath)


def main() -> None:
    envConfig = setupTools.setupEnvironment()

    with st.spinner("Initializing knowledge base..."):
        ragEngine = loadRagEngine()

    # Resolve sample preload BEFORE any widget with key="contractInput" is rendered.
    # Setting session_state for a widget key after the widget instantiates causes a crash.
    if st.session_state.pop("triggerSampleLoad", False):
        st.session_state["contractInput"] = SAMPLE_CONTRACT

    groqApiKey = renderSidebar(envConfig)
    renderHero()

    leftCol, rightCol = st.columns([7, 3], gap="large")

    with leftCol:
        # VS Code-style editor tab header
        st.markdown(
            "<div class='editorHeader'>"
            "  <div class='editorTab'><span class='editorTabDot'></span>contract.sol</div>"
            "  <div class='editorMeta'>Solidity &middot; UTF-8</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        contractCode = st.text_area(
            label="contract",
            placeholder=(
                "// SPDX-License-Identifier: MIT\n"
                "pragma solidity ^0.8.20;\n\n"
                "contract Example {\n\n"
                "    // Paste your Solidity source here\n\n"
                "}"
            ),
            height=420,
            key="contractInput",
            label_visibility="collapsed",
        )

        _, midCol, _ = st.columns([1, 2, 1])
        with midCol:
            st.markdown("<div class='runButtonWrap'>", unsafe_allow_html=True)
            scanClicked = st.button(
                "Run Analysis",
                key="runAnalysis",
                disabled=not envConfig.get("ready", False),
            )
            st.markdown("</div>", unsafe_allow_html=True)

    with rightCol:
        st.markdown("<div class='label'>Analysis Stack</div>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class='card' style='font-size:0.78rem;color:#6e7681;line-height:1.9'>
            <span style='color:#3fb950;font-weight:600'>Slither</span>
            &nbsp;&mdash;&nbsp;80+ Trail of Bits detectors<br>
            <span style='color:#58a6ff;font-weight:600'>Aderyn</span>
            &nbsp;&mdash;&nbsp;Cyfrin Rust-native analyzer<br>
            <span style='color:#c792ea;font-weight:600'>RAG Corpus</span>
            &nbsp;&mdash;&nbsp;SWC + DeFi patterns<br>
            <span style='color:#e3a832;font-weight:600'>Groq LLM</span>
            &nbsp;&mdash;&nbsp;llama-3.3-70b-versatile
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Load Sample Contract", key="loadSample"):
            st.session_state["triggerSampleLoad"] = True
            st.rerun()

        st.markdown(
            """
            <div class='card' style='font-size:0.73rem;color:#6e7681;line-height:1.7;
                border-color:rgba(248,81,73,0.18)'>
            <div style='color:#f85149;font-weight:600;font-size:0.76rem;margin-bottom:0.4rem'>
                Disclaimer
            </div>
            Automated analysis supplements but does not replace a professional manual audit.
            Never deploy to mainnet based solely on these findings.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Session scan history
        if "scanHistory" not in st.session_state:
            st.session_state.scanHistory = []

        if st.session_state.scanHistory:
            st.markdown(
                "<div class='label' style='margin-top:0.6rem'>Recent Scans</div>",
                unsafe_allow_html=True,
            )
            for entry in reversed(st.session_state.scanHistory[-4:]):
                st.markdown(
                    f"<div style='font-size:0.72rem;color:#6e7681;padding:0.28rem 0;"
                    f"border-bottom:1px solid rgba(255,255,255,0.05)'>"
                    f"<span style='color:#3d444d;font-family:JetBrains Mono,monospace'>"
                    f"{entry['time']}</span> &mdash; {entry['lines']} lines</div>",
                    unsafe_allow_html=True,
                )

    if scanClicked:
        if not contractCode or len(contractCode.strip()) < 20:
            st.error("Paste a valid Solidity contract before running analysis.")
        elif not groqApiKey:
            st.error("Enter your Groq API key in the sidebar to enable AI analysis.")
        else:
            from datetime import datetime
            st.session_state.scanHistory.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "lines": len(contractCode.splitlines()),
            })
            runScan(
                contractCode=contractCode,
                groqApiKey=groqApiKey,
                envConfig=envConfig,
                ragEngine=ragEngine,
            )


if __name__ == "__main__":
    main()
