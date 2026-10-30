"""
app.py -- RF LINE DOCTOR Academic-Grade Streamlit Application.

Virtual Transmission-Line Fault Diagnosis, Fault Location, and Impedance-Matching
System Using Smith-Chart Analysis.

Adheres strictly to the frozen team interface contracts:
  - line_model
  - measurements
  - diagnosis
  - matching
  - fault_simulation
  - core algorithms and validation modules
"""

import os
import sys
import io
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import line_model as lm
import measurements as meas
import fault_simulation as fs
import diagnosis as diag
import matching as match
from core.signal_analysis import decompose_impedance, compute_spectral_features
from core.fault_location import locate_fault_dual_method, calculate_resolution_metrics
from core.diagnostic_explanations import generate_full_diagnostic_report
from validation.classification_metrics import (
    compute_confusion_matrix,
    compute_classification_report,
)
from validation.location_metrics import compute_location_metrics

# ── Streamlit Page Configuration ──────────────────────────────────────────────
st.set_page_config(
    page_title="RF Line Doctor — Transmission Line Diagnostics Lab",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom Engineering CSS Styling ───────────────────────────────────────────
st.markdown("""
<style>
:root {
    --rld-bg: #0b1220;
    --rld-sidebar: #0d1726;
    --rld-panel: #111d2e;
    --rld-panel-raised: #17263a;
    --rld-border: #26374d;
    --rld-text: #e8eef6;
    --rld-muted: #91a2b8;
    --rld-cyan: #35c6d5;
    --rld-green: #40c894;
    --rld-amber: #e9ad55;
}
html, body, [class*="css"], button, input, textarea, select {
    font-family: Inter, "Segoe UI", system-ui, sans-serif;
}
.stApp {
    background:
        radial-gradient(ellipse at 88% 0%, rgba(34, 105, 128, .12), transparent 32%),
        linear-gradient(145deg, #0b1220 0%, #0e1828 54%, #0b1422 100%);
    color: var(--rld-text);
}
[data-testid="stHeader"] {
    background: rgba(11, 18, 32, .72);
}
[data-testid="stMainBlockContainer"] {
    max-width: 1500px;
    padding: 2rem 2.4rem 3rem;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1726 0%, #0a1320 100%);
    border-right: 1px solid var(--rld-border);
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.25rem;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: var(--rld-text);
    letter-spacing: -.02em;
}
[data-testid="stSidebar"] hr {
    border-color: var(--rld-border);
    margin: 1rem 0;
}
h1, h2, h3, h4 {
    color: var(--rld-text);
    letter-spacing: -.035em;
    font-weight: 650;
}
h1 { font-size: 2rem; line-height: 1.18; }
h2 { font-size: 1.48rem; line-height: 1.25; }
h3 { font-size: 1.12rem; line-height: 1.35; }
p, li, label, [data-testid="stMarkdownContainer"] {
    color: var(--rld-text);
    line-height: 1.62;
}
.stCaption, [data-testid="stCaptionContainer"] {
    color: var(--rld-muted) !important;
    font-size: .82rem;
}
[data-testid="stSidebar"] label,
[data-testid="stWidgetLabel"] p {
    color: #c6d2e1 !important;
    font-size: .86rem;
    font-weight: 550;
}
[data-testid="stSidebar"] div[role="radiogroup"] {
    gap: .35rem;
}
[data-testid="stSidebar"] div[role="radiogroup"] label {
    border: 1px solid transparent;
    border-radius: 10px;
    padding: .45rem .65rem;
    transition: background .18s ease, border-color .18s ease;
}
[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: #17263a;
    border-color: #2b425b;
}
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    background: #172b40;
    border-color: #31536b;
}
input, textarea, [data-baseweb="select"] > div {
    background: #142236 !important;
    color: var(--rld-text) !important;
    border-color: #2b4058 !important;
    border-radius: 9px !important;
}
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea {
    color: var(--rld-text) !important;
}
[data-baseweb="select"] span {
    color: var(--rld-text) !important;
}
div[data-testid="stNumberInput"] button,
div[data-testid="stSelectbox"] button {
    color: var(--rld-muted) !important;
    border-color: #2b4058 !important;
}
[data-testid="stSlider"] [role="slider"] {
    border-color: var(--rld-cyan) !important;
    box-shadow: 0 0 0 3px rgba(53, 198, 213, .16);
}
[data-testid="stSlider"] [data-testid="stTickBar"] {
    background: #2b4058;
}
.stButton > button, .stDownloadButton > button {
    min-height: 2.55rem;
    border-radius: 9px;
    border: 1px solid #2a6171;
    background: linear-gradient(135deg, #176477, #17475d);
    color: #f2fbff;
    font-weight: 650;
    letter-spacing: .01em;
    transition: transform .16s ease, box-shadow .16s ease, filter .16s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    border-color: var(--rld-cyan);
    color: #ffffff;
    filter: brightness(1.12);
    box-shadow: 0 7px 22px rgba(21, 154, 174, .18);
    transform: translateY(-1px);
}
.stButton > button:focus, .stDownloadButton > button:focus {
    box-shadow: 0 0 0 3px rgba(53, 198, 213, .23);
}
div[data-testid="stMetric"] {
    background: linear-gradient(145deg, #142338, #101c2c);
    border: 1px solid var(--rld-border);
    border-radius: 12px;
    padding: 1rem 1.1rem;
    box-shadow: 0 8px 24px rgba(0,0,0,.14);
}
div[data-testid="stMetric"] label {
    color: var(--rld-muted) !important;
    font-size: .75rem;
    font-weight: 650;
    letter-spacing: .055em;
    text-transform: uppercase;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--rld-cyan);
    font-weight: 700;
    letter-spacing: -.035em;
}
.metric-card {
    background: linear-gradient(145deg, #17283d, #111e30);
    border: 1px solid #2a3d55;
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 12px;
    box-shadow: 0 8px 24px rgba(0,0,0,.16);
}
.metric-title {
    color: #9aacc1;
    font-size: .72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .075em;
}
.metric-value {
    color: var(--rld-cyan);
    font-size: 1.55rem;
    font-weight: 750;
    font-family: "SFMono-Regular", Consolas, monospace;
    letter-spacing: -.035em;
}
.status-badge-healthy {
    background: rgba(64,200,148,.14);
    color: #63dfae;
    padding: 5px 12px;
    border: 1px solid rgba(64,200,148,.28);
    border-radius: 999px;
    font-weight: 700;
}
.status-badge-mismatch {
    background: rgba(233,173,85,.13);
    color: #f3bd70;
    padding: 5px 12px;
    border: 1px solid rgba(233,173,85,.28);
    border-radius: 999px;
    font-weight: 700;
}
.status-badge-fault {
    background: rgba(232,91,96,.13);
    color: #ff8589;
    padding: 5px 12px;
    border: 1px solid rgba(232,91,96,.28);
    border-radius: 999px;
    font-weight: 700;
}
.stTabs [data-baseweb="tab-list"] {
    gap: .35rem;
    border-bottom: 1px solid var(--rld-border);
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 9px 9px 0 0;
    color: var(--rld-muted);
    padding: .7rem 1rem;
}
.stTabs [aria-selected="true"] {
    color: var(--rld-cyan) !important;
    border-bottom: 2px solid var(--rld-cyan) !important;
}
[data-testid="stAlert"] {
    border: 1px solid var(--rld-border);
    border-radius: 11px;
    background: #142338;
}
[data-testid="stDataFrame"], [data-testid="stTable"] {
    border: 1px solid var(--rld-border);
    border-radius: 10px;
    overflow: hidden;
}
[data-testid="stPlotlyChart"], [data-testid="stPyplot"], [data-testid="stImage"] {
    border: 1px solid rgba(55, 78, 105, .7);
    border-radius: 12px;
    overflow: hidden;
}
[data-testid="stExpander"] {
    border: 1px solid var(--rld-border);
    border-radius: 10px;
    background: rgba(17, 29, 46, .62);
}
[data-testid="stMarkdownContainer"] pre {
    border: 1px solid var(--rld-border);
    border-radius: 10px;
    background: #0b1523;
}
[data-testid="stMarkdownContainer"] code {
    color: #8fe6ed;
    background: rgba(53,198,213,.09);
    border-radius: 5px;
    padding: .08rem .28rem;
}
.katex, .katex * {
    color: #eaf4fb !important;
}
.katex-display {
    margin: 1rem 0 !important;
    padding: .85rem 1rem;
    overflow-x: auto;
    background: rgba(24, 43, 63, .72);
    border: 1px solid #2a4057;
    border-radius: 10px;
}
[data-testid="stMarkdownContainer"] blockquote {
    border-left: 3px solid var(--rld-cyan);
    background: rgba(53,198,213,.06);
    padding: .55rem 1rem;
    border-radius: 0 9px 9px 0;
}
hr {
    border-color: var(--rld-border) !important;
}
*:focus-visible {
    outline: 2px solid rgba(53,198,213,.8) !important;
    outline-offset: 2px;
}
@media (max-width: 900px) {
    [data-testid="stMainBlockContainer"] { padding: 1.2rem 1rem 2rem; }
    h1 { font-size: 1.65rem; }
    div[data-testid="stMetric"] { padding: .8rem; }
}
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { transition: none !important; animation: none !important; }
}
</style>
""", unsafe_allow_html=True)

# Presentational styling for Matplotlib figures; calculation and data pipelines are unchanged.
plt.rcParams.update({
    "figure.facecolor": "#111d2e",
    "axes.facecolor": "#111d2e",
    "savefig.facecolor": "#111d2e",
    "text.color": "#e8eef6",
    "axes.labelcolor": "#c2cfdd",
    "xtick.color": "#a9b8ca",
    "ytick.color": "#a9b8ca",
    "axes.edgecolor": "#354961",
    "grid.color": "#2b3d54",
    "legend.facecolor": "#17263a",
    "legend.edgecolor": "#354961",
})
# ── Application Header ────────────────────────────────────────────────────────
st.title("📡 RF LINE DOCTOR")
st.markdown(
    "**Virtual Transmission-Line Fault Diagnosis, Fault Location & Impedance Matching System**  \n"
    "*EC-3104 Microwave Engineering Laboratory Virtual Prototype | Lossless Core Model*"
)

# ── Navigation Selector ───────────────────────────────────────────────────────
nav_section = st.sidebar.radio(
    "Navigation Menu",
    [
        "1. Overview & System Status",
        "2. Transmission-Line Simulator",
        "3. Signal Analysis & Smith Chart",
        "4. Fault Diagnosis Engine",
        "5. Fault Location (TDR & Phase)",
        "6. Quarter-Wave Matching Studio",
        "7. Independent Validation Lab",
    ],
    index=1,
)

# ── Sidebar: Common Simulation Controls ───────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.header("⚙️ Transmission Line Parameters")

Z0 = st.sidebar.number_input(
    "Characteristic Impedance Z₀ (Ω)",
    min_value=1.0,
    max_value=1000.0,
    value=50.0,
    step=5.0,
    help="Reference line characteristic impedance (e.g., 50 Ω or 75 Ω)",
)

length = st.sidebar.number_input(
    "Physical Line Length (m)",
    min_value=0.05,
    max_value=100.0,
    value=1.0,
    step=0.1,
    help="Physical end-to-end cable length in metres",
)

vf = st.sidebar.slider(
    "Velocity Factor (vf)",
    min_value=0.1,
    max_value=1.0,
    value=0.66,
    step=0.01,
    help="vₚ = vf × c₀. Typical: solid PE coax = 0.66, PTFE = 0.70, air = 1.0",
)

st.sidebar.subheader("📶 Frequency Sweep Range")
col_sf1, col_sf2 = st.sidebar.columns(2)
with col_sf1:
    f_start_mhz = st.number_input("fₘᵢₙ (MHz)", min_value=1.0, max_value=50000.0, value=500.0, step=50.0)
with col_sf2:
    f_stop_mhz = st.number_input("fₘₐₓ (MHz)", min_value=5.0, max_value=50000.0, value=4000.0, step=100.0)

if f_start_mhz >= f_stop_mhz:
    st.sidebar.error("f_start must be strictly less than f_stop")
    st.stop()

n_pts = st.sidebar.slider("Number of Points", min_value=50, max_value=1000, value=400, step=50)
freqs = np.linspace(f_start_mhz * 1e6, f_stop_mhz * 1e6, n_pts)

st.sidebar.subheader("⚡ Fault Injection & Termination")
scenario_preset = st.sidebar.selectbox(
    "Fault Preset Scenario",
    [
        "Case 1: Healthy Matched (ZL = Z0)",
        "Case 2: Resistive mismatch (Zₗ = Rₗ ≠ Z₀)",
        "Case 3: Open circuit (Zₗ = ∞)",
        "Case 4: Short circuit (Zₗ = 0)",
        "Case 5: Series inductive discontinuity (L)",
        "Case 6: Shunt capacitive discontinuity (C)",
        "Custom: Complex load (R + jX)",
    ],
    index=1,
)

# Parse scenario parameters
sim_scenario = "healthy"
ZL_val = complex(Z0)
fault_pos = float(length / 2.0)
L_val = 15e-9
C_val = 15e-12

if "Case 1" in scenario_preset:
    sim_scenario = "healthy"
    ZL_val = complex(Z0)
elif "Case 2" in scenario_preset:
    sim_scenario = "mismatch"
    RL_input = st.sidebar.number_input("Load Resistance RL (Ω)", min_value=1.0, max_value=2000.0, value=120.0, step=5.0)
    ZL_val = complex(RL_input)
elif "Case 3" in scenario_preset:
    sim_scenario = "open"
    ZL_val = lm.OPEN
elif "Case 4" in scenario_preset:
    sim_scenario = "short"
    ZL_val = 0.0 + 0j
elif "Case 5" in scenario_preset:
    sim_scenario = "series_L"
    L_nh = st.sidebar.number_input("Discontinuity Inductance L (nH)", min_value=0.5, max_value=200.0, value=15.0, step=1.0)
    L_val = L_nh * 1e-9
    fault_pos = st.sidebar.slider("Discontinuity Position (m)", min_value=0.01, max_value=float(length), value=float(length * 0.4), step=0.01)
elif "Case 6" in scenario_preset:
    sim_scenario = "shunt_C"
    C_pf = st.sidebar.number_input("Discontinuity Capacitance C (pF)", min_value=0.5, max_value=200.0, value=15.0, step=1.0)
    C_val = C_pf * 1e-12
    fault_pos = st.sidebar.slider("Discontinuity Position (m)", min_value=0.01, max_value=float(length), value=float(length * 0.6), step=0.01)
else:
    sim_scenario = "custom"
    c_r = st.sidebar.number_input("Load Resistance R (Ω)", min_value=0.0, max_value=2000.0, value=75.0, step=5.0)
    c_x = st.sidebar.number_input("Load Reactance X (Ω)", min_value=-2000.0, max_value=2000.0, value=35.0, step=5.0)
    ZL_val = complex(c_r, c_x)

noise_std = st.sidebar.slider(
    "Measurement Noise (σ on S₁₁)",
    min_value=0.0,
    max_value=0.15,
    value=0.0,
    step=0.01,
    help="Complex Gaussian noise added to simulated S11",
)

# ── Execute Core Simulation & Inference Pipeline ─────────────────────────────
if sim_scenario in fs.FAULT_SCENARIOS:
    sim_out = fs.simulate_fault(
        sim_scenario,
        Z0,
        length,
        freqs,
        vf=vf,
        fault_pos=fault_pos,
        L_val=L_val,
        C_val=C_val,
        ZL_mismatch=ZL_val.real if np.isfinite(ZL_val.real) else 100.0,
        noise_std=noise_std,
    )
    sweep_dict = sim_out["sweep"]
else:
    sweep_dict = meas.sweep(Z0, ZL_val, length, freqs, vf=vf)
    if noise_std > 0.0:
        rng = np.random.default_rng(42)
        noise = rng.normal(0, noise_std / np.sqrt(2), len(freqs)) + \
                1j * rng.normal(0, noise_std / np.sqrt(2), len(freqs))
        g_ideal = sweep_dict["gamma"]
        g_noisy = g_ideal + noise
        # Unclipped noisy reflection: preserve values where |S11| > 1.0
        sweep_dict["gamma"] = g_noisy
        sweep_dict["vswr"] = meas.vswr(g_noisy)
        sweep_dict["rl_db"] = meas.return_loss_db(g_noisy)
        sweep_dict.gamma_ideal = g_ideal
        sweep_dict["rl_db"] = meas.return_loss_db(g_noisy)

# Inferred Diagnosis (Strictly Single-Port S11 Only)
inferred_class = diag.classify(sweep_dict, Z0)
loc_dual = locate_fault_dual_method(sweep_dict["gamma"], freqs, vf=vf, fault_class=inferred_class)
res_info = calculate_resolution_metrics(freqs, vf=vf)
diag_report = generate_full_diagnostic_report(inferred_class, Z0, vf=vf)

# Decompose impedances & spectral features
rin, xin = decompose_impedance(sweep_dict["zin"])
spectral_feat = compute_spectral_features(sweep_dict["gamma"], freqs)
f_ghz = freqs / 1e9

# ─────────────────────────────────────────────────────────────────────────────
# VIEW 1: OVERVIEW & SYSTEM STATUS
# ─────────────────────────────────────────────────────────────────────────────
if nav_section == "1. Overview & System Status":
    st.header("1. System Overview & Laboratory Status")

    st.markdown("""
    **RF LINE DOCTOR** is a comprehensive virtual laboratory for investigating transmission-line wave propagation,
    boundary reflections, structural discontinuities, single-port automated fault diagnosis, and impedance matching.
    """)

    # Top KPI Metrics Cards
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    with kpi_col1:
        st.markdown('<div class="metric-card"><div class="metric-title">Inferred Diagnosis</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{str(inferred_class).upper()}</div></div>', unsafe_allow_html=True)
    with kpi_col2:
        st.markdown('<div class="metric-card"><div class="metric-title">Internal Subtype</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{inferred_class.subtype}</div></div>', unsafe_allow_html=True)
    with kpi_col3:
        st.markdown('<div class="metric-card"><div class="metric-title">Fault Distance (TDR)</div>', unsafe_allow_html=True)
        d_disp = f"{loc_dual['dist_ifft_m']:.3f} m" if loc_dual['dist_ifft_m'] is not None else "N/A (Matched)"
        st.markdown(f'<div class="metric-value">{d_disp}</div></div>', unsafe_allow_html=True)
    with kpi_col4:
        st.markdown('<div class="metric-card"><div class="metric-title">Range Resolution</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{res_info["range_res_m"]*100:.2f} cm</div></div>', unsafe_allow_html=True)

    st.subheader("System Workflow")
    st.info("""
    **End-to-End Operational Pipeline:**  
    `USER PARAMETERS` ➔ `TRANSMISSION LINE MODEL (ABCD CASCADING)` ➔ `FREQUENCY SWEEP (|S11|, VSWR, RL)`  
    ➔ `SMITH-CHART LOCUS` ➔ `RULE-BASED CLASSIFIER` ➔ `IFFT TDR FAULT LOCALIZATION` ➔ `QUARTER-WAVE MATCHING STUDIO`
    """)

    st.subheader("Current Coaxial Line Configuration")
    col_ov1, col_ov2 = st.columns(2)
    with col_ov1:
        st.write(f"- **Characteristic Impedance (Z₀):** `{Z0:.1f} Ω`")
        st.write(f"- **Physical Length (l):** `{length:.2f} m`")
        st.write(f"- **Velocity Factor (vf):** `{vf:.2f}` ($v_p = {lm.phase_velocity(vf)/1e8:.2f} \\times 10^8$ m/s)")
    with col_ov2:
        st.write(f"- **Frequency Span:** `{f_start_mhz:.0f} MHz` to `{f_stop_mhz:.0f} MHz` ({len(freqs)} points)")
        st.write(f"- **Measurement Noise (σ):** `{noise_std:.2f}`")
        st.write(f"- **Theoretical Range Resolution (ΔR):** `{res_info['range_res_m']*100:.2f} cm`")

# ─────────────────────────────────────────────────────────────────────────────
# VIEW 2: TRANSMISSION-LINE SIMULATOR
# ─────────────────────────────────────────────────────────────────────────────
elif nav_section == "2. Transmission-Line Simulator":
    st.header("2. Transmission-Line Simulator")
    st.caption("Interactive multi-parameter transmission-line simulation and reflection generation.")

    col_sim1, col_sim2 = st.columns([3, 2])
    with col_sim1:
        st.subheader("Simulated Reflection Sweep Profile")
        fig_s, ax_s = plt.subplots(figsize=(8, 4))
        ax_s.plot(f_ghz, np.abs(sweep_dict["gamma"]), color="#00e5ff", lw=2, label="|S11| (Input Reflection)")
        ax_s.axhline(0.05, color="green", linestyle="--", alpha=0.6, label="Healthy Threshold (0.05)")
        ax_s.set_xlabel("Frequency (GHz)")
        ax_s.set_ylabel("|S11| Magnitude")
        ax_s.set_ylim(-0.05, 1.05)
        ax_s.grid(True, alpha=0.3)
        ax_s.legend(loc="upper right")
        st.pyplot(fig_s)
        plt.close(fig_s)

    with col_sim2:
        st.subheader("Simulation Ground Truth (Hidden from Classifier)")
        st.json({
            "injected_scenario": sim_scenario,
            "load_impedance": str(ZL_val),
            "physical_fault_position_m": fault_pos if sim_scenario in ["series_L", "shunt_C"] else (length if sim_scenario != "healthy" else None),
            "series_L_H": L_val if sim_scenario == "series_L" else None,
            "shunt_C_F": C_val if sim_scenario == "shunt_C" else None,
            "configured_vf": vf,
        })
        st.caption("Ground truth parameters are used strictly for simulation generation and validation benchmarking.")

    # Data export table
    st.subheader("Frequency Sweep Data Table")
    df_sweep = pd.DataFrame({
        "Freq_MHz": freqs / 1e6,
        "Zin_Real_Ohm": np.real(sweep_dict["zin"]),
        "Zin_Imag_Ohm": np.imag(sweep_dict["zin"]),
        "S11_Mag": np.abs(sweep_dict["gamma"]),
        "S11_Phase_Deg": np.degrees(np.unwrap(np.angle(sweep_dict["gamma"]))),
        "VSWR": sweep_dict["vswr"],
        "Return_Loss_dB": sweep_dict["rl_db"],
    })
    st.dataframe(df_sweep.head(100), height=250)

    # Download CSV Button
    csv_buf = io.StringIO()
    df_sweep.to_csv(csv_buf, index=False)
    st.download_button(
        label="📥 Download Frequency Sweep CSV",
        data=csv_buf.getvalue(),
        file_name="rf_line_doctor_sweep_data.csv",
        mime="text/csv",
    )

# ─────────────────────────────────────────────────────────────────────────────
# VIEW 3: SIGNAL ANALYSIS & SMITH CHART
# ─────────────────────────────────────────────────────────────────────────────
elif nav_section == "3. Signal Analysis & Smith Chart":
    st.header("3. Signal Analysis & Smith Chart")

    tab_rf, tab_z, tab_smith = st.tabs([
        "📊 Reflection metrics (|S₁₁|, VSWR, return loss)",
        "🔌 Input Impedance (Rin, Xin, Phase)",
        "🧭 Normalized Smith Chart",
    ])

    with tab_rf:
        st.subheader("Reflection Magnitude, VSWR, and Return Loss")
        if np.any(np.isnan(sweep_dict["vswr"])):
            nan_cnt = int(np.sum(np.isnan(sweep_dict["vswr"])))
            st.warning(
                f"⚠️ Measurement noise caused |S11| > 1.0 at {nan_cnt} sample point(s). "
                "For non-passive observations, passive-line VSWR is physically undefined and evaluated as NaN. "
                "Ideal reflection data is preserved without artificial clipping."
            )

        fig_rf, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

        # 1. |S11|
        ax1.plot(f_ghz, np.abs(sweep_dict["gamma"]), color="#1f77b4", lw=2, label="|S11|")
        ax1.axhline(0.05, color="green", linestyle="--", alpha=0.7, label="Matched Threshold (0.05)")
        ax1.set_ylabel("|S11| Magnitude")
        ax1.set_ylim(-0.05, 1.05)
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc="upper right")

        # 2. VSWR
        vswr_plot = np.clip(sweep_dict["vswr"], 1.0, 50.0)
        ax2.plot(f_ghz, vswr_plot, color="#ff7f0e", lw=2, label="VSWR")
        ax2.axhline(2.0, color="gray", linestyle="--", alpha=0.7, label="VSWR = 2.0 Benchmark")
        ax2.set_ylabel("VSWR")
        ax2.set_ylim(1.0, min(max(np.nanmax(vswr_plot) * 1.1, 3.0), 30.0))
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc="upper right")

        # 3. Return Loss
        rl_plot = np.clip(sweep_dict["rl_db"], 0.0, 60.0)
        ax3.plot(f_ghz, rl_plot, color="#2ca02c", lw=2, label="Return Loss (dB)")
        ax3.axhline(20.0, color="green", linestyle="--", alpha=0.7, label="20 dB Match Benchmark")
        ax3.axhline(10.0, color="orange", linestyle=":", alpha=0.7, label="10 dB Minimal Benchmark")
        ax3.set_ylabel("Return Loss (dB)")
        ax3.set_xlabel("Frequency (GHz)")
        ax3.set_ylim(0, 60)
        ax3.grid(True, alpha=0.3)
        ax3.legend(loc="upper right")

        plt.tight_layout()
        st.pyplot(fig_rf)
        plt.close(fig_rf)

    with tab_z:
        st.subheader("Input Impedance Decomposition & Phase")
        fig_z, (ax_rin, ax_xin, ax_ph) = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

        rin_plot = np.clip(rin, -100.0, 500.0)
        ax_rin.plot(f_ghz, rin_plot, color="#9467bd", lw=2, label="Rin = Re(Zin)")
        ax_rin.axhline(Z0, color="black", linestyle="--", alpha=0.5, label=f"Z0 = {Z0} Ω")
        ax_rin.set_ylabel("Resistance (Ω)")
        ax_rin.grid(True, alpha=0.3)
        ax_rin.legend(loc="upper right")

        xin_plot = np.clip(xin, -500.0, 500.0)
        ax_xin.plot(f_ghz, xin_plot, color="#8c564b", lw=2, label="Xin = Im(Zin)")
        ax_xin.axhline(0, color="black", linestyle="-", alpha=0.5)
        ax_xin.set_ylabel("Reactance (Ω)")
        ax_xin.grid(True, alpha=0.3)
        ax_xin.legend(loc="upper right")

        ax_ph.plot(f_ghz, spectral_feat["phase_deg"], color="#e377c2", lw=2, label="Unwrapped Phase (deg)")
        ax_ph.set_ylabel("Phase (deg)")
        ax_ph.set_xlabel("Frequency (GHz)")
        ax_ph.grid(True, alpha=0.3)
        ax_ph.legend(loc="upper right")

        plt.tight_layout()
        st.pyplot(fig_z)
        plt.close(fig_z)

    with tab_smith:
        st.subheader("Normalized Smith Chart Trajectory")
        col_sm1, col_sm2 = st.columns([3, 2])
        with col_sm1:
            fig_sm, ax_sm = plt.subplots(figsize=(7, 7))
            meas.smith_plot(sweep_dict["gamma"], ax=ax_sm, label=f"Sweep ({f_start_mhz:.0f}-{f_stop_mhz:.0f} MHz)")
            ax_sm.legend(loc="lower right", fontsize=9)
            st.pyplot(fig_sm)
            plt.close(fig_sm)
        with col_sm2:
            st.markdown(r"""
            **Smith chart reference points:**
            - **Centre ($\Gamma = 0$):** Matched load, $Z = Z_0$.
            - **Right edge ($\Gamma = +1$):** Open circuit, $Z \to \infty$.
            - **Left edge ($\Gamma = -1$):** Short circuit, $Z \to 0$.
            - **Upper half ($\operatorname{Im}(Z) > 0$):** Inductive impedance.
            - **Lower half ($\operatorname{Im}(Z) < 0$):** Capacitive impedance.
            - **Rotation:** The locus shows how the reflection phase changes across the frequency sweep.
            """)

# ─────────────────────────────────────────────────────────────────────────────
# VIEW 4: FAULT DIAGNOSIS ENGINE
# ─────────────────────────────────────────────────────────────────────────────
elif nav_section == "4. Fault Diagnosis Engine":
    st.header("4. Transparent Rule-Based Fault Diagnosis")
    st.caption("Inferred strictly from single-port S11 measurements without access to simulation ground truth.")
    st.caption("⚙️ Classifier threshold values (e.g. |Γ| < 0.05, trend > 0.010) are engineering choices tuned to this simulation range. They are not universal electromagnetic constants.")

    diag_col1, diag_col2 = st.columns([2, 3])
    with diag_col1:
        st.subheader("Diagnostic Result")
        st.write(f"- **Frozen Contract Class:** `{str(inferred_class)}`")
        st.write(f"- **Physical Inferred Subtype:** `{inferred_class.subtype}`")
        st.write(f"- **Diagnostic Confidence:** `{inferred_class.confidence.upper()}`")
        st.write(f"- **Rules Triggered:** `{', '.join(inferred_class.rules_fired)}`")

        st.subheader("Observed Signal Evidence")
        for ev in diag_report["evidence"]:
            st.write(f"• {ev}")

    with diag_col2:
        st.subheader("Electromagnetic Theory Justification")
        st.info(diag_report["physics_explanation"])

        st.subheader("Potential Ambiguities & Failure Modes")
        for amb in diag_report["ambiguities"]:
            st.warning(f"⚠️ {amb}")

        st.subheader("Recommended Corrective Engineering Actions")
        for act in diag_report["corrective_actions"]:
            st.success(f"🔧 {act}")

    # Download Diagnostic Summary Report
    report_text = f"""================================================================================
RF LINE DOCTOR -- AUTOMATED FAULT DIAGNOSTIC REPORT
================================================================================
Classification Label (Contract): {str(inferred_class)}
Internal Physical Subtype      : {inferred_class.subtype}
Diagnostic Confidence          : {inferred_class.confidence.upper()}
Rules Triggered                : {', '.join(inferred_class.rules_fired)}

SIGNAL EVIDENCE:
{chr(10).join(['- ' + e for e in diag_report['evidence']])}

ELECTROMAGNETIC THEORY EXPLANATION:
{diag_report['physics_explanation']}

RECOMMENDED CORRECTIVE ACTIONS:
{chr(10).join(['- ' + a for a in diag_report['corrective_actions']])}
================================================================================
"""
    st.download_button(
        label="📥 Download Diagnostic Report (TXT)",
        data=report_text,
        file_name="rf_line_doctor_diagnostic_report.txt",
        mime="text/plain",
    )

# ─────────────────────────────────────────────────────────────────────────────
# VIEW 5: FAULT LOCATION (TDR & PHASE SLOPE)
# ─────────────────────────────────────────────────────────────────────────────
elif nav_section == "5. Fault Location (TDR & Phase)":
    st.header("5. Fault Location: Phase-Slope Estimation and IFFT Verification")
    st.caption("Estimated fault distance using two complementary methods derived from the frequency-swept reflection data.")

    st.info(r"""
**Primary Method — Phase-Slope / Frequency:**  
For a single dominant reflector at distance *d* from the measurement port, the round-trip path
introduces a linear phase rotation in the frequency-swept reflection:

$$\phi(f) \approx \phi_0 - \frac{4\pi d}{v_p}\,f$$

where $v_p = \mathrm{vf} \times c_0$ is the propagation velocity.  
The slope of the unwrapped phase gives the distance estimate:

$$d = -\frac{v_p}{4\pi}\,\frac{d\phi}{df}$$

This method is straightforward to derive from transmission-line phasor theory (EC-3104).  
**Limitation:** Reactive discontinuities (series L, shunt C) introduce a frequency-dependent
internal phase offset that biases the slope estimate. The result should be treated as an
*estimated* distance, not a precise measurement.

**Supporting Cross-Check — IFFT Pseudo-Time Profile:**  
The same reflection data is transformed to a pseudo-time domain via an inverse FFT (with a Hann
window to reduce spectral leakage). A peak in the time profile at travel time *t* corresponds to
distance $d = v_p\,t/2$.  Physical resolution of this approach is $\Delta R = v_p/(2B)$, where $B$ is
the sweep bandwidth.  This is presented as a visualisation aid, not as a separate primary method.
""")

    loc_col1, loc_col2 = st.columns([3, 2])
    with loc_col1:
        st.subheader("IFFT Pseudo-Time Echo Response |h(t)|")
        tdr = loc_dual["tdr_data"]
        fig_tdr, ax_t = plt.subplots(figsize=(8, 4.5))

        if tdr.get("d_axis_m") is not None and len(tdr["d_axis_m"]) > 0:
            d_axis = tdr["d_axis_m"]
            t_mag = tdr["tdr_mag"]
            view_mask = d_axis <= max(length * 1.5, 2.0)
            ax_t.plot(d_axis[view_mask], t_mag[view_mask], color="#9467bd", lw=2, label="IFFT Echo Profile")

            d_est = loc_dual["dist_ifft_m"]
            if d_est is not None:
                ax_t.axvline(d_est, color="red", linestyle="--", label=f"Detected Discontinuity: {d_est:.3f} m")

            ax_t.set_xlabel("Physical Distance (m)")
            ax_t.set_ylabel("Reflection Magnitude |h(t)|")
            ax_t.grid(True, alpha=0.3)
            ax_t.legend(loc="upper right")
            st.pyplot(fig_tdr)
            plt.close(fig_tdr)

    with loc_col2:
        st.subheader("Localization Results Summary")
        d1 = loc_dual["dist_ifft_m"]
        d2 = loc_dual["dist_phase_m"]

        st.write(f"- **Phase-Slope Estimate (Primary):** `{f'{d2:.3f} m' if d2 is not None else 'None (insufficient reflection)'}`")
        st.write(f"- **IFFT TDR Cross-Check (Supporting):** `{f'{d1:.3f} m' if d1 is not None else 'None (no clear echo)'}`")

        if loc_dual["discrepancy_m"] is not None:
            st.write(f"- **Discrepancy |M1 - M2|:** `{loc_dual['discrepancy_m']*100:.2f} cm`")

        st.write(f"- **Physical Rayleigh Resolution (ΔR):** `{res_info['range_res_m']*100:.2f} cm`")
        if "interp_step_m" in res_info and np.isfinite(res_info["interp_step_m"]):
            st.write(f"- **IFFT Interpolation Bin Step (δd):** `{res_info['interp_step_m']*100:.2f} cm`")
        st.write(f"- **Unambiguous Range (R_max):** `{res_info['unambig_range_m']:.2f} m`")

        st.info(
            "ℹ️ **Physical Principle:** Zero-padding interpolates the peak centroid between FFT bins, "
            "but does not improve the physical Rayleigh resolution limit ($\Delta R = \frac{v_p}{2B}$). "
            "Two discontinuities closer than ΔR cannot be resolved as separate peaks. "
            "Additionally, reactive discontinuities introduce frequency-dependent phase shifts that slightly bias phase-slope estimation."
        )

        for w in loc_dual["warnings"]:
            st.warning(f"⚠️ {w}")

        if loc_dual["is_reliable"]:
            st.success("✅ Fault location estimate is verified and reliable.")
        else:
            st.error("❌ High uncertainty in localization.")

# ─────────────────────────────────────────────────────────────────────────────
# VIEW 6: QUARTER-WAVE MATCHING STUDIO
# ─────────────────────────────────────────────────────────────────────────────
elif nav_section == "6. Quarter-Wave Matching Studio":
    st.header("6. Quarter-Wave Impedance Matching Studio")
    st.caption(r"Synthesis and passband evaluation of quarter-wave transformers using $Z_t = \sqrt{Z_0 R_L}$.")

    is_real = isinstance(ZL_val, complex) and np.isfinite(ZL_val.real) and ZL_val.real > 0 and abs(ZL_val.imag) < 1e-5

    if not is_real:
        st.warning(
            f"Quarter-wave matching requires a purely real load resistance $R_L > 0$. "
            f"Current termination is $Z_L = {ZL_val}$. Complex or singular loads require stub tuning or an L-network."
        )
    else:
        RL_val = float(ZL_val.real)
        f_mid = float(np.mean(freqs))

        match_col1, match_col2 = st.columns([1, 2])
        with match_col1:
            st.subheader("Design Specifications")
            f_design_mhz = st.number_input("Design Frequency f₀ (MHz)", min_value=10.0, max_value=20000.0, value=f_mid / 1e6, step=50.0)
            f_design = f_design_mhz * 1e6

            match_res = match.compare_matching(Z0, RL_val, freqs, vf=vf, f_design=f_design, rl_threshold=20.0)
            st.metric("Transformer impedance Zₜ (Ω)", f"{match_res['Zt']:.2f} Ω")
            st.metric("Transformer length lₜ (mm)", f"{match_res['length_m']*1000:.1f} mm")
            st.metric("Contiguous Usable BW (RL ≥ 20 dB)", f"{match_res['bandwidth_hz']/1e6:.1f} MHz")

            f0_rl = match_res["at_f_design"]["rl_db"]
            st.metric("Return loss at design frequency f₀", "∞ dB (Exact)" if np.isinf(f0_rl) else f"{f0_rl:.1f} dB")
            st.caption("Note: Load resistance Rₗ (Ω) is the physical termination; return loss (dB) measures reflected power.")

        with match_col2:
            st.subheader("Performance Comparison (Before vs After)")
            fig_mc, (ax_mv, ax_mr) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)

            # VSWR
            ax_mv.plot(f_ghz, match_res["before"]["vswr"], "r--", lw=1.8, label="Before Matching (Unmatched)")
            ax_mv.plot(f_ghz, match_res["after"]["vswr"], "b-", lw=2, label="After Matching (λ/4 Transformer)")
            ax_mv.axvline(f_design / 1e9, color="gray", linestyle=":", label=f"f0 = {f_design/1e9:.2f} GHz")
            ax_mv.set_ylabel("VSWR")
            ax_mv.set_ylim(1.0, 3.5)
            ax_mv.grid(True, alpha=0.3)
            ax_mv.legend()

            # Return Loss
            ax_mr.plot(f_ghz, match_res["before"]["rl_db"], "r--", lw=1.8, label="Before Matching")
            ax_mr.plot(f_ghz, match_res["after"]["rl_db"], "b-", lw=2, label="After Matching")
            ax_mr.axhline(20.0, color="green", linestyle="--", label="20 dB Match Benchmark")
            ax_mr.axvline(f_design / 1e9, color="gray", linestyle=":")
            ax_mr.set_ylabel("Return Loss (dB)")
            ax_mr.set_xlabel("Frequency (GHz)")
            ax_mr.set_ylim(0, 50)
            ax_mr.grid(True, alpha=0.3)
            ax_mr.legend()

            plt.tight_layout()
            st.pyplot(fig_mc)
            plt.close(fig_mc)

# ─────────────────────────────────────────────────────────────────────────────
# VIEW 7: INDEPENDENT VALIDATION LAB
# ─────────────────────────────────────────────────────────────────────────────
elif nav_section == "7. Independent Validation Lab":
    st.header("7. Independent Validation Laboratory")
    st.caption("Empirical Monte Carlo evaluation on randomized held-out test datasets.")

    st.markdown("""
    This section runs live automated validation across randomized transmission lines and held-out fault cases.
    **Ground truth is explicitly compared against inferred diagnosis only in this evaluation view.**
    """)

    if st.button("🚀 Run Live Monte Carlo Validation Test (N = 120 Trials)"):
        with st.spinner("Executing randomized held-out trials..."):
            rng_v = np.random.default_rng(42)
            n_per_c = 20
            v_dataset = []
            contract_labels = ["healthy", "open", "short", "mismatch", "unknown"]

            for sc in fs.FAULT_SCENARIOS:
                for _ in range(n_per_c):
                    z0_r = float(rng_v.choice([50.0, 75.0]))
                    len_r = float(rng_v.uniform(0.5, 2.0))
                    vf_r = float(rng_v.choice([0.66, 1.0]))
                    fp_r = float(rng_v.uniform(0.2 * len_r, 0.8 * len_r))
                    sim_v = fs.simulate_fault(sc, z0_r, len_r, freqs, vf=vf_r, fault_pos=fp_r, noise_std=0.02, rng=rng_v)
                    target = "healthy" if sc == "healthy" else ("open" if sc == "open" else ("short" if sc == "short" else "mismatch"))
                    pred_res = diag.classify(sim_v["sweep"], z0_r)
                    v_dataset.append({
                        "scenario": sc,
                        "target": target,
                        "pred": str(pred_res),
                        "subtype": pred_res.subtype,
                        "true_pos": fp_r if sc in ["series_L", "shunt_C"] else (len_r if sc != "healthy" else None),
                        "est_pos": diag.estimate_distance(sim_v["sweep"], vf_r, target),
                    })

            y_t = [it["target"] for it in v_dataset]
            y_p = [it["pred"] for it in v_dataset]
            val_rep = compute_classification_report(y_t, y_p, contract_labels)

            v_col1, v_col2 = st.columns([1, 1])
            with v_col1:
                st.subheader(f"Contract Confusion Matrix (Accuracy = {val_rep['accuracy']*100:.1f}%)")
                df_vcm = pd.DataFrame(
                    val_rep["confusion_matrix"],
                    index=[f"True: {l}" for l in contract_labels],
                    columns=[f"Pred: {l}" for l in contract_labels],
                )
                st.dataframe(df_vcm)

            with v_col2:
                st.subheader("Contract Classification Performance")
                m_rows = []
                for l in contract_labels:
                    r_dict = {"Class": l}
                    r_dict.update(val_rep["per_class"][l])
                    m_rows.append(r_dict)
                st.dataframe(pd.DataFrame(m_rows))

            # Subtype 6-scenario evaluation
            st.subheader("Physical Subtype Diagnostics (6 Scenarios)")
            sub_map = {
                "matched": "healthy",
                "resistive_mismatch": "mismatch",
                "open_circuit": "open",
                "short_circuit": "short",
                "series_L": "series_L",
                "shunt_C": "shunt_C",
                "uncertain": "unknown",
            }
            scen_labels = ["healthy", "mismatch", "open", "short", "series_L", "shunt_C"]
            y_s_true = [it["scenario"] for it in v_dataset]
            y_s_pred = [sub_map.get(it["subtype"], "unknown") for it in v_dataset]
            sub_rep = compute_classification_report(y_s_true, y_s_pred, scen_labels)

            s_col1, s_col2 = st.columns([1, 1])
            with s_col1:
                st.write(f"**Subtype Confusion Matrix (Accuracy = {sub_rep['accuracy']*100:.1f}%):**")
                df_scm = pd.DataFrame(
                    sub_rep["confusion_matrix"],
                    index=[f"True: {l}" for l in scen_labels],
                    columns=[f"Pred: {l}" for l in scen_labels],
                )
                st.dataframe(df_scm)

            with s_col2:
                st.write("**Subtype Classification Metrics:**")
                sm_rows = []
                for l in scen_labels:
                    sr_dict = {"Scenario": l}
                    sr_dict.update(sub_rep["per_class"][l])
                    sm_rows.append(sr_dict)
                st.dataframe(pd.DataFrame(sm_rows))

            # Location errors
            t_locs = [it["true_pos"] for it in v_dataset if it["true_pos"] is not None]
            e_locs = [it["est_pos"] for it in v_dataset if it["true_pos"] is not None]
            l_stats = compute_location_metrics(t_locs, e_locs)
            st.success(f"**Fault Location Performance:** MAE = `{l_stats['mae_m']*100:.2f} cm` | RMSE = `{l_stats['rmse_m']*100:.2f} cm` (Valid: {l_stats['valid_count']}/{len(t_locs)})")
