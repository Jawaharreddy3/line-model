"""
app.py -- RF LINE DOCTOR Interactive Streamlit Dashboard (Member 4).

Only calls public functions from:
  - line_model
  - measurements
  - diagnosis
  - matching
  - fault_simulation
"""

import sys
import numpy as np
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import line_model as lm
import measurements as meas
import fault_simulation as fs
import diagnosis as diag
import matching as match

# Page configuration
st.set_page_config(
    page_title="RF Line Doctor — Transmission Line Diagnostics",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🩺 RF LINE DOCTOR — Transmission-Line Fault Diagnosis & Matching")
st.caption(
    "Virtual RF & Microwave Engineering Diagnostics System | Lossless Transmission Line Core Model"
)

# ── Sidebar: Simulation Parameters ──────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Transmission Line Parameters")

    Z0 = st.number_input(
        "Characteristic Impedance Z₀ (Ω)",
        min_value=1.0,
        max_value=1000.0,
        value=50.0,
        step=5.0,
    )

    length = st.number_input(
        "Physical Line Length (m)",
        min_value=0.05,
        max_value=100.0,
        value=1.0,
        step=0.1,
    )

    vf = st.slider(
        "Velocity Factor (vf)",
        min_value=0.1,
        max_value=1.0,
        value=0.66,
        step=0.01,
        help="Typical values: Solid PE coax ≈ 0.66, PTFE ≈ 0.70, Air line = 1.0",
    )

    st.subheader("📶 Frequency Sweep")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        f_start_mhz = st.number_input("f_start (MHz)", min_value=1.0, max_value=50000.0, value=500.0, step=50.0)
    with col_f2:
        f_stop_mhz = st.number_input("f_stop (MHz)", min_value=5.0, max_value=50000.0, value=4000.0, step=100.0)

    if f_start_mhz >= f_stop_mhz:
        st.error("f_start must be less than f_stop")
        st.stop()

    n_pts = st.slider("Sweep Points", min_value=50, max_value=1000, value=400, step=50)
    freqs = np.linspace(f_start_mhz * 1e6, f_stop_mhz * 1e6, n_pts)

    st.subheader("⚡ Fault Injection & Termination")
    scenario_choice = st.selectbox(
        "Scenario / Fault Type",
        [
            "Healthy Matched (ZL = Z0)",
            "Resistive Mismatch",
            "Open Circuit (ZL = ∞)",
            "Short Circuit (ZL = 0)",
            "Series Inductive Discontinuity (Series L)",
            "Shunt Capacitive Discontinuity (Shunt C)",
            "Custom Complex Load (R + jX)",
        ],
        index=0,
    )

    # Dynamic scenario configuration
    fault_pos = float(length / 2.0)
    L_val = 15e-9
    C_val = 15e-12
    ZL_val = complex(Z0)
    sim_scenario = "healthy"

    if scenario_choice == "Healthy Matched (ZL = Z0)":
        sim_scenario = "healthy"
        ZL_val = complex(Z0)

    elif scenario_choice == "Resistive Mismatch":
        sim_scenario = "mismatch"
        RL_input = st.number_input("Load Resistance RL (Ω)", min_value=1.0, max_value=1000.0, value=120.0, step=5.0)
        ZL_val = complex(RL_input)

    elif scenario_choice == "Open Circuit (ZL = ∞)":
        sim_scenario = "open"
        ZL_val = lm.OPEN

    elif scenario_choice == "Short Circuit (ZL = 0)":
        sim_scenario = "short"
        ZL_val = 0.0 + 0j

    elif scenario_choice == "Series Inductive Discontinuity (Series L)":
        sim_scenario = "series_L"
        L_nh = st.number_input("Discontinuity Inductance L (nH)", min_value=0.5, max_value=200.0, value=15.0, step=1.0)
        L_val = L_nh * 1e-9
        fault_pos = st.slider("Discontinuity Position (m)", min_value=0.01, max_value=float(length), value=float(length * 0.4), step=0.01)

    elif scenario_choice == "Shunt Capacitive Discontinuity (Shunt C)":
        sim_scenario = "shunt_C"
        C_pf = st.number_input("Discontinuity Capacitance C (pF)", min_value=0.5, max_value=200.0, value=15.0, step=1.0)
        C_val = C_pf * 1e-12
        fault_pos = st.slider("Discontinuity Position (m)", min_value=0.01, max_value=float(length), value=float(length * 0.6), step=0.01)

    elif scenario_choice == "Custom Complex Load (R + jX)":
        sim_scenario = "custom"
        c_r = st.number_input("R (Ω)", min_value=0.0, max_value=2000.0, value=75.0, step=5.0)
        c_x = st.number_input("X (Ω, +Ind / -Cap)", min_value=-2000.0, max_value=2000.0, value=35.0, step=5.0)
        ZL_val = complex(c_r, c_x)

    noise_std = st.slider(
        "Measurement Noise (σ on S11)",
        min_value=0.0,
        max_value=0.15,
        value=0.0,
        step=0.01,
        help="Gaussian noise added to reflection measurements",
    )

# ── Simulation & Processing ──────────────────────────────────────────────────
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
    sweep_data = sim_out["sweep"]
else:
    # Custom complex load
    sweep_data = meas.sweep(Z0, ZL_val, length, freqs, vf=vf)
    if noise_std > 0.0:
        rng = np.random.default_rng(42)
        noise = rng.normal(0, noise_std / np.sqrt(2), len(freqs)) + \
                1j * rng.normal(0, noise_std / np.sqrt(2), len(freqs))
        gamma_noisy = sweep_data["gamma"] + noise
        mag = np.abs(gamma_noisy)
        gamma_noisy[mag > 1.0] /= mag[mag > 1.0]
        sweep_data["gamma"] = gamma_noisy
        sweep_data["vswr"] = meas.vswr(gamma_noisy)
        sweep_data["rl_db"] = meas.return_loss_db(gamma_noisy)

# Diagnosis & Distance Localization
diag_res = diag.classify(sweep_data, Z0)
fault_dist = diag.estimate_distance(sweep_data, vf, diag_res)
res_info = diag.distance_resolution(sweep_data, vf=vf)

# ── Top Level Diagnostic Dashboard KPI Cards ─────────────────────────────────
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    status_color = {
        "healthy": "🟢 HEALTHY",
        "mismatch": "🟠 MISMATCH",
        "open": "🔴 OPEN CIRCUIT",
        "short": "🔴 SHORT CIRCUIT",
        "unknown": "⚪ UNKNOWN",
    }.get(diag_res, "⚪ UNKNOWN")
    st.metric("Line Health Status", status_color)

with kpi2:
    st.metric("Classification (Contract)", str(diag_res).upper())

with kpi3:
    subtype_label = getattr(diag_res, "subtype", str(diag_res))
    st.metric("Internal Subtype", subtype_label)

with kpi4:
    if fault_dist is not None:
        st.metric("Fault Distance", f"{fault_dist:.3f} m")
    else:
        st.metric("Fault Distance", "N/A (Matched)")

with kpi5:
    res_val = res_info["range_res"]
    st.metric("Range Resolution (ΔR)", f"{res_val * 100:.1f} cm" if np.isfinite(res_val) else "N/A")

if hasattr(diag_res, "explanation") and diag_res.explanation:
    st.info(f"**Diagnostic Rationale:** {diag_res.explanation} | Confidence: **{diag_res.confidence.upper()}**")

# ── Visual Tabs ─────────────────────────────────────────────────────────────
tab_sweeps, tab_smith, tab_tdr, tab_matching, tab_benchmarks = st.tabs([
    "📈 Frequency Sweeps",
    "🧭 Smith Chart",
    "⏱️ TDR Fault Localization",
    "🔄 Matching Studio",
    "📚 Hand Benchmarks",
])

f_ghz = freqs / 1e9

# Tab 1: Frequency Sweeps
with tab_sweeps:
    st.subheader("Reflection Coefficient, VSWR, and Return Loss")
    fig, (ax_g, ax_v, ax_r) = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

    gamma_mag = np.abs(sweep_data["gamma"])
    ax_g.plot(f_ghz, gamma_mag, color="#1f77b4", lw=2, label="|Γ| (|S11|)")
    ax_g.axhline(0.05, color="green", linestyle="--", alpha=0.7, label="Matched Threshold (0.05)")
    ax_g.set_ylabel("|Γ| Magnitude")
    ax_g.set_ylim(-0.05, 1.05)
    ax_g.grid(True, alpha=0.3)
    ax_g.legend(loc="upper right")

    vswr_vals = np.clip(sweep_data["vswr"], 1.0, 50.0)
    ax_v.plot(f_ghz, vswr_vals, color="#ff7f0e", lw=2, label="VSWR")
    ax_v.axhline(2.0, color="gray", linestyle="--", alpha=0.7, label="VSWR = 2.0 Benchmark")
    ax_v.set_ylabel("VSWR")
    ax_v.set_ylim(1.0, min(max(np.nanmax(vswr_vals) * 1.1, 3.0), 30.0))
    ax_v.grid(True, alpha=0.3)
    ax_v.legend(loc="upper right")

    rl_vals = np.clip(sweep_data["rl_db"], 0.0, 60.0)
    ax_r.plot(f_ghz, rl_vals, color="#2ca02c", lw=2, label="Return Loss (dB)")
    ax_r.axhline(20.0, color="green", linestyle="--", alpha=0.7, label="20 dB Threshold")
    ax_r.axhline(10.0, color="orange", linestyle=":", alpha=0.7, label="10 dB Threshold")
    ax_r.set_ylabel("Return Loss (dB)")
    ax_r.set_xlabel("Frequency (GHz)")
    ax_r.set_ylim(0, 60)
    ax_r.grid(True, alpha=0.3)
    ax_r.legend(loc="upper right")

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

# Tab 2: Smith Chart
with tab_smith:
    st.subheader("Normalized Smith Chart Trajectory")
    col_sc1, col_sc2 = st.columns([3, 2])
    with col_sc1:
        fig_smith, ax_s = plt.subplots(figsize=(6, 6))
        meas.smith_plot(sweep_data["gamma"], ax=ax_s, label=f"Trajectory ({f_start_mhz:.0f} - {f_stop_mhz:.0f} MHz)")
        ax_s.legend(loc="lower right", fontsize=9)
        st.pyplot(fig_smith)
        plt.close(fig_smith)
    with col_sc2:
        st.markdown(r"""
        **Smith Chart Interpretation Guide:**
        - **Center Point (1.0, 0.0):** Perfectly matched load ($Z = Z_0$).
        - **Right Edge (+1.0, 0.0):** Open circuit ($Z \to \infty$).
        - **Left Edge (-1.0, 0.0):** Short circuit ($Z \to 0$).
        - **Upper Half ($\text{Im} > 0$):** Inductive impedance / reactance.
        - **Lower Half ($\text{Im} < 0$):** Capacitive impedance / susceptance.
        - **Rotation:** A complete circle corresponds to $\lambda/2$ in line length.
        """)

# Tab 3: TDR & Fault Localization
with tab_tdr:
    st.subheader("Time-Domain Reflectometry (IFFT Pseudo-Time Echo Profile)")
    col_tdr1, col_tdr2 = st.columns([3, 2])
    with col_tdr1:
        # Calculate time axis and IFFT magnitude
        Npad = max(len(freqs) * 8, 2048)
        window = np.hanning(len(freqs))
        gamma_win = sweep_data["gamma"] * window
        gamma_pad = np.zeros(Npad, dtype=complex)
        gamma_pad[: len(freqs)] = gamma_win
        time_mag = np.abs(np.fft.ifft(gamma_pad))
        df = freqs[1] - freqs[0] if len(freqs) > 1 else 1.0
        t_axis_ns = (np.arange(Npad) / (Npad * df)) * 1e9
        d_axis_m = (lm.phase_velocity(vf) * (t_axis_ns * 1e-9)) / 2.0

        fig_tdr, ax_t = plt.subplots(figsize=(8, 4.5))
        max_dist_view = max(length * 1.5, 2.0)
        mask = d_axis_m <= max_dist_view
        ax_t.plot(d_axis_m[mask], time_mag[mask], color="purple", lw=2, label="IFFT Echo Profile")
        if fault_dist is not None:
            ax_t.axvline(fault_dist, color="red", linestyle="--", label=f"Detected Fault: {fault_dist:.3f} m")
        ax_t.set_xlabel("Physical Distance (m)")
        ax_t.set_ylabel("Reflection Magnitude |h(t)|")
        ax_t.set_title("Pseudo-Time Domain Reflectometry")
        ax_t.grid(True, alpha=0.3)
        ax_t.legend()
        st.pyplot(fig_tdr)
        plt.close(fig_tdr)

    with col_tdr2:
        st.markdown("#### Range & Resolution Summary")
        st.write(f"- **Physical Line Length:** `{length:.2f} m`")
        vp_val = lm.phase_velocity(vf) / 1e8
        st.write(f"- **Velocity Factor (vf):** `{vf:.2f}` ($v_p = {vp_val:.2f} \\times 10^8$ m/s)")
        st.write(f"- **Sweep Bandwidth (B):** `{res_info['bandwidth_hz']/1e9:.2f} GHz`")
        st.write(f"- **Theoretical Range Resolution (ΔR):** `{res_info['range_res']*100:.2f} cm`")
        st.write(f"- **Unambiguous Range (R_max):** `{res_info['unambig_range']:.2f} m`")
        if fault_dist is not None:
            st.success(f"**Identified Distance to Discontinuity:** `{fault_dist:.3f} m`")

# Tab 4: Matching Studio
with tab_matching:
    st.subheader("Quarter-Wave Transformer Matching Studio")

    # Check if load is purely real
    is_real_load = False
    RL_match = None
    if isinstance(ZL_val, complex) and np.isfinite(ZL_val.real) and ZL_val.real > 0:
        if abs(ZL_val.imag) < 1e-5:
            is_real_load = True
            RL_match = float(ZL_val.real)

    if not is_real_load:
        st.warning(
            "Quarter-wave transformers require a purely real load resistance $R_L > 0$. "
            f"Current termination is $Z_L = {ZL_val}$. For reactive or singular loads, "
            "stub tuning or an L-network is required."
        )
        st.info("Select 'Resistive Mismatch' in the sidebar to design a quarter-wave matching section.")
    else:
        f_mid_ghz = float(np.mean(freqs) / 1e9)
        f_design_ghz = st.number_input(
            "Matching Design Center Frequency f₀ (GHz)",
            min_value=0.1,
            max_value=20.0,
            value=f_mid_ghz,
            step=0.1,
        )
        f_design = f_design_ghz * 1e9

        match_res = match.compare_matching(
            Z0, RL_match, freqs, vf=vf, f_design=f_design, rl_threshold=20.0
        )

        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.metric("Transformer Impedance (Zt)", f"{match_res['Zt']:.2f} Ω")
        with m_col2:
            st.metric("Physical Length (lt)", f"{match_res['length_m']*1000:.1f} mm")
        with m_col3:
            st.metric("Usable BW (RL ≥ 20 dB)", f"{match_res['bandwidth_hz']/1e6:.1f} MHz")
        with m_col4:
            f0_rl = match_res["at_f_design"]["rl_db"]
            st.metric("RL @ Design f₀", "∞ dB (Exact)" if np.isinf(f0_rl) else f"{f0_rl:.1f} dB")

        # Before vs After Plots
        fig_m, (ax_mv, ax_mr) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

        ax_mv.plot(f_ghz, match_res["before"]["vswr"], "r--", label="Before Matching (Unmatched)")
        ax_mv.plot(f_ghz, match_res["after"]["vswr"], "b-", lw=2, label="After Matching (λ/4 Transformer)")
        ax_mv.axvline(f_design_ghz, color="gray", linestyle=":", label=f"f0 = {f_design_ghz:.2f} GHz")
        ax_mv.set_ylabel("VSWR")
        ax_mv.set_ylim(1.0, 4.0)
        ax_mv.grid(True, alpha=0.3)
        ax_mv.legend()

        ax_mr.plot(f_ghz, match_res["before"]["rl_db"], "r--", label="Before Matching")
        ax_mr.plot(f_ghz, match_res["after"]["rl_db"], "b-", lw=2, label="After Matching")
        ax_mr.axhline(20.0, color="green", linestyle="--", label="20 dB Specification")
        ax_mr.axvline(f_design_ghz, color="gray", linestyle=":")
        ax_mr.set_ylabel("Return Loss (dB)")
        ax_mr.set_xlabel("Frequency (GHz)")
        ax_mr.set_ylim(0, 50)
        ax_mr.grid(True, alpha=0.3)
        ax_mr.legend()

        plt.tight_layout()
        st.pyplot(fig_m)
        plt.close(fig_m)

# Tab 5: Benchmarks
with tab_benchmarks:
    st.subheader("Verification Against Theoretical Hand Calculations")
    st.markdown(r"""
    All algorithms are cross-verified against the canonical benchmark calculations in `HAND_CALCULATIONS.md`:
    - **Item 1 (Matched):** $Z_L = 50\,\Omega \implies \Gamma = 0, Z_{\\text{in}} = 50\,\Omega$ for any length.
    - **Item 2 (Short at $\\lambda/8$):** $Z_{\\text{in}} = +j50\,\Omega$ (purely inductive).
    - **Item 3 (Open at $\\lambda/8$):** $Z_{\\text{in}} = -j50\,\Omega$ (purely capacitive).
    - **Item 4 (Quarter-wave $Z_L = 100\,\Omega$):** $Z_{\\text{in}} = Z_0^2 / Z_L = 25\,\Omega, |\\Gamma| = 1/3, \\text{VSWR} = 2.0, \\text{RL} = 9.542\\text{ dB}$.
    - **Item 5 (Half-wave):** $Z_{\\text{in}} = Z_L$ (impedance repeats every $\\lambda/2$).
    - **Item 6 (Transformer $50 \\to 200\,\Omega$):** $Z_t = \\sqrt{50 \\times 200} = 100\,\Omega, l_t = 0.75\\text{ m}$ at $100\\text{ MHz}$ ($\\text{vf}=1.0$).
    - **Item 7 (Singular cases):** Short at $\\lambda/4 \\implies Z_{\\text{in}} = \\infty$; Open at $\\lambda/4 \\implies Z_{\\text{in}} = 0$.
    """)
