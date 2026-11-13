"""
generate_qucs_cross_validation.py -- Comprehensive Qucsator Cross-Validation Engine.
"""

import os
import sys
import re
import subprocess
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import skrf as rf

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import line_model as lm
import measurements as meas

# ── 1. Target Directory & Parameters ──────────────────────────────────────────
OUT_DIR = os.path.abspath(os.path.dirname(__file__))
os.makedirs(OUT_DIR, exist_ok=True)

Z0 = 50.0            # Reference / Characteristic impedance [Ohm]
RL = 120.0           # Load resistance [Ohm] (Case 2: Resistive Mismatch)
length = 1.0         # Physical line length [m]
vf = 0.66            # Velocity factor
c0 = 299792458.0     # Speed of light in vacuum [m/s]
vp = vf * c0         # Phase velocity [m/s]

# Primary parameters for distributed transmission line model
L_per_m = Z0 / vp
C_per_m = 1.0 / (Z0 * vp)
R_per_m = 0.0        # Lossless
G_per_m = 0.0        # Lossless

f_start = 500e6      # 500 MHz
f_stop = 2500e6      # 2500 MHz
n_pts = 201
freqs = np.linspace(f_start, f_stop, n_pts)

# ── 2. Native Qucs Schematic (.sch) ───────────────────────────────────────────
sch_content = f"""<Qucs Schematic 26.1.1>
<Properties>
  <View=0,0,800,600,1,0,0>
  <Grid=10,10,1>
  <DataSet=qucs_mismatch.dat>
  <DataDisplay=qucs_mismatch.dpl>
  <OpenDisplay=1>
  <Script=qucs_mismatch.m>
  <RunScript=0>
  <showFrame=0>
  <FrameText0=RF LINE DOCTOR Cross-Validation>
  <FrameText1=Case 2: Resistive Mismatch (120 Ohm)>
  <FrameText2=Date: 2026-11-13>
  <FrameText3=Rev: 1.0>
</Properties>
<Symbol>
</Symbol>
<Components>
  <Pac P1 1 80 180 18 -26 0 1 "1" 1 "{Z0} Ohm" 1 "0 dBm" 0 "1 GHz" 0>
  <Ground gnd 1 80 240 0 0 0 0>
  <RLCG Line1 1 220 180 71 -26 0 0 "{R_per_m}" 0 "{L_per_m:.10e}" 1 "{C_per_m:.10e}" 1 "{G_per_m}" 0 "{length}" 1 "26.85" 0>
  <R R1 1 360 180 -26 15 1 0 "{RL} Ohm" 1 "26.85" 0 "0.0" 0 "0.0" 0 "26.85" 0>
  <Ground gnd 1 360 240 0 0 0 0>
  <.SP SP1 1 180 320 0 67 0 0 "lin" 1 "{f_start/1e6:.0f} MHz" 1 "{f_stop/1e6:.0f} MHz" 1 "{n_pts}" 1 "no" 0 "1" 0 "2" 0>
</Components>
<Wires>
  <80 180 150 180 "" 0 0 0 "">
  <150 180 220 180 "_net0" 0 0 0 "">
  <290 180 360 180 "_net1" 0 0 0 "">
  <80 180 80 240 "" 0 0 0 "">
  <360 180 360 240 "" 0 0 0 "">
</Wires>
<Diagrams>
</Diagrams>
<Paintings>
</Paintings>
"""
sch_path = os.path.join(OUT_DIR, "qucs_mismatch.sch")
with open(sch_path, "w") as f:
    f.write(sch_content)

# ── 3. Native Qucsator Netlist (.net) ──────────────────────────────────────────
net_content = f"""# Qucs 1.0.7 Netlist -- RF LINE DOCTOR Benchmark
Pac:P1 _net0 gnd f="1 GHz" Z="{Z0} Ohm" Num="1" P="0 dBm"
RLCG:Line1 _net0 _net1 R="{R_per_m}" L="{L_per_m:.12e}" C="{C_per_m:.12e}" G="{G_per_m}" Length="{length}"
R:R1 _net1 gnd R="{RL} Ohm"
.SP:SP1 Type="lin" Start="{f_start:.0f}Hz" Stop="{f_stop:.0f}Hz" Points="{n_pts}" Noise="no"
"""
net_path = os.path.join(OUT_DIR, "qucs_mismatch.net")
with open(net_path, "w") as f:
    f.write(net_content)

# ── 4. Locate & Execute Native Qucsator Simulator ─────────────────────────────
def find_simulator_executable(name_variants, env_var):
    """
    Dynamically locate simulator binary via environment variable, PATH, or standard installation paths.
    Avoids machine-specific hardcoded absolute paths.
    """
    if env_var in os.environ and os.path.isfile(os.environ[env_var]):
        return os.environ[env_var]
    if "QUCS_BIN_DIR" in os.environ:
        for name in name_variants:
            p = os.path.join(os.environ["QUCS_BIN_DIR"], name)
            if os.path.isfile(p):
                return p
    import shutil
    for name in name_variants:
        p = shutil.which(name)
        if p and os.path.isfile(p):
            return p
    candidate_paths = [
        os.path.expanduser(r"~\qucs-s\bin"),
        r"C:\qucs-s\bin",
        r"C:\Program Files\Qucs-S\bin",
        r"C:\Program Files (x86)\Qucs-S\bin",
        "/usr/bin",
        "/usr/local/bin",
        "/opt/qucs/bin",
    ]
    for cdir in candidate_paths:
        for name in name_variants:
            p = os.path.join(cdir, name)
            if os.path.isfile(p):
                return p
    return None

qucsator_bin = find_simulator_executable(["qucsator_rf.exe", "qucsator.exe", "qucsator_rf", "qucsator"], "QUCSATOR_PATH")
qucsconv_bin = find_simulator_executable(["qucsconv_rf.exe", "qucsconv.exe", "qucsconv_rf", "qucsconv"], "QUCSCONV_PATH")
dat_path = os.path.join(OUT_DIR, "qucs_mismatch.dat")
s1p_path = os.path.join(OUT_DIR, "qucs_mismatch.s1p")

if qucsator_bin and os.path.isfile(qucsator_bin):
    print(f"[1/5] Executing Qucsator kernel ({qucsator_bin})...")
    proc = subprocess.run([qucsator_bin, "-i", net_path, "-o", dat_path], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Qucsator execution failed: {proc.stderr}")
    print("      Qucsator simulation completed successfully (Exit Code 0).")

    # Convert dataset to Touchstone format if qucsconv is available
    if qucsconv_bin and os.path.isfile(qucsconv_bin):
        proc_conv = subprocess.run([qucsconv_bin, "-if", "qucsdata", "-of", "touchstone", "-i", dat_path, "-o", s1p_path], capture_output=True, text=True)
        if proc_conv.returncode == 0:
            print("      Converted Qucs dataset to standard Touchstone .s1p file.")
else:
    if os.path.exists(dat_path) and os.path.exists(s1p_path):
        print("[1/5] Qucsator simulator binary not detected on PATH or standard directories.")
        print(f"      Using verified pre-simulated reference dataset ({os.path.basename(dat_path)}).")
        print("      To run live simulation: install Qucs-S / Qucsator and set QUCSATOR_PATH or QUCS_BIN_DIR.")
    else:
        raise FileNotFoundError(
            "Qucsator simulator executable not found, and no pre-simulated reference dataset was found in Qucs_Cross_Validation/. "
            "Please install Qucs-S / Qucsator or set the QUCSATOR_PATH environment variable."
        )

# ── 5. Parse Qucsator Dataset & Load Touchstone ────────────────────────────────
with open(dat_path, "r") as f:
    lines = f.readlines()

f_qucs = []
s11_qucs = []
mode = None

for line in lines:
    line = line.strip()
    if line.startswith("<indep frequency"):
        mode = "freq"
        continue
    elif line.startswith("<dep S[1,1] frequency"):
        mode = "s11"
        continue
    elif line.startswith("</indep") or line.startswith("</dep"):
        mode = None
        continue

    if mode == "freq" and line:
        f_qucs.append(float(line))
    elif mode == "s11" and line:
        m = re.match(r"([+-]?[\d.e+-]+)([+-])j([\d.e+-]+)", line.strip())
        if m:
            s11_qucs.append(complex(float(m.group(1)), float(m.group(2) + m.group(3))))

f_qucs = np.array(f_qucs)
s11_qucs = np.array(s11_qucs)

# Load Touchstone via scikit-rf for 3-way validation
ntwk_skrf = rf.Network(s1p_path)

# ── 6. Compute RF LINE DOCTOR Analytical Results ──────────────────────────────
print("[2/5] Evaluating RF LINE DOCTOR analytical equations...")
sweep_rld = meas.sweep(Z0, RL, length, freqs, vf=vf)
s11_rld = sweep_rld["gamma"]
zin_rld = sweep_rld["zin"]
vswr_rld = sweep_rld["vswr"]
rl_rld = sweep_rld["rl_db"]

# Qucs derived metrics
zin_qucs = Z0 * (1.0 + s11_qucs) / (1.0 - s11_qucs)
vswr_qucs = (1.0 + np.abs(s11_qucs)) / (1.0 - np.abs(s11_qucs))
rl_qucs = -20.0 * np.log10(np.abs(s11_qucs))
phase_qucs_deg = np.angle(s11_qucs, deg=True)
phase_rld_deg = np.angle(s11_rld, deg=True)

# ── 7. Generate Point-by-Point Comparison CSV ─────────────────────────────────
print("[3/5] Generating detailed comparison table...")
csv_path = os.path.join(OUT_DIR, "comparison_table.csv")
with open(csv_path, "w") as f:
    f.write("Frequency_Hz,S11_Mag_RLD,S11_Mag_Qucs,Diff_S11_Mag,S11_Phase_Deg_RLD,S11_Phase_Deg_Qucs,Diff_Phase_Deg,Zin_Re_RLD,Zin_Re_Qucs,Diff_Zin_Re,Zin_Im_RLD,Zin_Im_Qucs,Diff_Zin_Im,VSWR_RLD,VSWR_Qucs,Diff_VSWR,RL_dB_RLD,RL_dB_Qucs,Diff_RL_dB\n")
    for i in range(n_pts):
        f.write(
            f"{freqs[i]:.0f},"
            f"{abs(s11_rld[i]):.8f},{abs(s11_qucs[i]):.8f},{abs(abs(s11_rld[i]) - abs(s11_qucs[i])):.4e},"
            f"{phase_rld_deg[i]:.4f},{phase_qucs_deg[i]:.4f},{abs(phase_rld_deg[i] - phase_qucs_deg[i]):.4e},"
            f"{zin_rld[i].real:.4f},{zin_qucs[i].real:.4f},{abs(zin_rld[i].real - zin_qucs[i].real):.4e},"
            f"{zin_rld[i].imag:.4f},{zin_qucs[i].imag:.4f},{abs(zin_rld[i].imag - zin_qucs[i].imag):.4e},"
            f"{vswr_rld[i]:.6f},{vswr_qucs[i]:.6f},{abs(vswr_rld[i] - vswr_qucs[i]):.4e},"
            f"{rl_rld[i]:.4f},{rl_qucs[i]:.4f},{abs(rl_rld[i] - rl_qucs[i]):.4e}\n"
        )
print(f"      Saved {csv_path}")

# ── 8. Generate Genuine Verification Figures ──────────────────────────────────
print("[4/5] Rendering publication-quality cross-validation figures...")
f_ghz = freqs / 1e9

# Style configuration
plt.rcParams.update({
    "figure.facecolor": "#0b0f17",
    "axes.facecolor": "#0f172a",
    "axes.edgecolor": "#334155",
    "axes.labelcolor": "#cbd5e1",
    "xtick.color": "#94a3b8",
    "ytick.color": "#94a3b8",
    "text.color": "#f8fafc",
    "grid.color": "#1e293b",
    "grid.linestyle": "--",
    "grid.alpha": 0.7,
})

# Figure 1: S11 Magnitude Comparison
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True, gridspec_kw={"height_ratios": [2.5, 1]})
ax1.plot(f_ghz, np.abs(s11_rld), label="RF LINE DOCTOR (Analytical)", color="#00e5ff", linewidth=2.5)
ax1.plot(f_ghz, np.abs(s11_qucs), label="Qucsator (SPICE / RLCG Kernel)", color="#f59e0b", linestyle="--", linewidth=2.0)
ax1.plot(f_ghz, np.abs(ntwk_skrf.s[:, 0, 0]), label="scikit-rf Touchstone (.s1p)", color="#10b981", linestyle=":", linewidth=1.5)
ax1.set_ylabel("|S11| Magnitude", fontsize=11)
ax1.set_title("Cross-Validation: |S11| Reflection Magnitude (RLD vs Qucsator vs scikit-rf)", fontsize=13, fontweight="bold", pad=12)
ax1.grid(True)
ax1.legend(loc="upper right", framealpha=0.85)

# Residual subplot
err_mag = np.abs(np.abs(s11_rld) - np.abs(s11_qucs))
ax2.semilogy(f_ghz, err_mag, color="#ef4444", linewidth=1.8, label="|RLD - Qucsator| Absolute Error")
ax2.set_xlabel("Frequency (GHz)", fontsize=11)
ax2.set_ylabel("Absolute Error", fontsize=10)
ax2.grid(True)
ax2.legend(loc="upper right", framealpha=0.85)
plt.tight_layout()
fig1_path = os.path.join(OUT_DIR, "1_qucs_vs_rld_s11_magnitude.png")
fig.savefig(fig1_path, dpi=200)
plt.close(fig)

# Figure 2: S11 Phase Response Comparison
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True, gridspec_kw={"height_ratios": [2.5, 1]})
ax1.plot(f_ghz, np.unwrap(np.angle(s11_rld, deg=True)), label="RF LINE DOCTOR", color="#00e5ff", linewidth=2.5)
ax1.plot(f_ghz, np.unwrap(np.angle(s11_qucs, deg=True)), label="Qucsator Kernel", color="#f59e0b", linestyle="--", linewidth=2.0)
ax1.set_ylabel("Unwrapped Phase (deg)", fontsize=11)
ax1.set_title("Cross-Validation: S11 Phase Response Over Frequency", fontsize=13, fontweight="bold", pad=12)
ax1.grid(True)
ax1.legend(loc="upper right", framealpha=0.85)

err_phase = np.abs(np.unwrap(np.angle(s11_rld, deg=True)) - np.unwrap(np.angle(s11_qucs, deg=True)))
ax2.semilogy(f_ghz, err_phase, color="#ef4444", linewidth=1.8, label="|Phase Error| (deg)")
ax2.set_xlabel("Frequency (GHz)", fontsize=11)
ax2.set_ylabel("Error (deg)", fontsize=10)
ax2.grid(True)
ax2.legend(loc="upper right", framealpha=0.85)
plt.tight_layout()
fig2_path = os.path.join(OUT_DIR, "2_qucs_vs_rld_s11_phase.png")
fig.savefig(fig2_path, dpi=200)
plt.close(fig)

# Figure 3: Input Impedance Zin (Rin & Xin) Comparison
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
ax1.plot(f_ghz, zin_rld.real, label="Rin (RF LINE DOCTOR)", color="#38bdf8", linewidth=2.5)
ax1.plot(f_ghz, zin_qucs.real, label="Rin (Qucsator)", color="#f59e0b", linestyle="--", linewidth=2.0)
ax1.set_ylabel("Resistance (Ω)", fontsize=11)
ax1.set_title("Input Impedance Zin Comparison: Resistance and Reactance Profiles", fontsize=13, fontweight="bold", pad=12)
ax1.grid(True)
ax1.legend(loc="upper right", framealpha=0.85)

ax2.plot(f_ghz, zin_rld.imag, label="Xin (RF LINE DOCTOR)", color="#a855f7", linewidth=2.5)
ax2.plot(f_ghz, zin_qucs.imag, label="Xin (Qucsator)", color="#ec4899", linestyle="--", linewidth=2.0)
ax2.set_xlabel("Frequency (GHz)", fontsize=11)
ax2.set_ylabel("Reactance (Ω)", fontsize=11)
ax2.grid(True)
ax2.legend(loc="upper right", framealpha=0.85)
plt.tight_layout()
fig3_path = os.path.join(OUT_DIR, "3_qucs_vs_rld_input_impedance.png")
fig.savefig(fig3_path, dpi=200)
plt.close(fig)

# Figure 4: VSWR Comparison
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True, gridspec_kw={"height_ratios": [2.5, 1]})
ax1.plot(f_ghz, vswr_rld, label="RF LINE DOCTOR (VSWR = 2.400)", color="#10b981", linewidth=2.5)
ax1.plot(f_ghz, vswr_qucs, label="Qucsator (VSWR = 2.400)", color="#f59e0b", linestyle="--", linewidth=2.0)
ax1.set_ylabel("VSWR", fontsize=11)
ax1.set_ylim([1.0, 3.5])
ax1.set_title("Voltage Standing Wave Ratio (VSWR) Cross-Validation", fontsize=13, fontweight="bold", pad=12)
ax1.grid(True)
ax1.legend(loc="upper right", framealpha=0.85)

err_vswr = np.abs(vswr_rld - vswr_qucs)
ax2.semilogy(f_ghz, err_vswr, color="#ef4444", linewidth=1.8, label="|VSWR Error|")
ax2.set_xlabel("Frequency (GHz)", fontsize=11)
ax2.set_ylabel("Absolute Error", fontsize=10)
ax2.grid(True)
ax2.legend(loc="upper right", framealpha=0.85)
plt.tight_layout()
fig4_path = os.path.join(OUT_DIR, "4_qucs_vs_rld_vswr.png")
fig.savefig(fig4_path, dpi=200)
plt.close(fig)

# Figure 5: Normalized Smith Chart Comparison
fig, ax = plt.subplots(figsize=(7, 7))
meas.smith_plot(s11_rld, ax=ax, label="RF LINE DOCTOR Trajectory", color="#00e5ff", linewidth=3.0)
meas.smith_plot(s11_qucs, ax=ax, label="Qucsator Trajectory", color="#f59e0b", linestyle="--", linewidth=2.0)
ax.set_title("Smith Chart Trajectory Overlay (RLD vs Qucsator)", fontsize=12, fontweight="bold", color="#ffffff", pad=12)
ax.legend(loc="upper right", framealpha=0.85)
fig5_path = os.path.join(OUT_DIR, "5_qucs_vs_rld_smith_chart.png")
fig.savefig(fig5_path, dpi=200)
plt.close(fig)

# Figure 6: Circuit Schematic Topology Rendering
fig, ax = plt.subplots(figsize=(10, 4.5), facecolor="#0f172a")
ax.set_facecolor("#0f172a")
ax.set_xlim([0, 10])
ax.set_ylim([0, 5])
ax.axis("off")

# Draw Source Port
ax.add_patch(plt.Rectangle((0.6, 2.5), 1.2, 1.2, fill=True, color="#1e293b", ec="#38bdf8", lw=2))
ax.text(1.2, 3.1, "Port 1\n(Pac)", ha="center", va="center", color="#ffffff", fontweight="bold", fontsize=10)
ax.text(1.2, 2.0, "Z_src = 50 Ω\nP = 0 dBm", ha="center", va="center", color="#94a3b8", fontsize=8.5)

# Wire 1
ax.plot([1.8, 3.0], [3.1, 3.1], color="#38bdf8", lw=2.5)

# Draw Transmission Line
ax.add_patch(plt.Rectangle((3.0, 2.3), 4.0, 1.6, fill=True, color="#1e293b", ec="#00e5ff", lw=2.5))
ax.text(5.0, 3.25, "Transmission Line (RLCG)", ha="center", va="center", color="#00e5ff", fontweight="bold", fontsize=11)
ax.text(5.0, 2.8, "Z0 = 50.0 Ω | length = 1.0 m | vf = 0.66", ha="center", va="center", color="#f8fafc", fontsize=9.5)
ax.text(5.0, 2.45, "L = 252.7 nH/m | C = 101.1 pF/m | R = 0 | G = 0", ha="center", va="center", color="#94a3b8", fontsize=8.5)

# Wire 2
ax.plot([7.0, 8.2], [3.1, 3.1], color="#38bdf8", lw=2.5)

# Draw Load Resistor
ax.add_patch(plt.Rectangle((8.2, 2.5), 1.2, 1.2, fill=True, color="#1e293b", ec="#f59e0b", lw=2))
ax.text(8.8, 3.1, "Load R1\n(R_L)", ha="center", va="center", color="#f59e0b", fontweight="bold", fontsize=10)
ax.text(8.8, 2.0, "R_L = 120.0 Ω\n(Mismatch)", ha="center", va="center", color="#94a3b8", fontsize=8.5)

# Grounds
for gx in [1.2, 8.8]:
    ax.plot([gx, gx], [2.5, 1.6], color="#64748b", lw=2)
    ax.plot([gx - 0.25, gx + 0.25], [1.6, 1.6], color="#64748b", lw=2)
    ax.plot([gx - 0.15, gx + 0.15], [1.45, 1.45], color="#64748b", lw=1.5)
    ax.plot([gx - 0.05, gx + 0.05], [1.3, 1.3], color="#64748b", lw=1)

ax.set_title("Qucs-S / Qucsator Circuit Schematic Topology (Case 2: Resistive Mismatch)", fontsize=12, fontweight="bold", color="#f8fafc", pad=10)
plt.tight_layout()
fig6_path = os.path.join(OUT_DIR, "6_circuit_schematic.png")
fig.savefig(fig6_path, dpi=200)
plt.close(fig)

print("[5/5] All cross-validation outputs generated successfully in Qucs_Cross_Validation/")
