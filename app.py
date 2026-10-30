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
    page_title="RF Line Doctor — Transmission Line Diagnostics",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Figma Design System Engineering CSS ───────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --rld-canvas: #0b0f17;
    --rld-sidebar: #080c14;
    --rld-card: #111827;
    --rld-card-raised: #131c2e;
    --rld-cell-bg: #0b0f17;
    --rld-border: #1e293b;
    --rld-border-subtle: #162032;
    --rld-text-white: #ffffff;
    --rld-text-main: #f1f5f9;
    --rld-text-muted: #94a3b8;
    --rld-text-dim: #64748b;
    --rld-cyan: #00e5ff;
    --rld-sky: #38bdf8;
    --rld-emerald: #10b981;
    --rld-amber: #f59e0b;
    --rld-rose: #ef4444;
}

html, body, [class*="css"], button, input, textarea, select {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.stApp {
    background-color: var(--rld-canvas) !important;
    color: var(--rld-text-main);
}

[data-testid="stHeader"] {
    background: rgba(11, 15, 23, 0.85) !important;
    backdrop-filter: blur(8px);
    border-bottom: 1px solid var(--rld-border-subtle);
}

[data-testid="stMainBlockContainer"] {
    max-width: 1480px;
    padding: 1.5rem 2.2rem 3.5rem;
}

/* ── Sidebar Styling ── */
[data-testid="stSidebar"] {
    background-color: var(--rld-sidebar) !important;
    border-right: 1px solid var(--rld-border-subtle) !important;
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.2rem;
    padding-left: 1.1rem;
    padding-right: 1.1rem;
}

[data-testid="stSidebar"] hr {
    border-color: var(--rld-border-subtle);
    margin: 1.1rem 0;
}

[data-testid="stSidebar"] div[role="radiogroup"] {
    gap: 3px;
}

[data-testid="stSidebar"] div[role="radiogroup"] label {
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 7px 12px;
    color: var(--rld-text-muted);
    font-size: 0.86rem;
    font-weight: 500;
    transition: all 0.15s ease-in-out;
    background: transparent;
    cursor: pointer;
}

[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: #111827;
    color: #ffffff;
}

[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    background: #131e33 !important;
    color: #ffffff !important;
    border-left: 3px solid var(--rld-cyan) !important;
    border-radius: 6px;
    font-weight: 600;
}

[data-testid="stSidebar"] div[role="radiogroup"] [data-testid="stWidgetSelectionIndicator"] {
    display: none;
}

[data-testid="stSidebar"] label,
[data-testid="stWidgetLabel"] p {
    color: #cbd5e1 !important;
    font-size: 0.8rem;
    font-weight: 600;
    margin-bottom: 3px;
}

/* ── Form Inputs ── */
input, textarea, [data-baseweb="select"] > div {
    background: #0f172a !important;
    color: #f8fafc !important;
    border: 1px solid var(--rld-border) !important;
    border-radius: 8px !important;
    font-size: 0.88rem !important;
}

[data-baseweb="input"] input:focus, [data-baseweb="select"] > div:focus-within {
    border-color: var(--rld-cyan) !important;
    box-shadow: 0 0 0 1px var(--rld-cyan) !important;
}

[data-testid="stSlider"] [role="slider"] {
    border-color: var(--rld-cyan) !important;
    background-color: var(--rld-cyan) !important;
    box-shadow: 0 0 10px rgba(0, 229, 255, 0.45);
}

[data-testid="stSlider"] [data-testid="stTickBar"] {
    background: var(--rld-border);
}

/* ── Action Buttons ── */
.stButton > button, .stDownloadButton > button {
    background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
    border: 1px solid #38bdf8 !important;
    border-radius: 8px !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    font-size: 0.84rem !important;
    letter-spacing: 0.02em !important;
    padding: 0.5rem 1.1rem !important;
    min-height: 2.4rem !important;
    transition: all 0.18s ease-in-out !important;
    box-shadow: 0 2px 8px rgba(2, 132, 199, 0.25) !important;
}

.stButton > button:hover, .stDownloadButton > button:hover {
    background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%) !important;
    border-color: var(--rld-cyan) !important;
    box-shadow: 0 0 16px rgba(0, 229, 255, 0.4) !important;
    transform: translateY(-1px);
    color: #ffffff !important;
}

/* ── Native Bordered Container Styling (Figma Cards) ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--rld-card) !important;
    border: 1px solid var(--rld-border) !important;
    border-radius: 12px !important;
    padding: 16px 20px !important;
    margin-bottom: 0.85rem !important;
}

/* ── Figma Cards & Components ── */
.figma-card {
    background: var(--rld-card);
    border: 1px solid var(--rld-border);
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 1rem;
}

.figma-section-title {
    font-size: 0.72rem;
    letter-spacing: 0.08em;
    color: var(--rld-text-dim);
    font-weight: 700;
    text-transform: uppercase;
    margin-bottom: 0.55rem;
}

.figma-pill-bar {
    background: var(--rld-card);
    border: 1px solid var(--rld-border);
    border-radius: 12px;
    padding: 12px 16px;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 1.4rem;
}

.figma-pill-cell {
    background: var(--rld-cell-bg);
    border: 1px solid var(--rld-border);
    border-radius: 8px;
    padding: 8px 14px;
}

/* ── Metric Card ── */
.figma-metric-card {
    background: var(--rld-card);
    border: 1px solid var(--rld-border);
    border-radius: 12px;
    padding: 16px 18px;
    height: 100%;
}

.figma-metric-label {
    font-size: 0.7rem;
    letter-spacing: 0.08em;
    color: var(--rld-text-dim);
    font-weight: 700;
    text-transform: uppercase;
}

.figma-metric-val {
    font-size: 1.65rem;
    font-weight: 750;
    margin-top: 4px;
    margin-bottom: 2px;
    letter-spacing: -0.02em;
    font-family: 'Inter', system-ui, sans-serif;
}

.figma-metric-sub {
    font-size: 0.74rem;
    color: var(--rld-text-muted);
}

.figma-quick-title {
    font-size: 0.9rem;
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 4px;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    border-bottom: 1px solid var(--rld-border);
    margin-bottom: 1rem;
}

.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 8px 8px 0 0;
    color: var(--rld-text-dim);
    padding: 0.65rem 1.1rem;
    font-size: 0.88rem;
    font-weight: 500;
    border-bottom: 2px solid transparent;
}

.stTabs [aria-selected="true"] {
    color: var(--rld-cyan) !important;
    border-bottom: 2px solid var(--rld-cyan) !important;
    font-weight: 600;
}

/* ── Charts, Tables, Alerts ── */
[data-testid="stPlotlyChart"], [data-testid="stPyplot"], [data-testid="stImage"] {
    border: none !important;
    border-radius: 12px;
    overflow: hidden;
    background: transparent !important;
}

[data-testid="stDataFrame"], [data-testid="stTable"] {
    border: 1px solid var(--rld-border);
    border-radius: 10px;
    overflow: hidden;
    background: #0f172a;
}

[data-testid="stAlert"] {
    border: 1px solid var(--rld-border);
    border-radius: 10px;
    background: var(--rld-card);
    color: var(--rld-text-main);
}

[data-testid="stExpander"] {
    border: 1px solid var(--rld-border);
    border-radius: 10px;
    background: var(--rld-card);
}

/* ── KaTeX Math (Cyan Glow & Prominent Styling) ── */
.katex, .katex * {
    color: #00e5ff !important;
    font-size: 1.04em;
}

.katex-display {
    margin: 0.5rem 0 !important;
    padding: 0.4rem 0 !important;
    overflow-x: auto;
    background: transparent !important;
    border: none !important;
}

@media (max-width: 900px) {
    [data-testid="stMainBlockContainer"] { padding: 1.2rem 1rem 2rem; }
    .figma-pill-bar { grid-template-columns: repeat(2, 1fr); }
}
</style>
""", unsafe_allow_html=True)

# ── Matplotlib Dark Theme (Matching Figma Palette) ───────────────────────────
plt.rcParams.update({
    "figure.facecolor": "#111827",
    "axes.facecolor": "#0b0f17",
    "savefig.facecolor": "#111827",
    "text.color": "#f8fafc",
    "axes.labelcolor": "#94a3b8",
    "xtick.color": "#64748b",
    "ytick.color": "#64748b",
    "axes.edgecolor": "#1e293b",
    "grid.color": "#1e293b",
    "grid.alpha": 0.6,
    "legend.facecolor": "#0b0f17",
    "legend.edgecolor": "#1e293b",
    "legend.labelcolor": "#cbd5e1",
})

# ── Reusable Figma Header / Breadcrumb Helpers ────────────────────────────────
def render_breadcrumb(page_name: str):
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
      <div style="font-size: 0.72rem; letter-spacing: 0.08em; color: #64748b; font-weight: 600; text-transform: uppercase;">
        WORKSPACE &nbsp;/&nbsp; {page_name.upper()}
      </div>
      <div style="display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.35); border-radius: 999px; font-size: 0.72rem; font-weight: 600; color: #10b981; letter-spacing: 0.05em;">
        <span style="font-size: 0.55rem;">●</span> MODEL ACTIVE
      </div>
    </div>
    """, unsafe_allow_html=True)

def render_page_header(title: str, subtitle: str):
    st.markdown(f"""
    <div style="margin-bottom: 1.4rem;">
      <h1 style="color: #ffffff; font-size: 1.85rem; font-weight: 700; margin: 0 0 0.25rem 0; letter-spacing: -0.02em;">{title}</h1>
      <p style="color: #94a3b8; font-size: 0.92rem; margin: 0;">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def render_footer():
    st.markdown("""
    <div style="margin-top: 2.8rem; padding-top: 1rem; border-top: 1px solid #162032; text-align: center; color: #475569; font-size: 0.72rem; letter-spacing: 0.1em; text-transform: uppercase;">
      RF LINE DOCTOR • EDUCATIONAL VIRTUAL PROTOTYPE
    </div>
    """, unsafe_allow_html=True)

def render_config_pill_bar(Z0_val, len_val, vf_val, f_min_mhz, f_max_mhz):
    st.markdown(f"""
    <div class="figma-section-title">SIMULATION CONFIGURATION</div>
    <div class="figma-pill-bar">
      <div class="figma-pill-cell">
        <div style="font-size: 0.68rem; color: #64748b; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;">CHARACTERISTIC IMPEDANCE (<i>Z</i><sub>0</sub>)</div>
        <div style="font-size: 1.05rem; color: #ffffff; font-weight: 600; margin-top: 2px;">{Z0_val:.0f} Ω</div>
      </div>
      <div class="figma-pill-cell">
        <div style="font-size: 0.68rem; color: #64748b; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;">PHYSICAL LENGTH (<i>l</i>)</div>
        <div style="font-size: 1.05rem; color: #ffffff; font-weight: 600; margin-top: 2px;">{len_val:.2f} m</div>
      </div>
      <div class="figma-pill-cell">
        <div style="font-size: 0.68rem; color: #64748b; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;">VELOCITY FACTOR (<i>v</i><sub>f</sub>)</div>
        <div style="font-size: 1.05rem; color: #ffffff; font-weight: 600; margin-top: 2px;">{vf_val:.2f}</div>
      </div>
      <div class="figma-pill-cell">
        <div style="font-size: 0.68rem; color: #64748b; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;">FREQUENCY RANGE (<i>f</i>)</div>
        <div style="font-size: 1.05rem; color: #ffffff; font-weight: 600; margin-top: 2px;">{f_min_mhz/1000:.2f} – {f_max_mhz/1000:.2f} GHz</div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ── Sidebar Branding & Navigation ─────────────────────────────────────────────
st.sidebar.markdown("""
<div style="padding: 0.1rem 0 0.8rem 0;">
  <div style="font-size: 1.2rem; font-weight: 800; color: #ffffff; letter-spacing: 0.04em;">RF LINE DOCTOR</div>
  <div style="font-size: 0.68rem; font-weight: 700; color: #38bdf8; letter-spacing: 0.1em; text-transform: uppercase; margin-top: 2px;">TRANSMISSION LINE DIAGNOSTICS</div>
  <div style="width: 32px; height: 3px; background: #00e5ff; border-radius: 2px; margin-top: 8px; margin-bottom: 14px;"></div>
  <div style="font-size: 0.7rem; font-weight: 700; color: #64748b; letter-spacing: 0.08em; text-transform: uppercase;">WORKSPACE</div>
</div>
""", unsafe_allow_html=True)

NAV_OPTIONS = [
    "Overview",
    "Line simulator",
    "Signal analysis",
    "Fault diagnosis",
    "Fault location",
    "Quarter-wave matching",
    "Validation lab",
]

nav_section = st.sidebar.radio(
    "WORKSPACE",
    NAV_OPTIONS,
    index=0,
    label_visibility="collapsed",
)

st.sidebar.markdown('<div style="height: 1px; background: #162032; margin: 1.1rem 0;"></div>', unsafe_allow_html=True)
st.sidebar.markdown('<div style="font-size: 0.7rem; font-weight: 700; color: #64748b; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.65rem;">TRANSMISSION LINE PARAMETERS</div>', unsafe_allow_html=True)

Z0 = st.sidebar.number_input(
    "Characteristic Impedance Z₀ (Ω)",
    min_value=1.0,
    max_value=1000.0,
    value=50.0,
    step=5.0,
    help="Reference line characteristic impedance Z₀ (e.g., 50 Ω or 75 Ω)",
)

length = st.sidebar.number_input(
    "Physical Line Length l (m)",
    min_value=0.05,
    max_value=100.0,
    value=1.0,
    step=0.1,
    help="Physical end-to-end cable length l in metres",
)

vf = st.sidebar.slider(
    "Velocity Factor vf (vₚ/c₀)",
    min_value=0.1,
    max_value=1.0,
    value=0.66,
    step=0.01,
    help="vₚ = vf × c₀. Typical: solid PE coax = 0.66, PTFE = 0.70, air = 1.0",
)

st.sidebar.markdown('<div style="font-size: 0.7rem; font-weight: 700; color: #64748b; letter-spacing: 0.08em; text-transform: uppercase; margin-top: 0.8rem; margin-bottom: 0.4rem;">FREQUENCY SWEEP RANGE</div>', unsafe_allow_html=True)
col_sf1, col_sf2 = st.sidebar.columns(2)
with col_sf1:
    f_start_mhz = st.number_input("fₘᵢₙ (MHz)", min_value=1.0, max_value=50000.0, value=500.0, step=50.0)
with col_sf2:
    f_stop_mhz = st.number_input("fₘₐₓ (MHz)", min_value=5.0, max_value=50000.0, value=4000.0, step=100.0)

if f_start_mhz >= f_stop_mhz:
    st.sidebar.error("Minimum frequency must be lower than maximum frequency.")
    st.stop()

n_pts = st.sidebar.slider("Sweep sample points", min_value=50, max_value=1000, value=400, step=50)
freqs = np.linspace(f_start_mhz * 1e6, f_stop_mhz * 1e6, n_pts)

st.sidebar.markdown('<div style="font-size: 0.7rem; font-weight: 700; color: #64748b; letter-spacing: 0.08em; text-transform: uppercase; margin-top: 0.8rem; margin-bottom: 0.4rem;">FAULT INJECTION & TERMINATION</div>', unsafe_allow_html=True)
scenario_preset = st.sidebar.selectbox(
    "Fault Preset Scenario",
    [
        "Case 1: Healthy matched (Z_L = Z_0)",
        "Case 2: Resistive mismatch (Z_L = R_L ≠ Z_0)",
        "Case 3: Open circuit (Z_L = ∞)",
        "Case 4: Short circuit (Z_L = 0)",
        "Case 5: Series inductive discontinuity (L)",
        "Case 6: Shunt capacitive discontinuity (C)",
        "Custom: Complex load (R + jX)",
    ],
    index=1,
)

# Parse scenario parameters (Unchanged physics / simulation logic)
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
    RL_input = st.sidebar.number_input("Load Resistance R_L (Ω)", min_value=1.0, max_value=2000.0, value=120.0, step=5.0)
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
    help="Complex Gaussian noise added to simulated S₁₁ reflection",
)

# Bottom Model Status Card in Sidebar (from Figma)
st.sidebar.markdown("""
<div style="background: #0b0f17; border: 1px solid #1e293b; border-radius: 10px; padding: 12px 14px; margin-top: 1.2rem;">
  <div style="font-size: 0.68rem; font-weight: 700; color: #64748b; letter-spacing: 0.08em; text-transform: uppercase;">CURRENT MODEL</div>
  <div style="font-size: 0.82rem; font-weight: 600; color: #ffffff; margin-top: 4px;">Lossless coaxial line</div>
  <div style="font-size: 0.74rem; color: #94a3b8; margin-top: 1px;">Single-port S₁₁ analysis</div>
  <div style="margin-top: 10px; display: flex; align-items: center; gap: 6px; font-size: 0.68rem; color: #10b981; font-weight: 700; letter-spacing: 0.06em;">
    <span style="font-size: 0.55rem;">●</span> SIMULATION ENVIRONMENT READY
  </div>
  <div style="margin-top: 6px; font-size: 0.65rem; color: #475569; letter-spacing: 0.08em; text-transform: uppercase;">
    EC-3104 • VIRTUAL PROTOTYPE
  </div>
</div>
""", unsafe_allow_html=True)

# ── Execute Core Simulation & Inference Pipeline (Unchanged) ──────────────────
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
        sweep_dict["gamma"] = g_noisy
        sweep_dict["vswr"] = meas.vswr(g_noisy)
        sweep_dict["rl_db"] = meas.return_loss_db(g_noisy)
        sweep_dict.gamma_ideal = g_ideal

# Inferred Diagnosis (Single-Port S11 Only)
inferred_class = diag.classify(sweep_dict, Z0)
loc_dual = locate_fault_dual_method(sweep_dict["gamma"], freqs, vf=vf, fault_class=inferred_class)
res_info = calculate_resolution_metrics(freqs, vf=vf)
diag_report = generate_full_diagnostic_report(inferred_class, Z0, vf=vf)

# Decompose impedances & spectral features
rin, xin = decompose_impedance(sweep_dict["zin"])
spectral_feat = compute_spectral_features(sweep_dict["gamma"], freqs)
f_ghz = freqs / 1e9


# ─────────────────────────────────────────────────────────────────────────────
# VIEW 1: OVERVIEW (Reproducing Figma Visual Specification)
# ─────────────────────────────────────────────────────────────────────────────
if "overview" in nav_section.lower():
    render_breadcrumb("OVERVIEW")
    render_page_header(
        "Transmission line overview",
        "A clear view of your configured line, measured response and diagnostic status.",
    )

    # 1. LIVE DIAGNOSTIC SUMMARY (4 KPI Metric Cards)
    st.markdown('<div class="figma-section-title">LIVE DIAGNOSTIC SUMMARY</div>', unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)

    diag_color = "#f59e0b"  # amber mismatch
    if str(inferred_class) == "healthy":
        diag_color = "#10b981"
    elif str(inferred_class) in ["open", "short"]:
        diag_color = "#ef4444"
    elif str(inferred_class) == "unknown":
        diag_color = "#38bdf8"

    mean_gamma = float(np.mean(np.abs(sweep_dict["gamma"])))
    d_est = loc_dual["dist_ifft_m"]
    d_disp_str = f"{d_est:.2f} m" if d_est is not None else "N/A"
    
    mean_vswr = np.nanmean(sweep_dict["vswr"])
    vswr_disp_str = f"{mean_vswr:.2f} : 1" if np.isfinite(mean_vswr) else "Undefined"

    with k1:
        st.markdown(f"""
        <div class="figma-metric-card">
          <div class="figma-metric-label">INFERRED DIAGNOSIS</div>
          <div class="figma-metric-val" style="color: {diag_color};">{str(inferred_class).upper()}</div>
          <div class="figma-metric-sub">Rule-based classification</div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div class="figma-metric-card">
          <div class="figma-metric-label">INPUT REFLECTION</div>
          <div class="figma-metric-val">
            <span style="color: #00e5ff; font-weight: 700; font-size: 1.25rem; margin-right: 6px;">|S<sub>11</sub>|</span><span style="color: #ffffff;">{mean_gamma:.2f}</span>
          </div>
          <div class="figma-metric-sub">Across selected sweep</div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="figma-metric-card">
          <div class="figma-metric-label">FAULT DISTANCE</div>
          <div class="figma-metric-val" style="color: #10b981;">{d_disp_str}</div>
          <div class="figma-metric-sub">Estimated from phase / IFFT</div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        st.markdown(f"""
        <div class="figma-metric-card">
          <div class="figma-metric-label">VSWR</div>
          <div class="figma-metric-val" style="color: #f59e0b;">{vswr_disp_str}</div>
          <div class="figma-metric-sub">At current observation</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # 2. SIMULATION CONFIGURATION (Horizontal 4-Cell Pill Bar)
    render_config_pill_bar(Z0, length, vf, f_start_mhz, f_stop_mhz)

    # 3. SIGNAL RESPONSE (Two Columns: Plot + Diagnostic Result Card)
    st.markdown('<div class="figma-section-title">SIGNAL RESPONSE</div>', unsafe_allow_html=True)
    resp_col1, resp_col2 = st.columns([13, 7])

    with resp_col1:
        with st.container(border=True):
            st.markdown('<div style="font-size: 0.95rem; font-weight: 600; color: #ffffff;">Reflection magnitude across frequency</div>', unsafe_allow_html=True)
            st.markdown('<div style="font-size: 0.75rem; color: #64748b; margin-top: 1px; margin-bottom: 8px;">Input reflection coefficient |S₁₁| • Frequency sweep</div>', unsafe_allow_html=True)
            
            fig_ov, ax_ov = plt.subplots(figsize=(7.6, 3.45))
            ax_ov.plot(f_ghz, np.abs(sweep_dict["gamma"]), color="#00e5ff", lw=2.2, label="|S₁₁| (input reflection)")
            ax_ov.axhline(0.05, color="#38bdf8", linestyle="--", alpha=0.5, label="Healthy Threshold (0.05)")
            ax_ov.set_xlabel("Frequency (GHz)", fontsize=9, color="#94a3b8")
            ax_ov.set_ylabel("|S₁₁| magnitude", fontsize=9, color="#94a3b8")
            ax_ov.set_ylim(-0.05, 1.05)
            ax_ov.set_yticks([0.0, 0.5, 1.0])
            ax_ov.grid(True, color="#1e293b", alpha=0.7, linestyle="-")
            ax_ov.tick_params(colors="#64748b", labelsize=8.5)
            for sp in ax_ov.spines.values():
                sp.set_color("#1e293b")
            ax_ov.legend(loc="upper right", fontsize=8, facecolor="#0b0f17", edgecolor="#1e293b")
            plt.tight_layout()
            st.pyplot(fig_ov)
            plt.close(fig_ov)

    with resp_col2:
        badge_bg = "rgba(245, 158, 11, 0.14)"
        badge_border = "rgba(245, 158, 11, 0.35)"
        badge_color = "#f59e0b"
        if str(inferred_class) == "healthy":
            badge_bg = "rgba(16, 185, 129, 0.14)"
            badge_border = "rgba(16, 185, 129, 0.35)"
            badge_color = "#10b981"
        elif str(inferred_class) in ["open", "short"]:
            badge_bg = "rgba(239, 68, 68, 0.14)"
            badge_border = "rgba(239, 68, 68, 0.35)"
            badge_color = "#ef4444"

        subtype_title = inferred_class.subtype.replace("_", " ").capitalize()
        
        # Tailored overview explanations matching Figma visual language
        overview_desc = "The measured reflection indicates a load that differs from the line impedance."
        overview_evidence = [
            "Reflection magnitude is above match threshold",
            "Frequency response remains consistent",
            "No open- or short-circuit signature detected",
        ]
        if str(inferred_class) == "healthy":
            overview_desc = "Transmission line is operating at peak efficiency with matched termination."
            overview_evidence = [
                "Reflection magnitude is below match threshold (0.05)",
                "Minimal standing waves detected across sweep",
                "Incident RF power transferred fully to load",
            ]
        elif str(inferred_class) == "open":
            overview_desc = "Open-circuit discontinuity identified with total in-phase voltage reflection."
            overview_evidence = [
                "Reflection magnitude is near unity (|S₁₁| ≈ 1.0)",
                "In-phase reflection phase signature at termination",
                "Full standing-wave voltage pattern established",
            ]
        elif str(inferred_class) == "short":
            overview_desc = "Short-circuit fault detected with 180° phase inversion at boundary."
            overview_evidence = [
                "Reflection magnitude is near unity (|S₁₁| ≈ 1.0)",
                "Negative real reflection indicating ground clamping",
                "Zero voltage node present at boundary",
            ]
        elif inferred_class.subtype == "series_L":
            overview_desc = "Series inductive discontinuity identified along the transmission path."
            overview_evidence = [
                "Reflection magnitude rises monotonically with frequency",
                "Inductive upper-half Smith chart locus transformation",
                "Localized discontinuity echo detected via TDR",
            ]
        elif inferred_class.subtype == "shunt_C":
            overview_desc = "Shunt capacitive discontinuity identified along the transmission path."
            overview_evidence = [
                "Reflection magnitude increases with frequency",
                "Capacitive lower-half Smith chart locus transformation",
                "Localized discontinuity echo detected via TDR",
            ]

        with st.container(border=True):
            st.markdown('<div class="figma-metric-label">DIAGNOSTIC RESULT</div>', unsafe_allow_html=True)
            st.markdown(f'<span style="display: inline-block; padding: 3px 14px; background: {badge_bg}; border: 1px solid {badge_border}; border-radius: 999px; font-size: 0.72rem; font-weight: 700; color: {badge_color}; letter-spacing: 0.06em; margin-top: 6px; margin-bottom: 8px;">{str(inferred_class).upper()}</span>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-size: 1.25rem; font-weight: 700; color: #ffffff; margin-bottom: 6px;">{subtype_title}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-size: 0.82rem; color: #94a3b8; line-height: 1.5; margin-bottom: 14px;">{overview_desc}</div>', unsafe_allow_html=True)
            st.markdown('<div class="figma-metric-label" style="margin-bottom: 8px;">OBSERVED EVIDENCE</div>', unsafe_allow_html=True)
            for ev in overview_evidence:
                st.markdown(f'<div style="font-size: 0.8rem; color: #cbd5e1; margin-bottom: 4px;">• {ev}</div>', unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # 4. QUICK INTERPRETATION (Unified Single Card matching Figma Specification)
    with st.container(border=True):
        st.markdown('<div class="figma-section-title" style="margin-bottom: 12px;">QUICK INTERPRETATION</div>', unsafe_allow_html=True)
        q1, q2, q3 = st.columns(3)
        with q1:
            st.markdown("""
            <div style="padding-right: 12px; border-right: 1px solid #1e293b;">
              <div style="font-size: 0.92rem; font-weight: 600; color: #ffffff; margin-bottom: 6px;">Reflection coefficient</div>
              <div style="font-size: 0.95rem; font-weight: 600; color: #00e5ff; margin-bottom: 8px; font-family: 'JetBrains Mono', monospace; white-space: nowrap;">
                Γ = (<i>Z</i><sub>L</sub> − <i>Z</i><sub>0</sub>) / (<i>Z</i><sub>L</sub> + <i>Z</i><sub>0</sub>)
              </div>
              <div style="font-size: 0.78rem; color: #94a3b8; line-height: 1.45;">Describes the ratio of reflected to incident wave.</div>
            </div>
            """, unsafe_allow_html=True)
        with q2:
            st.markdown("""
            <div style="padding-right: 12px; border-right: 1px solid #1e293b;">
              <div style="font-size: 0.92rem; font-weight: 600; color: #ffffff; margin-bottom: 6px;">Standing-wave ratio</div>
              <div style="font-size: 0.95rem; font-weight: 600; color: #00e5ff; margin-bottom: 8px; font-family: 'JetBrains Mono', monospace; white-space: nowrap;">
                VSWR = (1 + |Γ|) / (1 − |Γ|)
              </div>
              <div style="font-size: 0.78rem; color: #94a3b8; line-height: 1.45;">Indicates the severity of impedance mismatch.</div>
            </div>
            """, unsafe_allow_html=True)
        with q3:
            st.markdown("""
            <div style="padding-left: 4px;">
              <div style="font-size: 0.92rem; font-weight: 600; color: #ffffff; margin-bottom: 6px;">Input impedance</div>
              <div style="font-size: 0.95rem; font-weight: 600; color: #00e5ff; margin-bottom: 8px; font-family: 'JetBrains Mono', monospace; white-space: nowrap;">
                <i>Z</i><sub>in</sub> = <i>Z</i><sub>0</sub> (1 + Γ) / (1 − Γ)
              </div>
              <div style="font-size: 0.78rem; color: #94a3b8; line-height: 1.45;">Impedance presented at the input of the line.</div>
            </div>
            """, unsafe_allow_html=True)

    render_footer()


# ─────────────────────────────────────────────────────────────────────────────
# VIEW 2: TRANSMISSION-LINE SIMULATOR
# ─────────────────────────────────────────────────────────────────────────────
elif "simulator" in nav_section.lower():
    render_breadcrumb("LINE SIMULATOR")
    render_page_header(
        "Transmission line simulator",
        "Interactive multi-parameter transmission-line simulation and reflection generation.",
    )

    render_config_pill_bar(Z0, length, vf, f_start_mhz, f_stop_mhz)

    col_sim1, col_sim2 = st.columns([13, 7])
    with col_sim1:
        with st.container(border=True):
            st.markdown('<div style="font-size: 0.95rem; font-weight: 600; color: #ffffff;">Simulated reflection sweep profile</div>', unsafe_allow_html=True)
            st.markdown('<div style="font-size: 0.75rem; color: #64748b; margin-top: 1px; margin-bottom: 8px;">Calculated single-port |S₁₁| magnitude across swept frequency band</div>', unsafe_allow_html=True)
            
            fig_s, ax_s = plt.subplots(figsize=(7.6, 3.6))
            ax_s.plot(f_ghz, np.abs(sweep_dict["gamma"]), color="#00e5ff", lw=2.2, label="|S₁₁| (input reflection)")
            ax_s.axhline(0.05, color="#10b981", linestyle="--", alpha=0.6, label="Healthy Threshold (0.05)")
            ax_s.set_xlabel("Frequency (GHz)", fontsize=9, color="#94a3b8")
            ax_s.set_ylabel("|S₁₁| magnitude", fontsize=9, color="#94a3b8")
            ax_s.set_ylim(-0.05, 1.05)
            ax_s.grid(True, color="#1e293b", alpha=0.7)
            ax_s.tick_params(colors="#64748b", labelsize=8.5)
            for sp in ax_s.spines.values():
                sp.set_color("#1e293b")
            ax_s.legend(loc="upper right", fontsize=8, facecolor="#0b0f17", edgecolor="#1e293b")
            plt.tight_layout()
            st.pyplot(fig_s)
            plt.close(fig_s)

    with col_sim2:
        with st.container(border=True):
            st.markdown('<div class="figma-metric-label">SIMULATION GROUND TRUTH</div>', unsafe_allow_html=True)
            st.markdown('<div style="font-size: 0.8rem; color: #94a3b8; margin-top: 4px; margin-bottom: 12px;">Reference parameters used for virtual waveform generation (not accessible to classifier).</div>', unsafe_allow_html=True)
            
            fault_pos_str = f"{fault_pos:.2f} m" if sim_scenario in ["series_L", "shunt_C"] else (f"{length:.2f} m (Load)" if sim_scenario != "healthy" else "None (Uniform)")
            st.markdown(f"""
            <div style="display: flex; flex-direction: column; gap: 8px;">
              <div class="figma-pill-cell">
                <div style="font-size: 0.68rem; color: #64748b; font-weight: 700; text-transform: uppercase;">INJECTED SCENARIO</div>
                <div style="font-size: 0.95rem; color: #ffffff; font-weight: 600; margin-top: 2px;">{sim_scenario.upper()}</div>
              </div>
              <div class="figma-pill-cell">
                <div style="font-size: 0.68rem; color: #64748b; font-weight: 700; text-transform: uppercase;">TERMINATION IMPEDANCE (<i>Z</i><sub>L</sub>)</div>
                <div style="font-size: 0.95rem; color: #00e5ff; font-weight: 600; margin-top: 2px;">{str(ZL_val)}</div>
              </div>
              <div class="figma-pill-cell">
                <div style="font-size: 0.68rem; color: #64748b; font-weight: 700; text-transform: uppercase;">FAULT POSITION (<i>d</i>)</div>
                <div style="font-size: 0.95rem; color: #ffffff; font-weight: 600; margin-top: 2px;">{fault_pos_str}</div>
              </div>
              <div class="figma-pill-cell">
                <div style="font-size: 0.68rem; color: #64748b; font-weight: 700; text-transform: uppercase;">MEASUREMENT NOISE (&sigma;)</div>
                <div style="font-size: 0.95rem; color: #f59e0b; font-weight: 600; margin-top: 2px;">{noise_std:.2f}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    # Data export table with clean engineering column titles
    st.markdown('<div class="figma-section-title" style="margin-top: 1.2rem;">FREQUENCY SWEEP DATA TABLE</div>', unsafe_allow_html=True)
    df_sweep = pd.DataFrame({
        "f (MHz)": freqs / 1e6,
        "Re(Z_in) (Ω)": np.real(sweep_dict["zin"]),
        "Im(Z_in) (Ω)": np.imag(sweep_dict["zin"]),
        "|S11|": np.abs(sweep_dict["gamma"]),
        "Phase (deg)": np.degrees(np.unwrap(np.angle(sweep_dict["gamma"]))),
        "VSWR": sweep_dict["vswr"],
        "Return Loss (dB)": sweep_dict["rl_db"],
    })
    st.dataframe(df_sweep.head(100), height=240)

    csv_buf = io.StringIO()
    df_sweep.to_csv(csv_buf, index=False)
    st.download_button(
        label="📥 Download Frequency Sweep CSV",
        data=csv_buf.getvalue(),
        file_name="rf_line_doctor_sweep_data.csv",
        mime="text/csv",
    )

    render_footer()


# ─────────────────────────────────────────────────────────────────────────────
# VIEW 3: SIGNAL ANALYSIS & SMITH CHART
# ─────────────────────────────────────────────────────────────────────────────
elif "signal" in nav_section.lower():
    render_breadcrumb("SIGNAL ANALYSIS")
    render_page_header(
        "Signal analysis & Smith chart",
        "Reflection metrics, input impedance transformations, and complex Smith chart loci.",
    )

    tab_rf, tab_z, tab_smith = st.tabs([
        "📊 Reflection metrics (|S₁₁|, VSWR, Return Loss)",
        "🔌 Input impedance (Rᵢₙ, Xᵢₙ, Phase)",
        "🧭 Normalized Smith chart",
    ])

    with tab_rf:
        if np.any(np.isnan(sweep_dict["vswr"])):
            nan_cnt = int(np.sum(np.isnan(sweep_dict["vswr"])))
            st.warning(
                f"⚠️ Measurement noise caused |S₁₁| > 1.0 at {nan_cnt} sample point(s). "
                "For non-passive observations, passive-line VSWR is physically undefined and evaluated as NaN. "
                "Ideal reflection data is preserved without artificial clipping."
            )

        with st.container(border=True):
            st.markdown('<div style="font-size: 0.92rem; font-weight: 600; color: #ffffff; margin-bottom: 8px;">Multi-Metric Reflection Overview (|S₁₁|, VSWR, Return Loss)</div>', unsafe_allow_html=True)
            
            fig_rf, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 7.5), sharex=True)

            ax1.plot(f_ghz, np.abs(sweep_dict["gamma"]), color="#00e5ff", lw=2, label="|S₁₁|")
            ax1.axhline(0.05, color="#10b981", linestyle="--", alpha=0.7, label="Matched Threshold (0.05)")
            ax1.set_ylabel("|S₁₁| mag", fontsize=8.5, color="#94a3b8")
            ax1.set_ylim(-0.05, 1.05)
            ax1.grid(True, color="#1e293b", alpha=0.6)
            ax1.tick_params(colors="#64748b", labelsize=8)
            for sp in ax1.spines.values(): sp.set_color("#1e293b")
            ax1.legend(loc="upper right", fontsize=8, facecolor="#0b0f17", edgecolor="#1e293b")

            vswr_plot = np.clip(sweep_dict["vswr"], 1.0, 50.0)
            ax2.plot(f_ghz, vswr_plot, color="#f59e0b", lw=2, label="VSWR")
            ax2.axhline(2.0, color="#64748b", linestyle="--", alpha=0.7, label="VSWR = 2.0 Benchmark")
            ax2.set_ylabel("VSWR", fontsize=8.5, color="#94a3b8")
            ax2.set_ylim(1.0, min(max(np.nanmax(vswr_plot) * 1.1, 3.0), 30.0))
            ax2.grid(True, color="#1e293b", alpha=0.6)
            ax2.tick_params(colors="#64748b", labelsize=8)
            for sp in ax2.spines.values(): sp.set_color("#1e293b")
            ax2.legend(loc="upper right", fontsize=8, facecolor="#0b0f17", edgecolor="#1e293b")

            rl_plot = np.clip(sweep_dict["rl_db"], 0.0, 60.0)
            ax3.plot(f_ghz, rl_plot, color="#10b981", lw=2, label="Return Loss (dB)")
            ax3.axhline(20.0, color="#38bdf8", linestyle="--", alpha=0.7, label="20 dB Match Benchmark")
            ax3.axhline(10.0, color="#f59e0b", linestyle=":", alpha=0.7, label="10 dB Minimal Benchmark")
            ax3.set_ylabel("RL (dB)", fontsize=8.5, color="#94a3b8")
            ax3.set_xlabel("Frequency (GHz)", fontsize=8.5, color="#94a3b8")
            ax3.set_ylim(0, 60)
            ax3.grid(True, color="#1e293b", alpha=0.6)
            ax3.tick_params(colors="#64748b", labelsize=8)
            for sp in ax3.spines.values(): sp.set_color("#1e293b")
            ax3.legend(loc="upper right", fontsize=8, facecolor="#0b0f17", edgecolor="#1e293b")

            plt.tight_layout()
            st.pyplot(fig_rf)
            plt.close(fig_rf)

    with tab_z:
        with st.container(border=True):
            st.markdown('<div style="font-size: 0.92rem; font-weight: 600; color: #ffffff; margin-bottom: 8px;">Transformed Input Impedance Across Frequency (Rᵢₙ, Xᵢₙ, ∠S₁₁)</div>', unsafe_allow_html=True)
            
            fig_z, (ax_rin, ax_xin, ax_ph) = plt.subplots(3, 1, figsize=(10, 7.5), sharex=True)

            rin_plot = np.clip(rin, -100.0, 500.0)
            ax_rin.plot(f_ghz, rin_plot, color="#a855f7", lw=2, label="Rᵢₙ = Re(Zᵢₙ)")
            ax_rin.axhline(Z0, color="#64748b", linestyle="--", alpha=0.7, label=f"Z₀ = {Z0:.0f} Ω")
            ax_rin.set_ylabel("Resistance (Ω)", fontsize=8.5, color="#94a3b8")
            ax_rin.grid(True, color="#1e293b", alpha=0.6)
            ax_rin.tick_params(colors="#64748b", labelsize=8)
            for sp in ax_rin.spines.values(): sp.set_color("#1e293b")
            ax_rin.legend(loc="upper right", fontsize=8, facecolor="#0b0f17", edgecolor="#1e293b")

            xin_plot = np.clip(xin, -500.0, 500.0)
            ax_xin.plot(f_ghz, xin_plot, color="#ec4899", lw=2, label="Xᵢₙ = Im(Zᵢₙ)")
            ax_xin.axhline(0, color="#64748b", linestyle="-", alpha=0.5)
            ax_xin.set_ylabel("Reactance (Ω)", fontsize=8.5, color="#94a3b8")
            ax_xin.grid(True, color="#1e293b", alpha=0.6)
            ax_xin.tick_params(colors="#64748b", labelsize=8)
            for sp in ax_xin.spines.values(): sp.set_color("#1e293b")
            ax_xin.legend(loc="upper right", fontsize=8, facecolor="#0b0f17", edgecolor="#1e293b")

            ax_ph.plot(f_ghz, spectral_feat["phase_deg"], color="#38bdf8", lw=2, label="Unwrapped Phase ∠S₁₁ (deg)")
            ax_ph.set_ylabel("Phase (deg)", fontsize=8.5, color="#94a3b8")
            ax_ph.set_xlabel("Frequency (GHz)", fontsize=8.5, color="#94a3b8")
            ax_ph.grid(True, color="#1e293b", alpha=0.6)
            ax_ph.tick_params(colors="#64748b", labelsize=8)
            for sp in ax_ph.spines.values(): sp.set_color("#1e293b")
            ax_ph.legend(loc="upper right", fontsize=8, facecolor="#0b0f17", edgecolor="#1e293b")

            plt.tight_layout()
            st.pyplot(fig_z)
            plt.close(fig_z)

    with tab_smith:
        col_sm1, col_sm2 = st.columns([12, 8])
        with col_sm1:
            with st.container(border=True):
                st.markdown('<div style="font-size: 0.92rem; font-weight: 600; color: #ffffff; margin-bottom: 8px;">Normalized Reflection Locus Γ(f)</div>', unsafe_allow_html=True)
                fig_sm, ax_sm = plt.subplots(figsize=(6.5, 6.5))
                meas.smith_plot(sweep_dict["gamma"], ax=ax_sm, label=f"Sweep ({f_start_mhz:.0f}–{f_stop_mhz:.0f} MHz)")
                ax_sm.legend(loc="lower right", fontsize=8.5, facecolor="#0b0f17", edgecolor="#1e293b")
                plt.tight_layout()
                st.pyplot(fig_sm)
                plt.close(fig_sm)

        with col_sm2:
            with st.container(border=True):
                st.markdown('<div class="figma-metric-label">SMITH CHART LANDMARKS</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size: 0.8rem; color: #94a3b8; margin-top: 4px; margin-bottom: 14px;">Complex reflection mapped to normalized impedance <i>z</i> = <i>Z</i> / <i>Z</i><sub>0</sub>.</div>', unsafe_allow_html=True)

                st.markdown("""
                <div style="display: flex; flex-direction: column; gap: 10px;">
                  <div class="figma-pill-cell">
                    <div style="font-size: 0.72rem; color: #10b981; font-weight: 700;">● CENTRE (|Γ| = 0)</div>
                    <div style="font-size: 0.78rem; color: #cbd5e1; margin-top: 2px;">Matched load: <i>Z</i><sub>L</sub> = <i>Z</i><sub>0</sub>, Return Loss &rarr; &infin;, no reflection.</div>
                  </div>
                  <div class="figma-pill-cell">
                    <div style="font-size: 0.72rem; color: #ef4444; font-weight: 700;">● RIGHT EDGE (Γ = +1)</div>
                    <div style="font-size: 0.78rem; color: #cbd5e1; margin-top: 2px;">Open circuit: <i>Z</i><sub>L</sub> &rarr; &infin;, VSWR &rarr; &infin;, zero terminal current.</div>
                  </div>
                  <div class="figma-pill-cell">
                    <div style="font-size: 0.72rem; color: #ef4444; font-weight: 700;">● LEFT EDGE (Γ = −1)</div>
                    <div style="font-size: 0.78rem; color: #cbd5e1; margin-top: 2px;">Short circuit: <i>Z</i><sub>L</sub> = 0 &Omega;, terminal voltage cancellation.</div>
                  </div>
                  <div class="figma-pill-cell">
                    <div style="font-size: 0.72rem; color: #00e5ff; font-weight: 700;">● UPPER HALF (Im(Z) &gt; 0)</div>
                    <div style="font-size: 0.78rem; color: #cbd5e1; margin-top: 2px;">Inductive impedance: Series inductance or shorted line segment (<i>X</i><sub>L</sub> &gt; 0).</div>
                  </div>
                  <div class="figma-pill-cell">
                    <div style="font-size: 0.72rem; color: #a855f7; font-weight: 700;">● LOWER HALF (Im(Z) &lt; 0)</div>
                    <div style="font-size: 0.78rem; color: #cbd5e1; margin-top: 2px;">Capacitive impedance: Shunt capacitance or open stub section (<i>X</i><sub>C</sub> &lt; 0).</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

    render_footer()


# ─────────────────────────────────────────────────────────────────────────────
# VIEW 4: FAULT DIAGNOSIS ENGINE
# ─────────────────────────────────────────────────────────────────────────────
elif "diagnosis" in nav_section.lower():
    render_breadcrumb("FAULT DIAGNOSIS")
    render_page_header(
        "Transparent rule-based fault diagnosis",
        "Inferred strictly from single-port S11 measurements without access to simulation ground truth.",
    )

    st.markdown("""
    <div style="background: rgba(14, 165, 233, 0.08); border: 1px solid rgba(14, 165, 233, 0.25); border-radius: 10px; padding: 10px 16px; margin-bottom: 1.2rem; font-size: 0.8rem; color: #94a3b8;">
      ⚙️ <strong style="color: #38bdf8;">Engineering Tuning Note:</strong> Classifier threshold values (e.g., |Γ| &lt; 0.05, trend &gt; 0.010) are calibrated engineering parameters tuned to this coaxial operating range. They are transparent heuristic thresholds rather than universal electromagnetic constants.
    </div>
    """, unsafe_allow_html=True)

    diag_col1, diag_col2 = st.columns([8, 12])

    with diag_col1:
        with st.container(border=True):
            st.markdown('<div class="figma-metric-label">DIAGNOSTIC CLASSIFICATION</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div style="margin-top: 10px; display: flex; flex-direction: column; gap: 8px;">
              <div class="figma-pill-cell">
                <div style="font-size: 0.68rem; color: #64748b; font-weight: 700; text-transform: uppercase;">FROZEN CONTRACT CLASS</div>
                <div style="font-size: 1.1rem; color: #00e5ff; font-weight: 700; margin-top: 2px;">{str(inferred_class).upper()}</div>
              </div>
              <div class="figma-pill-cell">
                <div style="font-size: 0.68rem; color: #64748b; font-weight: 700; text-transform: uppercase;">PHYSICAL INFERRED SUBTYPE</div>
                <div style="font-size: 0.95rem; color: #ffffff; font-weight: 600; margin-top: 2px;">{inferred_class.subtype}</div>
              </div>
              <div class="figma-pill-cell">
                <div style="font-size: 0.68rem; color: #64748b; font-weight: 700; text-transform: uppercase;">DIAGNOSTIC CONFIDENCE</div>
                <div style="font-size: 0.95rem; color: #10b981; font-weight: 600; margin-top: 2px;">{inferred_class.confidence.upper()}</div>
              </div>
              <div class="figma-pill-cell">
                <div style="font-size: 0.68rem; color: #64748b; font-weight: 700; text-transform: uppercase;">RULES TRIGGERED</div>
                <div style="font-size: 0.8rem; color: #cbd5e1; margin-top: 2px; font-family: monospace;">{', '.join(inferred_class.rules_fired)}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown('<div style="font-size: 0.7rem; font-weight: 700; color: #64748b; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 8px;">OBSERVED SIGNAL EVIDENCE</div>', unsafe_allow_html=True)
            for e in diag_report["evidence"]:
                st.markdown(f"- {e}")

    with diag_col2:
        with st.container(border=True):
            st.markdown('<div style="font-size: 0.72rem; font-weight: 700; color: #00e5ff; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 8px;">ELECTROMAGNETIC PHYSICS EXPLANATION</div>', unsafe_allow_html=True)
            st.markdown(diag_report["physics_explanation"])

        with st.container(border=True):
            st.markdown('<div style="font-size: 0.72rem; font-weight: 700; color: #f59e0b; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 8px;">POTENTIAL AMBIGUITIES & LIMITATIONS</div>', unsafe_allow_html=True)
            for amb in diag_report["ambiguities"]:
                st.markdown(f"⚠️ {amb}")

        with st.container(border=True):
            st.markdown('<div style="font-size: 0.72rem; font-weight: 700; color: #10b981; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 8px;">RECOMMENDED CORRECTIVE ACTIONS</div>', unsafe_allow_html=True)
            for act in diag_report["corrective_actions"]:
                st.markdown(f"🔧 {act}")

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
        label="📥 Download Diagnostic Summary Report (TXT)",
        data=report_text,
        file_name="rf_line_doctor_diagnostic_report.txt",
        mime="text/plain",
    )

    render_footer()


# ─────────────────────────────────────────────────────────────────────────────
# VIEW 5: FAULT LOCATION (TDR & PHASE)
# ─────────────────────────────────────────────────────────────────────────────
elif "location" in nav_section.lower():
    render_breadcrumb("FAULT LOCATION")
    render_page_header(
        "Fault location: phase-slope estimation & IFFT verification",
        "Dual-method distance estimation derived from frequency-swept reflection data.",
    )

    th_col1, th_col2 = st.columns(2)
    with th_col1:
        with st.container(border=True):
            st.markdown('<div style="font-size: 0.74rem; font-weight: 700; color: #00e5ff; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px;">Primary Method — Phase Slope Analysis</div>', unsafe_allow_html=True)
            st.markdown("For a dominant boundary discontinuity at distance $d$, the round-trip delay imparts a linear phase ramp across frequency:")
            st.latex(r"\phi(f) \approx \phi_0 - \frac{4\pi d}{v_p}\,f \implies d = -\frac{v_p}{4\pi}\,\frac{d\phi}{df}")
            st.caption("Directly derived from course transmission-line phasor theory. Reactive discontinuities introduce minor frequency-dependent phase offsets.")

    with th_col2:
        with st.container(border=True):
            st.markdown('<div style="font-size: 0.74rem; font-weight: 700; color: #10b981; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px;">Supporting Cross-Check — IFFT Pseudo-TDR</div>', unsafe_allow_html=True)
            st.markdown("Inverse FFT with a Hann window synthesizes the pseudo-impulse reflection profile $|h(t)|$. A peak at round-trip time $t$ locates the reflection at:")
            st.latex(r"d = \frac{v_p\,t}{2}, \quad \Delta R = \frac{v_p}{2B}")
            st.caption("Zero-padding interpolates the peak centroid but does not exceed the physical Rayleigh resolution limit ΔR.")

    loc_col1, loc_col2 = st.columns([12, 8])

    with loc_col1:
        with st.container(border=True):
            st.markdown('<div style="font-size: 0.95rem; font-weight: 600; color: #ffffff;">IFFT Pseudo-Time Echo Response |h(t)|</div>', unsafe_allow_html=True)
            st.markdown('<div style="font-size: 0.75rem; color: #64748b; margin-top: 1px; margin-bottom: 8px;">Synthesized spatial reflection envelope with localized peak centroid</div>', unsafe_allow_html=True)

            tdr = loc_dual["tdr_data"]
            fig_tdr, ax_t = plt.subplots(figsize=(7.5, 3.8))

            if tdr.get("d_axis_m") is not None and len(tdr["d_axis_m"]) > 0:
                d_axis = tdr["d_axis_m"]
                t_mag = tdr["tdr_mag"]
                view_mask = d_axis <= max(length * 1.5, 2.0)
                ax_t.plot(d_axis[view_mask], t_mag[view_mask], color="#a855f7", lw=2, label="IFFT Echo Profile")

                d_est = loc_dual["dist_ifft_m"]
                if d_est is not None:
                    ax_t.axvline(d_est, color="#ef4444", linestyle="--", lw=1.8, label=f"Discontinuity Peak: {d_est:.3f} m")

                ax_t.set_xlabel("Physical Distance (m)", fontsize=9, color="#94a3b8")
                ax_t.set_ylabel("Reflection Magnitude |h(t)|", fontsize=9, color="#94a3b8")
                ax_t.grid(True, color="#1e293b", alpha=0.7)
                ax_t.tick_params(colors="#64748b", labelsize=8.5)
                for sp in ax_t.spines.values(): sp.set_color("#1e293b")
                ax_t.legend(loc="upper right", fontsize=8, facecolor="#0b0f17", edgecolor="#1e293b")

            plt.tight_layout()
            st.pyplot(fig_tdr)
            plt.close(fig_tdr)

    with loc_col2:
        d1 = loc_dual["dist_ifft_m"]
        d2 = loc_dual["dist_phase_m"]

        rel_badge = '<span style="color: #10b981; font-weight: 700;">● RELIABLE & VERIFIED</span>' if loc_dual["is_reliable"] else '<span style="color: #ef4444; font-weight: 700;">● HIGH UNCERTAINTY</span>'

        with st.container(border=True):
            st.markdown('<div class="figma-metric-label">LOCALIZATION RESULTS SUMMARY</div>', unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="margin-top: 10px; display: flex; flex-direction: column; gap: 8px;">
              <div class="figma-pill-cell">
                <div style="font-size: 0.68rem; color: #64748b; font-weight: 700; text-transform: uppercase;">PHASE-SLOPE ESTIMATE (PRIMARY, <i>d</i>)</div>
                <div style="font-size: 1rem; color: #00e5ff; font-weight: 600; margin-top: 2px;">
                  {f"{d2:.3f} m" if d2 is not None else "None (insufficient reflection)"}
                </div>
              </div>
              <div class="figma-pill-cell">
                <div style="font-size: 0.68rem; color: #64748b; font-weight: 700; text-transform: uppercase;">IFFT TDR CROSS-CHECK (SUPPORTING, <i>d</i>)</div>
                <div style="font-size: 1rem; color: #ffffff; font-weight: 600; margin-top: 2px;">
                  {f"{d1:.3f} m" if d1 is not None else "None (no clear echo)"}
                </div>
              </div>
              <div class="figma-pill-cell">
                <div style="font-size: 0.68rem; color: #64748b; font-weight: 700; text-transform: uppercase;">RAYLEIGH RESOLUTION LIMIT (&Delta;<i>R</i>)</div>
                <div style="font-size: 0.95rem; color: #cbd5e1; font-weight: 600; margin-top: 2px;">
                  {res_info['range_res_m']*100:.2f} cm
                </div>
              </div>
              <div class="figma-pill-cell">
                <div style="font-size: 0.68rem; color: #64748b; font-weight: 700; text-transform: uppercase;">UNAMBIGUOUS RANGE (<i>R</i><sub>max</sub>)</div>
                <div style="font-size: 0.95rem; color: #cbd5e1; font-weight: 600; margin-top: 2px;">
                  {res_info['unambig_range_m']:.2f} m
                </div>
              </div>
              <div class="figma-pill-cell">
                <div style="font-size: 0.68rem; color: #64748b; font-weight: 700; text-transform: uppercase;">ESTIMATION STATUS</div>
                <div style="font-size: 0.85rem; margin-top: 2px;">{rel_badge}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    render_footer()


# ─────────────────────────────────────────────────────────────────────────────
# VIEW 6: QUARTER-WAVE MATCHING STUDIO
# ─────────────────────────────────────────────────────────────────────────────
elif "matching" in nav_section.lower():
    render_breadcrumb("QUARTER-WAVE MATCHING")
    render_page_header(
        "Quarter-wave impedance matching studio",
        "Synthesis and passband evaluation of quarter-wave transformers using <i>Z</i><sub>t</sub> = &radic;(<i>Z</i><sub>0</sub> <i>R</i><sub>L</sub>).",
    )

    is_real = isinstance(ZL_val, complex) and np.isfinite(ZL_val.real) and ZL_val.real > 0 and abs(ZL_val.imag) < 1e-5

    if not is_real:
        st.markdown(f"""
        <div class="figma-card" style="border-left: 3px solid #f59e0b;">
          <div style="font-size: 0.88rem; font-weight: 600; color: #f59e0b;">⚠️ Real Load Requirement for Quarter-Wave Matching</div>
          <div style="font-size: 0.82rem; color: #cbd5e1; margin-top: 6px; line-height: 1.5;">
            Single-section quarter-wave transformers require a purely real load resistance <i>R</i><sub>L</sub> &gt; 0.<br>
            Current termination is <code><i>Z</i><sub>L</sub> = {ZL_val}</code>.<br>
            Select <strong>Case 2: Resistive Mismatch</strong> in the sidebar to design a matched transformer. Complex loads require reactive stub tuning.
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        RL_val = float(ZL_val.real)
        f_mid = float(np.mean(freqs))

        match_col1, match_col2 = st.columns([7, 13])

        with match_col1:
            with st.container(border=True):
                st.markdown('<div class="figma-metric-label">DESIGN PARAMETERS</div>', unsafe_allow_html=True)
                f_design_mhz = st.number_input("Design Frequency f₀ (MHz)", min_value=10.0, max_value=20000.0, value=f_mid / 1e6, step=50.0)
                f_design = f_design_mhz * 1e6

                match_res = match.compare_matching(Z0, RL_val, freqs, vf=vf, f_design=f_design, rl_threshold=20.0)
                f0_rl = match_res["at_f_design"]["rl_db"]
                rl_str = "∞ dB (Exact)" if np.isinf(f0_rl) else f"{f0_rl:.1f} dB"

                st.markdown(f"""
                <div style="display: flex; flex-direction: column; gap: 10px; margin-top: 12px;">
                  <div class="figma-metric-card">
                    <div class="figma-metric-label">TRANSFORMER IMPEDANCE (<i>Z</i><sub>t</sub>)</div>
                    <div class="figma-metric-val" style="color: #00e5ff;">{match_res['Zt']:.2f} Ω</div>
                    <div class="figma-metric-sub">Calculated via &radic;(<i>Z</i><sub>0</sub> &middot; <i>R</i><sub>L</sub>)</div>
                  </div>
                  <div class="figma-metric-card">
                    <div class="figma-metric-label">PHYSICAL LENGTH (<i>l</i><sub>t</sub>)</div>
                    <div class="figma-metric-val" style="color: #10b981;">{match_res['length_m']*1000:.1f} mm</div>
                    <div class="figma-metric-sub">Quarter-wave at {f_design_mhz:.0f} MHz (&lambda;/4)</div>
                  </div>
                  <div class="figma-metric-card">
                    <div class="figma-metric-label">USABLE BANDWIDTH (RL &ge; 20 dB)</div>
                    <div class="figma-metric-val" style="color: #f59e0b;">{match_res['bandwidth_hz']/1e6:.1f} MHz</div>
                    <div class="figma-metric-sub">Passband where VSWR &le; 1.22</div>
                  </div>
                  <div class="figma-metric-card">
                    <div class="figma-metric-label">MATCHED RETURN LOSS AT <i>f</i><sub>0</sub></div>
                    <div class="figma-metric-val" style="color: #38bdf8;">{rl_str}</div>
                    <div class="figma-metric-sub">Theoretical peak reflection attenuation</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

        with match_col2:
            with st.container(border=True):
                st.markdown('<div style="font-size: 0.95rem; font-weight: 600; color: #ffffff;">Performance Comparison (Before vs After Matching)</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size: 0.75rem; color: #64748b; margin-top: 1px; margin-bottom: 8px;">Evaluation of VSWR and return loss passband suppression</div>', unsafe_allow_html=True)

                fig_mc, (ax_mv, ax_mr) = plt.subplots(2, 1, figsize=(7.8, 5.8), sharex=True)

                # VSWR
                ax_mv.plot(f_ghz, match_res["before"]["vswr"], color="#ef4444", linestyle="--", lw=1.8, label="Before Matching (Unmatched)")
                ax_mv.plot(f_ghz, match_res["after"]["vswr"], color="#00e5ff", lw=2.2, label="After Matching (λ/4 Transformer)")
                ax_mv.axvline(f_design / 1e9, color="#64748b", linestyle=":", label=f"f₀ = {f_design/1e9:.2f} GHz")
                ax_mv.set_ylabel("VSWR", fontsize=8.5, color="#94a3b8")
                ax_mv.set_ylim(1.0, 3.5)
                ax_mv.grid(True, color="#1e293b", alpha=0.6)
                ax_mv.tick_params(colors="#64748b", labelsize=8)
                for sp in ax_mv.spines.values(): sp.set_color("#1e293b")
                ax_mv.legend(loc="upper right", fontsize=8, facecolor="#0b0f17", edgecolor="#1e293b")

                # Return Loss
                ax_mr.plot(f_ghz, match_res["before"]["rl_db"], color="#ef4444", linestyle="--", lw=1.8, label="Before Matching")
                ax_mr.plot(f_ghz, match_res["after"]["rl_db"], color="#10b981", lw=2.2, label="After Matching")
                ax_mr.axhline(20.0, color="#38bdf8", linestyle="--", label="20 dB Match Benchmark")
                ax_mr.axvline(f_design / 1e9, color="#64748b", linestyle=":")
                ax_mr.set_ylabel("Return Loss (dB)", fontsize=8.5, color="#94a3b8")
                ax_mr.set_xlabel("Frequency (GHz)", fontsize=8.5, color="#94a3b8")
                ax_mr.set_ylim(0, 50)
                ax_mr.grid(True, color="#1e293b", alpha=0.6)
                ax_mr.tick_params(colors="#64748b", labelsize=8)
                for sp in ax_mr.spines.values(): sp.set_color("#1e293b")
                ax_mr.legend(loc="lower right", fontsize=8, facecolor="#0b0f17", edgecolor="#1e293b")

                plt.tight_layout()
                st.pyplot(fig_mc)
                plt.close(fig_mc)

    render_footer()


# ─────────────────────────────────────────────────────────────────────────────
# VIEW 7: INDEPENDENT VALIDATION LAB
# ─────────────────────────────────────────────────────────────────────────────
elif "validation" in nav_section.lower():
    render_breadcrumb("VALIDATION LAB")
    render_page_header(
        "Independent validation laboratory",
        "Repeatable performance check across 120 randomized simulated line cases.",
    )

    with st.container(border=True):
        st.markdown('<div style="font-size: 0.88rem; font-weight: 600; color: #ffffff;">Repeatable Monte Carlo Simulation Suite</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 0.82rem; color: #94a3b8; margin-top: 4px; line-height: 1.5;">This automated test executes 120 randomized coaxial line configurations (20 trials per each of the 6 physical scenarios) with Gaussian measurement noise (σ = 0.02). The predicted condition is evaluated against the ground-truth simulation model to verify classifier reliability.</div>', unsafe_allow_html=True)

    if st.button("▶ Run Randomized Validation (120 Cases)"):
        with st.spinner("Executing randomized validation trials..."):
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

            v_col1, v_col2 = st.columns(2)
            with v_col1:
                with st.container(border=True):
                    st.markdown(f'<div class="figma-section-title">CONTRACT CONFUSION MATRIX (ACCURACY = {val_rep["accuracy"]*100:.1f}%)</div>', unsafe_allow_html=True)
                    df_vcm = pd.DataFrame(
                        val_rep["confusion_matrix"],
                        index=[f"True: {l}" for l in contract_labels],
                        columns=[f"Pred: {l}" for l in contract_labels],
                    )
                    st.dataframe(df_vcm)

            with v_col2:
                with st.container(border=True):
                    st.markdown('<div class="figma-section-title">PER-CLASS CLASSIFICATION METRICS</div>', unsafe_allow_html=True)
                    m_rows = []
                    for l in contract_labels:
                        r_dict = {"Class": l}
                        r_dict.update(val_rep["per_class"][l])
                        m_rows.append(r_dict)
                    st.dataframe(pd.DataFrame(m_rows))

            # Subtype 6-scenario evaluation
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

            s_col1, s_col2 = st.columns(2)
            with s_col1:
                with st.container(border=True):
                    st.markdown(f'<div class="figma-section-title">SUBTYPE CONFUSION MATRIX (6 SCENARIOS, ACCURACY = {sub_rep["accuracy"]*100:.1f}%)</div>', unsafe_allow_html=True)
                    df_scm = pd.DataFrame(
                        sub_rep["confusion_matrix"],
                        index=[f"True: {l}" for l in scen_labels],
                        columns=[f"Pred: {l}" for l in scen_labels],
                    )
                    st.dataframe(df_scm)

            with s_col2:
                with st.container(border=True):
                    st.markdown('<div class="figma-section-title">SUBTYPE CLASSIFICATION METRICS</div>', unsafe_allow_html=True)
                    sm_rows = []
                    for l in scen_labels:
                        sr_dict = {"Scenario": l}
                        sr_dict.update(sub_rep["per_class"][l])
                        sm_rows.append(sr_dict)
                    st.dataframe(pd.DataFrame(sm_rows))

            t_locs = [it["true_pos"] for it in v_dataset if it["true_pos"] is not None]
            e_locs = [it["est_pos"] for it in v_dataset if it["true_pos"] is not None]
            l_stats = compute_location_metrics(t_locs, e_locs)
            st.success(f"**Fault-Location Metric:** MAE = `{l_stats['mae_m']*100:.2f} cm` | RMSE = `{l_stats['rmse_m']*100:.2f} cm` (Valid Cases: {l_stats['valid_count']}/{len(t_locs)})")

    render_footer()
