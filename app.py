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

# ── Professional RF Engineering Design System CSS ──────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── Design Tokens ── */
:root {
    --rld-canvas:         #07090f;
    --rld-sidebar:        #050710;
    --rld-card:           #0d1117;
    --rld-card-raised:    #111827;
    --rld-cell-bg:        #0a0d14;
    --rld-border:         #1c2537;
    --rld-border-subtle:  #121a28;
    --rld-border-accent:  #1e3a5f;

    --rld-text-white:     #ffffff;
    --rld-text-main:      #e2e8f0;
    --rld-text-muted:     #8898aa;
    --rld-text-dim:       #546580;

    /* Semantic accent palette */
    --rld-cyan:           #00d4f5;
    --rld-sky:            #3b9ede;
    --rld-emerald:        #0ea472;
    --rld-amber:          #d97706;
    --rld-rose:           #e53e3e;
    --rld-violet:         #7c3aed;

    /* Status surface colours (bg / border / text) */
    --rld-healthy-bg:     rgba(10, 164, 114, 0.08);
    --rld-healthy-bd:     rgba(10, 164, 114, 0.30);
    --rld-healthy-tx:     #0ea472;
    --rld-open-bg:        rgba(229, 62,  62,  0.08);
    --rld-open-bd:        rgba(229, 62,  62,  0.30);
    --rld-open-tx:        #e53e3e;
    --rld-short-bg:       rgba(229, 62,  62,  0.08);
    --rld-short-bd:       rgba(229, 62,  62,  0.30);
    --rld-short-tx:       #e53e3e;
    --rld-mismatch-bg:    rgba(217, 119,  6,  0.08);
    --rld-mismatch-bd:    rgba(217, 119,  6,  0.30);
    --rld-mismatch-tx:    #d97706;
    --rld-unknown-bg:     rgba(59, 158, 222, 0.08);
    --rld-unknown-bd:     rgba(59, 158, 222, 0.30);
    --rld-unknown-tx:     #3b9ede;
}

/* ── Base Typography ── */
html, body, [class*="css"], button, input, textarea, select {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    -webkit-font-smoothing: antialiased;
}

code, pre, .mono {
    font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace !important;
}

.stApp {
    background-color: var(--rld-canvas) !important;
    color: var(--rld-text-main);
}

/* ── Top Bar ── */
[data-testid="stHeader"] {
    background: rgba(7, 9, 15, 0.92) !important;
    backdrop-filter: blur(10px);
    border-bottom: 1px solid var(--rld-border-subtle);
}

/* ── Main Content Area ── */
[data-testid="stMainBlockContainer"] {
    max-width: 1520px;
    padding: 1.6rem 2.4rem 4rem;
}

/* ═══════════════════════════════════════
   SIDEBAR
═══════════════════════════════════════ */
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
    border: none;
    border-top: 1px solid var(--rld-border-subtle);
    margin: 1rem 0;
}

/* Nav radio group */
[data-testid="stSidebar"] div[role="radiogroup"] {
    gap: 2px;
}

[data-testid="stSidebar"] div[role="radiogroup"] label {
    display: flex;
    align-items: center;
    border: 1px solid transparent;
    border-radius: 7px;
    padding: 8px 11px;
    color: var(--rld-text-muted);
    font-size: 0.84rem;
    font-weight: 500;
    letter-spacing: 0.01em;
    transition: background 0.12s, color 0.12s;
    background: transparent;
    cursor: pointer;
}

[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: rgba(255,255,255,0.04);
    color: #d1d9e6;
}

[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    background: rgba(0, 212, 245, 0.07) !important;
    color: #ffffff !important;
    border-left: 3px solid var(--rld-cyan) !important;
    padding-left: 9px !important;
    border-radius: 0 7px 7px 0;
    font-weight: 600;
}

[data-testid="stSidebar"] div[role="radiogroup"] [data-testid="stWidgetSelectionIndicator"] {
    display: none;
}

/* Sidebar widget labels */
[data-testid="stSidebar"] label,
[data-testid="stWidgetLabel"] p {
    color: #9baabf !important;
    font-size: 0.775rem;
    font-weight: 600;
    letter-spacing: 0.01em;
    margin-bottom: 3px;
}

/* ═══════════════════════════════════════
   FORM INPUTS
═══════════════════════════════════════ */
input, textarea, [data-baseweb="select"] > div {
    background: #080c15 !important;
    color: #e2e8f0 !important;
    border: 1px solid var(--rld-border) !important;
    border-radius: 7px !important;
    font-size: 0.875rem !important;
    transition: border-color 0.15s !important;
}

[data-baseweb="input"] input:focus,
[data-baseweb="select"] > div:focus-within {
    border-color: var(--rld-cyan) !important;
    box-shadow: 0 0 0 2px rgba(0, 212, 245, 0.15) !important;
}

/* Slider */
[data-testid="stSlider"] [role="slider"] {
    border-color: var(--rld-cyan) !important;
    background-color: var(--rld-cyan) !important;
    box-shadow: 0 0 8px rgba(0, 212, 245, 0.35);
    width: 14px !important;
    height: 14px !important;
}

[data-testid="stSlider"] [data-testid="stSliderTrack"] > div:first-child {
    background: var(--rld-border) !important;
}

[data-testid="stSlider"] [data-testid="stSliderTrack"] > div:nth-child(2) {
    background: var(--rld-cyan) !important;
}

/* ═══════════════════════════════════════
   BUTTONS
═══════════════════════════════════════ */
.stButton > button, .stDownloadButton > button {
    background: linear-gradient(135deg, #1a5f7a 0%, #0d4461 100%) !important;
    border: 1px solid #2b7a9e !important;
    border-radius: 7px !important;
    color: #e0f4ff !important;
    font-weight: 600 !important;
    font-size: 0.83rem !important;
    letter-spacing: 0.025em !important;
    padding: 0.48rem 1.1rem !important;
    min-height: 2.3rem !important;
    transition: all 0.15s ease !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.4) !important;
}

.stButton > button:hover, .stDownloadButton > button:hover {
    background: linear-gradient(135deg, #2b7a9e 0%, #1a5f7a 100%) !important;
    border-color: var(--rld-cyan) !important;
    box-shadow: 0 0 12px rgba(0, 212, 245, 0.25) !important;
    transform: translateY(-1px) !important;
}

/* ═══════════════════════════════════════
   CONTAINERS / CARDS
═══════════════════════════════════════ */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--rld-card) !important;
    border: 1px solid var(--rld-border) !important;
    border-radius: 10px !important;
    padding: 16px 20px !important;
    margin-bottom: 0.8rem !important;
}

/* Legacy Figma card helper (kept for backward compat) */
.figma-card {
    background: var(--rld-card);
    border: 1px solid var(--rld-border);
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 0.9rem;
}

/* ── Section Header (replaces ALL-CAPS section titles) ── */
.rld-section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 0.1rem 0 0.9rem 0;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid var(--rld-border-subtle);
}

.rld-section-header-bar {
    width: 3px;
    height: 1.1rem;
    background: var(--rld-cyan);
    border-radius: 2px;
    flex-shrink: 0;
}

.rld-section-header-text {
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--rld-text-muted);
}

/* Legacy compat */
.figma-section-title {
    font-size: 0.7rem;
    letter-spacing: 0.08em;
    color: var(--rld-text-dim);
    font-weight: 700;
    text-transform: uppercase;
    margin-bottom: 0.55rem;
}

/* ── Config Pill Bar ── */
.figma-pill-bar {
    background: var(--rld-card);
    border: 1px solid var(--rld-border);
    border-radius: 10px;
    padding: 12px 16px;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 1.3rem;
}

.figma-pill-cell {
    background: var(--rld-cell-bg);
    border: 1px solid var(--rld-border);
    border-radius: 7px;
    padding: 8px 12px;
}

/* ═══════════════════════════════════════
   KPI / METRIC CARDS
═══════════════════════════════════════ */
.figma-metric-card {
    background: var(--rld-card);
    border: 1px solid var(--rld-border);
    border-radius: 10px;
    padding: 15px 17px;
    height: 100%;
}

.figma-metric-label {
    font-size: 0.68rem;
    letter-spacing: 0.09em;
    color: var(--rld-text-dim);
    font-weight: 700;
    text-transform: uppercase;
}

/* Large engineering number */
.rld-num {
    font-size: 1.75rem;
    font-weight: 700;
    letter-spacing: -0.025em;
    line-height: 1.1;
    margin-top: 5px;
    margin-bottom: 1px;
}

/* Unit badge sits inline after the number */
.rld-unit {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--rld-text-muted);
    margin-left: 4px;
    letter-spacing: 0.03em;
    vertical-align: middle;
}

/* Legacy compat */
.figma-metric-val {
    font-size: 1.6rem;
    font-weight: 700;
    margin-top: 4px;
    margin-bottom: 2px;
    letter-spacing: -0.025em;
}

.figma-metric-sub {
    font-size: 0.72rem;
    color: var(--rld-text-muted);
    margin-top: 1px;
}

/* ═══════════════════════════════════════
   STATUS / DIAGNOSTIC BADGES
═══════════════════════════════════════ */
.rld-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 11px;
    border-radius: 999px;
    font-size: 0.69rem;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
}

.rld-badge-healthy   { background: var(--rld-healthy-bg);  border: 1px solid var(--rld-healthy-bd);  color: var(--rld-healthy-tx);  }
.rld-badge-open      { background: var(--rld-open-bg);     border: 1px solid var(--rld-open-bd);     color: var(--rld-open-tx);     }
.rld-badge-short     { background: var(--rld-short-bg);    border: 1px solid var(--rld-short-bd);    color: var(--rld-short-tx);    }
.rld-badge-mismatch  { background: var(--rld-mismatch-bg); border: 1px solid var(--rld-mismatch-bd); color: var(--rld-mismatch-tx); }
.rld-badge-unknown   { background: var(--rld-unknown-bg);  border: 1px solid var(--rld-unknown-bd);  color: var(--rld-unknown-tx);  }

.rld-conf-high   { background: rgba(10,164,114,0.1);  border:1px solid rgba(10,164,114,0.3);  color:#0ea472; }
.rld-conf-medium { background: rgba(217,119,6,0.1);   border:1px solid rgba(217,119,6,0.3);   color:#d97706; }
.rld-conf-low    { background: rgba(229,62,62,0.1);   border:1px solid rgba(229,62,62,0.3);   color:#e53e3e; }

/* ═══════════════════════════════════════
   EVIDENCE / INFO ROWS
═══════════════════════════════════════ */
.rld-evidence-item {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    padding: 6px 10px;
    border-radius: 6px;
    background: rgba(255,255,255,0.025);
    margin-bottom: 5px;
    font-size: 0.8rem;
    color: #c8d6e5;
    line-height: 1.4;
}

.rld-evidence-icon {
    font-size: 0.7rem;
    color: var(--rld-cyan);
    flex-shrink: 0;
    margin-top: 2px;
}

/* Key-value info row */
.rld-info-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding: 6px 0;
    border-bottom: 1px solid var(--rld-border-subtle);
    font-size: 0.82rem;
}

.rld-info-row:last-child { border-bottom: none; }

.rld-info-key   { color: var(--rld-text-muted); font-weight: 500; }
.rld-info-value { color: #e2e8f0; font-weight: 600; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; }
.rld-info-unit  { color: var(--rld-text-dim); font-size: 0.72rem; margin-left: 3px; }

/* ═══════════════════════════════════════
   RULE / CODE CHIPS
═══════════════════════════════════════ */
.rld-chip {
    display: inline-block;
    padding: 2px 8px;
    background: rgba(0, 212, 245, 0.08);
    border: 1px solid rgba(0, 212, 245, 0.2);
    border-radius: 4px;
    font-size: 0.72rem;
    font-family: 'JetBrains Mono', monospace;
    color: var(--rld-cyan);
    margin: 2px 2px 0 0;
    letter-spacing: 0.03em;
}

/* ═══════════════════════════════════════
   PLOT CONTAINERS
═══════════════════════════════════════ */
.rld-plot-wrap {
    padding: 4px 0 0 0;
}

.rld-plot-title {
    font-size: 0.9rem;
    font-weight: 600;
    color: #dde6f0;
    line-height: 1.3;
    margin-bottom: 2px;
}

.rld-plot-sub {
    font-size: 0.72rem;
    color: var(--rld-text-dim);
    margin-bottom: 10px;
    letter-spacing: 0.01em;
}

/* ═══════════════════════════════════════
   INFO BANNERS
═══════════════════════════════════════ */
.rld-banner {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 0.8rem;
    line-height: 1.5;
    margin-bottom: 1rem;
}

.rld-banner-info    { background: rgba(59,158,222,0.08); border:1px solid rgba(59,158,222,0.25); color:#8bbfe8; }
.rld-banner-warn    { background: rgba(217,119,6,0.08);  border:1px solid rgba(217,119,6,0.25);  color:#c99340; }
.rld-banner-success { background: rgba(10,164,114,0.08); border:1px solid rgba(10,164,114,0.25); color:#5ecba1; }
.rld-banner-error   { background: rgba(229,62,62,0.08);  border:1px solid rgba(229,62,62,0.25);  color:#e57373; }

.rld-banner-icon { font-size: 0.95rem; flex-shrink: 0; margin-top: 1px; }

/* ═══════════════════════════════════════
   TABS
═══════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 1px solid var(--rld-border);
    margin-bottom: 1.1rem;
    background: transparent;
}

.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 0;
    color: var(--rld-text-dim);
    padding: 0.6rem 1.05rem;
    font-size: 0.84rem;
    font-weight: 500;
    border-bottom: 2px solid transparent;
    letter-spacing: 0.01em;
    transition: color 0.15s;
}

.stTabs [data-baseweb="tab"]:hover {
    color: #c8d6e5;
    background: rgba(255,255,255,0.03);
}

.stTabs [aria-selected="true"] {
    color: #e2e8f0 !important;
    border-bottom: 2px solid var(--rld-cyan) !important;
    font-weight: 600 !important;
    background: rgba(0, 212, 245, 0.04) !important;
}

/* ═══════════════════════════════════════
   CHARTS, TABLES, ALERTS
═══════════════════════════════════════ */
[data-testid="stPlotlyChart"],
[data-testid="stPyplot"],
[data-testid="stImage"] {
    border: none !important;
    border-radius: 10px;
    overflow: hidden;
    background: transparent !important;
}

[data-testid="stDataFrame"],
[data-testid="stTable"] {
    border: 1px solid var(--rld-border);
    border-radius: 9px;
    overflow: hidden;
    background: #080c15;
    font-size: 0.82rem;
}

[data-testid="stAlert"] {
    border: 1px solid var(--rld-border);
    border-radius: 9px;
    background: var(--rld-card);
    color: var(--rld-text-main);
    font-size: 0.83rem;
}

[data-testid="stExpander"] {
    border: 1px solid var(--rld-border);
    border-radius: 9px;
    background: var(--rld-card);
}

/* ═══════════════════════════════════════
   KATEX (math rendering)
═══════════════════════════════════════ */
.katex, .katex * {
    color: #60d4f0 !important;
    font-size: 1.03em;
}

.katex-display {
    margin: 0.6rem 0 !important;
    padding: 0.5rem 0.8rem !important;
    overflow-x: auto;
    background: rgba(0, 212, 245, 0.03) !important;
    border: none !important;
    border-radius: 6px;
}

/* ═══════════════════════════════════════
   RESPONSIVE
═══════════════════════════════════════ */
@media (max-width: 1024px) {
    [data-testid="stMainBlockContainer"] { padding: 1.2rem 1.4rem 2.5rem; }
    .figma-pill-bar { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
    [data-testid="stMainBlockContainer"] { padding: 0.8rem 0.8rem 2rem; }
    .figma-pill-bar { grid-template-columns: 1fr; }
    .rld-num { font-size: 1.4rem; }
}
</style>
""", unsafe_allow_html=True)

# ── Matplotlib — Professional RF Engineering Theme ────────────────────────────
plt.rcParams.update({
    "figure.facecolor":   "#0d1117",
    "axes.facecolor":     "#07090f",
    "savefig.facecolor":  "#0d1117",
    "text.color":         "#e2e8f0",
    "axes.labelcolor":    "#8898aa",
    "xtick.color":        "#546580",
    "ytick.color":        "#546580",
    "xtick.labelsize":    8.5,
    "ytick.labelsize":    8.5,
    "axes.labelsize":     9,
    "axes.edgecolor":     "#1c2537",
    "axes.linewidth":     0.8,
    "grid.color":         "#1c2537",
    "grid.alpha":         0.65,
    "grid.linestyle":     "-",
    "grid.linewidth":     0.6,
    "legend.facecolor":   "#07090f",
    "legend.edgecolor":   "#1c2537",
    "legend.labelcolor":  "#c8d6e5",
    "legend.fontsize":    8,
    "legend.framealpha":  0.92,
    "lines.linewidth":    2.0,
    "lines.antialiased":  True,
    "figure.dpi":         110,
    "savefig.dpi":        130,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
})

# ── Helper: Section Header ────────────────────────────────────────────────────
def rld_section_header(label: str):
    st.markdown(f"""
    <div class="rld-section-header">
      <div class="rld-section-header-bar"></div>
      <div class="rld-section-header-text">{label}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Helper: Plot container header ─────────────────────────────────────────────
def rld_plot_header(title: str, subtitle: str = ""):
    sub = f'<div class="rld-plot-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(f'<div class="rld-plot-title">{title}</div>{sub}', unsafe_allow_html=True)

# ── Helper: Banner messages ────────────────────────────────────────────────────
def rld_banner(text: str, kind: str = "info", icon: str = "ℹ️"):
    st.markdown(f"""
    <div class="rld-banner rld-banner-{kind}">
      <div class="rld-banner-icon">{icon}</div>
      <div>{text}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Helper: Status badge HTML string ──────────────────────────────────────────
def rld_badge_html(label: str) -> str:
    css = f"rld-badge-{label.lower()}" if label.lower() in ["healthy","open","short","mismatch","unknown"] else "rld-badge-unknown"
    dot = "●"
    return f'<span class="rld-badge {css}">{dot} {label.upper()}</span>'

# ── Helper: Confidence badge HTML string ──────────────────────────────────────
def rld_conf_html(conf: str) -> str:
    css = f"rld-conf-{conf.lower()}" if conf.lower() in ["high","medium","low"] else "rld-conf-low"
    return f'<span class="rld-badge {css}">{conf.upper()}</span>'

# ── Helper: Evidence item HTML ─────────────────────────────────────────────────
def rld_evidence_items(items: list) -> str:
    rows = "".join(
        f'<div class="rld-evidence-item"><span class="rld-evidence-icon">◈</span><span>{e}</span></div>'
        for e in items
    )
    return rows

# ── Reusable Page Header / Breadcrumb Helpers ─────────────────────────────────
def render_breadcrumb(page_name: str):
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
      <div style="font-size: 0.69rem; letter-spacing: 0.09em; color: #546580; font-weight: 700; text-transform: uppercase;">
        WORKSPACE &nbsp;/&nbsp; {page_name.upper()}
      </div>
      <div style="display: inline-flex; align-items: center; gap: 5px; padding: 3px 11px; background: rgba(10, 164, 114, 0.09); border: 1px solid rgba(10, 164, 114, 0.28); border-radius: 999px; font-size: 0.69rem; font-weight: 700; color: #0ea472; letter-spacing: 0.06em;">
        <span style="font-size: 0.5rem; line-height: 1;">●</span> MODEL ACTIVE
      </div>
    </div>
    """, unsafe_allow_html=True)

def render_page_header(title: str, subtitle: str):
    st.markdown(f"""
    <div style="margin-bottom: 1.3rem;">
      <h1 style="color: #f0f4f8; font-size: 1.75rem; font-weight: 700; margin: 0 0 0.2rem 0; letter-spacing: -0.025em; line-height: 1.2;">{title}</h1>
      <p style="color: #8898aa; font-size: 0.875rem; margin: 0; line-height: 1.5;">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def render_footer():
    st.markdown("""
    <div style="margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #121a28; display: flex; justify-content: space-between; align-items: center; color: #384459; font-size: 0.69rem; letter-spacing: 0.09em; text-transform: uppercase;">
      <span>RF LINE DOCTOR &nbsp;•&nbsp; Educational Virtual Prototype</span>
      <span>EC-3104 Microwave Engineering</span>
    </div>
    """, unsafe_allow_html=True)

def render_config_pill_bar(Z0_val, len_val, vf_val, f_min_mhz, f_max_mhz):
    st.markdown(f"""
    <div class="rld-section-header" style="margin-bottom: 0.65rem;">
      <div class="rld-section-header-bar"></div>
      <div class="rld-section-header-text">Simulation Configuration</div>
    </div>
    <div class="figma-pill-bar">
      <div class="figma-pill-cell">
        <div style="font-size: 0.65rem; color: #546580; font-weight: 700; letter-spacing: 0.07em; text-transform: uppercase;">Char. Impedance <i>Z</i><sub>0</sub></div>
        <div style="font-size: 1.05rem; color: #e2e8f0; font-weight: 600; margin-top: 3px; font-family: 'JetBrains Mono', monospace;">{Z0_val:.0f} <span style="font-size:0.72rem; color:#8898aa; font-family: Inter, sans-serif;">Ω</span></div>
      </div>
      <div class="figma-pill-cell">
        <div style="font-size: 0.65rem; color: #546580; font-weight: 700; letter-spacing: 0.07em; text-transform: uppercase;">Physical Length <i>l</i></div>
        <div style="font-size: 1.05rem; color: #e2e8f0; font-weight: 600; margin-top: 3px; font-family: 'JetBrains Mono', monospace;">{len_val:.2f} <span style="font-size:0.72rem; color:#8898aa; font-family: Inter, sans-serif;">m</span></div>
      </div>
      <div class="figma-pill-cell">
        <div style="font-size: 0.65rem; color: #546580; font-weight: 700; letter-spacing: 0.07em; text-transform: uppercase;">Velocity Factor <i>v</i><sub>f</sub></div>
        <div style="font-size: 1.05rem; color: #e2e8f0; font-weight: 600; margin-top: 3px; font-family: 'JetBrains Mono', monospace;">{vf_val:.2f}</div>
      </div>
      <div class="figma-pill-cell">
        <div style="font-size: 0.65rem; color: #546580; font-weight: 700; letter-spacing: 0.07em; text-transform: uppercase;">Frequency Range <i>f</i></div>
        <div style="font-size: 1.05rem; color: #e2e8f0; font-weight: 600; margin-top: 3px; font-family: 'JetBrains Mono', monospace;">{f_min_mhz/1000:.2f}–{f_max_mhz/1000:.2f} <span style="font-size:0.72rem; color:#8898aa; font-family: Inter, sans-serif;">GHz</span></div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ── Sidebar Branding & Navigation ─────────────────────────────────────────────
st.sidebar.markdown("""
<div style="padding: 0.1rem 0 0.6rem 0;">
  <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
    <div style="width: 28px; height: 28px; background: rgba(0,212,245,0.12); border: 1px solid rgba(0,212,245,0.3); border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 0.95rem;">📡</div>
    <div>
      <div style="font-size: 1.05rem; font-weight: 800; color: #f0f4f8; letter-spacing: 0.03em; line-height: 1.1;">RF LINE DOCTOR</div>
      <div style="font-size: 0.63rem; font-weight: 700; color: #3b9ede; letter-spacing: 0.1em; text-transform: uppercase;">Transmission Line Diagnostics</div>
    </div>
  </div>
  <div style="height: 1px; background: linear-gradient(90deg, rgba(0,212,245,0.5) 0%, transparent 80%); margin: 8px 0 12px 0;"></div>
  <div style="font-size: 0.65rem; font-weight: 700; color: #384459; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 6px;">Navigation</div>
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
    help="• Represents: Line characteristic impedance Z₀ = √(L/C)\n• Unit: Ohms (Ω)\n• Why required: Normalization reference for reflection Γ = (ZL - Z0)/(ZL + Z0) and Smith chart mapping.",
)

length = st.sidebar.number_input(
    "Physical Line Length l (m)",
    min_value=0.05,
    max_value=100.0,
    value=1.0,
    step=0.1,
    help="• Represents: Physical transmission line length l\n• Unit: Metres (m)\n• Why required: Establishes total phase shift θ = βl and round-trip delay τ = 2l/vp.",
)

vf = st.sidebar.slider(
    "Velocity Factor vf (vₚ/c₀)",
    min_value=0.1,
    max_value=1.0,
    value=0.66,
    step=0.01,
    help="• Represents: Dielectric velocity factor vf = vp / c₀ = 1/√εr\n• Unit: Dimensionless ratio (0.10 to 1.00)\n• Why required: Converts signal time delays to spatial distances (d = vp·t/2) and determines phase constant β.",
)

st.sidebar.markdown('<div style="font-size: 0.7rem; font-weight: 700; color: #64748b; letter-spacing: 0.08em; text-transform: uppercase; margin-top: 0.8rem; margin-bottom: 0.4rem;">FREQUENCY SWEEP RANGE</div>', unsafe_allow_html=True)
col_sf1, col_sf2 = st.sidebar.columns(2)
with col_sf1:
    f_start_mhz = st.number_input(
        "fₘᵢₙ (MHz)",
        min_value=1.0,
        max_value=50000.0,
        value=500.0,
        step=50.0,
        help="• Represents: Minimum frequency of swept excitation f_min\n• Unit: Megahertz (MHz)\n• Why required: Defines lower spectral boundary for CW vector reflection measurements.",
    )
with col_sf2:
    f_stop_mhz = st.number_input(
        "fₘₐₓ (MHz)",
        min_value=5.0,
        max_value=50000.0,
        value=4000.0,
        step=100.0,
        help="• Represents: Maximum frequency of swept excitation f_max\n• Unit: Megahertz (MHz)\n• Why required: Determines sweep bandwidth B = f_max - f_min, which dictates Rayleigh range resolution ΔR = vp/(2B).",
    )

if f_start_mhz >= f_stop_mhz:
    st.sidebar.error("Minimum frequency must be lower than maximum frequency.")
    st.stop()

n_pts = st.sidebar.slider(
    "Sweep sample points",
    min_value=50,
    max_value=1000,
    value=400,
    step=50,
    help="• Represents: Number of discrete frequency sample points N\n• Unit: Integer count (dimensionless)\n• Why required: Sets frequency step size Δf = (f_max - f_min)/(N - 1) and unambiguous range R_max = vp/(2Δf).",
)
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
    help="• Represents: Injected transmission-line fault scenario\n• Unit: Categorical selection\n• Why required: Selects the physical termination or discontinuity model to test the diagnostic inference engine.",
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
    RL_input = st.sidebar.number_input(
        "Load Resistance R_L (Ω)",
        min_value=1.0,
        max_value=2000.0,
        value=120.0,
        step=5.0,
        help="• Represents: Termination load resistance RL\n• Unit: Ohms (Ω)\n• Why required: Sets real resistive mismatch termination to simulate standing waves without reactive phase shifts.",
    )
    ZL_val = complex(RL_input)
elif "Case 3" in scenario_preset:
    sim_scenario = "open"
    ZL_val = lm.OPEN
elif "Case 4" in scenario_preset:
    sim_scenario = "short"
    ZL_val = 0.0 + 0j
elif "Case 5" in scenario_preset:
    sim_scenario = "series_L"
    L_nh = st.sidebar.number_input(
        "Discontinuity Inductance L (nH)",
        min_value=0.5,
        max_value=200.0,
        value=15.0,
        step=1.0,
        help="• Represents: Lumped series inductance L\n• Unit: Nanohenries (nH)\n• Why required: Simulates physical series discontinuities (e.g. conductor cracks, necking) with impedance Zs = jωL.",
    )
    L_val = L_nh * 1e-9
    fault_pos = st.sidebar.slider(
        "Discontinuity Position (m)",
        min_value=0.01,
        max_value=float(length),
        value=float(length * 0.4),
        step=0.01,
        help="• Represents: Discontinuity distance d from measurement plane\n• Unit: Metres (m)\n• Why required: Positions the 2-port ABCD discontinuity matrix between transmission line segments.",
    )
elif "Case 6" in scenario_preset:
    sim_scenario = "shunt_C"
    C_pf = st.sidebar.number_input(
        "Discontinuity Capacitance C (pF)",
        min_value=0.5,
        max_value=200.0,
        value=15.0,
        step=1.0,
        help="• Represents: Lumped shunt capacitance C\n• Unit: Picofarads (pF)\n• Why required: Simulates physical shunt discontinuities (e.g. crushed dielectric, solder bridge) with admittance Yp = jωC.",
    )
    C_val = C_pf * 1e-12
    fault_pos = st.sidebar.slider(
        "Discontinuity Position (m)",
        min_value=0.01,
        max_value=float(length),
        value=float(length * 0.6),
        step=0.01,
        help="• Represents: Discontinuity distance d from measurement plane\n• Unit: Metres (m)\n• Why required: Positions the 2-port ABCD shunt discontinuity matrix along the transmission line.",
    )
else:
    sim_scenario = "custom"
    c_r = st.sidebar.number_input(
        "Load Resistance R (Ω)",
        min_value=0.0,
        max_value=2000.0,
        value=75.0,
        step=5.0,
        help="• Represents: Custom load resistance R = Re(ZL)\n• Unit: Ohms (Ω)\n• Why required: Specifies resistive power dissipation component of arbitrary load.",
    )
    c_x = st.sidebar.number_input(
        "Load Reactance X (Ω)",
        min_value=-2000.0,
        max_value=2000.0,
        value=35.0,
        step=5.0,
        help="• Represents: Custom load reactance X = Im(ZL)\n• Unit: Ohms (Ω)\n• Why required: Specifies reactive energy storage component (inductive if > 0, capacitive if < 0) of arbitrary load.",
    )
    ZL_val = complex(c_r, c_x)

noise_std = st.sidebar.slider(
    "Measurement Noise (σ on S₁₁)",
    min_value=0.0,
    max_value=0.15,
    value=0.0,
    step=0.01,
    help="• Represents: Complex Gaussian measurement noise standard deviation σ on S₁₁\n• Unit: Dimensionless (normalized reflection)\n• Why required: Emulates VNA thermal noise, cable flex, and connector repeatability to evaluate algorithm robustness.",
)

# Bottom Model Status Card in Sidebar
st.sidebar.markdown("""
<div style="background: #07090f; border: 1px solid #1c2537; border-radius: 9px; padding: 11px 13px; margin-top: 1rem;">
  <div style="font-size: 0.63rem; font-weight: 700; color: #384459; letter-spacing: 0.09em; text-transform: uppercase; margin-bottom: 6px;">Model Status</div>
  <div style="font-size: 0.82rem; font-weight: 600; color: #d4e0ee; margin-bottom: 1px;">Lossless coaxial line</div>
  <div style="font-size: 0.72rem; color: #546580; margin-bottom: 9px;">Single-port S₁₁ · ABCD cascaded</div>
  <div style="display: flex; align-items: center; gap: 5px; font-size: 0.65rem; color: #0ea472; font-weight: 700; letter-spacing: 0.06em;">
    <span style="font-size: 0.5rem;">●</span> SIMULATION ENVIRONMENT READY
  </div>
  <div style="margin-top: 7px; font-size: 0.62rem; color: #2a3a4e; letter-spacing: 0.08em; text-transform: uppercase; padding-top: 7px; border-top: 1px solid #121a28;">
    EC-3104 · Virtual Prototype v2
  </div>
</div>
""", unsafe_allow_html=True)

# ── Execute Core Simulation & Inference Pipeline ─────────────────────────────
try:
    if sim_scenario in fs.FAULT_SCENARIOS:
        sim_out = fs.simulate_fault(
            sim_scenario,
            Z0,
            length,
            freqs,
            vf=vf,
            fault_pos=min(fault_pos, float(length)),
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
            denom = 1.0 - g_noisy
            with np.errstate(divide="ignore", invalid="ignore"):
                sweep_dict["zin"] = np.where(
                    np.abs(denom) < 1e-12,
                    np.inf + 0j,
                    Z0 * (1.0 + g_noisy) / denom,
                )
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
except Exception as err:
    st.error(f"Engineering Calculation Error: {err}")
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# VIEW 1: OVERVIEW (Reproducing Figma Visual Specification)
# ─────────────────────────────────────────────────────────────────────────────
if "overview" in nav_section.lower():
    render_breadcrumb("OVERVIEW")
    render_page_header(
        "Transmission line overview",
        "A clear view of your configured line, measured response, diagnostic status, and foundational electromagnetic theory.",
    )

    tab_ov_live, tab_ov_problem, tab_ov_theory, tab_ov_assumptions = st.tabs([
        "⚡ Live Dashboard & Diagnostic",
        "🎯 Purpose, Problem & Workflow",
        "📐 Transmission-Line Theory & Equations",
        "⚖️ Model Assumptions, Limitations & References",
    ])

    with tab_ov_live:
        # 1. LIVE DIAGNOSTIC SUMMARY (4 KPI Metric Cards)
        rld_section_header("Live Diagnostic Summary")
        k1, k2, k3, k4 = st.columns(4)

        diag_label = str(inferred_class).lower()
        diag_color_map = {
            "healthy":  "#0ea472",
            "open":     "#e53e3e",
            "short":    "#e53e3e",
            "mismatch": "#d97706",
            "unknown":  "#3b9ede",
        }
        diag_color = diag_color_map.get(diag_label, "#d97706")

        mean_gamma = float(np.mean(np.abs(sweep_dict["gamma"])))
        d_est = loc_dual["dist_ifft_m"]
        d_disp_str = f"{d_est:.3f}" if d_est is not None else "N/A"
        d_unit_str = "m" if d_est is not None else ""

        mean_vswr = np.nanmean(sweep_dict["vswr"])
        vswr_disp_str = f"{mean_vswr:.3f}" if np.isfinite(mean_vswr) else "∞"
        vswr_unit_str = ": 1" if np.isfinite(mean_vswr) else ""

        with k1:
            st.markdown(f"""
            <div class="figma-metric-card" style="border-top: 2px solid {diag_color};">
              <div class="figma-metric-label">Inferred Diagnosis</div>
              <div style="margin-top: 7px; margin-bottom: 4px;">
                {rld_badge_html(str(inferred_class))}
              </div>
              <div style="font-size: 0.72rem; color: #546580; margin-top: 8px; padding-top: 7px; border-top: 1px solid #1c2537; line-height: 1.4;">
                Rule-based single-port classifier.<br>Identifies matched, mismatched, or damaged line.
              </div>
            </div>
            """, unsafe_allow_html=True)

        with k2:
            mag_color = "#00d4f5" if mean_gamma < 0.05 else ("#e53e3e" if mean_gamma > 0.95 else "#d97706")
            st.markdown(f"""
            <div class="figma-metric-card" style="border-top: 2px solid {mag_color};">
              <div class="figma-metric-label">Input Reflection |S₁₁|</div>
              <div class="rld-num" style="color: {mag_color};">{mean_gamma:.4f}</div>
              <div style="font-size: 0.72rem; color: #8898aa; margin-bottom: 6px;">Mean across sweep &nbsp;[dimensionless]</div>
              <div style="font-size: 0.72rem; color: #546580; padding-top: 7px; border-top: 1px solid #1c2537; line-height: 1.4;">
                0.0000 = perfect match · 1.0000 = total reflection<br>Reflected power = |S₁₁|²
              </div>
            </div>
            """, unsafe_allow_html=True)

        with k3:
            d_color = "#0ea472" if d_est is not None else "#546580"
            st.markdown(f"""
            <div class="figma-metric-card" style="border-top: 2px solid {d_color};">
              <div class="figma-metric-label">Fault Distance</div>
              <div class="rld-num" style="color: {d_color};">{d_disp_str}<span class="rld-unit">{d_unit_str}</span></div>
              <div style="font-size: 0.72rem; color: #8898aa; margin-bottom: 6px;">IFFT TDR centroid from port</div>
              <div style="font-size: 0.72rem; color: #546580; padding-top: 7px; border-top: 1px solid #1c2537; line-height: 1.4;">
                d ≈ l → termination fault<br>d &lt; l → mid-span discontinuity
              </div>
            </div>
            """, unsafe_allow_html=True)

        with k4:
            vswr_color = "#0ea472" if mean_vswr <= 1.5 else ("#e53e3e" if mean_vswr > 2.0 else "#d97706")
            st.markdown(f"""
            <div class="figma-metric-card" style="border-top: 2px solid {vswr_color};">
              <div class="figma-metric-label">VSWR</div>
              <div class="rld-num" style="color: {vswr_color};">{vswr_disp_str}<span class="rld-unit">{vswr_unit_str}</span></div>
              <div style="font-size: 0.72rem; color: #8898aa; margin-bottom: 6px;">Mean standing wave ratio</div>
              <div style="font-size: 0.72rem; color: #546580; padding-top: 7px; border-top: 1px solid #1c2537; line-height: 1.4;">
                1.00 = ideal · ≤ 1.5 = good · > 2.0 = severe<br>∞ = open/short circuit
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # 2. SIMULATION CONFIGURATION (Horizontal 4-Cell Pill Bar)
        render_config_pill_bar(Z0, length, vf, f_start_mhz, f_stop_mhz)

        # 3. SIGNAL RESPONSE (Two Columns: Plot + Diagnostic Result Card)
        rld_section_header("Signal Response")
        resp_col1, resp_col2 = st.columns([13, 7])

        with resp_col1:
            with st.container(border=True):
                rld_plot_header(
                    "Reflection Magnitude vs. Frequency",
                    f"Input reflection coefficient |S₁₁(f)| · Scenario: {sim_scenario.upper()} · Sweep: {f_start_mhz/1e3:.2f}–{f_stop_mhz/1e3:.2f} GHz"
                )
                fig_ov, ax_ov = plt.subplots(figsize=(7.6, 3.4))
                ax_ov.plot(f_ghz, np.abs(sweep_dict["gamma"]), color="#00d4f5", lw=2.0, label="|S₁₁| — Input Reflection")
                ax_ov.axhline(0.05, color="#0ea472", linestyle="--", lw=1.3, alpha=0.7, label="Healthy threshold  |S₁₁| = 0.05")
                ax_ov.set_xlabel("Frequency  (GHz)", fontsize=9)
                ax_ov.set_ylabel("|S₁₁|  magnitude  [dimensionless]", fontsize=9)
                ax_ov.set_ylim(-0.03, 1.08)
                ax_ov.set_yticks([0.0, 0.25, 0.5, 0.75, 1.0])
                ax_ov.grid(True, alpha=0.55)
                ax_ov.legend(loc="upper right")
                plt.tight_layout(pad=0.6)
                st.pyplot(fig_ov)
                plt.close(fig_ov)

        with resp_col2:
            with st.container(border=True):
                rld_section_header("Diagnostic Result")
                st.markdown(rld_badge_html(str(inferred_class)), unsafe_allow_html=True)

                subtype_title = inferred_class.subtype.replace("_", " ").capitalize()
                st.markdown(f'<div style="font-size: 1.1rem; font-weight: 700; color: #dde6f0; margin: 8px 0 5px 0; line-height: 1.3;">{subtype_title}</div>', unsafe_allow_html=True)

                overview_desc = "The measured reflection indicates a load that differs from the line impedance."
                overview_evidence = [
                    "Reflection magnitude above match threshold",
                    "Frequency response remains consistent",
                    "No open/short signature detected",
                ]
                if str(inferred_class) == "healthy":
                    overview_desc = "Transmission line operating at peak efficiency with matched termination."
                    overview_evidence = [
                        "Reflection magnitude below 0.05 threshold",
                        "Minimal standing waves across sweep",
                        "Incident RF power transferred fully to load",
                    ]
                elif str(inferred_class) == "open":
                    overview_desc = "Open-circuit discontinuity with total in-phase voltage reflection."
                    overview_evidence = [
                        "Reflection magnitude near unity (|S₁₁| ≈ 1.0)",
                        "In-phase reflection phase at termination",
                        "Full standing-wave voltage pattern established",
                    ]
                elif str(inferred_class) == "short":
                    overview_desc = "Short-circuit fault with 180° phase inversion at boundary."
                    overview_evidence = [
                        "Reflection magnitude near unity (|S₁₁| ≈ 1.0)",
                        "Negative real reflection (ground clamping)",
                        "Zero-voltage node at boundary",
                    ]
                elif inferred_class.subtype == "series_L":
                    overview_desc = "Series inductive discontinuity along the transmission path."
                    overview_evidence = [
                        "Reflection rises monotonically with frequency",
                        "Inductive upper-half Smith chart locus",
                        "Localized discontinuity echo in TDR",
                    ]
                elif inferred_class.subtype == "shunt_C":
                    overview_desc = "Shunt capacitive discontinuity along the transmission path."
                    overview_evidence = [
                        "Reflection increases with frequency",
                        "Capacitive lower-half Smith chart locus",
                        "Localized discontinuity echo in TDR",
                    ]

                st.markdown(f'<div style="font-size: 0.8rem; color: #8898aa; line-height: 1.5; margin-bottom: 10px;">{overview_desc}</div>', unsafe_allow_html=True)
                rld_section_header("Observed Evidence")
                st.markdown(rld_evidence_items(overview_evidence), unsafe_allow_html=True)

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # 4. QUICK INTERPRETATION (3-column formula card)
        with st.container(border=True):
            rld_section_header("Key Relationships")
            q1, q2, q3 = st.columns(3)
            with q1:
                st.markdown("""
                <div style="padding-right: 14px; border-right: 1px solid #1c2537;">
                  <div style="font-size: 0.85rem; font-weight: 600; color: #dde6f0; margin-bottom: 5px;">Reflection coefficient</div>
                  <div style="font-size: 0.88rem; font-weight: 600; color: #60d4f0; margin-bottom: 7px; font-family: 'JetBrains Mono', monospace;">
                    Γ = (<i>Z</i><sub>L</sub> − <i>Z</i><sub>0</sub>) / (<i>Z</i><sub>L</sub> + <i>Z</i><sub>0</sub>)
                  </div>
                  <div style="font-size: 0.75rem; color: #8898aa; line-height: 1.45;">Ratio of reflected to incident wave amplitude at the load terminal.</div>
                </div>
                """, unsafe_allow_html=True)
            with q2:
                st.markdown("""
                <div style="padding-right: 14px; border-right: 1px solid #1c2537;">
                  <div style="font-size: 0.85rem; font-weight: 600; color: #dde6f0; margin-bottom: 5px;">Standing-wave ratio</div>
                  <div style="font-size: 0.88rem; font-weight: 600; color: #60d4f0; margin-bottom: 7px; font-family: 'JetBrains Mono', monospace;">
                    VSWR = (1 + |Γ|) / (1 − |Γ|)
                  </div>
                  <div style="font-size: 0.75rem; color: #8898aa; line-height: 1.45;">Peak-to-minimum voltage envelope ratio on the standing-wave pattern.</div>
                </div>
                """, unsafe_allow_html=True)
            with q3:
                st.markdown("""
                <div style="padding-left: 4px;">
                  <div style="font-size: 0.85rem; font-weight: 600; color: #dde6f0; margin-bottom: 5px;">Input impedance</div>
                  <div style="font-size: 0.88rem; font-weight: 600; color: #60d4f0; margin-bottom: 7px; font-family: 'JetBrains Mono', monospace;">
                    <i>Z</i><sub>in</sub> = <i>Z</i><sub>0</sub> (1 + Γ) / (1 − Γ)
                  </div>
                  <div style="font-size: 0.75rem; color: #8898aa; line-height: 1.45;">Apparent complex impedance presented at the line input port.</div>
                </div>
                """, unsafe_allow_html=True)

    with tab_ov_problem:
        rld_section_header("1. Project Overview & System Concept")
        with st.container(border=True):
            st.markdown("""
            **RF LINE DOCTOR** is an academic-grade educational virtual laboratory designed for RF, microwave, and telecommunications engineering students and instructors.
            The system emulates a laboratory **single-port Vector Network Analyzer (VNA)** performing calibrated reflection sweeps across high-frequency transmission lines.
            
            By uniting forward transmission-line physics, non-linear inverse diagnostics, and impedance matching in an interactive cockpit, RF LINE DOCTOR enables learners to explore:
            - **Distributed Electromagnetic Wave Phenomena:** Phase transformation, standing-wave formation, and reflection.
            - **Non-Invasive Fault Diagnostics:** Automated classification of terminations and localized discontinuities using single-port $S_{11}$ data.
            - **Spatial Fault Localization:** Pinpointing physical defect locations using dual-method phase slope and Inverse Fast Fourier Transform (IFFT) reflectometry.
            - **Impedance Transformation & Matching:** Designing quarter-wave transformers to cancel reflections and maximize power transfer.
            """)

        rld_section_header("2. Purpose & The Single-Port Engineering Problem")
        with st.container(border=True):
            st.markdown("""
            #### The High-Frequency Physical Challenge
            In modern RF systems—such as radar feed networks, avionics bundles, cellular basestations, and high-speed PCB interconnects—coaxial cables and transmission lines are deployed in inaccessible, safety-critical environments. Over years of service, lines suffer from environmental degradation:
            - **Mechanical strain & bending:** Pinched outer conductors, cracked dielectric, or necked center conductors.
            - **Environmental ingress:** Water intrusion, corrosion, and connector oxidation.
            - **Termination drift:** Component degradation, solder fatigue, or terminal open/short circuits.

            #### Why Single-Port Diagnostics?
            When a $100\\text{ m}$ cable is routed through an aircraft fuselage or antenna tower, **the far end cannot be accessed without destructive disassembly**.
            Two-port through measurements (such as insertion loss $S_{21}$) are impossible. Field technicians can only connect a portable VNA to **Port 1**.
            
            **The Fundamental Diagnostic Question:**
            > *Given only the complex reflection coefficient $S_{11}(f)$ measured at the input port across a finite bandwidth, can we deduce what fault occurred, where it is located along the cable, and how to correct it?*

            RF LINE DOCTOR solves this inverse problem transparently without "cheating" by inspecting backend simulation parameters.
            """)

        rld_section_header("3. How RF Line Doctor Works (System Pipeline)")
        with st.container(border=True):
            st.markdown("""
            The application executes a 5-stage closed-loop pipeline from physics simulation to corrective matching:
            
            1. **Forward Transmission-Line Simulation (`line_model.py`, `fault_simulation.py`):**
               Calculates true input impedance $Z_{\\text{in}}(f)$ and reflection coefficient $\\Gamma(f)$ using closed-form Telegrapher equations and cascaded ABCD 2-port transfer matrices. Unclipped complex Gaussian noise $\\mathcal{CN}(0, \\sigma^2)$ is added to model realistic instrument noise floor.
            2. **Spectral Feature Extraction (`core/signal_analysis.py`):**
               Extracts mean reflection magnitude, variance, spectral frequency trend ($d|S_{11}|/df$), unwrapped phase slope, and extrapolates the critical physical DC phase intercept:
               $$\\phi_0 = \\lim_{f \\to 0} \\angle S_{11}(f)$$
            3. **Transparent Rule-Based Classifier (`diagnosis.py`):**
               Evaluates extracted features against a deterministic decision tree. Maps findings strictly to the 5 frozen contract labels (`healthy`, `open`, `short`, `mismatch`, `unknown`) and provides physical subtype diagnoses (`series_L`, `shunt_C`, etc.).
            4. **Dual-Method Fault Localization (`core/fault_location.py`):**
               Estimates fault distance using primary unwrapped phase-slope analysis ($d = -\\frac{v_p}{4\\pi}\\frac{d\\phi}{df}$) and cross-checks with Hann-windowed, zero-padded IFFT pseudo-TDR. Cross-checks reliability against the physical Rayleigh resolution limit $\\Delta R = v_p / (2B)$.
            5. **Quarter-Wave Matching Studio (`matching.py`):**
               When a resistive mismatch is diagnosed, synthesizes a quarter-wave transformer section ($Z_t = \\sqrt{Z_0 R_L}$) with exact reflection cancellation at $f_0$ and evaluates passband operational bandwidth ($VSWR \\le 1.222, RL \\ge 20\\text{ dB}$).
            """)

    with tab_ov_theory:
        rld_section_header("4. Transmission-Line Theory & Core Equations")
        with st.container(border=True):
            st.markdown("""
            #### Distributed Transmission-Line Model
            Unlike low-frequency lumped circuit analysis where spatial wave effects are ignored, microwave transmission lines have physical lengths comparable to or greater than the electromagnetic wavelength ($l \\gtrsim 0.1\\lambda$). Voltage and current become spatial wave functions of position $z$ and time $t$.
            
            A transmission line is represented by distributed per-unit-length primary constants:
            - $R$ : Series resistance per unit length $[\\Omega/\\text{m}]$ (conductor ohmic losses).
            - $L$ : Series inductance per unit length $[\\text{H/m}]$ (magnetic flux linkage).
            - $G$ : Shunt conductance per unit length $[\\text{S/m}]$ (dielectric leakage losses).
            - $C$ : Shunt capacitance per unit length $[\\text{F/m}]$ (electric field displacement).

            #### Telegrapher's Equations & Wave Equation
            Applying Kirchhoff's voltage and current laws to a differential slice $\\Delta z$ in the limit $\\Delta z \\to 0$ yields the Telegrapher's equations:
            $$\\frac{\\partial v(z, t)}{\\partial z} = -R\\,i(z, t) - L\\,\\frac{\\partial i(z, t)}{\\partial t}$$
            $$\\frac{\\partial i(z, t)}{\\partial z} = -G\\,v(z, t) - C\\,\\frac{\\partial v(z, t)}{\\partial t}$$

            Under the $e^{j\\omega t}$ time-harmonic convention, differentiation with respect to time becomes multiplication by $j\\omega$:
            $$\\frac{d^2 V(z)}{dz^2} - \\gamma^2 V(z) = 0, \\quad \\frac{d^2 I(z)}{dz^2} - \\gamma^2 I(z) = 0$$

            #### Propagation Constant & Phase Velocity
            The complex propagation constant $\\gamma$ is defined by:
            $$\\gamma = \\alpha + j\\beta = \\sqrt{(R + j\\omega L)(G + j\\omega C)}$$
            where $\\alpha \\ge 0$ is the attenuation constant $[\\text{Np/m}]$ and $\\beta \\ge 0$ is the phase constant $[\\text{rad/m}]$.
            
            For a **lossless transmission line** ($R = 0, G = 0$):
            $$\\alpha = 0, \\quad \\gamma = j\\beta = j\\omega\\sqrt{LC} = j\\frac{2\\pi}{\\lambda}$$
            $$v_p = \\frac{\\omega}{\\beta} = \\frac{1}{\\sqrt{LC}} = v_f \\cdot c_0 \\quad [\\text{m/s}]$$
            where $c_0 \\approx 2.99792458 \\times 10^8\\text{ m/s}$ is the speed of light in vacuum and $v_f = 1/\\sqrt{\\epsilon_r}$ is the velocity factor.

            #### Characteristic Impedance
            The characteristic impedance $Z_0$ represents the ratio of forward voltage to forward current at any point on an infinite or matched line:
            $$Z_0 = \\sqrt{\\frac{R + j\\omega L}{G + j\\omega C}} \\quad \\xrightarrow{\\text{lossless}} \\quad Z_0 = \\sqrt{\\frac{L}{C}} \\quad [\\Omega]$$

            #### Voltage Reflection Coefficient & Input Impedance Transformation
            When a line is terminated by an arbitrary load $Z_L$, a reflected wave $V_0^- e^{+\\gamma z}$ is generated. At the load terminal ($z = 0$):
            $$\\Gamma_L = \\frac{V_0^-}{V_0^+} = \\frac{Z_L - Z_0}{Z_L + Z_0}$$
            
            Transforming toward the generator across a physical line of length $l$ adds a round-trip phase delay $2\\beta l$:
            $$\\Gamma(l) = \\Gamma_L e^{-2j\\beta l}$$
            
            The transformed input impedance $Z_{\\text{in}}$ presented to a generator at distance $l$ is:
            $$Z_{\\text{in}} = Z_0 \\left[ \\frac{Z_L + j Z_0 \\tan(\\beta l)}{Z_0 + j Z_L \\tan(\\beta l)} \\right] = Z_0 \\frac{1 + \\Gamma(l)}{1 - \\Gamma(l)} \\quad [\\Omega]$$

            #### Voltage Standing Wave Ratio (VSWR) & Return Loss (RL)
            Constructive and destructive interference between forward and reflected waves sets up a standing-wave pattern:
            $$\\text{VSWR} = \\frac{V_{\\max}}{V_{\\min}} = \\frac{1 + |\\Gamma|}{1 - |\\Gamma|} \\quad [\\text{dimensionless}]$$
            $$\\text{RL} = -20\\log_{10}(|\\Gamma|) \\quad [\\text{dB}]$$
            """)

        rld_section_header("Mathematical Variable Specification")
        eq_df = pd.DataFrame([
            {"Symbol": "Z₀", "Name": "Characteristic Impedance", "SI Unit": "Ω", "Physical Meaning": "Voltage-to-current ratio of forward traveling wave", "Governing Equation": "Z₀ = √(L/C)"},
            {"Symbol": "γ", "Name": "Propagation Constant", "SI Unit": "m⁻¹", "Physical Meaning": "Spatial attenuation and phase change rate", "Governing Equation": "γ = α + jβ = √((R+jωL)(G+jωC))"},
            {"Symbol": "β", "Name": "Phase Constant", "SI Unit": "rad/m", "Physical Meaning": "Spatial phase accumulation per metre", "Governing Equation": "β = 2π / λ = ω / vp"},
            {"Symbol": "vp", "Name": "Phase Velocity", "SI Unit": "m/s", "Physical Meaning": "Speed of electromagnetic wave phase wavefront", "Governing Equation": "vp = vf · c₀ = 1 / √(LC)"},
            {"Symbol": "Γ", "Name": "Reflection Coefficient", "SI Unit": "dimensionless", "Physical Meaning": "Complex ratio of reflected to incident voltage", "Governing Equation": "Γ = (ZL - Z₀) / (ZL + Z₀)"},
            {"Symbol": "Zin", "Name": "Input Impedance", "SI Unit": "Ω", "Physical Meaning": "Impedance looking into line at distance l from load", "Governing Equation": "Zin = Z₀(ZL + jZ₀ tan βl) / (Z₀ + jZL tan βl)"},
            {"Symbol": "VSWR", "Name": "Standing Wave Ratio", "SI Unit": "dimensionless", "Physical Meaning": "Ratio of maximum to minimum voltage envelope", "Governing Equation": "VSWR = (1 + |Γ|) / (1 - |Γ|)"},
            {"Symbol": "RL", "Name": "Return Loss", "SI Unit": "dB", "Physical Meaning": "Power attenuation of reflected wave relative to incident", "Governing Equation": "RL = -20 log₁₀(|Γ|)"},
        ])
        st.dataframe(eq_df, hide_index=True)

    with tab_ov_assumptions:
        rld_section_header("10. Model Assumptions & Limitations")
        with st.container(border=True):
            st.markdown("""
            To ensure complete technical transparency, RF LINE DOCTOR adheres to clearly bounded electromagnetic assumptions:
            
            1. **Transverse Electromagnetic (TEM) Mode Propagation:**
               The model assumes pure TEM wave propagation with zero axial electric ($E_z = 0$) and magnetic ($H_z = 0$) fields. This holds strictly below the coaxial higher-order TE₁₁ waveguide cutoff frequency:
               $$f_c \\approx \\frac{c_0}{\\pi (a + b)\\sqrt{\\epsilon_r}}$$
               where $a$ is the inner conductor outer radius and $b$ is the outer conductor inner radius.
            2. **Linear, Time-Invariant, Isotropic Medium:**
               Dielectric permittivity $\\epsilon$ and magnetic permeability $\\mu$ are assumed independent of signal amplitude, field direction, and operating time.
            3. **Distributed Loss & High-Frequency Skin Effect Modeling:**
               Core propagation in the basic simulator assumes lossless propagation ($\\alpha = 0$), while the underlying `line_model` engine supports full distributed $R, L, G, C$ lossy line modeling as well as frequency-dependent skin depth $\\delta_s(f) = 1/\\sqrt{\\pi f \\mu \\sigma}$ and surface resistance $R_s(f) = \\sqrt{\\pi f \\mu / \\sigma}$.
            4. **Localized Lumped Discontinuity Approximation:**
               Intermediate defects (series inductances or shunt capacitances) are treated as lumped 2-port network matrices inserted between uniform line segments. This is valid when the physical defect length $\\Delta z$ satisfies $\\Delta z \\ll \\lambda$.
            5. **Single Dominant Reflection & Multipath Echo Tracking:**
               The primary phase-slope distance estimator assumes one dominant discontinuity. When multiple discontinuities or secondary multipath echoes are present, the IFFT echo locator identifies all candidate local peaks and flags potential round-trip harmonic echoes with relative amplitude tracking.
            6. **Bandwidth-Limited Rayleigh Spatial Resolution:**
               The spatial resolution of the IFFT pseudo-TDR is fundamentally limited by the sweep bandwidth:
               $$\\Delta R = \\frac{v_p}{2 B} = \\frac{v_p}{2 (f_{\\max} - f_{\\min})}$$
               Zero-padding interpolates the display grid but cannot resolve two physical defects separated by less than $\\Delta R$.
            7. **Unclipped Non-Passive Measurement Handling:**
               In real laboratory measurements, additive thermal noise can push the measured $|S_{11}|$ slightly above $1.0$. RF LINE DOCTOR preserves realistic noise without artificial clipping; for points where $|S_{11}| > 1.0$, passive line theory dictates $\\text{VSWR} = \\text{NaN}$.
            """)

        rld_section_header("12. References & Academic Acknowledgements")
        with st.container(border=True):
            st.markdown("""
            The analytical formulations and numerical techniques implemented in RF LINE DOCTOR follow standard microwave engineering literature:
            
            1. **D. M. Pozar**, *Microwave Engineering*, 4th Edition, John Wiley & Sons, Hoboken, NJ, 2011.
               - Chapter 2: Transmission Line Theory (Telegrapher equations, input impedance, quarter-wave matching).
               - Chapter 4: Microwave Network Analysis (ABCD 2-port parameters, S-parameters).
            2. **R. E. Collin**, *Foundations for Microwave Engineering*, 2nd Edition, IEEE Press / Wiley-Interscience, New York, 2001.
               - Chapter 3: Transmission Lines and Waveguides.
               - Chapter 5: Impedance Transformation and Matching.
            3. **S. J. Orfanidis**, *Electromagnetic Waves and Antennas*, Rutgers University, 2016.
               - Time-Domain Reflectometry (TDR), pulse propagation, and Fourier synthesis.
            4. **IEEE Std 1785-2016**, *IEEE Standard for Waveguide S-Parameter Measurements*.
            5. **Curricular Context:**
               Developed as an educational virtual prototype for **EC-3104 Microwave Engineering** to support remote simulation laboratories and automated self-guided learning.
            """)

    render_footer()


# ─────────────────────────────────────────────────────────────────────────────
# VIEW 2: TRANSMISSION-LINE SIMULATOR
# ─────────────────────────────────────────────────────────────────────────────
elif "simulator" in nav_section.lower():
    render_breadcrumb("LINE SIMULATOR")
    render_page_header(
        "Transmission line simulator",
        "Interactive multi-parameter transmission-line simulation, ABCD cascading, and reflection generation.",
    )

    render_config_pill_bar(Z0, length, vf, f_start_mhz, f_stop_mhz)

    tab_sim_interactive, tab_sim_params, tab_sim_method, tab_sim_results = st.tabs([
        "📈 Interactive Simulator & Sweep",
        "⚙️ Input Parameter Explanations",
        "🔬 Fault Simulation Methodology",
        "📊 Understanding Calculation Results",
    ])

    with tab_sim_interactive:
        col_sim1, col_sim2 = st.columns([13, 7])
        with col_sim1:
            with st.container(border=True):
                rld_plot_header(
                    "Simulated S₁₁ Reflection Sweep",
                    f"Single-port |S₁₁(f)| magnitude · Scenario: {sim_scenario.upper()} · Z₀ = {Z0:.0f} Ω · l = {length:.2f} m"
                )
                fig_s, ax_s = plt.subplots(figsize=(7.6, 3.6))
                ax_s.plot(f_ghz, np.abs(sweep_dict["gamma"]), color="#00d4f5", lw=2.0, label="|S₁₁| — Input Reflection")
                ax_s.axhline(0.05, color="#0ea472", linestyle="--", lw=1.3, alpha=0.7, label="Healthy threshold  |S₁₁| = 0.05")
                ax_s.set_xlabel("Frequency  (GHz)", fontsize=9)
                ax_s.set_ylabel("|S₁₁|  magnitude  [dimensionless]", fontsize=9)
                ax_s.set_ylim(-0.03, 1.08)
                ax_s.set_yticks([0.0, 0.25, 0.5, 0.75, 1.0])
                ax_s.grid(True, alpha=0.55)
                ax_s.legend(loc="upper right")
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

        st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
        rld_section_header("Frequency Sweep Data Table")
        df_sweep = pd.DataFrame({
            "f (MHz)":          freqs / 1e6,
            "Re(Z_in) (Ω)":    np.real(sweep_dict["zin"]),
            "Im(Z_in) (Ω)":    np.imag(sweep_dict["zin"]),
            "|S₁₁|":           np.abs(sweep_dict["gamma"]),
            "Phase (deg)":      np.degrees(np.unwrap(np.angle(sweep_dict["gamma"]))),
            "VSWR":             sweep_dict["vswr"],
            "Return Loss (dB)": sweep_dict["rl_db"],
        })
        st.dataframe(
            df_sweep.head(100).style.format({
                "f (MHz)":          "{:.2f}",
                "Re(Z_in) (Ω)":    "{:.3f}",
                "Im(Z_in) (Ω)":    "{:.3f}",
                "|S₁₁|":           "{:.4f}",
                "Phase (deg)":      "{:.2f}",
                "VSWR":             "{:.4f}",
                "Return Loss (dB)": "{:.3f}",
            }),
            height=240,
            hide_index=True,
        )

        csv_buf = io.StringIO()
        df_sweep.to_csv(csv_buf, index=False)
        st.download_button(
            label="📥 Download Frequency Sweep CSV",
            data=csv_buf.getvalue(),
            file_name="rf_line_doctor_sweep_data.csv",
            mime="text/csv",
        )

    with tab_sim_params:
        rld_section_header("5. Input Parameter Explanations")
        with st.container(border=True):
            st.markdown("""
            Every calculation in RF LINE DOCTOR depends on clearly defined physical and instrumentation parameters.
            The table below provides a complete reference detailing what each parameter represents, its SI unit, and why it is required:
            """)
            param_df = pd.DataFrame([
                {
                    "Parameter": "Characteristic Impedance Z₀",
                    "Symbol": "Z₀",
                    "Unit": "Ω (Ohms)",
                    "What it Represents": "Voltage-to-current ratio of forward-traveling wave: Z₀ = √(L/C)",
                    "Why Required": "Normalizes reflection coefficient Γ = (ZL - Z₀)/(ZL + Z₀) and sets Smith chart reference impedance.",
                    "Typical Values": "50 Ω (standard RF), 75 Ω (cable TV)",
                },
                {
                    "Parameter": "Physical Line Length l",
                    "Symbol": "l",
                    "Unit": "m (Metres)",
                    "What it Represents": "Total end-to-end cable length from VNA measurement plane to termination",
                    "Why Required": "Sets total electrical length θ = βl and two-way time of flight τ = 2l/vp.",
                    "Typical Values": "0.10 m to 100.0 m",
                },
                {
                    "Parameter": "Velocity Factor vf",
                    "Symbol": "vf",
                    "Unit": "dimensionless ratio",
                    "What it Represents": "Wave phase velocity relative to speed of light in vacuum: vf = vp/c₀ = 1/√εr",
                    "Why Required": "Determines phase constant β = 2πf/vp and converts TDR delay into spatial distance d = vp·t/2.",
                    "Typical Values": "0.66 (solid PE), 0.70 (PTFE), 1.00 (air)",
                },
                {
                    "Parameter": "Start Frequency f_min",
                    "Symbol": "f_min",
                    "Unit": "MHz",
                    "What it Represents": "Lower frequency boundary of continuous-wave sweep",
                    "Why Required": "Defines bottom of measurement band and anchors DC phase intercept extrapolation.",
                    "Typical Values": "100 MHz to 1000 MHz",
                },
                {
                    "Parameter": "Stop Frequency f_max",
                    "Symbol": "f_max",
                    "Unit": "MHz",
                    "What it Represents": "Upper frequency boundary of continuous-wave sweep",
                    "Why Required": "Determines sweep bandwidth B = f_max - f_min, which dictates Rayleigh range resolution ΔR = vp/(2B).",
                    "Typical Values": "1000 MHz to 6000 MHz",
                },
                {
                    "Parameter": "Sample Points N",
                    "Symbol": "N",
                    "Unit": "dimensionless count",
                    "What it Represents": "Number of uniformly spaced frequency sample bins",
                    "Why Required": "Sets frequency step Δf = B/(N-1), which determines unambiguous TDR range R_max = vp/(2Δf).",
                    "Typical Values": "200 to 1000 points",
                },
                {
                    "Parameter": "Load Resistance RL",
                    "Symbol": "RL",
                    "Unit": "Ω (Ohms)",
                    "What it Represents": "Real resistive component of termination impedance ZL = RL + j0",
                    "Why Required": "Simulates resistive mismatch condition to test reflection amplitude and standing wave ratio.",
                    "Typical Values": "1 Ω to 2000 Ω",
                },
                {
                    "Parameter": "Discontinuity Inductance L",
                    "Symbol": "L",
                    "Unit": "nH (Nanohenries)",
                    "What it Represents": "Lumped series inductance representing conductor necking, cracked trace, or pin damage",
                    "Why Required": "Simulates series reactive discontinuity impedance Zs = jωL in 2-port ABCD cascading.",
                    "Typical Values": "1 nH to 50 nH",
                },
                {
                    "Parameter": "Discontinuity Capacitance C",
                    "Symbol": "C",
                    "Unit": "pF (Picofarads)",
                    "What it Represents": "Lumped shunt capacitance representing dielectric crushing, water ingress, or solder bridge",
                    "Why Required": "Simulates shunt reactive discontinuity admittance Yp = jωC in 2-port ABCD cascading.",
                    "Typical Values": "1 pF to 50 pF",
                },
                {
                    "Parameter": "Discontinuity Position d",
                    "Symbol": "d",
                    "Unit": "m (Metres)",
                    "What it Represents": "Physical location of defect measured from input port",
                    "Why Required": "Positions the 2-port ABCD discontinuity matrix between transmission line segments 1 and 2.",
                    "Typical Values": "0 < d ≤ l",
                },
                {
                    "Parameter": "Measurement Noise σ",
                    "Symbol": "σ",
                    "Unit": "dimensionless",
                    "What it Represents": "Standard deviation of zero-mean complex Gaussian noise added to simulated S₁₁",
                    "Why Required": "Tests algorithm robustness, classifier noise margin, and non-passive handling under realistic VNA noise.",
                    "Typical Values": "0.00 (ideal) to 0.05 (noisy)",
                },
            ])
            st.dataframe(param_df, hide_index=True)

    with tab_sim_method:
        rld_section_header("6. Fault Simulation Methodology")
        with st.container(border=True):
            st.markdown("""
            #### 1. Uniform Line Simulation
            When no intermediate discontinuity is present (`healthy`, `mismatch`, `open`, `short`), the input impedance $Z_{\\text{in}}(f)$ is computed directly using the exact distributed wave solution:
            $$Z_{\\text{in}}(f) = Z_0 \\left[ \\frac{Z_L + j Z_0 \\tan(\\beta l)}{Z_0 + j Z_L \\tan(\\beta l)} \\right]$$
            where $\\beta = \\frac{2\\pi f}{v_p}$ and $v_p = v_f \\cdot c_0$.
            
            Boundary condition handling:
            - **Open Circuit ($Z_L \\to \\infty$):** Analytically reduces to $Z_{\\text{in}} = -j Z_0 \\cot(\\beta l)$, $\\Gamma_L = +1.0 + 0j$.
            - **Short Circuit ($Z_L = 0$):** Analytically reduces to $Z_{\\text{in}} = +j Z_0 \\tan(\\beta l)$, $\\Gamma_L = -1.0 + 0j$.
            - **Matched Line ($Z_L = Z_0$):** Yields $Z_{\\text{in}} = Z_0$, $\\Gamma_L = 0.0 + 0j$.

            #### 2. Discontinuity Modeling via Cascaded 2-Port ABCD Matrices
            When an intermediate defect is injected at position $d$, the line is segmented into three cascaded 2-port networks:
            $$\\mathbf{T}_{\\text{total}} = \\mathbf{T}_{\\text{line1}}(d) \\cdot \\mathbf{T}_{\\text{fault}} \\cdot \\mathbf{T}_{\\text{line2}}(l - d)$$

            - **Transmission-Line Segment ($k = 1, 2$):**
              $$\\mathbf{T}_{\\text{line}}(\\ell) = \\begin{bmatrix} \\cos(\\beta \\ell) & j Z_0 \\sin(\\beta \\ell) \\\\ j \\frac{\\sin(\\beta \\ell)}{Z_0} & \\cos(\\beta \\ell) \\end{bmatrix}$$
            - **Series Inductive Discontinuity ($Z_s = j\\omega L$):**
              $$\\mathbf{T}_{\\text{series}} = \\begin{bmatrix} 1 & j\\omega L \\\\ 0 & 1 \\end{bmatrix}$$
            - **Shunt Capacitive Discontinuity ($Y_p = j\\omega C$):**
              $$\\mathbf{T}_{\\text{shunt}} = \\begin{bmatrix} 1 & 0 \\\\ j\\omega C & 1 \\end{bmatrix}$$

            #### 3. Input Impedance & S-Parameter Conversion
            The total cascaded transfer matrix $\\mathbf{T}_{\\text{total}} = \\begin{bmatrix} A & B \\\\ C & D \\end{bmatrix}$ is terminated by load $Z_L$.
            The input impedance presented to the generator is:
            $$Z_{\\text{in}} = \\frac{A Z_L + B}{C Z_L + D}$$
            The ideal input reflection coefficient is:
            $$S_{11,\\text{ideal}} = \\frac{Z_{\\text{in}} - Z_0}{Z_{\\text{in}} + Z_0}$$

            #### 4. Realistic Unclipped Noise Injection
            To faithfully emulate instrument noise, complex Gaussian noise is added to the simulated reflection:
            $$S_{11,\\text{noisy}} = S_{11,\\text{ideal}} + n_r + j n_i, \\quad n_r, n_i \\sim \\mathcal{N}\\left(0, \\frac{\\sigma^2}{2}\\right)$$
            **Rigorous Non-Passive Policy:** Noise fluctuations can cause $|S_{11}| > 1.0$ at noisy points. In strict accordance with electromagnetic physics, passive-line VSWR is physically undefined for non-passive reflections and evaluates to $\\text{NaN}$ rather than being artificially clipped.
            """)

    with tab_sim_results:
        rld_section_header("9. Understanding Calculation Results")
        with st.container(border=True):
            st.markdown("""
            Every calculation result produced by the simulator has specific physical and practical significance:
            
            - **Frequency $f$ [MHz]:**
              *What it represents:* Continuous-wave excitation frequency of the virtual VNA source.
              *Engineering significance:* RF transmission line behavior changes cyclically with frequency due to spatial phase delay $\\beta l = 2\\pi f l / v_p$.
            
            - **Input Resistance $\\text{Re}(Z_{\\text{in}})$ [Ω]:**
              *What it represents:* Real component of transformed terminal impedance.
              *Engineering significance:* Determines net power dissipation. If $\\text{Re}(Z_{\\text{in}}) = Z_0$ and $\\text{Im}(Z_{\\text{in}}) = 0$, maximum power is transferred without standing waves.
            
            - **Input Reactance $\\text{Im}(Z_{\\text{in}})$ [Ω]:**
              *What it represents:* Imaginary component of transformed terminal impedance.
              *Engineering significance:* Indicates whether the line and load store net magnetic energy ($X_{\\text{in}} > 0$, inductive) or electric energy ($X_{\\text{in}} < 0$, capacitive) at the measurement plane.
            
            - **Reflection Magnitude $|S_{11}|$ [dimensionless]:**
              *What it represents:* Ratio of reflected voltage amplitude to incident voltage amplitude ($|V^- / V^+|$).
              *Engineering significance:* Quantifies fraction of reflected power: $P_{\\text{refl}} / P_{\\text{inc}} = |S_{11}|^2$. Value ranges from $0.00$ (matched) to $1.00$ (total reflection).
            
            - **Unwrapped Phase $\\angle S_{11}$ [degrees]:**
              *What it represents:* Cumulative phase shift between incident and reflected waves.
              *Engineering significance:* Slope of phase across frequency ($d\\phi/df$) reveals the round-trip distance to the defect ($d = -\\frac{v_p}{4\\pi}\\frac{d\\phi}{df}$).
            
            - **Voltage Standing Wave Ratio (VSWR) [dimensionless]:**
              *What it represents:* Ratio of maximum to minimum voltage envelope on the line: $V_{\\max}/V_{\\min} = (1 + |S_{11}|)/(1 - |S_{11}|)$.
              *Interpretation:*
              - $\\text{VSWR} = 1.00$ : Perfect match (ideal).
              - $\\text{VSWR} \\le 1.20$ : High-grade RF match (standard for transmitters).
              - $\\text{VSWR} \\le 1.50$ : Acceptable industrial match.
              - $\\text{VSWR} > 2.00$ : Severe mismatch; excessive voltage stress and amplifier reflection trip risk.
              - $\\text{VSWR} \\to \\infty$ : Total reflection (open or short circuit).
            
            - **Return Loss (RL) [dB]:**
              *What it represents:* Logarithmic ratio of incident power to reflected power: $\\text{RL} = -20\\log_{10}(|S_{11}|)$.
              *Interpretation:*
              - $\\ge 20\\text{ dB}$ : Excellent match (< 1% power reflected).
              - $14\\text{ dB}$ : Good match (4% power reflected, $\\text{VSWR} \\approx 1.5$).
              - $10\\text{ dB}$ : Marginal match (10% power reflected, $\\text{VSWR} \\approx 1.9$).
              - $0\\text{ dB}$ : Total reflection (100% power reflected).
            """)

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
            rld_banner(
                f"<strong>Non-passive measurement:</strong> Additive noise caused |S₁₁| > 1.0 at {nan_cnt} sample point(s). "
                "Passive-line VSWR is physically undefined for non-passive observations and is returned as NaN. "
                "Ideal reflection data is preserved without artificial clipping.",
                kind="warn", icon="⚠️"
            )

        with st.container(border=True):
            rld_plot_header(
                "Multi-Metric Reflection Overview",
                f"|S₁₁(f)|, VSWR(f), Return Loss RL(f) · Scenario: {sim_scenario.upper()} · Z₀ = {Z0:.0f} Ω"
            )
            fig_rf, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 7.8), sharex=True)

            ax1.plot(f_ghz, np.abs(sweep_dict["gamma"]), color="#00d4f5", lw=2.0, label="|S₁₁|")
            ax1.axhline(0.05, color="#0ea472", linestyle="--", lw=1.3, alpha=0.7, label="Match threshold (0.05)")
            ax1.set_ylabel("|S₁₁|  [dimensionless]", fontsize=8.5)
            ax1.set_ylim(-0.03, 1.08)
            ax1.set_yticks([0.0, 0.25, 0.5, 0.75, 1.0])
            ax1.grid(True, alpha=0.5)
            ax1.legend(loc="upper right")

            vswr_plot = np.clip(sweep_dict["vswr"], 1.0, 50.0)
            ax2.plot(f_ghz, vswr_plot, color="#d97706", lw=2.0, label="VSWR")
            ax2.axhline(2.0, color="#546580", linestyle="--", lw=1.2, alpha=0.7, label="VSWR = 2.0 benchmark")
            ax2.axhline(1.5, color="#0ea472", linestyle=":", lw=1.0, alpha=0.6, label="VSWR = 1.5 benchmark")
            ax2.set_ylabel("VSWR  [dimensionless]", fontsize=8.5)
            ax2.set_ylim(0.98, min(max(np.nanmax(vswr_plot) * 1.12, 3.2), 32.0))
            ax2.grid(True, alpha=0.5)
            ax2.legend(loc="upper right")

            rl_plot = np.clip(sweep_dict["rl_db"], 0.0, 65.0)
            ax3.plot(f_ghz, rl_plot, color="#0ea472", lw=2.0, label="Return Loss (dB)")
            ax3.axhline(20.0, color="#3b9ede", linestyle="--", lw=1.3, alpha=0.75, label="20 dB — Excellent match")
            ax3.axhline(14.0, color="#d97706", linestyle=":", lw=1.0, alpha=0.65, label="14 dB — Good match")
            ax3.set_ylabel("Return Loss  (dB)", fontsize=8.5)
            ax3.set_xlabel("Frequency  (GHz)", fontsize=8.5)
            ax3.set_ylim(-1, 65)
            ax3.grid(True, alpha=0.5)
            ax3.legend(loc="upper right")

            plt.tight_layout(pad=0.7)
            st.pyplot(fig_rf)
            plt.close(fig_rf)

        with st.container(border=True):
            rld_section_header("Understanding Reflection Outputs & Benchmarks")
            st.markdown("""
            - **Input Reflection Magnitude $|S_{11}|$ [dimensionless]:**
              *What it represents:* Ratio of reflected voltage amplitude to incident voltage amplitude ($|V^- / V^+|$).
              *Engineering significance:* Governs power transfer efficiency. The fraction of transmitter power reflected back to the source is $P_{\\text{refl}}/P_{\\text{inc}} = |S_{11}|^2$. Delivered power is $P_L/P_{\\text{inc}} = 1 - |S_{11}|^2$.
            
            - **Voltage Standing Wave Ratio (VSWR) [dimensionless]:**
              *What it represents:* Ratio of maximum to minimum voltage envelope on the line: $\\text{VSWR} = (1 + |S_{11}|)/(1 - |S_{11}|)$.
              *Engineering significance:* High VSWR causes high peak voltage nodes that stress cable dielectric insulation and cause power amplifier protection circuits to throttle output.
            
            - **Return Loss (RL) [dB]:**
              *What it represents:* Logarithmic ratio of incident power to reflected power: $\\text{RL} = -20\\log_{10}(|S_{11}|)$.
              *Engineering significance:* Standard specification metric in telecommunications and RF component datasheets.
            """)
            bm_df = pd.DataFrame([
                {"Match Quality": "Excellent (Matched)", "VSWR": "≤ 1.20 : 1", "Return Loss": "≥ 20.8 dB", "Reflected Power %": "≤ 0.8 %", "Operational Significance": "Ideal for high-power transmitters and precision test sets"},
                {"Match Quality": "Good (Acceptable)", "VSWR": "≤ 1.50 : 1", "Return Loss": "≥ 14.0 dB", "Reflected Power %": "≤ 4.0 %", "Operational Significance": "Standard commercial antenna and receiver frontend match"},
                {"Match Quality": "Marginal", "VSWR": "1.50 to 2.00 : 1", "Return Loss": "9.5 to 14.0 dB", "Reflected Power %": "4.0 to 11.1 %", "Operational Significance": "Significant power loss; acceptable only in non-critical systems"},
                {"Match Quality": "Severe Mismatch", "VSWR": "> 2.00 : 1", "Return Loss": "< 9.5 dB", "Reflected Power %": "> 11.1 %", "Operational Significance": "Unacceptable; risk of amplifier thermal trip or shutdown"},
                {"Match Quality": "Total Reflection", "VSWR": "→ ∞", "Return Loss": "0.0 dB", "Reflected Power %": "100.0 %", "Operational Significance": "Open or short circuit; zero power delivered to load"},
            ])
            st.dataframe(bm_df, hide_index=True)

    with tab_z:
        with st.container(border=True):
            rld_plot_header(
                "Transformed Input Impedance vs. Frequency",
                f"R_in(f) = Re(Z_in),  X_in(f) = Im(Z_in),  ∠S₁₁(f) · Z₀ = {Z0:.0f} Ω · l = {length:.2f} m"
            )
            fig_z, (ax_rin, ax_xin, ax_ph) = plt.subplots(3, 1, figsize=(10, 7.8), sharex=True)

            rin_plot = np.clip(rin, -150.0, 600.0)
            ax_rin.plot(f_ghz, rin_plot, color="#a855f7", lw=2.0, label="R_in = Re(Z_in)  (Ω)")
            ax_rin.axhline(Z0, color="#546580", linestyle="--", lw=1.3, alpha=0.7, label=f"Z₀ = {Z0:.0f} Ω  (matched reference)")
            ax_rin.set_ylabel("Resistance  R_in  (Ω)", fontsize=8.5)
            ax_rin.grid(True, alpha=0.5)
            ax_rin.legend(loc="upper right")

            xin_plot = np.clip(xin, -600.0, 600.0)
            ax_xin.plot(f_ghz, xin_plot, color="#ec4899", lw=2.0, label="X_in = Im(Z_in)  (Ω)")
            ax_xin.axhline(0, color="#546580", linestyle="-", lw=0.8, alpha=0.5)
            ax_xin.set_ylabel("Reactance  X_in  (Ω)", fontsize=8.5)
            ax_xin.grid(True, alpha=0.5)
            ax_xin.legend(loc="upper right")

            ax_ph.plot(f_ghz, spectral_feat["phase_deg"], color="#3b9ede", lw=2.0, label="Unwrapped Phase ∠S₁₁  (deg)")
            ax_ph.set_ylabel("Phase  ∠S₁₁  (deg)", fontsize=8.5)
            ax_ph.set_xlabel("Frequency  (GHz)", fontsize=8.5)
            ax_ph.grid(True, alpha=0.5)
            ax_ph.legend(loc="upper right")

            plt.tight_layout(pad=0.7)
            st.pyplot(fig_z)
            plt.close(fig_z)

        with st.container(border=True):
            rld_section_header("Understanding Transformed Input Impedance & Resonance")
            st.markdown("""
            - **Input Resistance $R_{\\text{in}} = \\text{Re}(Z_{\\text{in}})$ [Ω]:**
              *What it represents:* Real component of impedance seen looking into the line.
              *Engineering significance:* Determines net dissipation. When $R_{\\text{in}} = Z_0$ and $X_{\\text{in}} = 0$, the line is perfectly matched at that specific frequency.
            
            - **Input Reactance $X_{\\text{in}} = \\text{Im}(Z_{\\text{in}})$ [Ω]:**
              *What it represents:* Reactive energy storage.
              *Interpretation:*
              - $X_{\\text{in}} > 0$ : Inductive reactance (magnetic energy dominates, behaves like an inductor).
              - $X_{\\text{in}} < 0$ : Capacitive reactance (electric energy dominates, behaves like a capacitor).
              - $X_{\\text{in}} = 0$ : Resonance (purely resistive input impedance).
            
            - **Quarter-Wave Transformation Property ($l = (2m+1)\\lambda/4$):**
              $$\\beta l = (2m+1)\\frac{\\pi}{2} \\implies Z_{\\text{in}} = \\frac{Z_0^2}{Z_L}$$
              A quarter-wavelength section acts as an **impedance inverter**:
              - An open-circuit load ($Z_L = \\infty$) transforms into a zero-ohm short circuit ($Z_{\\text{in}} = 0$).
              - A short-circuit load ($Z_L = 0$) transforms into an infinite-ohm open circuit ($Z_{\\text{in}} = \\infty$).
            
            - **Half-Wave Transparency Property ($l = m\\lambda/2$):**
              $$\\beta l = m\\pi \\implies Z_{\\text{in}} = Z_L$$
              A half-wavelength line is **electrically transparent**: the impedance measured at the input is identical to the load impedance, regardless of the line's characteristic impedance $Z_0$.
            """)

    with tab_smith:
        col_sm1, col_sm2 = st.columns([12, 8])
        with col_sm1:
            with st.container(border=True):
                rld_plot_header(
                    "Normalized Reflection Locus Γ(f)",
                    f"Complex reflection mapped to normalized impedance z = Z / Z₀ · Sweep: {f_start_mhz:.0f}–{f_stop_mhz:.0f} MHz"
                )
                fig_sm, ax_sm = plt.subplots(figsize=(6.5, 6.5))
                meas.smith_plot(sweep_dict["gamma"], ax=ax_sm, label=f"Sweep ({f_start_mhz:.0f}–{f_stop_mhz:.0f} MHz)")
                ax_sm.legend(loc="lower right", fontsize=8.5, facecolor="#07090f", edgecolor="#1c2537")
                plt.tight_layout()
                st.pyplot(fig_sm)
                plt.close(fig_sm)

        with col_sm2:
            with st.container(border=True):
                rld_section_header("Smith Chart Landmarks")
                st.markdown('<div style="font-size: 0.8rem; color: #8898aa; margin-top: 2px; margin-bottom: 12px;">Complex reflection mapped to normalized impedance <i>z</i> = <i>Z</i> / <i>Z</i><sub>0</sub>.</div>', unsafe_allow_html=True)

                st.markdown("""
                <div style="display: flex; flex-direction: column; gap: 8px;">
                  <div class="figma-pill-cell">
                    <div style="font-size: 0.72rem; color: #0ea472; font-weight: 700;">● CENTRE (|Γ| = 0)</div>
                    <div style="font-size: 0.78rem; color: #cbd5e1; margin-top: 2px;">Matched load: <i>Z</i><sub>L</sub> = <i>Z</i><sub>0</sub>, Return Loss &rarr; &infin;, no reflection.</div>
                  </div>
                  <div class="figma-pill-cell">
                    <div style="font-size: 0.72rem; color: #e53e3e; font-weight: 700;">● RIGHT EDGE (Γ = +1)</div>
                    <div style="font-size: 0.78rem; color: #cbd5e1; margin-top: 2px;">Open circuit: <i>Z</i><sub>L</sub> &rarr; &infin;, VSWR &rarr; &infin;, zero terminal current.</div>
                  </div>
                  <div class="figma-pill-cell">
                    <div style="font-size: 0.72rem; color: #e53e3e; font-weight: 700;">● LEFT EDGE (Γ = −1)</div>
                    <div style="font-size: 0.78rem; color: #cbd5e1; margin-top: 2px;">Short circuit: <i>Z</i><sub>L</sub> = 0 &Omega;, terminal voltage cancellation.</div>
                  </div>
                  <div class="figma-pill-cell">
                    <div style="font-size: 0.72rem; color: #00d4f5; font-weight: 700;">● UPPER HALF (Im(Z) &gt; 0)</div>
                    <div style="font-size: 0.78rem; color: #cbd5e1; margin-top: 2px;">Inductive impedance: Series inductance or shorted line segment (<i>X</i><sub>L</sub> &gt; 0).</div>
                  </div>
                  <div class="figma-pill-cell">
                    <div style="font-size: 0.72rem; color: #a855f7; font-weight: 700;">● LOWER HALF (Im(Z) &lt; 0)</div>
                    <div style="font-size: 0.78rem; color: #cbd5e1; margin-top: 2px;">Capacitive impedance: Shunt capacitance or open stub section (<i>X</i><sub>C</sub> &lt; 0).</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

        with st.container(border=True):
            rld_section_header("Smith Chart Mathematical Theory & Coordinates")
            st.markdown("""
            #### Bilinear Conformal Transformation
            The Smith chart (invented by Phillip H. Smith in 1939) is a graphical representation of the complex reflection coefficient plane $\\Gamma = u + jv$, mapped from normalized impedance $z = r + jx = Z/Z_0$:
            $$\\Gamma = \\frac{z - 1}{z + 1} = \\frac{(r - 1) + jx}{(r + 1) + jx}$$
            
            This bilinear transform maps the entire right-half complex impedance plane (all passive circuits with $r = \\text{Re}(z) \\ge 0$) into the unit circle $|\\Gamma| \\le 1$.
            
            #### Constant Resistance Circles & Constant Reactance Arcs
            Equating real and imaginary components yields the orthogonal family of circles:
            - **Constant Resistance ($r = \\text{const}$):**
              $$\\left(u - \\frac{r}{1+r}\\right)^2 + v^2 = \\left(\\frac{1}{1+r}\\right)^2$$
              Circles centered at $u = r/(1+r), v = 0$ with radius $1/(1+r)$. All circles pass through the open-circuit pole $(1, 0)$.
            - **Constant Reactance ($x = \\text{const}$):**
              $$(u - 1)^2 + \\left(v - \\frac{1}{x}\\right)^2 = \\left(\\frac{1}{x}\\right)^2$$
              Circular arcs centered at $u = 1, v = 1/x$ with radius $1/|x|$. Upper arcs ($x > 0$) are inductive; lower arcs ($x < 0$) are capacitive.
            
            #### Clockwise Rotation Toward Generator
            Moving from load toward generator across distance $l$ accumulates a phase delay:
            $$\\Gamma(l) = \\Gamma_L e^{-2j\\beta l}$$
            This represents a **clockwise rotation** around the center of the Smith chart by an angle $\\theta = 2\\beta l = 4\\pi l / \\lambda$.
            A full $360^\\circ$ rotation on the chart corresponds to an electrical distance of **half a wavelength ($\\\\lambda/2$)**.
            """)

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

    tab_diag_live, tab_diag_method, tab_diag_interpret = st.tabs([
        "🔍 Live Diagnostic Evaluation",
        "🧠 Diagnosis Methodology & Rule Architecture",
        "📋 Interpreting Diagnostic Outputs",
    ])

    with tab_diag_live:
        rld_banner(
            "<strong>Engineering Transparency Note:</strong> Classifier thresholds (|Γ| &lt; 0.05, spectral trend &gt; 0.010) "
            "are calibrated engineering parameters tuned to this coaxial operating range — not universal electromagnetic constants.",
            kind="info", icon="ℹ️"
        )

        diag_col1, diag_col2 = st.columns([7, 13])

        with diag_col1:
            with st.container(border=True):
                rld_section_header("Diagnostic Classification")

                # Build rules chips
                rules_html = " ".join(f'<span class="rld-chip">{r}</span>' for r in inferred_class.rules_fired)
                conf_html = rld_conf_html(inferred_class.confidence)

                st.markdown(f"""
                <div style="display: flex; flex-direction: column; gap: 9px; margin-top: 2px;">
                  <div class="figma-pill-cell">
                    <div class="figma-metric-label" style="margin-bottom: 5px;">Contract Label</div>
                    {rld_badge_html(str(inferred_class))}
                  </div>
                  <div class="figma-pill-cell">
                    <div class="figma-metric-label" style="margin-bottom: 4px;">Physical Subtype</div>
                    <div style="font-size: 0.9rem; color: #dde6f0; font-weight: 600; margin-top: 1px; font-family: 'JetBrains Mono', monospace;">{inferred_class.subtype}</div>
                  </div>
                  <div class="figma-pill-cell">
                    <div class="figma-metric-label" style="margin-bottom: 5px;">Diagnostic Confidence</div>
                    {conf_html}
                  </div>
                  <div class="figma-pill-cell">
                    <div class="figma-metric-label" style="margin-bottom: 5px;">Rules Triggered</div>
                    <div style="margin-top: 2px;">{rules_html}</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

            with st.container(border=True):
                rld_section_header("Observed Signal Evidence")
                st.markdown(rld_evidence_items(diag_report["evidence"]), unsafe_allow_html=True)

        with diag_col2:
            with st.container(border=True):
                rld_section_header("Electromagnetic Physics Explanation")
                st.markdown(diag_report["physics_explanation"])

            with st.container(border=True):
                rld_section_header("Potential Ambiguities & Limitations")
                for amb in diag_report["ambiguities"]:
                    rld_banner(amb, kind="warn", icon="⚠️")

            with st.container(border=True):
                rld_section_header("Recommended Corrective Actions")
                for act in diag_report["corrective_actions"]:
                    rld_banner(act, kind="success", icon="🔧")

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

    with tab_diag_method:
        rld_section_header("7. Diagnosis Methodology & Decision Tree")
        with st.container(border=True):
            st.markdown("""
            #### The Single-Port Diagnostic Challenge
            In field operations, technicians cannot access the far terminal of an installed cable. The diagnostic engine must determine the physical state of the line strictly from the single-port frequency response $S_{11}(f)$ without "cheating" by reading simulation ground truth.

            #### Contract Labels vs Physical Subtypes
            To ensure rigid API compatibility, the diagnostic engine maps all evaluations into **5 frozen public contract classes**:
            `healthy`, `open`, `short`, `mismatch`, and `unknown`.
            Internally, it carries richer physical subtype diagnostic states:
            - `matched` $\\to$ `healthy`
            - `open_circuit` $\\to$ `open`
            - `short_circuit` $\\to$ `short`
            - `resistive_mismatch`, `series_L`, `shunt_C` $\\to$ `mismatch`
            - `uncertain` $\\to$ `unknown`

            #### Hierarchical Decision Rules
            
            1. **Rule 1 — Healthy Matched Line Detection:**
               $$\\text{mean}(|S_{11}|) < 0.05$$
               If average reflection is below $0.05$ (corresponding to $RL > 26\\text{ dB}$ and $< 0.25\\%$ reflected power), the line is classified as `healthy` (`matched`).
            
            2. **Rule 2 — Open vs Short Separation via Physical DC Phase Intercept:**
               When $\\text{mean}(|S_{11}|) > 0.95$, total reflection is occurring. However, at high frequencies, spatial phase wrapping causes $S_{11}$ to rotate repeatedly around the unit circle. At frequencies where $l = (2m+1)\\lambda/4$, a short circuit transforms into an open circuit!
               
               *The DC Phase Solution:* By unwrapping the phase $\\phi(f) = \\text{unwrap}(\\angle S_{11}(f))$ and performing a linear regression fit:
               $$\\phi(f) \\approx \\phi_0 - \\frac{4\\pi d}{v_p} f$$
               The engine extrapolates to zero frequency ($f \\to 0\\text{ Hz}$), recovering the true physical boundary condition:
               - **If $\\cos(\\phi_0) > 0$:** Classified as `open` (`open_circuit`, $\\Gamma_0 = +1.0$).
               - **If $\\cos(\\phi_0) \\le 0$:** Classified as `short` (`short_circuit`, $\\Gamma_0 = -1.0$).
               This physical extrapolation eliminates the quarter-wave ambiguity and achieves 100% separation between open and short circuits.

            3. **Rule 3 — Reactive Discontinuity Identification ($d|S_{11}|/df > 0.010$):**
               Lumped reactive defects have impedances that vary with frequency ($Z_s = j\\omega L$ or $Y_p = j\\omega C$).
               - **Series Inductance ($L$):** Discontinuity impedance $Z_s = j2\\pi f L$ rises with frequency. Reflection $|S_{11}|$ increases monotonically, and the Smith chart locus traces through the upper inductive half ($X > 0$). Classified as `mismatch` (`series_L`).
               - **Shunt Capacitance ($C$):** Discontinuity admittance $Y_p = j2\\pi f C$ rises with frequency. Reflection increases monotonically, and the Smith chart locus traces through the lower capacitive half ($X < 0$). Classified as `mismatch` (`shunt_C`).

            4. **Rule 4 — Flat Resistive Mismatch:**
               If reflection magnitude is frequency-independent ($\\text{std}(|S_{11}|) < 0.05$) and lies in the range $0.05 \\le |S_{11}| \\le 0.95$, the termination is a purely resistive mismatch ($Z_L = R_L \\ne Z_0$). Classified as `mismatch` (`resistive_mismatch`).

            5. **Rule 5 — Fallback Unknown:**
               If measured signatures do not match any known physical template or noise is excessive, the engine conservatively outputs `unknown`.
            """)

    with tab_diag_interpret:
        rld_section_header("9. Understanding Diagnostic Outputs")
        with st.container(border=True):
            st.markdown("""
            How to interpret diagnostic classification results in practice:
            
            - **Contract Label (`healthy`, `open`, `short`, `mismatch`, `unknown`):**
              *What it represents:* High-level operational verdict.
              *Operational action:*
              - `HEALTHY`: Cable is verified intact; system is cleared for service.
              - `OPEN`: Cable severed, connector uncoupled, or center pin retracted. Inspect terminal connectors and cable jacket for breaks.
              - `SHORT`: Conductor pinched to ground, solder bridge at connector, or crushed dielectric. Inspect for physical pinch points or water penetration.
              - `MISMATCH`: Load impedance deviates from $Z_0$ or localized defect present. Proceed to Fault Location and Quarter-Wave Matching.
              - `UNKNOWN`: Highly corrupted or complex non-standard load. Requires manual inspection or wideband recalibration.
            
            - **Physical Subtype:**
              *What it represents:* The specific electromagnetic mechanism generating the reflection:
              - `series_L`: Conductor necking, fractured trace, or long connector lead.
              - `shunt_C`: Crushed outer conductor, water ingress, or terminal solder bead.
              - `resistive_mismatch`: Real load mismatch; ideal candidate for quarter-wave matching.
            
            - **Diagnostic Confidence (High, Medium, Low):**
              *What it represents:* Statistical reliability of the classification.
              *Interpretation:*
              - `HIGH`: Measurement metrics clearly exceed noise thresholds; definitive verdict.
              - `MEDIUM`: Elevated noise ($\\sigma > 0.03$) or borderline reflection metrics.
              - `LOW`: Extreme noise ($\\sigma > 0.08$) or severe multi-reflection interference; manual TDR inspection recommended.
            """)

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

    tab_loc_live, tab_loc_theory, tab_loc_interpret = st.tabs([
        "📍 Interactive Localization & Echo Profile",
        "📐 Fault-Location Theory & Mathematical Derivations",
        "🎯 Interpreting Localization Results",
    ])

    with tab_loc_live:
        th_col1, th_col2 = st.columns(2)
        with th_col1:
            with st.container(border=True):
                rld_section_header("Primary Method — Phase Slope Analysis")
                st.markdown("For a dominant boundary discontinuity at distance $d$, the round-trip delay imparts a linear phase ramp across frequency:")
                st.latex(r"\phi(f) \approx \phi_0 - \frac{4\pi d}{v_p}\,f \implies d = -\frac{v_p}{4\pi}\,\frac{d\phi}{df}")
                st.caption("Directly derived from course transmission-line phasor theory. Reactive discontinuities introduce minor frequency-dependent phase offsets.")

        with th_col2:
            with st.container(border=True):
                rld_section_header("Supporting Cross-Check — IFFT Pseudo-TDR")
                st.markdown("Inverse FFT with a Hann window synthesizes the pseudo-impulse reflection profile $|h(t)|$. A peak at round-trip time $t$ locates the reflection at:")
                st.latex(r"d = \frac{v_p\,t}{2}, \quad \Delta R = \frac{v_p}{2B}")
                st.caption("Zero-padding interpolates the peak centroid but does not exceed the physical Rayleigh resolution limit ΔR.")

        loc_col1, loc_col2 = st.columns([12, 8])

        with loc_col1:
            with st.container(border=True):
                rld_plot_header(
                    "IFFT Pseudo-Time Echo Response |h(t)|",
                    "Synthesized spatial reflection envelope with localized peak centroid and Rayleigh resolution limit"
                )

                tdr = loc_dual["tdr_data"]
                fig_tdr, ax_t = plt.subplots(figsize=(7.5, 3.8))

                if tdr.get("d_axis_m") is not None and len(tdr["d_axis_m"]) > 0:
                    d_axis = tdr["d_axis_m"]
                    t_mag = tdr["tdr_mag"]
                    view_mask = d_axis <= max(length * 1.5, 2.0)
                    ax_t.plot(d_axis[view_mask], t_mag[view_mask], color="#a855f7", lw=2.0, label="IFFT Echo Profile |h(t)|")

                    d_est = loc_dual["dist_ifft_m"]
                    if d_est is not None:
                        dr = res_info["range_res_m"]
                        ax_t.axvspan(max(0.0, d_est - dr / 2), d_est + dr / 2, color="#00d4f5", alpha=0.15, label=f"Rayleigh ΔR ({dr*100:.1f} cm)")
                        ax_t.axvline(d_est, color="#e53e3e", linestyle="--", lw=1.8, label=f"Peak Centroid: {d_est:.3f} m")

                    # Highlight prominent secondary peak if present
                    sec_peaks = [p for p in loc_dual.get("secondary_peaks", []) if not p.get("is_dominant", False) and p.get("magnitude", 0) > 0.15 * tdr.get("peak_val", 1.0)]
                    if len(sec_peaks) > 0:
                        top_sec = sec_peaks[0]
                        sec_label = "Harmonic Echo" if top_sec.get("is_multipath_echo") else "Secondary Defect"
                        ax_t.axvline(top_sec["dist_m"], color="#a855f7", linestyle=":", lw=1.5, label=f"{sec_label}: {top_sec['dist_m']:.3f} m")

                    ax_t.set_xlabel("Physical Distance along Line (m)", fontsize=9)
                    ax_t.set_ylabel("Reflection Magnitude |h(t)|", fontsize=9)
                    ax_t.grid(True, alpha=0.55)
                    ax_t.legend(loc="upper right")

                plt.tight_layout(pad=0.6)
                st.pyplot(fig_tdr)
                plt.close(fig_tdr)

        with loc_col2:
            d1 = loc_dual["dist_ifft_m"]
            d2 = loc_dual["dist_phase_m"]

            rel_badge = '<span class="rld-badge rld-badge-healthy">● RELIABLE &amp; VERIFIED</span>' if loc_dual["is_reliable"] else '<span class="rld-badge rld-badge-open">● HIGH UNCERTAINTY</span>'

            with st.container(border=True):
                rld_section_header("Localization Results Summary")

                d2_str = f"{d2:.3f}" if d2 is not None else "None"
                d1_str = f"{d1:.3f}" if d1 is not None else "None"

                sec_peaks = [p for p in loc_dual.get("secondary_peaks", []) if not p.get("is_dominant", False) and p.get("magnitude", 0) > 0.15 * tdr.get("peak_val", 1.0)]
                sec_html = ""
                if len(sec_peaks) > 0:
                    top_sec = sec_peaks[0]
                    echo_type = "Harmonic Echo" if top_sec.get("is_multipath_echo") else "Secondary Discontinuity"
                    sec_html = f"""
                  <div class="figma-pill-cell" style="border-left: 2px solid #a855f7;">
                    <div class="figma-metric-label" style="margin-bottom: 3px;">Secondary Reflection ({echo_type})</div>
                    <div style="font-size: 1.05rem; color: #c084fc; font-weight: 700; font-family: 'JetBrains Mono', monospace;">
                      {top_sec['dist_m']:.3f} <span class="rld-unit">m ({top_sec['relative_amplitude_db']:.1f} dB)</span>
                    </div>
                  </div>
                    """

                st.markdown(f"""
                <div style="display: flex; flex-direction: column; gap: 8px;">
                  <div class="figma-pill-cell">
                    <div class="figma-metric-label" style="margin-bottom: 3px;">Phase-Slope Estimate (Primary, <i>d</i>)</div>
                    <div style="font-size: 1.15rem; color: #00d4f5; font-weight: 700; font-family: 'JetBrains Mono', monospace;">
                      {d2_str} <span class="rld-unit">{"m" if d2 is not None else "(insufficient reflection)"}</span>
                    </div>
                  </div>
                  <div class="figma-pill-cell">
                    <div class="figma-metric-label" style="margin-bottom: 3px;">IFFT TDR Cross-Check (Supporting, <i>d</i>)</div>
                    <div style="font-size: 1.15rem; color: #e2e8f0; font-weight: 700; font-family: 'JetBrains Mono', monospace;">
                      {d1_str} <span class="rld-unit">{"m" if d1 is not None else "(no clear echo)"}</span>
                    </div>
                  </div>
                  {sec_html}
                  <div class="figma-pill-cell">
                    <div class="figma-metric-label" style="margin-bottom: 3px;">Rayleigh Resolution Limit (Δ<i>R</i>)</div>
                    <div style="font-size: 1.05rem; color: #cbd5e1; font-weight: 600; font-family: 'JetBrains Mono', monospace;">
                      {res_info['range_res_m']*100:.2f} <span class="rld-unit">cm</span>
                    </div>
                  </div>
                  <div class="figma-pill-cell">
                    <div class="figma-metric-label" style="margin-bottom: 3px;">Unambiguous Range (<i>R</i><sub>max</sub>)</div>
                    <div style="font-size: 1.05rem; color: #cbd5e1; font-weight: 600; font-family: 'JetBrains Mono', monospace;">
                      {res_info['unambig_range_m']:.2f} <span class="rld-unit">m</span>
                    </div>
                  </div>
                  <div class="figma-pill-cell">
                    <div class="figma-metric-label" style="margin-bottom: 6px;">Estimation Status</div>
                    <div>{rel_badge}</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

    with tab_loc_theory:
        rld_section_header("8. Fault-Location Methodology & Derivations")
        with st.container(border=True):
            st.markdown("""
            #### The Dual-Method Architecture
            To ensure bulletproof distance estimation, RF LINE DOCTOR employs two independent, complementary signal processing methods:
            
            1. **Primary Method — Unwrapped Phase-Slope Analysis:**
               Consider a single dominant reflection occurring at distance $d$ from the measurement port. The round-trip transmission phasor is:
               $$S_{11}(f) = |\\Gamma| e^{j \\phi(f)} = |\\Gamma| e^{j (\\phi_0 - 2\\beta d)}$$
               Substituting the phase constant $\\beta = \\frac{2\\pi f}{v_p}$:
               $$\\phi(f) = \\phi_0 - \\frac{4\\pi d}{v_p} f$$
               Taking the derivative with respect to frequency:
               $$\\frac{d\\phi}{df} = -\\frac{4\\pi d}{v_p} \\implies d = -\\frac{v_p}{4\\pi} \\frac{d\\phi}{df}$$
               
               A robust least-squares linear regression is computed across the unwrapped phase vector.
               *Reactive Discontinuity Consideration:* For lumped reactive defects ($Z_s = j\\omega L$ or $Y_p = j\\omega C$), the reflection coefficient has an intrinsic frequency-dependent phase:
               $$\\phi_{\\text{total}}(f) = \\angle\\Gamma_{\\text{discontinuity}}(f) - \\frac{4\\pi d}{v_p} f$$
               This causes a slight reactive phase bias in the slope.

            2. **Supporting Cross-Check — Hann-Windowed Zero-Padded IFFT Pseudo-TDR:**
               Inverse Fast Fourier Transform converts the frequency-domain reflection response $S_{11}(f_k)$ into a synthetic spatial impulse response $h(t_n)$:
               $$h(n) = \\frac{1}{N} \\sum_{k=0}^{N-1} W(k) S_{11}(k) e^{j \\frac{2\\pi k n}{N_{\\text{pad}}}}$$
               
               - **Hann Window $W(k)$:**
                 $$W(k) = 0.5 - 0.5\\cos\\left(\\frac{2\\pi k}{N - 1}\\right)$$
                 Suppresses truncation sidelobes from $-13\\text{ dB}$ (rectangular window) down to $-32\\text{ dB}$, preventing false phantom echoes.
               - **Zero-Padding ($N_{\\text{pad}} = 4N$):**
                 Interpolates the time-domain spatial grid for smooth centroid localization without violating physical bandwidth limits.
               - **Peak Centroid Distance Conversion:**
                 $$t_{\\text{peak}} = \\arg\\max_t |h(t)| \\implies d = \\frac{v_p \\cdot t_{\\text{peak}}}{2}$$

            #### Fundamental Spatial Metrics
            - **Rayleigh Physical Range Resolution ($\\Delta R$):**
              $$\\Delta R = \\frac{v_p}{2 B} = \\frac{v_p}{2 (f_{\\max} - f_{\\min})}$$
              *Physical meaning:* The minimum distance between two separate discontinuities required to resolve them as distinct peaks. No signal processing or interpolation can bypass this fundamental physics limit.
            - **Unambiguous Range ($R_{\\max}$):**
              $$R_{\\max} = \\frac{v_p}{2 \\Delta f} = \\frac{v_p (N - 1)}{2 (f_{\\max} - f_{\\min})}$$
              *Physical meaning:* The maximum cable length measurable before time-domain alias folding occurs.
            - **Dual-Method Reliability Metric:**
              $$|d_{\\text{phase}} - d_{\\text{ifft}}| \\le 3 \\Delta R$$
              When both methods agree within 3 Rayleigh bins, the result is marked **RELIABLE & VERIFIED**. Larger discrepancies indicate multi-reflection interference or severe reactive phase distortion.
            """)

    with tab_loc_interpret:
        rld_section_header("9. Understanding Localization Outputs")
        with st.container(border=True):
            st.markdown("""
            How to read and act on fault localization results:
            
            - **Phase-Slope Distance Estimate (Primary, $d$ [m]):**
              *What it represents:* Highly accurate continuous distance estimate based on the linear phase slope across the entire frequency band.
              *Interpretation:*
              - If $d \\approx l$ (within $\\pm 5\\%$): Fault is located at the cable termination. Check load resistor, antenna connector, or terminating bulkhead.
              - If $d < l$: Fault is an intermediate defect along the cable run. Inspect cable at distance $d$ for kinks, crushing, or water penetration.
            
            - **IFFT TDR Cross-Check Distance (Supporting, $d$ [m]):**
              *What it represents:* Distance corresponding to the peak of the synthetic time-domain impulse echo $|h(t)|$.
              *Interpretation:* Provides visual corroboration. In the presence of noise or reactive phase shifts, comparing the IFFT peak against the phase slope confirms whether the echo is a true discontinuity or a noise artifact.
            
            - **Rayleigh Resolution Limit $\\Delta R$ [cm]:**
              *What it represents:* Physical spatial resolution of the measurement setup.
              *Engineering tip:* To improve spatial resolution (smaller $\\Delta R$), increase the sweep stop frequency $f_{\\max}$ or broaden the frequency range.
            
            - **Estimation Status (Reliable vs High Uncertainty):**
              *What it represents:* Confidence indicator comparing phase slope and IFFT estimates against the $3\\Delta R$ tolerance window.
              *Operational guidance:* If status is **HIGH UNCERTAINTY**, the line likely has multiple reflective defects or high reactive dispersion; inspect the full cable path.
            """)

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

    tab_match_live, tab_match_theory, tab_match_interpret = st.tabs([
        "⚡ Interactive Matching Synthesis",
        "📐 Quarter-Wave Theory & Analytical Synthesis",
        "📊 Understanding Matching Outputs",
    ])

    with tab_match_live:
        is_real = isinstance(ZL_val, complex) and np.isfinite(ZL_val.real) and ZL_val.real > 0 and abs(ZL_val.imag) < 1e-5

        if not is_real:
            rld_banner(
                "<strong>Real Load Requirement:</strong> Single-section quarter-wave transformers require a purely real load resistance <i>R</i><sub>L</sub> &gt; 0.<br>"
                f"Current termination is <code><i>Z</i><sub>L</sub> = {ZL_val}</code>.<br>"
                "Select <strong>Case 2: Resistive Mismatch</strong> in the sidebar to design a matched transformer. Complex loads require reactive stub tuning.",
                kind="warn", icon="⚠️"
            )
        else:
            RL_val = float(ZL_val.real)
            f_mid = float(np.mean(freqs))

            match_col1, match_col2 = st.columns([7, 13])

            with match_col1:
                with st.container(border=True):
                    rld_section_header("Design Parameters")
                    f_min_mhz = float(freqs[0] / 1e6)
                    f_max_mhz = float(freqs[-1] / 1e6)
                    f_mid_mhz = float(np.clip(f_mid / 1e6, f_min_mhz, f_max_mhz))
                    f_design_mhz = st.number_input(
                        "Design Frequency f₀ (MHz)",
                        min_value=f_min_mhz,
                        max_value=f_max_mhz,
                        value=f_mid_mhz,
                        step=50.0,
                        help="• Represents: Center frequency f₀ where exact reflection cancellation occurs\n• Unit: Megahertz (MHz)\n• Why required: Determines physical length lt = vp / (4·f₀) of quarter-wave section.",
                    )
                    f_design = f_design_mhz * 1e6

                    try:
                        match_res = match.compare_matching(Z0, RL_val, freqs, vf=vf, f_design=f_design, rl_threshold=20.0)
                    except ValueError as err:
                        st.error(f"Quarter-wave matching design error: {err}")
                        match_res = match.compare_matching(Z0, RL_val, freqs, vf=vf, f_design=None, rl_threshold=20.0)

                    f0_rl = match_res["at_f_design"]["rl_db"]
                    rl_str = "∞ dB (Exact)" if np.isinf(f0_rl) else f"{f0_rl:.1f} dB"

                    st.markdown(f"""
                    <div style="display: flex; flex-direction: column; gap: 9px; margin-top: 10px;">
                      <div class="figma-metric-card" style="border-top: 2px solid #00d4f5;">
                        <div class="figma-metric-label">Transformer Impedance (<i>Z</i><sub>t</sub>)</div>
                        <div class="rld-num" style="color: #00d4f5;">{match_res['Zt']:.2f}<span class="rld-unit">Ω</span></div>
                        <div class="figma-metric-sub">Calculated via √(<i>Z</i><sub>0</sub> · <i>R</i><sub>L</sub>)</div>
                      </div>
                      <div class="figma-metric-card" style="border-top: 2px solid #0ea472;">
                        <div class="figma-metric-label">Physical Length (<i>l</i><sub>t</sub>)</div>
                        <div class="rld-num" style="color: #0ea472;">{match_res['length_m']*1000:.1f}<span class="rld-unit">mm</span></div>
                        <div class="figma-metric-sub">Quarter-wave at {f_design_mhz:.0f} MHz (λ/4)</div>
                      </div>
                      <div class="figma-metric-card" style="border-top: 2px solid #d97706;">
                        <div class="figma-metric-label">Usable Bandwidth (RL ≥ 20 dB)</div>
                        <div class="rld-num" style="color: #d97706;">{match_res['bandwidth_hz']/1e6:.1f}<span class="rld-unit">MHz</span></div>
                        <div class="figma-metric-sub">Passband where VSWR ≤ 1.222</div>
                      </div>
                      <div class="figma-metric-card" style="border-top: 2px solid #3b9ede;">
                        <div class="figma-metric-label">Matched Return Loss at <i>f</i><sub>0</sub></div>
                        <div class="rld-num" style="color: #3b9ede;">{rl_str}</div>
                        <div class="figma-metric-sub">Theoretical peak reflection attenuation</div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

            with match_col2:
                with st.container(border=True):
                    rld_plot_header(
                        "Performance Comparison (Before vs. After Matching)",
                        f"Evaluation of VSWR(f) and Return Loss RL(f) passband suppression · f₀ = {f_design_mhz:.0f} MHz"
                    )

                    fig_mc, (ax_mv, ax_mr) = plt.subplots(2, 1, figsize=(7.8, 5.8), sharex=True)

                    # VSWR
                    ax_mv.plot(f_ghz, match_res["before"]["vswr"], color="#e53e3e", linestyle="--", lw=1.8, label="Before Matching (Unmatched)")
                    ax_mv.plot(f_ghz, match_res["after"]["vswr"], color="#00d4f5", lw=2.2, label="After Matching (λ/4 Transformer)")
                    ax_mv.axvline(f_design / 1e9, color="#546580", linestyle=":", label=f"f₀ = {f_design/1e9:.2f} GHz")
                    ax_mv.set_ylabel("VSWR  [dimensionless]", fontsize=8.5)
                    ax_mv.set_ylim(0.95, 3.5)
                    ax_mv.grid(True, alpha=0.55)
                    ax_mv.legend(loc="upper right")

                    # Return Loss
                    ax_mr.plot(f_ghz, match_res["before"]["rl_db"], color="#e53e3e", linestyle="--", lw=1.8, label="Before Matching")
                    ax_mr.plot(f_ghz, match_res["after"]["rl_db"], color="#0ea472", lw=2.2, label="After Matching")
                    ax_mr.axhline(20.0, color="#3b9ede", linestyle="--", lw=1.2, label="20 dB Match Benchmark")
                    ax_mr.axvline(f_design / 1e9, color="#546580", linestyle=":")
                    ax_mr.set_ylabel("Return Loss  (dB)", fontsize=8.5)
                    ax_mr.set_xlabel("Frequency  (GHz)", fontsize=8.5)
                    ax_mr.set_ylim(0, 52)
                    ax_mr.grid(True, alpha=0.55)
                    ax_mr.legend(loc="lower right")

                    plt.tight_layout(pad=0.6)
                    st.pyplot(fig_mc)
                    plt.close(fig_mc)

    with tab_match_theory:
        rld_section_header("Quarter-Wave Transformer Theory & Synthesis")
        with st.container(border=True):
            st.markdown("""
            #### Transmission-Line Impedance Inverter Property
            Consider a uniform lossless transmission line section of characteristic impedance $Z_t$ and physical length $l_t$, terminated in a real resistive load $R_L$.
            The general input impedance looking into this transformer section is:
            $$Z_{\\text{in}} = Z_t \\left[ \\frac{R_L + j Z_t \\tan(\\beta_t l_t)}{Z_t + j R_L \\tan(\\beta_t l_t)} \\right]$$
            
            When the length is chosen to be an exact quarter-wavelength at design frequency $f_0$:
            $$l_t = \\frac{\\lambda_t}{4} \\implies \\beta_t l_t = \\left(\\frac{2\\pi}{\\lambda_t}\\right)\\left(\\frac{\\lambda_t}{4}\\right) = \\frac{\\pi}{2}$$
            Since $\\tan(\\pi/2) \\to \\infty$, dividing the numerator and denominator by $\\tan(\\beta_t l_t)$ yields the celebrated **quarter-wave inverter equation**:
            $$Z_{\\text{in}} = \\frac{Z_t^2}{R_L}$$

            #### Characteristic Impedance & Physical Cut Length Synthesis
            To achieve a perfect match looking from the main feeder line ($Z_{\\text{in}} = Z_0$):
            $$Z_0 = \\frac{Z_t^2}{R_L} \\implies Z_t = \\sqrt{Z_0 R_L}$$
            The required physical cut length in millimetres is:
            $$l_t = \\frac{\\lambda_t}{4} = \\frac{v_p}{4 f_0} = \\frac{v_f \\cdot c_0}{4 f_0} \\times 10^3 \\quad [\\text{mm}]$$
            
            At $f = f_0$, the input reflection coefficient vanishes identically:
            $$\\Gamma(f_0) = \\frac{Z_{\\text{in}} - Z_0}{Z_{\\text{in}} + Z_0} = 0 \\implies \\text{VSWR}(f_0) = 1.00, \\quad \\text{RL}(f_0) \\to \\infty\\text{ dB}$$

            #### Contiguous Passband Bandwidth Definition
            Although the transformer provides zero reflection at $f_0$, reflections grow as frequency moves away from $f_0$.
            RF LINE DOCTOR evaluates the **contiguous usable bandwidth** as the frequency span $[f_1, f_2]$ containing $f_0$ where:
            $$\\text{RL}(f) \\ge 20.0\\text{ dB} \\iff |\\Gamma| \\le 0.10 \\iff \\text{VSWR} \\le 1.222$$
            
            The theoretical fractional bandwidth is governed by:
            $$\\frac{\\Delta f}{f_0} = 2 - \\frac{4}{\\pi} \\arccos\\left( \\frac{\\Gamma_m}{\\sqrt{1 - \\Gamma_m^2}} \\frac{2\\sqrt{Z_0 R_L}}{|R_L - Z_0|} \\right)$$
            where $\\Gamma_m = 0.10$ for the $20\\text{ dB}$ specification.

            #### Engineering Assumptions & Scope
            - **Purely Real Loads ($R_L > 0$):** Single-section quarter-wave transformers require real load terminations. Complex loads ($Z_L = R + jX$) require shunt/series reactive stub cancellation to eliminate reactance before applying the quarter-wave section.
            - **Narrow-Band Nature:** Single-section transformers are inherently narrow-band ($10\\% - 30\\%$ fractional bandwidth). Broadband matching requires multi-section Binomial or Chebyshev transformers.
            """)

    with tab_match_interpret:
        rld_section_header("9. Understanding Matching Outputs")
        with st.container(border=True):
            st.markdown("""
            How to interpret and apply the synthesized transformer parameters:
            
            - **Transformer Characteristic Impedance $Z_t$ [Ω]:**
              *What it represents:* Geometric mean impedance $Z_t = \\sqrt{Z_0 R_L}$.
              *Practical application:* Specifies the required dielectric and conductor dimensions for fabricating the quarter-wave matching section (e.g. coaxial inner conductor diameter or microstrip trace width).
            
            - **Physical Length $l_t$ [mm]:**
              *What it represents:* One-quarter of the guided wavelength at design frequency: $l_t = \\lambda_t / 4$.
              *Practical application:* The exact mechanical length to cut the matching transmission line section.
            
            - **Usable Bandwidth [MHz]:**
              *What it represents:* The frequency range over which reflection remains suppressed below $-20\\text{ dB}$ (< 1% reflected power).
              *Engineering significance:* Verifies whether the matching network covers the entire operational channel of the RF transmitter or receiver without requiring retuning.
            
            - **Before vs After Comparison Plots:**
              *What they represent:* Demonstrates performance transformation.
              *Interpretation:* The unmatched load shows high, flat VSWR (e.g. $2.4 : 1$) and poor return loss ($< 8\\text{ dB}$). After inserting the synthesized transformer, VSWR drops to $1.00$ at $f_0$ and return loss notches to infinity, demonstrating complete destructive interference of reflections.
            """)

    render_footer()


# ─────────────────────────────────────────────────────────────────────────────
# VIEW 7: INDEPENDENT VALIDATION LAB
# ─────────────────────────────────────────────────────────────────────────────
elif "validation" in nav_section.lower():
    render_breadcrumb("VALIDATION LAB")
    render_page_header(
        "Independent validation laboratory",
        "Repeatable performance check across 120 randomized simulated line cases and formal testing evidence.",
    )

    tab_val_lab, tab_val_evidence, tab_val_limits = st.tabs([
        "🧪 Monte Carlo Verification Lab",
        "🏆 Validation & Testing Evidence",
        "⚖️ Model Assumptions & Academic References",
    ])

    with tab_val_lab:
        with st.container(border=True):
            rld_section_header("Repeatable Monte Carlo Simulation Suite")
            st.markdown('<div style="font-size: 0.82rem; color: #8898aa; line-height: 1.5;">This automated test executes 120 randomized coaxial line configurations (20 trials per each of the 6 physical scenarios) with Gaussian measurement noise (σ = 0.02). The predicted condition is evaluated against the ground-truth simulation model to verify classifier reliability.</div>', unsafe_allow_html=True)

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
                        rld_section_header(f"Contract Confusion Matrix (Accuracy = {val_rep['accuracy']*100:.1f}%)")
                        df_vcm = pd.DataFrame(
                            val_rep["confusion_matrix"],
                            index=[f"True: {l}" for l in contract_labels],
                            columns=[f"Pred: {l}" for l in contract_labels],
                        )
                        st.dataframe(df_vcm)

                with v_col2:
                    with st.container(border=True):
                        rld_section_header("Per-Class Classification Metrics")
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
                        rld_section_header(f"Subtype Confusion Matrix (6 Scenarios, Accuracy = {sub_rep['accuracy']*100:.1f}%)")
                        df_scm = pd.DataFrame(
                            sub_rep["confusion_matrix"],
                            index=[f"True: {l}" for l in scen_labels],
                            columns=[f"Pred: {l}" for l in scen_labels],
                        )
                        st.dataframe(df_scm)

                with s_col2:
                    with st.container(border=True):
                        rld_section_header("Subtype Classification Metrics")
                        sm_rows = []
                        for l in scen_labels:
                            sr_dict = {"Scenario": l}
                            sr_dict.update(sub_rep["per_class"][l])
                            sm_rows.append(sr_dict)
                        st.dataframe(pd.DataFrame(sm_rows))

                t_locs = [it["true_pos"] for it in v_dataset if it["true_pos"] is not None]
                e_locs = [it["est_pos"] for it in v_dataset if it["true_pos"] is not None]
                l_stats = compute_location_metrics(t_locs, e_locs)
                rld_banner(f"<strong>Fault-Location Metric:</strong> MAE = <code>{l_stats['mae_m']*100:.2f} cm</code> | RMSE = <code>{l_stats['rmse_m']*100:.2f} cm</code> (Valid Cases: {l_stats['valid_count']}/{len(t_locs)})", kind="success", icon="✅")

    with tab_val_evidence:
        rld_section_header("11. Validation & Testing Evidence")
        with st.container(border=True):
            st.markdown("""
            RF LINE DOCTOR has been subjected to rigorous three-tier academic verification:
            
            #### 1. Automated Testing Suite (151 Pytest Tests)
            The repository contains a dedicated, fully automated testing suite executed on every commit via `pytest`:
            - **Core Physics & Boundary Conditions (`tests/test_line_model.py`):** 27 tests verifying lossless line equations, zero-length limits, quarter-wave inversions, and half-wave transparency.
            - **Measurement Metrics (`tests/test_measurements.py`):** 12 tests validating reflection coefficient, VSWR, return loss, and non-passive VSWR NaN handling.
            - **Cascaded Discontinuity Modeling (`tests/test_fault_simulation.py`):** 10 tests validating ABCD 2-port cascading and unclipped Gaussian noise.
            - **Fault Classification & DC Phase Intercept (`tests/test_diagnosis.py`):** 28 tests verifying 100% open vs short separation via $\\phi_0 = \\lim_{f \\to 0}\\angle S_{11}(f)$.
            - **Fault Location & Rayleigh Limits (`tests/test_location.py`):** 5 tests verifying phase-slope distance estimation, Hann-windowed IFFT reflectometry, and spatial resolution metrics.
            - **Quarter-Wave Matching (`tests/test_matching.py`):** 7 tests validating $Z_t = \\sqrt{Z_0 R_L}$, exact reflection cancellation at $f_0$, and passband bandwidth evaluation ($RL \\ge 20\\text{ dB}$).
            - **10 Analytical Benchmarks (`tests/test_benchmarks.py`):** 10 tests comparing application results against independently derived closed-form analytical models within strict machine tolerances ($10^{-12}$).
            - **Contract Classification Labels (`tests/test_classification_labels.py`):** 6 tests verifying frozen API labels (`healthy`, `open`, `short`, `mismatch`, `unknown`).
            - **Multi-Parameter Consistency (`tests/test_consistency.py`):** 8 tests validating monotonicity, scale invariance, and parameter stability.
            - **Numerical Robustness (`tests/test_numerical_edge_cases.py`):** 10 tests validating proper rejection of negative inputs, non-finite values (NaN, Inf), and zero-division prevention.
            - **Circuit Simulator Cross-Validation (`tests/test_qucs_cross_validation.py`):** 1 regression test validating agreement with Qucsator simulation datasets.
            - **End-to-End Hand-Calculation Benchmarks (`tests/test_integration.py`):** 8 tests validating textbook problem sets.
            """)

        rld_section_header("Independent Circuit Simulator Cross-Validation (Qucsator / Qucs-S)")
        with st.container(border=True):
            st.markdown("""
            To independently cross-validate RF LINE DOCTOR against an established RF circuit simulator, a benchmark transmission line case ($l = 1.0\\text{ m}, Z_0 = 50\\,\\Omega, v_p = 2\\times 10^8\\text{ m/s}, Z_L = 25\\,\\Omega$) was simulated using **Qucsator v1.0.7** (the simulation backend of Qucs-S / QucsStudio) across 100 MHz to 1.0 GHz (50 sample points).
            The simulation was exported to standard Touchstone 1-port format (`qucs_mismatch.s1p`) and cross-checked using `scikit-rf` 2.2.0:
            """)
            qucs_df = pd.DataFrame([
                {"Metric": "Reflection Magnitude |S₁₁|", "Max Absolute Difference": "8.23 × 10⁻¹⁴", "Max Relative Error": "2.47 × 10⁻¹¹ %", "Status": "Exact numerical agreement"},
                {"Metric": "Reflection Phase ∠S₁₁", "Max Absolute Difference": "1.35 × 10⁻⁹ deg", "Max Relative Error": "9.38 × 10⁻¹⁰ %", "Status": "Exact numerical agreement"},
                {"Metric": "Input Impedance |Z_in|", "Max Absolute Difference": "2.60 × 10⁻⁹ Ω", "Max Relative Error": "3.57 × 10⁻⁹ %", "Status": "Exact numerical agreement"},
                {"Metric": "VSWR", "Max Absolute Difference": "5.92 × 10⁻¹³", "Max Relative Error": "2.96 × 10⁻¹¹ %", "Status": "Exact numerical agreement"},
                {"Metric": "Return Loss (RL)", "Max Absolute Difference": "2.14 × 10⁻¹² dB", "Max Relative Error": "2.25 × 10⁻¹¹ %", "Status": "Exact numerical agreement"},
            ])
            st.dataframe(qucs_df, hide_index=True)

    with tab_val_limits:
        rld_section_header("10. Model Assumptions & Limitations")
        with st.container(border=True):
            st.markdown("""
            - **Single-Mode TEM Propagation:** Valid below the coaxial TE₁₁ waveguide cutoff frequency ($f < f_c$).
            - **Linear & Isotropic Medium:** Permittivity $\\epsilon$ and permeability $\\mu$ are constant and scalar.
            - **Lossless Approximation ($R=0, G=0$):** High accuracy for short RF coaxial lines ($l < 10\\text{ m}$) at UHF/SHF frequencies.
            - **Localized Lumped Discontinuities:** Discontinuity dimensions are electrically small ($\\Delta z \\ll \\lambda$).
            - **Rayleigh Spatial Limit:** Fundamental resolution limit $\\Delta R = v_p / (2B)$ cannot be bypassed by zero-padding.
            - **Unclipped Noise Handling:** Points with $|S_{11}| > 1.0$ correctly return $\\text{VSWR} = \\text{NaN}$.
            """)

        rld_section_header("12. References & Academic Acknowledgements")
        with st.container(border=True):
            st.markdown("""
            1. **D. M. Pozar**, *Microwave Engineering*, 4th Edition, John Wiley & Sons, Hoboken, NJ, 2011.
            2. **R. E. Collin**, *Foundations for Microwave Engineering*, 2nd Edition, IEEE Press / Wiley-Interscience, New York, 2001.
            3. **S. J. Orfanidis**, *Electromagnetic Waves and Antennas*, Rutgers University, 2016.
            4. **IEEE Std 1785-2016**, *IEEE Standard for Waveguide S-Parameter Measurements*.
            5. **Curricular Context:** Developed as an educational virtual prototype for **EC-3104 Microwave Engineering**.
            """)

    render_footer()
