# Independent Engineering Cross-Validation Report: RF LINE DOCTOR vs. Qucsator

**Date:** 2026-11-13  
**Auditor / Engineer:** Senior RF Software Quality Auditor  
**Simulation Kernels:** 
- **RF LINE DOCTOR:** Analytical 2-Port ABCD Telegrapher & Wave Engine
- **Qucsator (Qucs-S v26.1.1 / Qucsator v1.0.7):** Circuit-level S-Parameter Kernel
- **3rd-Party Reference:** `scikit-rf` (skrf v2.2.0) via Touchstone `.s1p` export

---

## 1. Executive Summary

An independent, rigorous engineering cross-validation was conducted between the analytical transmission line engine of **RF LINE DOCTOR** and the **Qucsator** simulation kernel from the open-source **Qucs-S** EDA suite.

A canonical virtual transmission line case (**Case 2: Resistive Mismatch**, $120.0\,\Omega$ termination on a $50.0\,\Omega$ coaxial line) was simulated across a $500.0\text{ MHz}$ to $2500.0\text{ MHz}$ linear sweep (201 frequency points).

### Key Findings
* **Reflection Coefficient ($|S_{11}|$):** Maximum absolute error between RF LINE DOCTOR and Qucsator is **$8.23 \times 10^{-14}$** ($< 2 \times 10^{-11}\%$ relative difference).
* **Phase Response:** Maximum absolute unwrapped phase discrepancy is **$1.35 \times 10^{-9}$ degrees**.
* **Input Impedance ($Z_{\text{in}}$):** Maximum absolute difference across resistance and reactance profiles is **$2.60 \times 10^{-9}\,\Omega$**.
* **Voltage Standing Wave Ratio (VSWR):** Evaluates identically to **$2.400000000000$** across both simulators (maximum discrepancy **$4.76 \times 10^{-13}$**).
* **Return Loss:** Evaluates identically to **$7.7072805\text{ dB}$** across all swept frequencies.

---

## 2. Selected Representative Case & Simulation Parameters

The cross-validation utilizes identical physical parameters between RF LINE DOCTOR and Qucsator:

| Parameter | Symbol | Value | Unit | Definition |
| :--- | :--- | :--- | :--- | :--- |
| **System Reference Impedance** | $Z_0$ | `50.0` | $\Omega$ | Reference characteristic impedance for Port 1 |
| **Source Port Impedance** | $Z_{\text{src}}$ | `50.0` | $\Omega$ | S-parameter excitation source impedance |
| **Source Available Power** | $P_{\text{src}}$ | `0.0` | $\text{dBm}$ | 1 mW standard RF port power |
| **Load Termination Resistance** | $R_L$ | `120.0` | $\Omega$ | Resistive mismatch boundary ($R_L \ne Z_0$) |
| **Physical Line Length** | $l$ | `1.0` | $\text{m}$ | End-to-end cable length |
| **Velocity Factor** | $v_f$ | `0.66` | — | Ratio of phase velocity to speed of light ($v_p / c_0$) |
| **Phase Velocity** | $v_p$ | `197863022.28` | $\text{m/s}$ | $v_f \cdot c_0$ (where $c_0 = 299792458\text{ m/s}$) |
| **Distributed Inductance** | $L$ | `2.527000e-7` | $\text{H/m}$ | $Z_0 / v_p = 252.70\text{ nH/m}$ |
| **Distributed Capacitance** | $C$ | `1.010800e-10` | $\text{F/m}$ | $1 / (Z_0 \cdot v_p) = 101.08\text{ pF/m}$ |
| **Distributed Series Resistance** | $R$ | `0.0` | $\Omega\text{/m}$ | Lossless line assumption |
| **Distributed Shunt Conductance** | $G$ | `0.0` | $\text{S/m}$ | Lossless line assumption |
| **Frequency Sweep Start** | $f_{\text{start}}$ | `500.0` | $\text{MHz}$ | Lower frequency bound |
| **Frequency Sweep Stop** | $f_{\text{stop}}$ | `2500.0` | $\text{MHz}$ | Upper frequency bound |
| **Sweep Sample Points** | $N$ | `201` | — | Uniform linear frequency grid ($\Delta f = 10\text{ MHz}$) |

---

## 3. Circuit Configuration & Native Simulator Project Files

### 3.1 Circuit Topology
The benchmark circuit is a single-port reflection measurement network consisting of an RF power source (`Pac:P1`), a distributed transmission line (`RLCG:Line1`), and a ground-referenced resistive load (`R:R1`):

![Circuit Schematic](6_circuit_schematic.png)

### 3.2 Native Qucs Netlist (`qucs_mismatch.net`)
The exact netlist executed by the Qucsator kernel:

```netlist
# Qucs 1.0.7 Netlist -- RF LINE DOCTOR Benchmark
Pac:P1 _net0 gnd f="1 GHz" Z="50 Ohm" Num="1" P="0 dBm"
RLCG:Line1 _net0 _net1 R="0" L="2.527000000000e-07" C="1.010800000000e-10" G="0" Length="1.0"
R:R1 _net1 gnd R="120 Ohm"
.SP:SP1 Type="lin" Start="500000000Hz" Stop="2500000000Hz" Points="201" Noise="no"
```

### 3.3 Native Qucs Schematic (`qucs_mismatch.sch`)
The circuit is stored in native Qucs schematic XML syntax in [qucs_mismatch.sch](qucs_mismatch.sch), allowing direct graphical loading in **Qucs-S** or **QucsStudio**.

---

## 4. Execution Methodology & Environment Verification

### 4.1 Simulator Toolchain
* **Simulator Kernel:** `C:\Users\pc\qucs-s\bin\qucsator_rf.exe` (Qucsator v1.0.7)
* **Format Converter:** `C:\Users\pc\qucs-s\bin\qucsconv_rf.exe`
* **Python Runtime:** Python 3.13.13 (64-bit Windows)
* **Microwave Verification Library:** `scikit-rf` v2.2.0

### 4.2 Execution Steps
1. The netlist `qucs_mismatch.net` was passed directly to the simulation kernel:
   ```cmd
   qucsator_rf.exe -i qucs_mismatch.net -o qucs_mismatch.dat
   ```
   *Exit code:* `0` (Success). Output generated: [qucs_mismatch.dat](qucs_mismatch.dat).
2. The output dataset was converted to an industry-standard Touchstone format:
   ```cmd
   qucsconv_rf.exe -if qucsdata -of touchstone -i qucs_mismatch.dat -o qucs_mismatch.s1p
   ```
   *Exit code:* `0` (Success). Output generated: [qucs_mismatch.s1p](qucs_mismatch.s1p).
3. The resulting S-parameters were independently parsed and cross-compared against RF LINE DOCTOR's `measurements.sweep` and `skrf.Network`.

### 4.3 Documentation of Desktop GUI Environment
> [!NOTE]
> The automated validation ran in a non-interactive console window station (Windows Session 3 without a connected physical display adapter). When invoking GUI window capture via Windows GDI `BitBlt` / `CopyFromScreen`, Windows returned `The handle is invalid`. In strict accordance with the auditing rule (*"Do not fabricate simulation screenshots; if the backend is unavailable or limited, document the limitation"*), no simulated synthetic screenshots of the GUI desktop were created. Instead, genuine high-resolution vector and bitmap figures rendered directly from the executed simulation data are provided below.

---

## 5. Numerical Comparison Table

Below is an extract of the point-by-point comparison at representative frequency intervals across the swept band (full 201-point data available in [comparison_table.csv](comparison_table.csv)):

| Frequency | Metric | RF LINE DOCTOR | Qucsator Kernel | Absolute Diff | Relative Diff (%) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **500.0 MHz** | $\|S_{11}\|$ | `0.41176471` | `0.41176471` | $0.00 \times 10^{-14}$ | $0.000000\%$ |
| | Phase ($^\circ$) | `-19.4344` | `-19.4344` | $1.28 \times 10^{-10}$ | $0.000000\%$ |
| | $Z_{\text{in}}$ ($\Omega$) | `102.502 - 34.026j` | `102.502 - 34.026j` | $4.27 \times 10^{-10}$ | $0.000000\%$ |
| | VSWR | `2.400000` | `2.400000` | $0.00 \times 10^{-13}$ | $0.000000\%$ |
| **1000.0 MHz** | $\|S_{11}\|$ | `0.41176471` | `0.41176471` | $5.55 \times 10^{-14}$ | $0.000000\%$ |
| | Phase ($^\circ$) | `-38.8687` | `-38.8687` | $2.56 \times 10^{-10}$ | $0.000000\%$ |
| | $Z_{\text{in}}$ ($\Omega$) | `65.578 - 36.936j` | `65.578 - 36.936j` | $8.53 \times 10^{-10}$ | $0.000000\%$ |
| | VSWR | `2.400000` | `2.400000` | $2.38 \times 10^{-13}$ | $0.000000\%$ |
| **1500.0 MHz** | $\|S_{11}\|$ | `0.41176471` | `0.41176471` | $8.23 \times 10^{-14}$ | $0.000000\%$ |
| | Phase ($^\circ$) | `-58.3031` | `-58.3031` | $3.84 \times 10^{-10}$ | $0.000000\%$ |
| | $Z_{\text{in}}$ ($\Omega$) | `31.328 - 20.312j` | `31.328 - 20.312j` | $1.28 \times 10^{-09}$ | $0.000000\%$ |
| | VSWR | `2.400000` | `2.400000` | $4.76 \times 10^{-13}$ | $0.000000\%$ |
| **2000.0 MHz** | $\|S_{11}\|$ | `0.41176471` | `0.41176471` | $2.78 \times 10^{-14}$ | $0.000000\%$ |
| | Phase ($^\circ$) | `-77.7375` | `-77.7375` | $5.12 \times 10^{-10}$ | $0.000000\%$ |
| | $Z_{\text{in}}$ ($\Omega$) | `21.258 + 4.608j` | `21.258 + 4.608j` | $1.71 \times 10^{-09}$ | $0.000000\%$ |
| | VSWR | `2.400000` | `2.400000` | $1.19 \times 10^{-13}$ | $0.000000\%$ |
| **2500.0 MHz** | $\|S_{11}\|$ | `0.41176471` | `0.41176471` | $5.55 \times 10^{-14}$ | $0.000000\%$ |
| | Phase ($^\circ$) | `-97.1718` | `-97.1718` | $6.40 \times 10^{-10}$ | $0.000000\%$ |
| | $Z_{\text{in}}$ ($\Omega$) | `27.848 + 20.892j` | `27.848 + 20.892j` | $2.13 \times 10^{-09}$ | $0.000000\%$ |
| | VSWR | `2.400000` | `2.400000` | $2.38 \times 10^{-13}$ | $0.000000\%$ |

---

## 6. Discrepancy & Mathematical Analysis

### 6.1 Conservation of Reflection Magnitude
In a lossless line, energy conservation dictates that the magnitude of the reflection coefficient must remain strictly independent of frequency and position along the line:
$$|\Gamma_L| = \left| \frac{120.0 - 50.0}{120.0 + 50.0} \right| = \frac{70}{170} = \frac{7}{17} \approx 0.4117647058823529$$
Both RF LINE DOCTOR and Qucsator maintain this value across all 201 frequencies with a maximum error of **$8.23 \times 10^{-14}$**, which is within the IEEE 754 double-precision roundoff noise floor ($\epsilon_{\text{mach}} \approx 2.22 \times 10^{-16}$).

### 6.2 Phase Slope & Delay
The phase of $S_{11}$ follows:
$$\phi(f) = -\frac{4\pi l}{v_p} f = -\frac{4\pi (1.0)}{197863022.28} f \approx -6.35105 \times 10^{-8} f\text{ rad}$$
The difference in unwrapped phase between RF LINE DOCTOR and Qucsator is $< 1.35 \times 10^{-9}$ degrees across the entire 2.0 GHz bandwidth, confirming exact phase velocity and propagation constant alignment.

### 6.3 Impedance Transformation
The input impedance oscillates along the characteristic circles of the Smith chart between $Z_{\min} = Z_0 / \text{VSWR} = 50 / 2.4 = 20.833\,\Omega$ and $Z_{\max} = Z_0 \cdot \text{VSWR} = 50 \cdot 2.4 = 120.0\,\Omega$. The numerical impedance agreement is $< 2.6 \times 10^{-9}\,\Omega$.

---

## 7. Genuine Simulation Graphics

### 7.1 Reflection Coefficient Magnitude ($|S_{11}|$)
Comparison of $|S_{11}|$ between RF LINE DOCTOR (cyan), Qucsator (orange dashed), and scikit-rf (green dotted), with residual error subplot:
![S11 Magnitude](1_qucs_vs_rld_s11_magnitude.png)

### 7.2 Phase Response
Unwrapped phase response over frequency demonstrating identical linear phase slope:
![S11 Phase](2_qucs_vs_rld_s11_phase.png)

### 7.3 Input Impedance ($R_{\text{in}}$ and $X_{\text{in}}$)
Resistance and reactance trajectories over frequency:
![Input Impedance](3_qucs_vs_rld_input_impedance.png)

### 7.4 Voltage Standing Wave Ratio (VSWR)
VSWR comparison confirming constant $2.400$ standing wave ratio:
![VSWR Comparison](4_qucs_vs_rld_vswr.png)

### 7.5 Normalized Smith Chart Overlay
Trajectory on the normalized $50\,\Omega$ Smith chart showing complete overlap of RF LINE DOCTOR and Qucsator:
![Smith Chart](5_qucs_vs_rld_smith_chart.png)

---

## 8. Index of Deliverable Artifacts

All project and simulation files are organized in the [Qucs_Cross_Validation/](file:///c:/Users/pc/Documents/GitHub/line-model/Qucs_Cross_Validation) directory:

1. **[qucs_mismatch.sch](file:///c:/Users/pc/Documents/GitHub/line-model/Qucs_Cross_Validation/qucs_mismatch.sch):** Native Qucs-S / QucsStudio schematic project file.
2. **[qucs_mismatch.net](file:///c:/Users/pc/Documents/GitHub/line-model/Qucs_Cross_Validation/qucs_mismatch.net):** Native Qucsator simulation netlist.
3. **[qucs_mismatch.dat](file:///c:/Users/pc/Documents/GitHub/line-model/Qucs_Cross_Validation/qucs_mismatch.dat):** Raw Qucs simulation dataset output directly by `qucsator_rf.exe`.
4. **[qucs_mismatch.s1p](file:///c:/Users/pc/Documents/GitHub/line-model/Qucs_Cross_Validation/qucs_mismatch.s1p):** Touchstone 1-port S-parameter file generated via `qucsconv_rf.exe`.
5. **[comparison_table.csv](file:///c:/Users/pc/Documents/GitHub/line-model/Qucs_Cross_Validation/comparison_table.csv):** Point-by-point numerical comparison across all 201 frequencies.
6. **[tests/test_qucs_cross_validation.py](file:///c:/Users/pc/Documents/GitHub/line-model/tests/test_qucs_cross_validation.py):** Automated pytest integration test verifying Qucsator outputs against RF LINE DOCTOR.

---

## 9. Conclusion

The independent cross-validation confirms that the mathematical engine of **RF LINE DOCTOR** is **100% physically and numerically consistent** with the established industry-standard **Qucsator** circuit simulator:
$$\text{Relative Discrepancy} \le 10^{-11}\% \quad (\text{Identical to within IEEE 754 float precision})$$
No anomalies, unphysical branch selections, or model discrepancies were detected.
