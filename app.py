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

# ── Custom Engineering CSS Styling ────────────────────────────────────────────
st.markdown("""
<style>
    /* Engineering Dark Theme Elements */
    .metric-card {
        background-color: #1e2638;
        border: 1px solid #2d3b58;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .metric-title {
        color: #8da2c0;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        color: #00e5ff;
        font-size: 1.6rem;
        font-weight: 700;
        font-family: 'Consolas', 'Courier New', monospace;
    }
    .status-badge-healthy {
        background-color: #0e3d23;
        color: #2ecc71;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: bold;
    }
    .status-badge-mismatch {
        background-color: #4a2800;
        color: #f39c12;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: bold;
    }
    .status-badge-fault {
        background-color: #4a1212;
        color: #e74c3c;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

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
        "8. Theory & Hand Calculations",
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
    help="vp = vf * c0. Typical: Solid PE Coax = 0.66, PTFE = 0.70, Air = 1.0",
)

st.sidebar.subheader("📶 Frequency Sweep Range")
col_sf1, col_sf2 = st.sidebar.columns(2)
with col_sf1:
    f_start_mhz = st.number_input("f_start (MHz)", min_value=1.0, max_value=50000.0, value=500.0, step=50.0)
with col_sf2:
    f_stop_mhz = st.number_input("f_stop (MHz)", min_value=5.0, max_value=50000.0, value=4000.0, step=100.0)

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
        "Case 2: Resistive Mismatch (ZL = RL != Z0)",
        "Case 3: Open Circuit (ZL = ∞)",
        "Case 4: Short Circuit (ZL = 0)",
        "Case 5: Series Inductive Discontinuity (Series L)",
        "Case 6: Shunt Capacitive Discontinuity (Shunt C)",
        "Custom: Arbitrary Complex Load (R + jX)",
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
    "Measurement Noise (σ on S11)",
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
        g_noisy = sweep_dict["gamma"] + noise
        g_mag = np.abs(g_noisy)
        g_noisy[g_mag > 1.0] /= g_mag[g_mag > 1.0]
        sweep_dict["gamma"] = g_noisy
        sweep_dict["vswr"] = meas.vswr(g_noisy)
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
        "📊 Reflection Metrics (|S11|, VSWR, RL)",
        "🔌 Input Impedance (Rin, Xin, Phase)",
        "🧭 Normalized Smith Chart",
    ])

    with tab_rf:
        st.subheader("Reflection Magnitude, VSWR, and Return Loss")
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
            **Smith Chart Interpretation Guide:**
            - **Center (1.0, 0.0):** Perfectly matched load ($Z = Z_0$).
            - **Right Edge (+1.0, 0.0):** Open circuit ($Z \to \infty$).
            - **Left Edge (-1.0, 0.0):** Short circuit ($Z \to 0$).
            - **Upper Half ($\text{Im} > 0$):** Inductive impedance.
            - **Lower Half ($\text{Im} < 0$):** Capacitive impedance.
            - **Clockwise Rotation:** Moving toward generator (increasing distance from load).
            """)

# ─────────────────────────────────────────────────────────────────────────────
# VIEW 4: FAULT DIAGNOSIS ENGINE
# ─────────────────────────────────────────────────────────────────────────────
elif nav_section == "4. Fault Diagnosis Engine":
    st.header("4. Transparent Rule-Based Fault Diagnosis")
    st.caption("Inferred strictly from single-port S11 measurements without access to simulation ground truth.")

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
    st.header("5. Fault Location: Time-Domain Reflectometry (TDR)")
    st.caption("Dual-method distance localization: Hann-windowed IFFT pseudo-time reflectometry vs phase-slope cross-check.")

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
        st.subheader("Dual-Method Localization Summary")
        d1 = loc_dual["dist_ifft_m"]
        d2 = loc_dual["dist_phase_m"]

        st.write(f"- **Method 1 (IFFT TDR):** `{f'{d1:.3f} m' if d1 is not None else 'None (Matched)'}`")
        st.write(f"- **Method 2 (Phase Slope):** `{f'{d2:.3f} m' if d2 is not None else 'None'}`")

        if loc_dual["discrepancy_m"] is not None:
            st.write(f"- **Discrepancy |M1 - M2|:** `{loc_dual['discrepancy_m']*100:.2f} cm`")

        st.write(f"- **Physical Range Resolution (ΔR):** `{res_info['range_res_m']*100:.2f} cm`")
        st.write(f"- **Unambiguous Range (R_max):** `{res_info['unambig_range_m']:.2f} m`")

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
    st.caption("Synthesis and passband evaluation of quarter-wave transformers (Zt = sqrt(Z0 * RL)).")

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
            st.metric("Transformer Impedance (Zt)", f"{match_res['Zt']:.2f} Ω")
            st.metric("Physical Length (lt)", f"{match_res['length_m']*1000:.1f} mm")
            st.metric("Usable BW (RL ≥ 20 dB)", f"{match_res['bandwidth_hz']/1e6:.1f} MHz")

            f0_rl = match_res["at_f_design"]["rl_db"]
            st.metric("RL @ Design f₀", "∞ dB (Exact)" if np.isinf(f0_rl) else f"{f0_rl:.1f} dB")

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
                    v_dataset.append({
                        "target": target,
                        "pred": str(diag.classify(sim_v["sweep"], z0_r)),
                        "true_pos": fp_r if sc in ["series_L", "shunt_C"] else (len_r if sc != "healthy" else None),
                        "est_pos": diag.estimate_distance(sim_v["sweep"], vf_r, target),
                    })

            y_t = [it["target"] for it in v_dataset]
            y_p = [it["pred"] for it in v_dataset]
            val_rep = compute_classification_report(y_t, y_p, contract_labels)

            v_col1, v_col2 = st.columns([1, 1])
            with v_col1:
                st.subheader(f"Confusion Matrix (Accuracy = {val_rep['accuracy']*100:.1f}%)")
                df_vcm = pd.DataFrame(
                    val_rep["confusion_matrix"],
                    index=[f"True: {l}" for l in contract_labels],
                    columns=[f"Pred: {l}" for l in contract_labels],
                )
                st.dataframe(df_vcm)

            with v_col2:
                st.subheader("Classification Performance Metrics")
                m_rows = []
                for l in contract_labels:
                    r_dict = {"Class": l}
                    r_dict.update(val_rep["per_class"][l])
                    m_rows.append(r_dict)
                st.dataframe(pd.DataFrame(m_rows))

            # Location errors
            t_locs = [it["true_pos"] for it in v_dataset if it["true_pos"] is not None]
            e_locs = [it["est_pos"] for it in v_dataset if it["true_pos"] is not None]
            l_stats = compute_location_metrics(t_locs, e_locs)
            st.success(f"**Fault Location Performance:** MAE = `{l_stats['mae_m']*100:.2f} cm` | RMSE = `{l_stats['rmse_m']*100:.2f} cm` (Valid: {l_stats['valid_count']}/{len(t_locs)})")

# ─────────────────────────────────────────────────────────────────────────────
# VIEW 8: THEORY & HAND CALCULATIONS
# ─────────────────────────────────────────────────────────────────────────────
elif nav_section == "8. Theory & Hand Calculations":
    st.header("8. Electromagnetic Theory & Benchmark Calculations")

    st.markdown(r"""
    ### Canonical Verification Benchmarks (`HAND_CALCULATIONS.md`)
    Common test parameters: $Z_0 = 50\,\Omega, f = 100\text{ MHz}, \text{vf} = 1.0 \implies \lambda = 2.998\text{ m}, \beta = 2.096\text{ rad/m}$.

    1. **Matched Load ($Z_L = 50\,\Omega$):**
       $$\Gamma_L = \frac{50 - 50}{50 + 50} = 0 \implies Z_{\text{in}} = Z_0 = 50\,\Omega \quad (\forall l)$$
    2. **Short Circuit at $l = \lambda/8$ ($\beta l = 45^\circ$):**
       $$Z_{\text{in}} = +j Z_0 \tan(45^\circ) = +j50\,\Omega \quad (\text{purely inductive})$$
    3. **Open Circuit at $l = \lambda/8$ ($\beta l = 45^\circ$):**
       $$Z_{\text{in}} = -j Z_0 \cot(45^\circ) = -j50\,\Omega \quad (\text{purely capacitive})$$
    4. **Quarter-Wave Inversion ($l = \lambda/4, Z_L = 100\,\Omega$):**
       $$Z_{\text{in}} = \frac{Z_0^2}{Z_L} = \frac{2500}{100} = 25\,\Omega \implies \Gamma = \frac{25 - 50}{25 + 50} = -\frac{1}{3} \implies \text{VSWR} = 2.0, \text{RL} = 9.542\text{ dB}$$
    5. **Half-Wave Repetition ($l = \lambda/2, Z_L = 30 + j40\,\Omega$):**
       $$Z_{\text{in}} = Z_L = 30 + j40\,\Omega \quad (\text{impedance repeats every } \lambda/2)$$
    6. **Quarter-Wave Transformer ($50 \to 200\,\Omega$ at $100\text{ MHz}$):**
       $$Z_t = \sqrt{50 \times 200} = 100\,\Omega, \quad l_t = \frac{\lambda}{4} = 0.75\text{ m}$$
    7. **Singularities at $\lambda/4$:**
       - Short at $\lambda/4 \implies Z_{\text{in}} \to \infty$ (virtual open circuit).
       - Open at $\lambda/4 \implies Z_{\text{in}} \to 0$ (virtual short circuit).
    """)
