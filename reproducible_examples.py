"""
reproducible_examples.py -- End-to-end verification and figure generator.

Runs all 6 canonical transmission line scenarios:
  1. healthy (matched line)
  2. mismatch (resistive mismatch)
  3. open (open circuit)
  4. short (short circuit)
  5. series_L (series inductive discontinuity)
  6. shunt_C (shunt capacitive discontinuity)

Generates publication-quality figures in figures/ and prints a verification summary.
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import line_model as lm
import measurements as meas
import fault_simulation as fs
import diagnosis as diag
import matching as match

FIG_DIR = os.path.join(os.path.dirname(__file__), "figures")
os.makedirs(FIG_DIR, exist_ok=True)

Z0 = 50.0
LENGTH = 1.0
VF = 0.66
FREQS = np.linspace(500e6, 4000e6, 400)
F_GHZ = FREQS / 1e9

COLORS = {
    "healthy": "#2ca02c",
    "mismatch": "#1f77b4",
    "open": "#d62728",
    "short": "#ff7f0e",
    "series_L": "#9467bd",
    "shunt_C": "#8c564b",
}


def run_pipeline():
    print("=" * 80)
    print("RF LINE DOCTOR -- Comprehensive End-to-End Verification Pipeline")
    print("=" * 80)
    print(f"System Parameters: Z0 = {Z0} Ohm | Length = {LENGTH} m | vf = {VF} (vp = {lm.phase_velocity(VF):.2e} m/s)")
    print(f"Frequency Sweep  : {FREQS[0]/1e6:.1f} MHz to {FREQS[-1]/1e6:.1f} MHz ({len(FREQS)} points)")
    print("-" * 80)

    results = {}
    diagnoses = {}
    distances = {}

    for name in fs.FAULT_SCENARIOS:
        sim = fs.simulate_fault(
            name,
            Z0,
            LENGTH,
            FREQS,
            vf=VF,
            fault_pos=0.4 if name == "series_L" else (0.6 if name == "shunt_C" else None),
            L_val=15e-9,
            C_val=15e-12,
            ZL_mismatch=120.0,
        )
        sw = sim["sweep"]
        results[name] = sw
        d_res = diag.classify(sw, Z0)
        diagnoses[name] = d_res
        dist = diag.estimate_distance(sw, VF, d_res)
        distances[name] = dist

    res_info = diag.distance_resolution(results["healthy"], vf=VF)
    print(f"Range Resolution (delta_R): {res_info['range_res']*100:.2f} cm | Unambiguous Range: {res_info['unambig_range']:.2f} m\n")

    header = f"{'Scenario':<12} | {'Contract Label':<15} | {'Subtype':<18} | {'Confidence':<10} | {'True Pos':<10} | {'Est Dist':<10} | {'Error (cm)':<10}"
    print(header)
    print("-" * len(header))

    for name in fs.FAULT_SCENARIOS:
        d_res = diagnoses[name]
        d_est = distances[name]
        true_pos = 0.4 if name == "series_L" else (0.6 if name == "shunt_C" else (LENGTH if name != "healthy" else None))

        if true_pos is not None and d_est is not None:
            err_cm = abs(d_est - true_pos) * 100.0
            err_str = f"{err_cm:6.2f}"
            est_str = f"{d_est:6.3f} m"
            true_str = f"{true_pos:6.3f} m"
        else:
            err_str = "  N/A "
            est_str = "  N/A " if d_est is None else f"{d_est:6.3f} m"
            true_str = "  N/A " if true_pos is None else f"{true_pos:6.3f} m"

        print(f"{name:<12} | {str(d_res):<15} | {d_res.subtype:<18} | {d_res.confidence:<10} | {true_str:<10} | {est_str:<10} | {err_str:<10}")

    print("=" * 80)

    # ── Figure 1: Multi-Scenario Sweep Overlay ──────────────────────────────
    print("\nGenerating Figure 1: Scenario Sweeps (|Gamma|, VSWR, Return Loss)...")
    fig1, (ax_g, ax_v, ax_r) = plt.subplots(3, 1, figsize=(10, 9), sharex=True)

    for name, sw in results.items():
        col = COLORS[name]
        mag = np.abs(sw["gamma"])
        ax_g.plot(F_GHZ, mag, color=col, lw=1.8, label=name)
        vswr_c = np.clip(sw["vswr"], 1.0, 30.0)
        ax_v.plot(F_GHZ, vswr_c, color=col, lw=1.8, label=name)
        rl_c = np.clip(sw["rl_db"], 0.0, 60.0)
        ax_r.plot(F_GHZ, rl_c, color=col, lw=1.8, label=name)

    ax_g.set_ylabel("|Gamma| (|S11|)")
    ax_g.set_ylim(-0.05, 1.05)
    ax_g.axhline(0.05, color="gray", linestyle="--", alpha=0.5, label="Matched (0.05)")
    ax_g.set_title("Transmission Line Frequency Sweeps Across 6 Canonical Scenarios")
    ax_g.grid(True, alpha=0.3)
    ax_g.legend(loc="upper right", ncol=2, fontsize=8)

    ax_v.set_ylabel("VSWR")
    ax_v.set_ylim(1.0, 10.0)
    ax_v.grid(True, alpha=0.3)

    ax_r.set_ylabel("Return Loss (dB)")
    ax_r.set_xlabel("Frequency (GHz)")
    ax_r.set_ylim(0, 50)
    ax_r.axhline(20.0, color="green", linestyle="--", alpha=0.5, label="20 dB Threshold")
    ax_r.grid(True, alpha=0.3)
    ax_r.legend(loc="upper right", fontsize=8)

    plt.tight_layout()
    f1_path = os.path.join(FIG_DIR, "1_scenario_sweeps.png")
    fig1.savefig(f1_path, dpi=150)
    plt.close(fig1)
    print(f"Saved: {f1_path}")

    # ── Figure 2: Smith Chart Overlay ─────────────────────────────────────────
    print("Generating Figure 2: Smith Chart Trajectories...")
    fig2, ax2 = plt.subplots(figsize=(7, 7))
    # Draw blank smith chart
    meas.smith_plot(np.array([0.0]), ax=ax2, alpha=0.0)
    # Overlay trajectories
    for name, sw in results.items():
        col = COLORS[name]
        g = sw["gamma"]
        ax2.plot(g.real, g.imag, color=col, lw=1.6, label=name, alpha=0.85)
        ax2.scatter(g.real[0], g.imag[0], color=col, s=25, zorder=4)

    ax2.set_title("Normalized Smith Chart — Reflection Trajectories (6 Scenarios)")
    ax2.legend(loc="lower right", fontsize=8)
    plt.tight_layout()
    f2_path = os.path.join(FIG_DIR, "2_smith_chart_overlay.png")
    fig2.savefig(f2_path, dpi=150)
    plt.close(fig2)
    print(f"Saved: {f2_path}")

    # ── Figure 3: Quarter-Wave Matching Comparison ────────────────────────────
    print("Generating Figure 3: Quarter-Wave Matching Analysis...")
    f_mid = 2.0e9
    m_eval = match.compare_matching(Z0, 120.0, FREQS, vf=VF, f_design=f_mid, rl_threshold=20.0)

    fig3, (ax3_v, ax3_r) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    ax3_v.plot(F_GHZ, m_eval["before"]["vswr"], "r--", lw=1.8, label="Before (Unmatched 120 Ω)")
    ax3_v.plot(F_GHZ, m_eval["after"]["vswr"], "b-", lw=2.0, label="After (λ/4 Transformer)")
    ax3_v.axvline(f_mid / 1e9, color="gray", linestyle=":", label=f"f0 = {f_mid/1e9:.2f} GHz")
    ax3_v.set_ylabel("VSWR")
    ax3_v.set_ylim(1.0, 3.0)
    ax3_v.set_title(f"Quarter-Wave Matching ($Z_0={Z0}$ Ohm -> $R_L=120$ Ohm, $Z_t={m_eval['Zt']:.1f}$ Ohm)")
    ax3_v.grid(True, alpha=0.3)
    ax3_v.legend(loc="upper right")

    ax3_r.plot(F_GHZ, m_eval["before"]["rl_db"], "r--", lw=1.8, label="Before Matching")
    ax3_r.plot(F_GHZ, m_eval["after"]["rl_db"], "b-", lw=2.0, label="After Matching")
    ax3_r.axhline(20.0, color="green", linestyle="--", label="20 dB Bandwidth Specification")
    ax3_r.set_ylabel("Return Loss (dB)")
    ax3_r.set_xlabel("Frequency (GHz)")
    ax3_r.set_ylim(0, 50)
    ax3_r.grid(True, alpha=0.3)
    ax3_r.legend(loc="upper right")

    plt.tight_layout()
    f3_path = os.path.join(FIG_DIR, "3_matching_before_after.png")
    fig3.savefig(f3_path, dpi=150)
    plt.close(fig3)
    print(f"Saved: {f3_path}")

    # ── Figure 4: TDR Fault Localization Profile ──────────────────────────────
    print("Generating Figure 4: TDR Distance Localization...")
    fig4, ax4 = plt.subplots(figsize=(9, 4.5))
    df = FREQS[1] - FREQS[0]
    Npad = max(len(FREQS) * 8, 2048)
    t_axis = (np.arange(Npad) / (Npad * df))
    d_axis = (lm.phase_velocity(VF) * t_axis) / 2.0
    mask = d_axis <= 1.5

    for name in ["open", "short", "series_L", "shunt_C"]:
        col = COLORS[name]
        sw = results[name]
        window = np.hanning(len(FREQS))
        pad = np.zeros(Npad, dtype=complex)
        pad[: len(FREQS)] = sw["gamma"] * window
        time_mag = np.abs(np.fft.ifft(pad))
        ax4.plot(d_axis[mask], time_mag[mask], color=col, lw=1.6, label=f"{name} (Est: {distances[name]:.3f} m)")

    ax4.set_xlabel("Physical Distance (m)")
    ax4.set_ylabel("Echo Magnitude |h(t)|")
    ax4.set_title("IFFT Pseudo-Time Domain Reflectometry (TDR) Profiles")
    ax4.grid(True, alpha=0.3)
    ax4.legend(loc="upper right")

    plt.tight_layout()
    f4_path = os.path.join(FIG_DIR, "4_tdr_localization.png")
    fig4.savefig(f4_path, dpi=150)
    plt.close(fig4)
    print(f"Saved: {f4_path}")

    print("\nAll reproducible examples and figures generated successfully!")


if __name__ == "__main__":
    run_pipeline()
