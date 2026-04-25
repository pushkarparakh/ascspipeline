import streamlit as st

st.set_page_config(
    page_title="ASCSPipeline — Documentation",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "ASCSPipeline v1.0 — Smart Contract Security Platform"},
)

from src.theme import applyTheme, renderNav

applyTheme()
renderNav("docs")


RAG_CORPUS = [
    ("SWC-101", "Integer Overflow / Underflow",           "Arithmetic wrap-around in Solidity < 0.8.0"),
    ("SWC-107", "Reentrancy",                             "External call before state update enables recursive drain"),
    ("SWC-105", "Unprotected Ether Withdrawal",           "Missing access control on fund-sending functions"),
    ("SWC-106", "Unprotected SELFDESTRUCT",               "Any caller can destroy the contract and seize Ether"),
    ("SWC-108", "State Variable Default Visibility",      "Implicit internal visibility leads to unintended exposure"),
    ("SWC-110", "Assert Violation",                       "assert() consuming all gas on reachable failure paths"),
    ("SWC-113", "DoS via Failed Call",                    "Loop over array of addresses can be permanently blocked"),
    ("SWC-115", "tx.origin Authorization",                "Phishing bypass via intermediate contract caller"),
    ("SWC-116", "Block Timestamp Manipulation",           "Miner influence on timestamp-dependent logic"),
    ("SWC-120", "Weak On-Chain Randomness",               "block.number / blockhash are predictable by miners"),
    ("SWC-114", "ERC-20 Approve Race Condition",          "Front-running allowance changes"),
    ("DeFi-01", "Flash Loan Attack",                      "Uncollateralized capital used for oracle manipulation"),
    ("DeFi-02", "Price Oracle Manipulation",              "AMM spot price used as trusted price feed"),
    ("DeFi-03", "Missing Access Control",                 "Admin functions callable by any EOA"),
    ("DeFi-04", "Uninitialized Proxy",                    "Implementation contract callable directly pre-init"),
    ("DeFi-05", "Unbounded Loop / Gas Limit DoS",         "Array growth causes block gas limit breach"),
]

SLITHER_EXCLUSIONS = [
    ("naming-convention", "Stylistic — no security relevance"),
    ("solc-version",      "Informational — suppressed unless pragma is critically old"),
    ("pragma",            "Informational — redundant with solc-version"),
]


with st.sidebar:
    st.markdown(
        "<div style='font-size:0.7rem;color:#8b949e;margin-top:1rem;line-height:1.7'>"
        "Pipeline v1.0.0<br>"
        "Slither &middot; Aderyn &middot; Groq &middot; scikit-learn"
        "</div>",
        unsafe_allow_html=True,
    )


st.markdown(
    """
    <div class="hero">
        <div class="heroTitle">Documentation</div>
        <p class="heroSub">
            Pipeline architecture, tool reference, knowledge base corpus,
            and false-positive mitigation strategy.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ── Pipeline Architecture ──────────────────────────────────────────────────────

st.markdown("## Pipeline Architecture")
st.markdown(
    "Each scan executes four deterministic stages in sequence. "
    "The first two stages produce raw, noisy tool output. "
    "Stages three and four convert that output into an actionable, "
    "false-positive-filtered security report."
)

st.markdown(
    """
    <div class="flowGrid">
        <div class="flowStep s1">
            <div class="stepNum">Stage 1</div>
            <div class="stepTitle">Static Analysis</div>
            <div class="stepDesc">
                Slither and Aderyn run as subprocesses against the uploaded
                <code>.sol</code> file. Output is captured as structured JSON.
            </div>
        </div>
        <div class="flowStep s2">
            <div class="stepNum">Stage 2</div>
            <div class="stepTitle">Knowledge Retrieval</div>
            <div class="stepDesc">
                TF-IDF cosine similarity retrieves the top-4 most relevant
                vulnerability entries from the SWC + DeFi corpus.
            </div>
        </div>
        <div class="flowStep s3">
            <div class="stepNum">Stage 3</div>
            <div class="stepTitle">AI Synthesis</div>
            <div class="stepDesc">
                Groq LLM receives contract source, tool output, and RAG context.
                The SecurityAuditor persona triages findings and suppresses false positives.
            </div>
        </div>
        <div class="flowStep s4">
            <div class="stepNum">Stage 4</div>
            <div class="stepTitle">Report Generation</div>
            <div class="stepDesc">
                A structured Markdown report is assembled with severity, exploit
                scenario, and secure code fix for each confirmed finding.
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)


# ── Tool Reference ─────────────────────────────────────────────────────────────

st.markdown("## Tool Reference")

col1, col2 = st.columns(2, gap="medium")

with col1:
    st.markdown(
        """
        <div class="card">
        <div style="font-size:0.95rem;font-weight:700;color:#3fb950;margin-bottom:0.6rem">
            Slither
        </div>
        <div style="font-size:0.79rem;color:#8b949e;line-height:1.7">
            <b style="color:#e6edf3">Developer:</b> Trail of Bits<br>
            <b style="color:#e6edf3">Language:</b> Python, runs on any platform<br>
            <b style="color:#e6edf3">Detectors:</b> 80+ vulnerability patterns<br>
            <b style="color:#e6edf3">Invocation:</b>
            <code>slither &lt;file.sol&gt; --solc &lt;path&gt; --json &lt;out&gt;</code><br><br>
            <b style="color:#e6edf3">Exit codes</b><br>
            <code>0</code> — No findings<br>
            <code>1</code> — Findings present (not an error)<br>
            <code>255</code> — Compilation failure<br><br>
            <b style="color:#e6edf3">Solc management</b><br>
            Solidity compiler is provisioned at runtime via
            <code>py-solc-x</code>. No system-level apt installation required.
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="card">
        <div style="font-size:0.95rem;font-weight:700;color:#58a6ff;margin-bottom:0.6rem">
            Aderyn
        </div>
        <div style="font-size:0.79rem;color:#8b949e;line-height:1.7">
            <b style="color:#e6edf3">Developer:</b> Cyfrin<br>
            <b style="color:#e6edf3">Language:</b> Rust — zero interpreter overhead<br>
            <b style="color:#e6edf3">Mode:</b> Foundry project analysis<br>
            <b style="color:#e6edf3">Invocation:</b>
            <code>aderyn &lt;project/&gt; --output &lt;report.json&gt;</code><br><br>
            <b style="color:#e6edf3">Project scaffold</b><br>
            A minimal Foundry project is created in <code>/tmp/</code> around
            the uploaded contract. This satisfies Aderyn's project-structure requirement.<br><br>
            <b style="color:#e6edf3">Binary provisioning</b><br>
            The pre-built Linux x86_64 musl binary is downloaded from GitHub
            Releases at startup and cached for the session lifecycle.
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)


# ── RAG Knowledge Base ─────────────────────────────────────────────────────────

st.markdown("## RAG Knowledge Base")
st.markdown(
    "The retrieval corpus contains 16 entries covering the SWC registry and common DeFi attack patterns. "
    "At query time, TF-IDF with bigram features and cosine similarity selects the top-4 most relevant entries "
    "to include as grounding context in the Groq prompt. "
    "No neural embeddings or GPU are required — this keeps the deployment fully serverless and deterministic."
)

corpusRows = "".join(
    f"<tr><td><code>{entry[0]}</code></td><td>{entry[1]}</td><td style='color:#8b949e'>{entry[2]}</td></tr>"
    for entry in RAG_CORPUS
)
st.markdown(
    f"""
    <div class="report" style="padding:1rem">
    <table>
    <thead><tr>
        <th>ID</th><th>Vulnerability</th><th>Core Risk</th>
    </tr></thead>
    <tbody>{corpusRows}</tbody>
    </table>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)


# ── False Positive Mitigation ──────────────────────────────────────────────────

st.markdown("## False Positive Mitigation")
st.markdown(
    "Raw Slither output is verbose. Three filter layers ensure only actionable findings "
    "reach the LLM prompt."
)

st.markdown(
    """
    <div class="techGrid">
        <div class="techCard">
            <div class="tcName">Layer 1 — Detector Exclusion List</div>
            <div class="tcDesc">
                Certain Slither check identifiers are excluded before the output
                is passed downstream. These checks produce exclusively stylistic
                or informational output with no exploit relevance.
            </div>
        </div>
        <div class="techCard">
            <div class="tcName">Layer 2 — Confidence Threshold</div>
            <div class="tcDesc">
                Findings with <code>confidence = Low</code> and
                <code>impact &le; Low</code> are suppressed. Only Medium or higher
                confidence findings at Low impact and above are forwarded.
            </div>
        </div>
        <div class="techCard">
            <div class="tcName">Layer 3 — LLM Triage</div>
            <div class="tcDesc">
                The SecurityAuditor system prompt explicitly instructs the model
                to suppress unactionable findings and never hallucinate issues
                not evidenced by the contract source or tool output.
            </div>
        </div>
        <div class="techCard">
            <div class="tcName">Finding Cap</div>
            <div class="tcDesc">
                Slither output is capped at 20 findings before prompt injection.
                This prevents token budget overflow and forces prioritization of
                the highest-severity items.
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

exclusionRows = "".join(
    f"<tr><td><code>{r[0]}</code></td><td style='color:#8b949e'>{r[1]}</td></tr>"
    for r in SLITHER_EXCLUSIONS
)
st.markdown(
    f"""
    <div class="report" style="padding:1rem;margin-top:0.8rem">
    <table>
    <thead><tr><th>Excluded Detector</th><th>Reason</th></tr></thead>
    <tbody>{exclusionRows}</tbody>
    </table>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)


# ── API Reference ──────────────────────────────────────────────────────────────

st.markdown("## API Reference")
st.markdown("The core audit function signature and Groq model parameters.")

st.code(
    '''\
# src/groqClient.py

def generateReport(
    apiKey:        str,   # Groq API key — never stored or logged
    contractCode:  str,   # Raw Solidity source (max 8000 chars sent to prompt)
    slitherOutput: str,   # Filtered Slither findings summary (max 3000 chars)
    aderynOutput:  str,   # Parsed Aderyn report (max 2000 chars)
    ragContext:    str,   # Top-4 RAG chunks (max 2000 chars)
    model: str = "llama-3.3-70b-versatile",
) -> str:
    ...

# Groq call parameters
{
    "model":       "llama-3.3-70b-versatile",
    "max_tokens":  4096,
    "temperature": 0.2,   # Low temperature for deterministic security output
}
''',
    language="python",
)

st.markdown(
    """
    <div class="card" style="font-size:0.79rem;color:#8b949e;line-height:1.7;margin-top:0">
    <b style="color:#e6edf3">System prompt persona:</b> SecurityAuditor<br>
    The model is instructed to behave as a senior smart contract auditor. It is
    explicitly told to never hallucinate findings, to triage tool output skeptically,
    and to prioritize findings that lead to loss of funds or privilege escalation above all else.
    The output format is enforced via prompt: Severity / SWC ID / Affected Code /
    Description / Exploit Scenario / Recommended Fix.
    </div>
    """,
    unsafe_allow_html=True,
)
