"""
app.py -- RF LINE DOCTOR Streamlit Simulation Platform.

A clean, results-focused virtual transmission-line simulation and diagnostics tool.
Supports physical fault modeling, frequency sweeps, fault diagnosis,
time-domain reflectometry localization, impedance matching, and data export.
"""

import io
import os
import sys
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
from core.fault_location import locate_fault_dual_method, calculate_resolution_metrics
from core.diagnostic_explanations import generate_full_diagnostic_report

# ── Streamlit Page Configuration ──────────────────────────────────────────────
st.set_page_config(
    page_title="RF Line Doctor - Transmission Line Simulation",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Minimalist Clean CSS Styling ─────────────────────────────────────────────
st.markdown("""
<style>
/* Clean typography and base styling */
html, body, [class*="css"], button, input, select, textarea {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #0f172a;
}

/* Page container constraints */
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2.5rem;
    padding-left: 1.8rem;
    padding-right: 1.8rem;
    max-width: 1480px;
}

/* Header styling */
.main-title {
    font-size: 1.65rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.2rem;
    letter-spacing: -0.01em;
}
.main-subtitle {
    font-size: 0.92rem;
    color: #475569;
    margin-bottom: 1.25rem;
}

/* Metric cards responsive grids */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 0.85rem;
    margin-bottom: 1.25rem;
    width: 100%;
}
@media (max-width: 1400px) {
    .metrics-grid {
        grid-template-columns: repeat(3, 1fr);
    }
}
@media (max-width: 768px) {
    .metrics-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}
@media (max-width: 480px) {
    .metrics-grid {
        grid-template-columns: 1fr;
    }
}

.metrics-grid-5 {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 0.85rem;
    margin-bottom: 1.25rem;
    width: 100%;
}
@media (max-width: 1400px) {
    .metrics-grid-5 {
        grid-template-columns: repeat(3, 1fr);
    }
}
@media (max-width: 768px) {
    .metrics-grid-5 {
        grid-template-columns: repeat(2, 1fr);
    }
}
@media (max-width: 480px) {
    .metrics-grid-5 {
        grid-template-columns: 1fr;
    }
}

.metrics-grid-4 {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.85rem;
    margin-bottom: 1.25rem;
    width: 100%;
}
@media (max-width: 1200px) {
    .metrics-grid-4 {
        grid-template-columns: repeat(2, 1fr);
    }
}
@media (max-width: 520px) {
    .metrics-grid-4 {
        grid-template-columns: 1fr;
    }
}

.metrics-grid-3 {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.85rem;
    margin-bottom: 1.25rem;
    width: 100%;
}
@media (max-width: 900px) {
    .metrics-grid-3 {
        grid-template-columns: repeat(2, 1fr);
    }
}
@media (max-width: 550px) {
    .metrics-grid-3 {
        grid-template-columns: 1fr;
    }
}

/* Standardized metric card */
.metric-card {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 0.95rem 1.1rem;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 110px;
    height: 100%;
    box-sizing: border-box;
}

.metric-card, .metric-card * {
    word-break: normal !important;
    overflow-wrap: normal !important;
    hyphens: none !important;
}

.metric-card-top {
    display: flex;
    flex-direction: column;
}

.metric-card-label {
    font-size: 0.88rem;
    font-weight: 500;
    color: #475569;
    margin-bottom: 0.3rem;
    line-height: 1.3;
    white-space: normal;
}

.metric-card-value {
    font-size: 1.55rem;
    font-weight: 700;
    color: #0f172a;
    font-variant-numeric: tabular-nums;
    line-height: 1.2;
    margin-bottom: 0.2rem;
    white-space: nowrap;
}

.metric-card-sub {
    font-size: 0.8rem;
    color: #64748b;
    line-height: 1.35;
    margin-top: 0.3rem;
    white-space: normal;
}

/* Status banner */
.status-card {
    background-color: #ffffff;
    border-radius: 6px;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #0284c7;
    padding: 1.1rem 1.25rem;
    margin-bottom: 1.25rem;
}
.status-card-healthy {
    border-left-color: #059669;
}
.status-card-mismatch {
    border-left-color: #d97706;
}
.status-card-fault {
    border-left-color: #dc2626;
}
.status-card-unknown {
    border-left-color: #64748b;
}

/* Parameters card on the left */
.params-card {
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 1.15rem;
    box-sizing: border-box;
    margin-bottom: 1.5rem;
}

.status-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.25rem;
}
.status-text {
    font-size: 0.9rem;
    color: #334155;
    line-height: 1.45;
}

/* Layout: Position Navigation Sidebar on the RIGHT */
[data-testid="stAppViewContainer"] {
    flex-direction: row-reverse !important;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background-color: #f8fafc;
    border-left: 1px solid #e2e8f0 !important;
    border-right: none !important;
    min-width: 250px !important;
    max-width: 290px !important;
    width: 270px !important;
}

/* Sidebar collapse/expand behavior for right positioning */
section[data-testid="stSidebar"][data-collapsed="true"] {
    transform: translateX(100%) !important;
    min-width: 0 !important;
    max-width: 0 !important;
    width: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}

/* Flip collapse button arrow inside sidebar to point right */
[data-testid="stSidebarCollapseButton"] button {
    transform: scaleX(-1) !important;
}

/* Position expand button in top right when sidebar is collapsed */
[data-testid="stExpandSidebarButton"] {
    position: fixed !important;
    right: 1.25rem !important;
    top: 0.75rem !important;
    z-index: 1000000 !important;
    transform: scaleX(-1) !important;
}

[data-testid="collapsedControl"] {
    left: auto !important;
    right: 1.25rem !important;
    transform: scaleX(-1) !important;
}

/* Ensure resize handle is on the left of the sidebar */
[data-testid="stSidebarResizeHandle"] {
    left: 0 !important;
    right: auto !important;
}

/* Main content styling */
section[data-testid="stMain"] {
    flex: 1 1 0% !important;
    width: 100% !important;
    overflow-x: hidden !important;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    [data-testid="stAppViewContainer"] {
        flex-direction: column !important;
    }
    section[data-testid="stSidebar"] {
        border-left: none !important;
        border-bottom: 1px solid #e2e8f0 !important;
        width: 100% !important;
        max-width: 100% !important;
    }
    section[data-testid="stSidebar"][data-collapsed="true"] {
        transform: translateY(-100%) !important;
        height: 0 !important;
    }
    [data-testid="stExpandSidebarButton"] {
        right: 0.75rem !important;
        top: 0.5rem !important;
    }
}
.sidebar-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.2rem;
}
.sidebar-subtitle {
    font-size: 0.8rem;
    color: #64748b;
    margin-bottom: 1rem;
}
.sidebar-heading {
    font-size: 0.76rem;
    font-weight: 700;
    color: #475569;
    margin-top: 0.9rem;
    margin-bottom: 0.35rem;
}
</style>
""", unsafe_allow_html=True)


# ── Plot Styling Helper ───────────────────────────────────────────────────────
def create_clean_plot(figsize=(5.8, 3.6)):
    """Initialize a clean, publication-ready matplotlib figure with light styling."""
    fig, ax = plt.subplots(figsize=figsize, dpi=120)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")
    ax.grid(True, linestyle="--", linewidth=0.5, color="#cbd5e1", alpha=0.7)
    for spine in ax.spines.values():
        spine.set_color("#94a3b8")
        spine.set_linewidth(0.8)
    ax.tick_params(colors="#334155", labelsize=8.5)
    ax.xaxis.label.set_color("#0f172a")
    ax.yaxis.label.set_color("#0f172a")
    ax.title.set_color("#0f172a")
    return fig, ax


# ── Metric Card Rendering Helpers ─────────────────────────────────────────────
def render_metric_card(label: str, value: str, sub: str = "", value_size: str = None) -> str:
    """
    Generate clean, standardized HTML for a single metric card.
    Uses flexbox column layout to vertically align label, prominent value, and subtext.
    """
    val_style = f' style="font-size: {value_size};"' if value_size else ""
    sub_html = f'<div class="metric-card-sub">{sub}</div>' if sub else ""
    return f"""<div class="metric-card">
    <div class="metric-card-top">
        <div class="metric-card-label">{label}</div>
        <div class="metric-card-value"{val_style}>{value}</div>
    </div>
    {sub_html}
</div>"""


def render_metrics_grid(cards_html_list: list, grid_class: str = "metrics-grid") -> str:
    """
    Render a collection of metric cards inside a responsive CSS Grid container.
    """
    cards_str = "\n".join(cards_html_list)
    return f"""<div class="{grid_class}">
{cards_str}
</div>"""


# ── Simulation Runner & Caching ───────────────────────────────────────────────
def run_simulation(scenario_key, Z0, length, vf, f_start_mhz, f_stop_mhz, n_points, fault_args, noise_std):
    """
    Execute end-to-end transmission line simulation and analysis pipeline.
    Returns a unified result dictionary.
    """
    freqs = np.linspace(f_start_mhz * 1e6, f_stop_mhz * 1e6, int(n_points))
    
    # Run physical fault simulation
    sim_output = fs.simulate_fault(
        scenario_key,
        Z0,
        length,
        freqs,
        vf=vf,
        noise_std=noise_std,
        **fault_args
    )
    sweep = sim_output["sweep"]
    
    # Execute diagnostic classification
    diag_res = diag.classify(sweep, Z0)
    
    # Execute fault localization
    loc_res = locate_fault_dual_method(
        sweep["gamma"],
        freqs,
        vf=vf,
        fault_class=str(diag_res)
    )
    
    # Generate diagnostic report
    report = generate_full_diagnostic_report(diag_res, Z0, vf=vf)
    
    # Resolution metrics
    res_metrics = calculate_resolution_metrics(freqs, vf=vf)
    
    return {
        "scenario": scenario_key,
        "Z0": float(Z0),
        "length": float(length),
        "vf": float(vf),
        "freqs": freqs,
        "f_start_mhz": float(f_start_mhz),
        "f_stop_mhz": float(f_stop_mhz),
        "n_points": int(n_points),
        "fault_args": fault_args,
        "noise_std": float(noise_std),
        "sweep": sweep,
        "diag_res": diag_res,
        "loc_res": loc_res,
        "report": report,
        "res_metrics": res_metrics,
    }


# ── Sidebar Configuration Panel (Right Side: Navigation Only) ─────────────────
st.sidebar.markdown('<div class="sidebar-title">RF Line Doctor</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sidebar-subtitle">Transmission Line Simulation System</div>', unsafe_allow_html=True)

NAV_OPTIONS = [
    "Simulation",
    "Diagnosis",
    "Fault Location",
    "Impedance Matching",
    "Results",
]

nav_section = st.sidebar.radio(
    "Navigation",
    NAV_OPTIONS,
    index=0,
    label_visibility="collapsed",
)

st.sidebar.markdown('<div style="height: 1px; background: #e2e8f0; margin: 0.8rem 0;"></div>', unsafe_allow_html=True)


# ── Main Two-Column Layout: Parameters on Left, Simulation on Right ──────────
col_params, col_sim = st.columns([1, 3.2], gap="medium")

with col_params:
    st.markdown('<div class="params-card">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-heading" style="margin-top:0;">Line Parameters</div>', unsafe_allow_html=True)
    
    Z0 = st.number_input(
        "Characteristic Impedance Z0 (Ohms)",
        min_value=5.0,
        max_value=1000.0,
        value=50.0,
        step=5.0,
        key="param_z0",
    )
    
    length = st.number_input(
        "Line Length (m)",
        min_value=0.05,
        max_value=100.0,
        value=1.0,
        step=0.1,
        key="param_length",
    )
    
    vf = st.number_input(
        "Velocity Factor (v/c)",
        min_value=0.01,
        max_value=1.0,
        value=0.66,
        step=0.01,
        key="param_vf",
    )
    
    st.markdown('<div class="sidebar-heading">Frequency Settings</div>', unsafe_allow_html=True)
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        f_start_mhz = st.number_input(
            "Start (MHz)",
            min_value=1.0,
            max_value=50000.0,
            value=500.0,
            step=50.0,
            key="param_f_start",
        )
    with col_f2:
        f_stop_mhz = st.number_input(
            "Stop (MHz)",
            min_value=2.0,
            max_value=50000.0,
            value=4000.0,
            step=50.0,
            key="param_f_stop",
        )
    
    n_points = st.number_input(
        "Frequency Points",
        min_value=21,
        max_value=2001,
        value=201,
        step=20,
        key="param_n_points",
    )
    
    st.markdown('<div class="sidebar-heading">Line Condition</div>', unsafe_allow_html=True)
    
    FAULT_MAP = {
        "Healthy line": "healthy",
        "Resistive mismatch": "mismatch",
        "Open circuit": "open",
        "Short circuit": "short",
        "Series inductance": "series_L",
        "Shunt capacitance": "shunt_C",
    }
    
    fault_label = st.selectbox(
        "Select Condition",
        list(FAULT_MAP.keys()),
        index=0,
        key="param_fault_label",
    )
    selected_scenario = FAULT_MAP[fault_label]
    
    fault_args = {}
    if selected_scenario == "mismatch":
        RL = st.number_input(
            "Load Resistance RL (Ohms)",
            min_value=0.1,
            max_value=10000.0,
            value=100.0,
            step=10.0,
            key="param_rl",
        )
        fault_args["ZL_mismatch"] = RL
    elif selected_scenario == "series_L":
        L_nH = st.number_input(
            "Discontinuity Inductance L (nH)",
            min_value=0.01,
            max_value=500.0,
            value=5.0,
            step=0.5,
            key="param_l",
        )
        d_fault = st.number_input(
            "Discontinuity Position (m)",
            min_value=0.01,
            max_value=float(length),
            value=min(0.5, float(length)),
            step=0.05,
            key="param_fault_pos",
        )
        fault_args["L_val"] = L_nH * 1e-9
        fault_args["fault_pos"] = d_fault
    elif selected_scenario == "shunt_C":
        C_pF = st.number_input(
            "Discontinuity Capacitance C (pF)",
            min_value=0.01,
            max_value=500.0,
            value=2.0,
            step=0.2,
            key="param_c",
        )
        d_fault = st.number_input(
            "Discontinuity Position (m)",
            min_value=0.01,
            max_value=float(length),
            value=min(0.5, float(length)),
            step=0.05,
            key="param_fault_pos",
        )
        fault_args["C_val"] = C_pF * 1e-12
        fault_args["fault_pos"] = d_fault
    
    st.markdown('<div class="sidebar-heading">Measurement Settings</div>', unsafe_allow_html=True)
    
    noise_std = st.number_input(
        "Measurement Noise (std dev)",
        min_value=0.0,
        max_value=0.2,
        value=0.0,
        step=0.005,
        format="%.3f",
        key="param_noise",
    )
    
    run_clicked = st.button("Run Simulation", type="primary", use_container_width=True, key="param_run_btn")
    st.markdown('</div>', unsafe_allow_html=True)


# ── Validation & Simulation Execution ─────────────────────────────────────────
validation_error = None
if f_stop_mhz <= f_start_mhz:
    validation_error = "Stop frequency must be greater than start frequency."
if length <= 0:
    validation_error = "Line length must be positive."
if Z0 <= 0:
    validation_error = "Characteristic impedance must be positive."

# Check if simulation should be executed (button clicked or initial load)
if "sim_data" not in st.session_state or run_clicked:
    if validation_error:
        with col_sim:
            st.error(validation_error)
    else:
        st.session_state["sim_data"] = run_simulation(
            selected_scenario,
            Z0,
            length,
            vf,
            f_start_mhz,
            f_stop_mhz,
            n_points,
            fault_args,
            noise_std,
        )

# Retrieve current simulation data
sim = st.session_state.get("sim_data")


# ── PAGE VIEWS (Rendered Inside Main Simulation Column) ───────────────────────
with col_sim:
    # ── PAGE 1: SIMULATION ────────────────────────────────────────────────────
    if nav_section == "Simulation":
        st.markdown('<div class="main-title">Transmission Line Simulation</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="main-subtitle">Simulate wave propagation, standing waves, and impedance across frequency.</div>',
            unsafe_allow_html=True,
        )
    
        if sim is None:
            st.warning("Please configure parameters and click Run Simulation.")
        else:
            sweep = sim["sweep"]
            gamma = sweep["gamma"]
            vswr = sweep["vswr"]
            rl_db = sweep["rl_db"]
            zin = sweep["zin"]
            freqs_mhz = sim["freqs"] / 1e6
    
            # Key output metric calculations
            mean_gamma = float(np.mean(np.abs(gamma)))
            mid_idx = len(freqs_mhz) // 2
            ref_vswr = float(vswr[mid_idx]) if np.isfinite(vswr[mid_idx]) else float("inf")
            ref_rl = float(rl_db[mid_idx]) if np.isfinite(rl_db[mid_idx]) else 0.0
            ref_zin = zin[mid_idx]
    
            dist_est = sim["loc_res"].get("dist_ifft_m")
    
            # Metric Cards Layout
            if abs(ref_zin.imag) < 0.05:
                zin_text = f"{ref_zin.real:.1f}"
            elif ref_zin.imag >= 0:
                zin_text = f"{ref_zin.real:.1f} + j{ref_zin.imag:.1f}"
            else:
                zin_text = f"{ref_zin.real:.1f} - j{abs(ref_zin.imag):.1f}"
    
            dist_text = f"{dist_est:.2f} m" if dist_est is not None else "None"
            vswr_text = f"{ref_vswr:.2f}" if ref_vswr < 100 else "Infinity" if np.isinf(ref_vswr) else f"{ref_vswr:.1f}"
            rl_text = f"{ref_rl:.1f} dB" if ref_rl < 100 else "> 100 dB"
    
            cards = [
                render_metric_card("Condition", fault_label, f"Z0 = {sim['Z0']:.0f} Ohms", value_size="1.35rem"),
                render_metric_card("Reflection |Gamma|", f"{mean_gamma:.4f}", "Mean reflection magnitude"),
                render_metric_card("VSWR", vswr_text, f"At {freqs_mhz[mid_idx]:.0f} MHz"),
                render_metric_card("Return Loss", rl_text, f"At {freqs_mhz[mid_idx]:.0f} MHz"),
                render_metric_card("Input Impedance", zin_text, "Ohms at mid-band", value_size="1.35rem"),
                render_metric_card("Fault Distance", dist_text, "From line input"),
            ]
            st.markdown(render_metrics_grid(cards, "metrics-grid"), unsafe_allow_html=True)
    
            # Engineering Plots Section
            row1_col1, row1_col2 = st.columns(2)
    
            with row1_col1:
                fig1, ax1 = create_clean_plot()
                ax1.plot(freqs_mhz, np.abs(gamma), color="#0284c7", linewidth=1.8, label="|Gamma|")
                ax1.set_title("Reflection Coefficient Magnitude vs Frequency")
                ax1.set_xlabel("Frequency (MHz)")
                ax1.set_ylabel("Magnitude |Gamma|")
                ax1.set_ylim(-0.05, 1.05)
                ax1.legend(loc="upper right", framealpha=0.9)
                fig1.tight_layout()
                st.pyplot(fig1, use_container_width=True)
                plt.close(fig1)
    
            with row1_col2:
                fig2, ax2 = create_clean_plot()
                vswr_clean = np.where(np.isinf(vswr), 50.0, np.clip(vswr, 1.0, 50.0))
                ax2.plot(freqs_mhz, vswr_clean, color="#d97706", linewidth=1.8, label="VSWR")
                ax2.axhline(1.0, color="#94a3b8", linestyle=":", linewidth=1.0)
                ax2.axhline(2.0, color="#dc2626", linestyle="--", linewidth=0.9, alpha=0.7, label="VSWR = 2.0")
                ax2.set_title("Voltage Standing Wave Ratio (VSWR) vs Frequency")
                ax2.set_xlabel("Frequency (MHz)")
                ax2.set_ylabel("VSWR")
                ax2.set_ylim(0.8, min(10.0, max(3.0, float(np.nanmax(vswr_clean[:100])) + 1.0)))
                ax2.legend(loc="upper right", framealpha=0.9)
                fig2.tight_layout()
                st.pyplot(fig2, use_container_width=True)
                plt.close(fig2)
    
            row2_col1, row2_col2 = st.columns(2)
    
            with row2_col1:
                fig3, ax3 = create_clean_plot()
                rl_clean = np.where(np.isinf(rl_db), 100.0, np.clip(rl_db, 0.0, 100.0))
                ax3.plot(freqs_mhz, rl_clean, color="#059669", linewidth=1.8, label="Return Loss")
                ax3.axhline(20.0, color="#0284c7", linestyle="--", linewidth=0.9, label="20 dB reference")
                ax3.set_title("Return Loss vs Frequency")
                ax3.set_xlabel("Frequency (MHz)")
                ax3.set_ylabel("Return Loss (dB)")
                ax3.set_ylim(-2.0, max(35.0, float(np.nanmax(rl_clean)) + 5.0))
                ax3.legend(loc="lower right", framealpha=0.9)
                fig3.tight_layout()
                st.pyplot(fig3, use_container_width=True)
                plt.close(fig3)
    
            with row2_col2:
                fig4, ax4 = create_clean_plot()
                ax4.plot(freqs_mhz, zin.real, color="#0284c7", linewidth=1.6, label="Resistance Re(Zin)")
                ax4.plot(freqs_mhz, zin.imag, color="#7c3aed", linewidth=1.6, linestyle="--", label="Reactance Im(Zin)")
                ax4.axhline(sim["Z0"], color="#94a3b8", linestyle=":", linewidth=0.9, label=f"Z0 = {sim['Z0']:.0f} Ohms")
                ax4.set_title("Input Impedance vs Frequency")
                ax4.set_xlabel("Frequency (MHz)")
                ax4.set_ylabel("Impedance (Ohms)")
                ax4.legend(loc="upper right", framealpha=0.9)
                fig4.tight_layout()
                st.pyplot(fig4, use_container_width=True)
                plt.close(fig4)
    
            # Row 3: Normalized Smith Chart
            st.markdown('<div class="sidebar-heading" style="margin-top: 1rem;">Smith Chart</div>', unsafe_allow_html=True)
            col_smith, _ = st.columns([1.8, 1.0])
            with col_smith:
                fig_smith, ax_smith = plt.subplots(figsize=(5.2, 5.2), dpi=120)
                fig_smith.patch.set_facecolor("#ffffff")
                meas.smith_plot(gamma, ax=ax_smith, color="#0284c7", linewidth=2.0)
                ax_smith.set_title("Normalized Smith Chart Trajectory", fontsize=10, pad=10)
                fig_smith.tight_layout()
                st.pyplot(fig_smith, use_container_width=False)
                plt.close(fig_smith)
    
    
    # ── PAGE 2: DIAGNOSIS ─────────────────────────────────────────────────────
    elif nav_section == "Diagnosis":
        st.markdown('<div class="main-title">Fault Diagnosis</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="main-subtitle">Automated detection and classification of line health, terminations, and localized discontinuities.</div>',
            unsafe_allow_html=True,
        )
    
        if sim is None:
            st.warning("Please run a simulation first to view diagnostic findings.")
        else:
            diag_res = sim["diag_res"]
            category = str(diag_res)
            subtype = getattr(diag_res, "subtype", "uncertain")
            confidence = getattr(diag_res, "confidence", "medium")
            report = sim["report"]
    
            # Human-readable labels
            category_titles = {
                "healthy": "Healthy Line",
                "open": "Open Circuit",
                "short": "Short Circuit",
                "mismatch": "Impedance Mismatch",
                "unknown": "Unknown Condition",
            }
            display_title = category_titles.get(category, category.title())
    
            # Plain language explanations
            plain_explanations = {
                "healthy": "The transmission line is terminated in a matched load. Reflections are negligible and energy transmission is optimal.",
                "open": "The line is severed or terminated in an open circuit. Signals experience near-total in-phase reflection.",
                "short": "The line is short-circuited at the termination. Signals experience near-total reflection with complete 180-degree phase inversion.",
                "mismatch": "An impedance discontinuity is present along or at the end of the line, creating standing waves and partial signal reflection.",
                "unknown": "Measurement signals exhibit ambiguous or non-passive characteristics that cannot be reliably matched to a known fault model.",
            }
    
            # Suggested actions
            suggested_actions = {
                "healthy": "No corrective action required. Line is operating at peak transmission efficiency.",
                "open": "Inspect the far-end termination connector, check center pin contact, and verify physical cable continuity.",
                "short": "Inspect the line for conductor bridging, solder shorts, or damaged dielectric insulation at the load connector.",
                "mismatch": "Verify the load impedance, inspect intermediate joints, or install a quarter-wave matching section.",
                "unknown": "Check instrumentation calibration, verify measurement noise floor, and ensure frequency sweep settings cover the operational band.",
            }
    
            # Status border color class
            status_class = (
                "status-card-healthy" if category == "healthy"
                else "status-card-mismatch" if category == "mismatch"
                else "status-card-fault" if category in ["open", "short"]
                else "status-card-unknown"
            )
    
            st.markdown(f"""
            <div class="status-card {status_class}">
                <div class="status-title">Diagnosis: {display_title}</div>
                <div class="status-text">{plain_explanations.get(category, '')}</div>
            </div>
            """, unsafe_allow_html=True)
    
            cards_diag = [
                render_metric_card("Health State", display_title, "Standardized classification", value_size="1.35rem"),
                render_metric_card("Physical Condition", subtype.replace('_', ' ').title(), "Identified mechanism", value_size="1.35rem"),
                render_metric_card("Detection Confidence", confidence.title(), "Diagnostic certainty", value_size="1.35rem"),
            ]
            st.markdown(render_metrics_grid(cards_diag, "metrics-grid-3"), unsafe_allow_html=True)
    
            st.markdown('<div style="height: 0.5rem;"></div>', unsafe_allow_html=True)
    
            c_ev, c_act = st.columns(2)
    
            with c_ev:
                st.markdown('<div class="sidebar-heading">Measured Evidence</div>', unsafe_allow_html=True)
                evidence_items = report.get("evidence", [])
                if evidence_items:
                    for ev in evidence_items:
                        st.markdown(f"• {ev}")
                else:
                    gamma_mag = float(np.mean(np.abs(sim['sweep']['gamma'])))
                    st.markdown(f"• Mean reflection magnitude: {gamma_mag:.4f}")
                    st.markdown(f"• Cable total length: {sim['length']:.2f} m")
                    st.markdown(f"• Characteristic impedance: {sim['Z0']:.1f} Ohms")
    
            with c_act:
                st.markdown('<div class="sidebar-heading">Recommended Troubleshooting Action</div>', unsafe_allow_html=True)
                st.markdown(suggested_actions.get(category, "Review line connections and repeat measurement."))
    
    
    # ── PAGE 3: FAULT LOCATION ────────────────────────────────────────────────
    elif nav_section == "Fault Location":
        st.markdown('<div class="main-title">Fault Location (TDR)</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="main-subtitle">Estimate the physical position of discontinuities along the line using time-domain reflectometry.</div>',
            unsafe_allow_html=True,
        )
    
        if sim is None:
            st.warning("Please run a simulation first to calculate fault location.")
        else:
            loc_res = sim["loc_res"]
            dist_est = loc_res.get("dist_ifft_m")
            res_metrics = sim["res_metrics"]
            range_res_m = res_metrics.get("range_res_m", 0.0)
            unambig_m = res_metrics.get("unambig_range_m", 0.0)
            line_len = sim["length"]
            category = str(sim["diag_res"])
    
            dist_disp = f"{dist_est:.2f} m" if dist_est is not None else "No Fault Detected"
            dist_sub = "Distance from line input" if dist_est is not None else "Matched termination"
            res_cm = range_res_m * 100.0 if range_res_m is not None and np.isfinite(range_res_m) else 0.0
            unambig_disp = f"{unambig_m:.1f} m" if unambig_m is not None and np.isfinite(unambig_m) else "N/A"
    
            cards_loc = [
                render_metric_card("Fault Position", dist_disp, dist_sub, value_size="1.4rem"),
                render_metric_card("Total Line Length", f"{line_len:.2f} m", "Physical cable span"),
                render_metric_card("Distance Resolution", f"{res_cm:.2f} cm", "Minimum resolvable distance"),
                render_metric_card("Maximum Range", unambig_disp, "Unambiguous measurement limit"),
            ]
            st.markdown(render_metrics_grid(cards_loc, "metrics-grid-4"), unsafe_allow_html=True)
    
            # Status text callout
            if category == "healthy":
                st.info("The transmission line is matched. No reflection echo was detected along the cable.")
            elif dist_est is not None:
                st.success(f"Discontinuity detected approximately {dist_est:.2f} metres from the input connector.")
            else:
                st.warning("Could not identify a distinct reflection peak along the line span.")
    
            # TDR Impulse Response Plot
            tdr_data = loc_res.get("tdr_data", {})
            d_axis = tdr_data.get("d_axis_m", np.array([]))
            tdr_mag = tdr_data.get("tdr_mag", np.array([]))
    
            if len(d_axis) > 0 and len(tdr_mag) > 0:
                fig_tdr, ax_tdr = create_clean_plot(figsize=(9, 4.0))
    
                # Restrict plot view to line length + 25% margin
                plot_max_d = min(line_len * 1.35, d_axis[-1])
                mask = (d_axis >= 0) & (d_axis <= plot_max_d)
    
                # Normalize magnitude for clean display
                max_val = np.max(tdr_mag[mask]) if np.any(mask) and np.max(tdr_mag[mask]) > 0 else 1.0
                norm_mag = tdr_mag / max_val
    
                ax_tdr.plot(d_axis[mask], norm_mag[mask], color="#0284c7", linewidth=1.8, label="TDR Reflection Profile")
    
                # Mark estimated fault position
                if dist_est is not None and dist_est <= plot_max_d:
                    ax_tdr.axvline(dist_est, color="#dc2626", linestyle="--", linewidth=1.4, label=f"Estimated Fault ({dist_est:.2f} m)")
    
                # Mark total line length
                ax_tdr.axvline(line_len, color="#475569", linestyle=":", linewidth=1.2, label=f"Line End ({line_len:.2f} m)")
    
                ax_tdr.set_title("Time-Domain Reflection Profile (Echo Magnitude vs Distance)")
                ax_tdr.set_xlabel("Distance from Input (m)")
                ax_tdr.set_ylabel("Normalized Reflection Amplitude")
                ax_tdr.set_xlim(0, plot_max_d)
                ax_tdr.set_ylim(-0.05, 1.15)
                ax_tdr.legend(loc="upper right", framealpha=0.9)
                fig_tdr.tight_layout()
                st.pyplot(fig_tdr, use_container_width=True)
                plt.close(fig_tdr)
    
    
    # ── PAGE 4: IMPEDANCE MATCHING ────────────────────────────────────────────
    elif nav_section == "Impedance Matching":
        st.markdown('<div class="main-title">Impedance Matching Studio</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="main-subtitle">Design a quarter-wave transformer section to eliminate reflections and restore power transfer.</div>',
            unsafe_allow_html=True,
        )
    
        # Initial sensible values derived from current simulation if applicable
        default_z0 = sim["Z0"] if sim is not None else 50.0
        default_rl = 100.0
        if sim is not None and sim["scenario"] == "mismatch":
            default_rl = float(sim["fault_args"].get("ZL_mismatch", 100.0))
        default_f0 = (sim["f_start_mhz"] + sim["f_stop_mhz"]) / 2.0 if sim is not None else 2000.0
        default_vf = sim["vf"] if sim is not None else 0.66
    
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            match_z0 = st.number_input("Line Impedance Z0 (Ohms)", min_value=5.0, max_value=1000.0, value=float(default_z0), step=5.0)
        with col_m2:
            match_rl = st.number_input("Load Resistance RL (Ohms)", min_value=1.0, max_value=5000.0, value=float(default_rl), step=5.0)
        with col_m3:
            match_f0 = st.number_input("Design Frequency f0 (MHz)", min_value=10.0, max_value=50000.0, value=float(default_f0), step=50.0)
        with col_m4:
            match_vf = st.number_input("Velocity Factor", min_value=0.01, max_value=1.0, value=float(default_vf), step=0.01, key="match_vf")
    
        # Synthesize transformer
        try:
            f_span = np.linspace(max(10e6, (match_f0 - 1500) * 1e6), (match_f0 + 1500) * 1e6, 201)
            matching_res = match.compare_matching(
                match_z0,
                match_rl,
                f_span,
                vf=match_vf,
                f_design=match_f0 * 1e6,
                rl_threshold=20.0,
            )
    
            Zt = matching_res["Zt"]
            lt_m = matching_res["length_m"]
            lt_mm = lt_m * 1000.0
            bw_mhz = matching_res["bandwidth_hz"] / 1e6
    
            # Output Metric Cards using responsive 5-card grid
            cards_match = [
                render_metric_card("Transformer Zt", f"{Zt:.1f} Ohms", "Quarter-wave characteristic impedance", value_size="1.4rem"),
                render_metric_card("Section Length", f"{lt_mm:.1f} mm", "Quarter-wavelength physical length", value_size="1.4rem"),
                render_metric_card("Matched VSWR", "1.00", f"Target match at {match_f0:.0f} MHz"),
                render_metric_card("Matched Return Loss", "> 100 dB", "Near-zero reflected power"),
                render_metric_card("20 dB Bandwidth", f"{bw_mhz:.1f} MHz", "Passband with return loss >= 20 dB", value_size="1.4rem"),
            ]
            st.markdown(render_metrics_grid(cards_match, "metrics-grid-5"), unsafe_allow_html=True)
    
            st.markdown('<div style="height: 0.5rem;"></div>', unsafe_allow_html=True)
    
            # Before and After Comparison Plots
            p_col1, p_col2 = st.columns(2)
            f_plot_mhz = f_span / 1e6
            before_rl = matching_res["before"]["rl_db"]
            after_rl = np.where(np.isinf(matching_res["after"]["rl_db"]), 100.0, matching_res["after"]["rl_db"])
            before_vswr = matching_res["before"]["vswr"]
            after_vswr = matching_res["after"]["vswr"]
    
            with p_col1:
                fig_m1, ax_m1 = create_clean_plot()
                ax_m1.plot(f_plot_mhz, before_rl, color="#dc2626", linestyle="--", linewidth=1.5, label="Unmatched Line")
                ax_m1.plot(f_plot_mhz, after_rl, color="#059669", linewidth=2.0, label="Quarter-Wave Matched")
                ax_m1.axhline(20.0, color="#0284c7", linestyle=":", linewidth=1.0, label="20 dB Threshold")
                ax_m1.axvline(match_f0, color="#64748b", linestyle=":", linewidth=0.8)
                ax_m1.set_title("Return Loss: Before vs After Matching")
                ax_m1.set_xlabel("Frequency (MHz)")
                ax_m1.set_ylabel("Return Loss (dB)")
                ax_m1.set_ylim(-2.0, 60.0)
                ax_m1.legend(loc="upper right", framealpha=0.9)
                fig_m1.tight_layout()
                st.pyplot(fig_m1, use_container_width=True)
                plt.close(fig_m1)
    
            with p_col2:
                fig_m2, ax_m2 = create_clean_plot()
                ax_m2.plot(f_plot_mhz, before_vswr, color="#dc2626", linestyle="--", linewidth=1.5, label="Unmatched Line")
                ax_m2.plot(f_plot_mhz, after_vswr, color="#059669", linewidth=2.0, label="Quarter-Wave Matched")
                ax_m2.axhline(1.0, color="#94a3b8", linestyle=":", linewidth=1.0)
                ax_m2.axhline(1.5, color="#d97706", linestyle=":", linewidth=1.0, label="VSWR = 1.5")
                ax_m2.axvline(match_f0, color="#64748b", linestyle=":", linewidth=0.8)
                ax_m2.set_title("VSWR: Before vs After Matching")
                ax_m2.set_xlabel("Frequency (MHz)")
                ax_m2.set_ylabel("VSWR")
                ax_m2.set_ylim(0.9, max(3.5, float(np.max(before_vswr)) + 0.5))
                ax_m2.legend(loc="upper right", framealpha=0.9)
                fig_m2.tight_layout()
                st.pyplot(fig_m2, use_container_width=True)
                plt.close(fig_m2)
    
            # Matching Summary Table
            st.markdown('<div class="sidebar-heading" style="margin-top: 1rem;">Transformer Design Summary</div>', unsafe_allow_html=True)
            f_low = matching_res.get("f_low_hz", 0.0) / 1e6
            f_high = matching_res.get("f_high_hz", 0.0) / 1e6
            summary_df = pd.DataFrame([
                {"Design Parameter": "Required Line Impedance", "Value": f"{Zt:.2f} Ohms", "Description": "Characteristic impedance of the quarter-wave line section"},
                {"Design Parameter": "Physical Section Length", "Value": f"{lt_mm:.1f} mm", "Description": f"Quarter-wavelength at design frequency {match_f0:.0f} MHz"},
                {"Design Parameter": "Matched 20 dB Passband", "Value": f"{f_low:.1f} - {f_high:.1f} MHz", "Description": f"Bandwidth of {bw_mhz:.1f} MHz achieving return loss >= 20 dB"},
            ])
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
        except Exception as e:
            st.error(f"Quarter-wave matching calculation error: {str(e)}")
    
    
    # ── PAGE 5: RESULTS ───────────────────────────────────────────────────────
    elif nav_section == "Results":
        st.markdown('<div class="main-title">Simulation Results & Data Export</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="main-subtitle">Inspect frequency-point calculation records, evaluate summary metrics, and export data to CSV.</div>',
            unsafe_allow_html=True,
        )
    
        if sim is None:
            st.warning("Please run a simulation first to inspect tabular data.")
        else:
            sweep = sim["sweep"]
            f_arr = sim["freqs"]
            gamma_arr = sweep["gamma"]
            zin_arr = sweep["zin"]
            vswr_arr = sweep["vswr"]
            rl_arr = sweep["rl_db"]
    
            # Build clean formatted DataFrame
            results_df = pd.DataFrame({
                "Frequency (MHz)": np.round(f_arr / 1e6, 2),
                "Reflection |Gamma|": np.round(np.abs(gamma_arr), 4),
                "Reflection Phase (deg)": np.round(np.angle(gamma_arr, deg=True), 2),
                "Input Resistance (Ohms)": np.round(zin_arr.real, 2),
                "Input Reactance (Ohms)": np.round(zin_arr.imag, 2),
                "VSWR": np.round(np.where(np.isinf(vswr_arr), 9999.0, vswr_arr), 2),
                "Return Loss (dB)": np.round(np.where(np.isinf(rl_arr), 999.0, rl_arr), 2),
            })
    
            finite_vswr = vswr_arr[np.isfinite(vswr_arr)]
            min_v = f"{np.min(finite_vswr):.2f}" if len(finite_vswr) > 0 else "N/A"
            finite_rl = rl_arr[np.isfinite(rl_arr)]
            max_rl = f"{np.max(finite_rl):.1f} dB" if len(finite_rl) > 0 else "N/A"
    
            cards_res = [
                render_metric_card("Total Frequency Points", f"{len(results_df)}", f"{sim['f_start_mhz']:.0f} to {sim['f_stop_mhz']:.0f} MHz"),
                render_metric_card("Mean Reflection", f"{np.mean(np.abs(gamma_arr)):.4f}", "Average |Gamma| across band"),
                render_metric_card("Minimum VSWR", min_v, "Best matching point"),
                render_metric_card("Peak Return Loss", max_rl, "Maximum return loss across band"),
            ]
            st.markdown(render_metrics_grid(cards_res, "metrics-grid-4"), unsafe_allow_html=True)
    
            st.markdown('<div style="height: 0.5rem;"></div>', unsafe_allow_html=True)
    
            # Download CSV Button
            csv_buffer = io.StringIO()
            results_df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue().encode("utf-8")
    
            st.download_button(
                label="Download Results as CSV",
                data=csv_data,
                file_name=f"rf_line_doctor_{sim['scenario']}_results.csv",
                mime="text/csv",
                type="primary",
            )
    
            # Tabular Display
            st.dataframe(
                results_df,
                use_container_width=True,
                hide_index=True,
                height=450,
            )
