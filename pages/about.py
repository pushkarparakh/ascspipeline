import streamlit as st

st.set_page_config(
    page_title="ASCSPipeline — About",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "ASCSPipeline v1.0 — Smart Contract Security Platform"},
)

from src.theme import applyTheme, renderNav

applyTheme()
renderNav("about")


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
        <div class="heroTitle">About ASCSPipeline</div>
        <p class="heroSub">
            Complete lifecycle security for on-chain systems &mdash;
            from development through post-deployment.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ── Mission ────────────────────────────────────────────────────────────────────

st.markdown("## Mission")
st.markdown(
    """
    <div class="card" style="font-size:0.95rem;color:#c9d1d9;line-height:1.8;
        border-left:3px solid #3fb950;border-radius:0 10px 10px 0">
    ASCSPipeline exists to close the window between code deployment and exploit.
    By combining deterministic static analysis with context-aware AI reasoning,
    we give builders the audit-grade intelligence they need at development speed
    &mdash; not after the damage is done.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div style="font-size:0.88rem;color:#8b949e;line-height:1.8;margin-top:1.2rem;
        max-width:820px">
    Smart contract exploits are not random events. They are the predictable outcome
    of known vulnerability classes that reach production undetected. The tools to find
    these flaws have existed for years &mdash; Slither, Aderyn, and the SWC registry
    are industry standards. What has been missing is a cohesive system that combines
    their deterministic output with the reasoning capacity needed to triage findings,
    eliminate noise, and communicate risk in terms developers can act on immediately.
    That is what this platform provides.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)


# ── Security Lifecycle ─────────────────────────────────────────────────────────

st.markdown("## The Security Lifecycle")
st.markdown(
    "ASCSPipeline is designed to integrate at every phase of a contract's lifecycle, "
    "not just as a pre-deployment checkpoint."
)

st.markdown(
    """
    <div class="lifecycleGrid">
        <div class="lcCard" style="border-top:2px solid #3fb950">
            <div class="lcPhase">Phase 1</div>
            <div class="lcTitle">Development</div>
            <div class="lcBody">
                Run ASCSPipeline on each iteration of your contract as you write it.
                Slither and Aderyn catch structural flaws early, when fixing them costs
                minutes rather than millions. Integrate into your CI pipeline via the
                Slither GitHub Action for continuous coverage.
            </div>
        </div>
        <div class="lcCard" style="border-top:2px solid #58a6ff">
            <div class="lcPhase">Phase 2</div>
            <div class="lcTitle">Audit Preparation</div>
            <div class="lcBody">
                Before engaging a professional audit firm, run a full ASCSPipeline scan.
                The AI report surfaces all high and critical findings your team should
                remediate first. Arriving at an audit with known issues pre-fixed
                accelerates the audit and reduces its cost.
            </div>
        </div>
        <div class="lcCard" style="border-top:2px solid #bc8cff">
            <div class="lcPhase">Phase 3</div>
            <div class="lcTitle">Post-Deployment</div>
            <div class="lcBody">
                Re-scan after every upgrade, parameter change, or dependency update.
                On-chain systems evolve. Each change introduces a new attack surface.
                A post-deployment scan validates that remediations held and that no
                new issues were introduced by the most recent change.
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)


# ── Technology Stack ───────────────────────────────────────────────────────────

st.markdown("## Technology Stack")

st.markdown(
    """
    <div class="techGrid">
        <div class="techCard" style="border-left:2px solid #3fb950">
            <div class="tcName">Slither</div>
            <div class="tcDesc">
                Trail of Bits' battle-tested Python static analyzer. 80+ built-in
                detectors covering reentrancy, access control, arithmetic, and more.
                The most widely deployed Solidity analysis tool in professional audits.
            </div>
        </div>
        <div class="techCard" style="border-left:2px solid #58a6ff">
            <div class="tcName">Aderyn</div>
            <div class="tcDesc">
                Cyfrin's Rust-native static analyzer. Zero interpreter overhead,
                purpose-built for Foundry project structures. Complements Slither
                with a distinct detection approach and independent finding set.
            </div>
        </div>
        <div class="techCard" style="border-left:2px solid #d29922">
            <div class="tcName">Groq AI — llama-3.3-70b-versatile</div>
            <div class="tcDesc">
                Sub-second inference on a 70-billion parameter model. The SecurityAuditor
                system prompt constrains the model to produce only evidenced, actionable
                findings — preventing hallucination and enforcing audit-grade output discipline.
            </div>
        </div>
        <div class="techCard" style="border-left:2px solid #bc8cff">
            <div class="tcName">RAG Corpus — scikit-learn TF-IDF</div>
            <div class="tcDesc">
                16 vulnerability entries from the SWC registry and DeFi attack pattern
                library, retrieved at query-time via cosine similarity. Fully deterministic,
                zero cold-start latency, no GPU required. Grounded output, not hallucinated.
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)


# ── Responsible Use ────────────────────────────────────────────────────────────

st.markdown("## Responsible Use")
st.markdown(
    """
    <div class="card" style="font-size:0.84rem;color:#8b949e;line-height:1.8;
        border-color:rgba(248,81,73,0.2)">
    <div style="color:#e6edf3;font-weight:600;margin-bottom:0.7rem;font-size:0.9rem">
        Automated analysis is a starting point, not a conclusion.
    </div>
    ASCSPipeline is a powerful supplementary tool. It is not a substitute for a
    professional manual audit by a specialized security firm. Automated static
    analysis cannot reason about complex multi-contract interactions, economic
    attack vectors that require protocol-level understanding, or novel vulnerability
    classes not yet represented in any detector suite.<br><br>
    Before deploying any contract that holds significant value on mainnet, engage
    a professional audit. The following firms are industry leaders:
    </div>
    """,
    unsafe_allow_html=True,
)

auditCol1, auditCol2, auditCol3 = st.columns(3, gap="medium")

with auditCol1:
    st.markdown(
        """
        <div class="card" style="text-align:center;padding:1.2rem">
        <div style="font-size:0.88rem;font-weight:600;color:#e6edf3;margin-bottom:0.3rem">
            Cyfrin
        </div>
        <div style="font-size:0.74rem;color:#8b949e">cyfrin.io</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with auditCol2:
    st.markdown(
        """
        <div class="card" style="text-align:center;padding:1.2rem">
        <div style="font-size:0.88rem;font-weight:600;color:#e6edf3;margin-bottom:0.3rem">
            Trail of Bits
        </div>
        <div style="font-size:0.74rem;color:#8b949e">trailofbits.com</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with auditCol3:
    st.markdown(
        """
        <div class="card" style="text-align:center;padding:1.2rem">
        <div style="font-size:0.88rem;font-weight:600;color:#e6edf3;margin-bottom:0.3rem">
            Code4rena
        </div>
        <div style="font-size:0.74rem;color:#8b949e">code4rena.com</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
