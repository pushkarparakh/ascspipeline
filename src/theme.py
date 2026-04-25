import streamlit as st

SITE_NAME = "ASCSPipeline"
SITE_TAGLINE = "Smart Contract Security Platform"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── Tokens ── */
:root {
    --base:    #07090f;
    --surface: #0c1018;
    --raised:  #111622;
    --card:    #141b27;
    --border:  rgba(255,255,255,0.07);
    --border2: rgba(255,255,255,0.12);
    --green:   #3fb950;
    --blue:    #58a6ff;
    --orange:  #e3a832;
    --red:     #f85149;
    --purple:  #c792ea;
    --cyan:    #66c2cd;
    --text:    #e8edf5;
    --muted:   #6e7681;
    --dim:     #3d444d;
}

/* ── Reset ── */
*, *::before, *::after { box-sizing: border-box; }

/* ── Background — deep dark with radial mesh ── */
.stApp {
    background-color: var(--base) !important;
    background-image:
        radial-gradient(ellipse 80% 60% at 10% 0%,   rgba(63,185,80,0.04) 0%, transparent 60%),
        radial-gradient(ellipse 60% 50% at 90% 100%,  rgba(88,166,255,0.04) 0%, transparent 60%),
        radial-gradient(ellipse 50% 40% at 70% 20%,   rgba(199,146,234,0.03) 0%, transparent 50%);
    font-family: 'Inter', sans-serif;
    color: var(--text);
}

/* Subtle grid overlay */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(255,255,255,0.012) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.012) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
}

.block-container {
    padding: 1.5rem 2.5rem 5rem !important;
    max-width: 1120px !important;
    position: relative;
    z-index: 1;
}

/* ── Hide all Streamlit chrome ── */
#MainMenu, footer, header,
[data-testid="stDeployButton"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavItems"],
[data-testid="stSidebarNavSeparator"] { display: none !important; }

/* ── Custom scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--base); }
::-webkit-scrollbar-thumb { background: var(--dim); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }

/* ════════════════════════════════════════════════
   SIDEBAR
   ════════════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebarContent"] { padding: 0 !important; }

/* Sidebar wordmark area */
.sidebarBrand {
    padding: 1.4rem 1.2rem 1rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 0.6rem;
}
.sidebarBrandName {
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: -0.3px;
    background: linear-gradient(90deg, #3fb950, #58a6ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.sidebarBrandSub {
    font-size: 0.69rem;
    color: var(--muted);
    margin-top: 0.1rem;
    letter-spacing: 0.01em;
}

/* Nav section label */
.navLabel {
    font-size: 0.63rem;
    font-weight: 600;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    padding: 0 1.2rem;
    margin-bottom: 0.25rem;
}

/* st.page_link nav items */
[data-testid="stPageLink"] {
    padding: 0 0.6rem;
}
[data-testid="stPageLink"] a,
[data-testid="stPageLink-NavLink"] {
    display: flex !important;
    align-items: center !important;
    gap: 0.5rem !important;
    padding: 0.5rem 0.65rem !important;
    border-radius: 7px !important;
    font-size: 0.83rem !important;
    font-weight: 500 !important;
    color: var(--muted) !important;
    text-decoration: none !important;
    transition: all 0.14s ease !important;
    border: 1px solid transparent !important;
    background: transparent !important;
    margin-bottom: 0.1rem !important;
}
[data-testid="stPageLink"] a:hover,
[data-testid="stPageLink-NavLink"]:hover {
    background: rgba(255,255,255,0.04) !important;
    color: var(--text) !important;
    border-color: var(--border) !important;
}
[data-testid="stPageLink"] a[aria-current="page"],
[data-testid="stPageLink-NavLink"][aria-current="page"] {
    background: rgba(63,185,80,0.1) !important;
    color: #3fb950 !important;
    border-color: rgba(63,185,80,0.2) !important;
    font-weight: 600 !important;
}

/* Sidebar text input */
[data-testid="stSidebar"] input {
    background: var(--base) !important;
    border: 1px solid var(--border2) !important;
    border-radius: 7px !important;
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
    padding: 0.5rem 0.75rem !important;
    transition: border-color 0.15s !important;
}
[data-testid="stSidebar"] input:focus {
    border-color: rgba(88,166,255,0.4) !important;
    box-shadow: 0 0 0 3px rgba(88,166,255,0.07) !important;
    outline: none !important;
}
[data-testid="stSidebar"] label {
    color: var(--muted) !important;
    font-size: 0.75rem !important;
}

/* Status section divider */
.sidebarDivider {
    height: 1px;
    background: var(--border);
    margin: 0.8rem 1.2rem;
}

/* Status rows */
.statusRow {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.4rem 1.2rem;
    transition: background 0.12s;
}
.statusRow:hover { background: rgba(255,255,255,0.02); border-radius: 6px; }
.statusRowLabel { font-size: 0.8rem; font-weight: 500; color: var(--text); }
.statusRowSub   { font-size: 0.68rem; color: var(--muted); }

/* Pulsing status dot */
@keyframes pulseGreen {
    0%, 100% { box-shadow: 0 0 0 0 rgba(63,185,80,0.4); }
    50%       { box-shadow: 0 0 0 4px rgba(63,185,80,0); }
}
.dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
}
.dot.on {
    background: var(--green);
    animation: pulseGreen 2.5s ease-in-out infinite;
}
.dot.off { background: var(--orange); opacity: 0.7; }

/* ════════════════════════════════════════════════
   HERO
   ════════════════════════════════════════════════ */
.hero {
    position: relative;
    overflow: hidden;
    background: linear-gradient(135deg, #0c1a14 0%, #0f1c2c 50%, #120d1e 100%);
    border: 1px solid var(--border2);
    border-radius: 14px;
    padding: 2.4rem 3rem;
    margin-bottom: 2rem;
}
.hero::before {
    content: '';
    position: absolute;
    inset: 0;
    background:
        radial-gradient(ellipse 60% 80% at 0% 50%, rgba(63,185,80,0.07) 0%, transparent 60%),
        radial-gradient(ellipse 50% 70% at 100% 50%, rgba(88,166,255,0.06) 0%, transparent 60%);
    pointer-events: none;
}
.hero::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(63,185,80,0.3), rgba(88,166,255,0.3), transparent);
}

@keyframes gradientFlow {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
.heroTitle {
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    background: linear-gradient(90deg, #3fb950, #58a6ff, #c792ea, #3fb950);
    background-size: 300% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: gradientFlow 8s ease infinite;
    margin: 0 0 0.35rem;
    position: relative;
}
.heroSub {
    color: var(--muted);
    font-size: 0.88rem;
    font-weight: 400;
    margin: 0 0 1.2rem;
    position: relative;
}
.tagRow { display: flex; gap: 0.4rem; flex-wrap: wrap; position: relative; }
.tag {
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--border2);
    border-radius: 5px;
    padding: 0.18rem 0.6rem;
    font-size: 0.68rem;
    font-weight: 600;
    color: var(--muted);
    letter-spacing: 0.05em;
    text-transform: uppercase;
    transition: all 0.15s;
}
.tag:hover { background: rgba(255,255,255,0.07); color: var(--text); }
.tag.g { border-color: rgba(63,185,80,0.3);   color: #3fb950; background: rgba(63,185,80,0.06); }
.tag.b { border-color: rgba(88,166,255,0.3);  color: #58a6ff; background: rgba(88,166,255,0.06); }
.tag.o { border-color: rgba(227,168,50,0.3);  color: #e3a832; background: rgba(227,168,50,0.06); }
.tag.p { border-color: rgba(199,146,234,0.3); color: #c792ea; background: rgba(199,146,234,0.06); }

/* ════════════════════════════════════════════════
   EDITOR PANEL
   ════════════════════════════════════════════════ */
/* VS Code-style editor header */
.editorHeader {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--raised);
    border: 1px solid var(--border2);
    border-bottom: none;
    border-radius: 10px 10px 0 0;
    padding: 0.55rem 1rem;
}
.editorTab {
    font-size: 0.75rem;
    font-weight: 500;
    color: #3fb950;
    font-family: 'JetBrains Mono', monospace;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}
.editorTabDot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #3fb950;
    display: inline-block;
}
.editorMeta {
    font-size: 0.68rem;
    color: var(--muted);
    font-family: 'JetBrains Mono', monospace;
}

/* Textarea — this targets Streamlit's structure */
.stTextArea {
    margin-top: 0 !important;
}
.stTextArea > div {
    border-radius: 0 0 10px 10px !important;
}
.stTextArea textarea {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important;
    background: #060a10 !important;
    border: 1px solid var(--border2) !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
    color: #abb2bf !important;
    line-height: 1.75 !important;
    caret-color: #3fb950 !important;
    padding: 1rem 1.2rem !important;
    resize: none !important;
}
.stTextArea textarea:focus {
    border-color: rgba(63,185,80,0.3) !important;
    box-shadow: 0 0 0 3px rgba(63,185,80,0.06), inset 0 0 60px rgba(0,0,0,0.2) !important;
    outline: none !important;
}
.stTextArea textarea::placeholder {
    color: rgba(110,118,129,0.5) !important;
}

/* ════════════════════════════════════════════════
   CARDS
   ════════════════════════════════════════════════ */
.card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.3rem;
    margin-bottom: 0.9rem;
    transition: border-color 0.2s, box-shadow 0.2s;
    position: relative;
    overflow: hidden;
}
.card::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: inherit;
    background: linear-gradient(135deg, rgba(255,255,255,0.02) 0%, transparent 60%);
    pointer-events: none;
}
.card:hover {
    border-color: rgba(88,166,255,0.2);
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
}

/* Section label */
.label {
    font-size: 0.67rem;
    font-weight: 700;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.65rem;
}

/* ════════════════════════════════════════════════
   BUTTONS
   ════════════════════════════════════════════════ */
.stButton > button {
    background: linear-gradient(135deg, #1a6b2a 0%, #2ea043 50%, #1e7b30 100%) !important;
    background-size: 200% auto !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.03em !important;
    padding: 0.6rem 2rem !important;
    width: 100% !important;
    box-shadow:
        0 0 20px rgba(63,185,80,0.15),
        inset 0 1px 0 rgba(255,255,255,0.1),
        inset 0 -1px 0 rgba(0,0,0,0.15) !important;
    transition: all 0.25s ease !important;
    position: relative;
    overflow: hidden;
}
.stButton > button::before {
    content: '';
    position: absolute;
    top: 0; left: -100%;
    width: 100%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
    transition: left 0.4s ease;
}
.stButton > button:hover {
    background-position: right center !important;
    box-shadow:
        0 0 35px rgba(63,185,80,0.28),
        0 4px 20px rgba(0,0,0,0.35),
        inset 0 1px 0 rgba(255,255,255,0.15) !important;
    transform: translateY(-2px) !important;
}
.stButton > button:hover::before {
    left: 100%;
}
.stButton > button:active {
    transform: translateY(0) !important;
    box-shadow: 0 0 15px rgba(63,185,80,0.18) !important;
}

/* Run button — special full-row glow */
.runButtonWrap {
    position: relative;
    margin-top: 0.8rem;
}
.runButtonWrap::before {
    content: '';
    position: absolute;
    inset: -1px;
    border-radius: 9px;
    background: linear-gradient(90deg, rgba(63,185,80,0.4), rgba(88,166,255,0.3), rgba(63,185,80,0.4));
    background-size: 200% auto;
    animation: gradientFlow 4s linear infinite;
    z-index: 0;
    filter: blur(4px);
    opacity: 0.6;
}

/* ════════════════════════════════════════════════
   REPORT
   ════════════════════════════════════════════════ */
.report {
    background: linear-gradient(135deg, var(--surface) 0%, var(--raised) 100%);
    border: 1px solid var(--border2);
    border-radius: 12px;
    padding: 2rem 2.4rem;
    margin-top: 1.2rem;
    box-shadow: 0 8px 40px rgba(0,0,0,0.4);
}
.report h1 {
    background: linear-gradient(90deg, var(--blue), var(--purple));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 1.4rem !important;
    font-weight: 700 !important;
}
.report h2 {
    color: var(--text) !important;
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.4rem;
    margin-top: 1.5rem !important;
}
.report h3 {
    color: var(--orange) !important;
    font-size: 0.93rem !important;
    font-weight: 600 !important;
}
.report table { width: 100%; border-collapse: collapse; }
.report th {
    background: rgba(255,255,255,0.03);
    color: var(--muted);
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 0.5rem 0.8rem;
    border: 1px solid var(--border);
}
.report td {
    padding: 0.45rem 0.8rem;
    border: 1px solid var(--border);
    font-size: 0.84rem;
    color: var(--text);
}
.report code {
    background: rgba(0,0,0,0.35);
    border: 1px solid var(--border2);
    border-radius: 4px;
    padding: 0.1rem 0.4rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82em;
    color: #e6c07b;
}
.report pre {
    background: #060a10;
    border: 1px solid var(--border2);
    border-radius: 8px;
    padding: 1.1rem;
}
.report pre code {
    background: none;
    border: none;
    padding: 0;
    color: #abb2bf;
}

/* ════════════════════════════════════════════════
   DOCS / ABOUT LAYOUT COMPONENTS
   ════════════════════════════════════════════════ */
.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.07) 20%, rgba(255,255,255,0.07) 80%, transparent);
    margin: 2.4rem 0;
}

.flowGrid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin: 1.2rem 0;
}
.flowStep {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 9px;
    padding: 1.1rem;
    transition: transform 0.15s, box-shadow 0.15s;
}
.flowStep:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.3); }
.stepNum  { font-size: 0.62rem; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.4rem; }
.stepTitle{ font-size: 0.88rem; font-weight: 600; color: var(--text); margin-bottom: 0.3rem; }
.stepDesc { font-size: 0.76rem; color: var(--muted); line-height: 1.55; }
.flowStep.s1 { border-top: 2px solid var(--green);  }
.flowStep.s2 { border-top: 2px solid var(--blue);   }
.flowStep.s3 { border-top: 2px solid var(--purple); }
.flowStep.s4 { border-top: 2px solid var(--orange); }

.techGrid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
    margin: 1.2rem 0;
}
.techCard {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 9px;
    padding: 1.2rem;
    transition: border-color 0.15s;
}
.techCard:hover { border-color: var(--border2); }
.tcName { font-size: 0.88rem; font-weight: 600; color: var(--text); margin-bottom: 0.3rem; }
.tcDesc { font-size: 0.77rem; color: var(--muted); line-height: 1.6; }

.lifecycleGrid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin: 1.2rem 0;
}
.lcCard {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 9px;
    padding: 1.3rem;
    transition: transform 0.15s, box-shadow 0.15s;
}
.lcCard:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.3); }
.lcPhase { font-size: 0.62rem; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.45rem; }
.lcTitle { font-size: 0.93rem; font-weight: 600; color: var(--text); margin-bottom: 0.5rem; }
.lcBody  { font-size: 0.78rem; color: var(--muted); line-height: 1.65; }

/* ════════════════════════════════════════════════
   MISC OVERRIDES
   ════════════════════════════════════════════════ */
.stSpinner > div {
    border-color: var(--green) transparent transparent transparent !important;
}
.stAlert {
    border-radius: 8px !important;
    font-size: 0.83rem !important;
}
/* Expander */
[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    background: var(--card) !important;
}
[data-testid="stExpanderToggleIcon"] { color: var(--muted) !important; }
/* Code block */
[data-testid="stCodeBlock"] {
    background: #060a10 !important;
    border: 1px solid var(--border2) !important;
    border-radius: 8px !important;
    font-size: 0.8rem !important;
}
/* Download button — style as secondary */
[data-testid="stDownloadButton"] button {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid var(--border2) !important;
    color: var(--text) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    border-radius: 7px !important;
    box-shadow: none !important;
    transition: all 0.15s !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: rgba(255,255,255,0.07) !important;
    border-color: rgba(88,166,255,0.3) !important;
    transform: none !important;
}
</style>
"""


def applyTheme():
    st.markdown(CSS, unsafe_allow_html=True)


def renderNav(activePage: str = "scanner"):
    with st.sidebar:
        st.markdown(
            f"<div class='sidebarBrand'>"
            f"<div class='sidebarBrandName'>{SITE_NAME}</div>"
            f"<div class='sidebarBrandSub'>{SITE_TAGLINE}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div class='navLabel'>Navigation</div>", unsafe_allow_html=True)
        st.page_link("app.py",          label="Scanner")
        st.page_link("pages/docs.py",   label="Documentation")
        st.page_link("pages/about.py",  label="About")
        st.markdown("<div class='sidebarDivider'></div>", unsafe_allow_html=True)
