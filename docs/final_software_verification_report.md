# RF LINE DOCTOR — Final Software Verification Report

**Project Title:** RF Line Doctor: Virtual Transmission-Line Fault Diagnosis, Fault Location and Impedance-Matching System Using Smith-Chart Analysis  
**Course:** EC-3104 Microwave Engineering  
**Branch Audited:** `rf-line-doctor-build`  
**Latest Verification Commit:** `1911d55`  
**Audit Date:** 2026-10-30  
**Status:** **100% Verified — Fully Ready for Faculty Demonstration**

---

## 1. Environment & Pre-Flight Verification

| Item | Requirement / Target | Observed State | Status |
|---|---|---|---|
| **Git Branch** | `rf-line-doctor-build` | `rf-line-doctor-build` | ✅ Verified |
| **Git Tree Status** | Clean working directory | `nothing to commit, working tree clean` | ✅ Verified |
| **Main Branch Integrity** | Untouched, strictly preserved | Last commit `0305a96` (original 3 commits) | ✅ Verified |
| **Python Environment** | Python 3.10+ compatible | Python 3.13.13 (x64) on Windows | ✅ Verified |
| **Key Dependencies** | Streamlit, NumPy, SciPy, Matplotlib | Streamlit 1.66.1, NumPy 2.x, Matplotlib 3.x | ✅ Verified |
| **HTTP Server Response** | Streamlit web server binding | Port 8501 HTTP 200 OK (`Invoke-WebRequest`) | ✅ Verified |

---

## 2. Automated Test Suite Results

The full automated regression suite was executed via `python -m pytest -v`:

```
======================= 102 passed, 1 warning in 1.40s =======================
```

| Test Module | Test Count | Scope Verified | Result |
|---|---|---|---|
| `test_line_model.py` | 27 | Closed-form lossless equations, boundary conditions, singular limits ($\lambda/4, \lambda/2$), broadcasting | **27 / 27 PASS** |
| `test_measurements.py` | 12 | Reflection coefficient, VSWR, return loss, SweepResult metadata, non-passive sample handling, Smith plot generation | **12 / 12 PASS** |
| `test_fault_simulation.py` | 10 | 6 canonical scenarios, 2-port ABCD cascading for series-L/shunt-C, zero-limit convergence, unclipped noise modeling | **10 / 10 PASS** |
| `test_diagnosis.py` | 28 | Frozen contract classification (`healthy`, `mismatch`, `open`, `short`, `unknown`), subtype extraction, DC phase intercept, frequency grid uniformity validation | **28 / 28 PASS** |
| `test_matching.py` | 7 | Quarter-wave transformer design, exact cancellation at $f_0$, complex load rejection, contiguous passband evaluation | **7 / 7 PASS** |
| `test_location.py` | 5 | Hann-windowed IFFT pseudo-TDR, phase-slope estimation, dual-method discrepancy detection, Rayleigh resolution | **5 / 5 PASS** |
| `test_integration.py` | 8 | End-to-end data pipeline, type stability, all 7 analytical hand-calculation benchmarks | **8 / 8 PASS** |
| `test_validation.py` | 3 | Confusion matrix math, classification report generation, location metrics error calculations | **3 / 3 PASS** |
| `test_app.py` | 2 | Clean importability of Streamlit application and core pipeline execution | **2 / 2 PASS** |
| **Total** | **102** | **Full system coverage without breaking frozen contracts** | **102 / 102 PASS (100%)** |

---

## 3. Systematic Testing of the Six Proposed Simulation Scenarios

Each of the six canonical fault conditions specified in the original proposal was independently tested using nominal line parameters: $Z_0 = 50\,\Omega$, length $\ell = 1.0\text{ m}$, velocity factor $\text{vf} = 0.66$ ($v_p = 1.979 \times 10^8\text{ m/s}$), frequency sweep $500\text{ MHz}$ to $4000\text{ MHz}$ (400 points, uniform spacing).

### Scenario 1: Healthy / Matched Line ($Z_L = Z_0$)
- **Simulation Parameters:** $Z_L = 50.0\,\Omega$.
- **Measured Metrics:** $|\Gamma| = 0.0000$ (constant across all frequencies); $\text{VSWR} = 1.000$; Return Loss $= \infty\text{ dB}$; $Z_{\text{in}} = 50.00 + j0.00\,\Omega$.
- **Classifier Inference:** Contract Class: `healthy` | Subtype: `matched` | Confidence: `high` | Rule Fired: `R1_HEALTHY_MATCHED`.
- **Fault Location:** Returns `None` with documented status `"Line is healthy/matched; no reflection echo present."`
- **Smith Chart:** Stays exactly at the center coordinate $(0, 0)$.

### Scenario 2: Pure Resistive Mismatch ($Z_L = R_L \ne Z_0$)
- **Simulation Parameters:** $Z_L = 120.0\,\Omega$ ($R_L > Z_0$).
- **Measured Metrics:** Theoretical $|\Gamma| = (120-50)/(120+50) = 0.4118$; Measured $|\Gamma| = 0.4118$; $\text{VSWR} = 2.400$; Return Loss $= 7.71\text{ dB}$; $Z_{\text{in}}$ oscillates between $20.83\,\Omega$ ($Z_0^2/R_L$) and $120.00\,\Omega$.
- **Classifier Inference:** Contract Class: `mismatch` | Subtype: `resistive_mismatch` | Confidence: `high` | Rule Fired: `R6_RESISTIVE_MISMATCH`.
- **Fault Location:** IFFT distance $= 1.004\text{ m}$; Phase-slope distance $= 1.000\text{ m}$ (true load position $= 1.000\text{ m}$). Discrepancy $= 0.45\text{ cm} \le \Delta R$. Reliable: `True`.
- **Smith Chart:** Circular trajectory centered on the real axis with radius $\rho = 0.4118$.

### Scenario 3: Open-Circuit Termination ($Z_L = \infty$)
- **Simulation Parameters:** $Z_L = \text{np.inf}$ (`lm.OPEN`).
- **Measured Metrics:** $|\Gamma| = 1.0000$ across all frequencies; $\text{VSWR} = \infty$; Return Loss $= 0.00\text{ dB}$; $Z_{\text{in}}$ alternates between pure capacitive and pure inductive singularities.
- **Classifier Inference:** Contract Class: `open` | Subtype: `open_circuit` | Confidence: `high` | Rule Fired: `R4_OPEN_CIRCUIT` (DC phase intercept $\cos(\phi_0) = +1.000 > 0.1$).
- **Fault Location:** IFFT distance $= 1.004\text{ m}$; Phase-slope distance $= 1.000\text{ m}$ (true $= 1.000\text{ m}$). Reliable: `True`.
- **Smith Chart:** Follows the outer boundary $|\Gamma| = 1.0$, passing through the open-circuit point $(+1, 0)$ at $f \to 0$.

### Scenario 4: Short-Circuit Termination ($Z_L = 0$)
- **Simulation Parameters:** $Z_L = 0.0 + j0.0\,\Omega$.
- **Measured Metrics:** $|\Gamma| = 1.0000$ across all frequencies; $\text{VSWR} = \infty$; Return Loss $= 0.00\text{ dB}$; $Z_{\text{in}}$ alternates between pure inductive and pure capacitive singularities.
- **Classifier Inference:** Contract Class: `short` | Subtype: `short_circuit` | Confidence: `high` | Rule Fired: `R5_SHORT_CIRCUIT` (DC phase intercept $\cos(\phi_0) = -1.000 < -0.1$).
- **Fault Location:** IFFT distance $= 1.004\text{ m}$; Phase-slope distance $= 1.000\text{ m}$ (true $= 1.000\text{ m}$). Reliable: `True`.
- **Smith Chart:** Follows the outer boundary $|\Gamma| = 1.0$, passing through the short-circuit point $(-1, 0)$ at $f \to 0$.

### Scenario 5: Series Inductive Discontinuity (Series L)
- **Simulation Parameters:** $L = 15.0\text{ nH}$ located at $d = 0.40\text{ m}$ from port, terminated in matched load $Z_L = 50\,\Omega$.
- **Measured Metrics:** $|\Gamma|$ rises monotonically with frequency from $0.4287$ at $500\text{ MHz}$ to $0.9689$ at $4000\text{ MHz}$; Mean $|\Gamma| = 0.8524$; Frequency trend $= +0.2523 > 0.010$; De-embedded imaginary reflection $= +0.76 > 0$ (inductive).
- **Classifier Inference:** Contract Class: `mismatch` | Subtype: `series_L` | Confidence: `high` | Rule Fired: `R2_SERIES_L_MISMATCH`.
- **Fault Location:** IFFT distance $= 0.403\text{ m}$; Phase-slope distance $= 0.402\text{ m}$ (true $= 0.400\text{ m}$). Discrepancy $= 0.04\text{ cm}$. Reliable: `True`.
- **Smith Chart:** Trajectory spirals toward the inductive upper half-plane as frequency increases.

### Scenario 6: Shunt Capacitive Discontinuity (Shunt C)
- **Simulation Parameters:** $C = 15.0\text{ pF}$ located at $d = 0.60\text{ m}$ from port, terminated in matched load $Z_L = 50\,\Omega$.
- **Measured Metrics:** $|\Gamma|$ rises monotonically with frequency from $0.7624$ at $500\text{ MHz}$ to $0.9944$ at $4000\text{ MHz}$; Mean $|\Gamma| = 0.9617$; Frequency trend $= +0.0988 > 0.010$; De-embedded imaginary reflection $= -0.56 < 0$ (capacitive).
- **Classifier Inference:** Contract Class: `mismatch` | Subtype: `shunt_C` | Confidence: `high` | Rule Fired: `R3_SHUNT_C_MISMATCH`.
- **Fault Location:** IFFT distance $= 0.603\text{ m}$; Phase-slope distance $= 0.602\text{ m}$ (true $= 0.600\text{ m}$). Discrepancy $= 0.07\text{ cm}$. Reliable: `True`.
- **Smith Chart:** Trajectory spirals toward the capacitive lower half-plane as frequency increases.

---

## 4. Verification Against Analytical Hand Calculations (`HAND_CALCULATIONS.md`)

Each of the canonical benchmarks from [`HAND_CALCULATIONS.md`](../HAND_CALCULATIONS.md) was executed and compared against the software output:

| Case | Theoretical Parameters | Expected Analytical Value | Observed Software Value | Discrepancy |
|---|---|---|---|---|
| **Case A** | Matched: $Z_0 = 50\,\Omega, Z_L = 50\,\Omega$ | $\Gamma = 0, \text{VSWR} = 1.0, Z_{\text{in}} = 50\,\Omega$ | $\Gamma = 0j, \text{VSWR} = 1.0, Z_{\text{in}} = 50.0 + j0.0\,\Omega$ | **$0.000$ (Exact)** |
| **Case B** | Short at $\ell = \lambda/8$ ($f=100\text{ MHz}, \text{vf}=1.0$) | $Z_{\text{in}} = +j Z_0 \tan(45^\circ) = +j50\,\Omega$ | $Z_{\text{in}} = -3.55 \times 10^{-15} + j50.00\,\Omega$ | **$< 10^{-14}\,\Omega$ (Machine $\epsilon$)** |
| **Case C** | Open at $\ell = \lambda/8$ ($f=100\text{ MHz}, \text{vf}=1.0$) | $Z_{\text{in}} = -j Z_0 \cot(45^\circ) = -j50\,\Omega$ | $Z_{\text{in}} = -3.55 \times 10^{-15} - j50.00\,\Omega$ | **$< 10^{-14}\,\Omega$ (Machine $\epsilon$)** |
| **Case D** | Quarter-wave inversion: $Z_0 = 50\,\Omega, Z_L = 100\,\Omega, \ell = \lambda/4$ | $Z_{\text{in}} = 50^2/100 = 25\,\Omega, \Gamma = -1/3, \text{VSWR} = 2.0$ | $Z_{\text{in}} = 25.0 + j0.0\,\Omega, \Gamma = -0.3333, \text{VSWR} = 2.000$ | **$0.000$ (Exact)** |
| **Case E** | Half-wave repetition: $Z_L = 30 + j40\,\Omega, \ell = \lambda/2$ | $Z_{\text{in}} = Z_L = 30 + j40\,\Omega$ | $Z_{\text{in}} = 30.00 + j40.00\,\Omega$ | **$0.000$ (Exact)** |
| **Case F** | QW Transformer: $50 \to 200\,\Omega$ at $100\text{ MHz}, \text{vf}=1.0$ | $Z_t = \sqrt{50 \times 200} = 100.0\,\Omega, \ell_t = \lambda/4 = 0.7495\text{ m}$ | $Z_t = 100.00\,\Omega, \ell_t = 0.749481\text{ m}$ | **$0.000$ (Exact)** |
| **Case G** | Singularities at $\lambda/4$ | Short $\to \infty$ (virtual open); Open $\to 0$ (virtual short) | Handled safely via $\Gamma$ formulation: Short $\to \infty$, Open $\to 0$ | **Exact** |

---

## 5. Fault Location Verification: Dual-Method & Resolution Hierarchy

For the nominal sweep ($500\text{ to }4000\text{ MHz}$, $\text{vf} = 0.66$):
- **Bandwidth ($B$):** $3.50\text{ GHz}$.
- **Frequency Step ($\Delta f$):** $8.772\text{ MHz}$.
- **Phase Velocity ($v_p$):** $197,863,022\text{ m/s}$ ($0.66 \times c_0$).
- **Theoretical Rayleigh Range Resolution ($\Delta R$):**
  $$\Delta R = \frac{v_p}{2B} = \frac{1.979 \times 10^8}{2 \times 3.50 \times 10^9} = 0.0283\text{ m} = 2.83\text{ cm}$$
- **Zero-Padded Interpolation Bin Step ($\delta d$):**
  $$\delta d = \frac{v_p}{2 N_{\text{pad}} \Delta f} = 0.0035\text{ m} = 0.35\text{ cm}$$
- **Unambiguous Range ($R_{\text{max}}$):**
  $$R_{\text{max}} = \frac{v_p}{2 \Delta f} = 11.28\text{ m}$$

### Observations:
1. **Rayleigh Limit vs Interpolation Step:** The documentation and UI prominently explain that zero-padding ($N_{\text{pad}} = 3200$) provides fine display interpolation ($\delta d = 0.35\text{ cm}$), but does **not** allow two separate reflectors closer than $2.83\text{ cm}$ to be resolved as two separate peaks.
2. **Phase-Slope Method:** Directly derived from linear phase rotation $\phi(f) \approx \phi_0 - (4\pi d / v_p) f$. For resistive mismatch, open, and short, the phase slope gives an exact distance estimate ($1.000\text{ m}$ for a $1.0\text{ m}$ line).
3. **Reactive Discontinuity Bias:** For series L ($15\text{ nH}$) and shunt C ($15\text{ pF}$), the internal frequency-dependent phase shift adds a slight curvature to $\phi(f)$. The software cross-checks the two methods and flags discrepancies exceeding $3 \Delta R$ as indicative of reactive discontinuities.

---

## 6. Smith Chart Verification

- **Normalization:** Fully normalized to $Z_0$; chart coordinates represent the complex reflection coefficient $\Gamma = u + jv$.
- **Grid Structure:** Constant normalized resistance circles ($r = 0, 0.2, 0.5, 1.0, 2.0, 5.0$) and constant reactance arcs ($x = \pm 0.2, \pm 0.5, \pm 1.0, \pm 2.0, \pm 5.0$) are accurately rendered.
- **Reference Coordinates:**
  - Center $(0, 0)$: Matched load $Z = Z_0$ ($r = 1, x = 0$).
  - Left pole $(-1, 0)$: Short circuit $Z = 0$ ($r = 0, x = 0$).
  - Right pole $(+1, 0)$: Open circuit $Z = \infty$ ($r = \infty$).
- **Rotation Sense:** Clockwise rotation with frequency verifies physical wave propagation toward the generator.

---

## 7. Quarter-Wave Impedance Matching Studio Verification

- **Synthesis:** Designed at arbitrary frequency $f_0$ for purely real loads $R_L > 0$.
  - Formula: $Z_t = \sqrt{Z_0 R_L}$, $\ell_t = v_p / (4 f_0)$.
  - Rejection of Complex Loads: Tested with $Z_L = 75 + j35\,\Omega$; cleanly raises warning in UI and prevents erroneous transformer fabrication.
- **Before-and-After Performance ($50 \to 120\,\Omega$ at $2.25\text{ GHz}$):**
  - **Before:** Flat VSWR $= 2.400$; Return Loss $= 7.71\text{ dB}$.
  - **After at $f_0$:** Exact cancellation: $\Gamma = 0.0000$; $\text{VSWR} = 1.0000$; Return Loss $= \infty\text{ dB}$.
  - **Contiguous Passband:** Bandwidth where $\text{RL} \ge 20\text{ dB}$ ($\text{VSWR} \le 1.22$) is continuously evaluated and displayed ($498.7\text{ MHz}$).

---

## 8. Validation Laboratories & CSV Artifact Consistency

All three validation configurations were re-verified against live execution outputs:

| Configuration | Sample Size | Noise ($\sigma$) | Random Seed | Key Outputs / Artifacts | Verified Accuracy / MAE |
|---|---|---|---|---|---|
| **Streamlit Live Validation** | $N = 120$ | $0.02$ | `42` | Interactive confusion matrices & metrics rendered in View 7 | **100% Contract Accuracy**<br>Location MAE: **$0.22\text{ cm}$** |
| **Standalone Batch Validation** (`run_validation.py`) | $N = 240$ | $0.02$ | `42` | • `results/csv/confusion_matrix.csv`<br>• `results/csv/classification_metrics.csv`<br>• `results/csv/subtype_confusion_matrix.csv`<br>• `results/csv/subtype_classification_metrics.csv`<br>• `results/csv/location_errors.csv`<br>• Figures in `results/figures/` | **99.58% Contract Accuracy**<br>**99.58% Subtype Accuracy**<br>Location MAE: **$0.16\text{ cm}$**<br>Location RMSE: **$0.22\text{ cm}$** |
| **Noise Sensitivity Study** | $N = 120$ per level (6 levels) | $0.00$ to $0.18$ | Distinct seeds: `100 + int(σ*100)` | • `results/csv/noise_sensitivity.csv`<br>• `results/figures/accuracy_vs_noise.png` | $\sigma=0.00: 98.3\%$, $\sigma=0.02: 100.0\%$, $\sigma=0.05: 61.7\%$, $\sigma \ge 0.08: 50.0\%$ (Majority baseline) |

---

## 9. User Experience & Dashboard Integrity (Streamlit `AppTest`)

The application was exercised through Streamlit's official `AppTest` framework across all 8 navigation views:
1. **View 1 (Overview & System Status):** KPI metric cards, system architecture diagram, line parameters display cleanly.
2. **View 2 (Transmission-Line Simulator):** Multi-parameter sweeps, ground truth inspection, CSV download button functioning.
3. **View 3 (Signal Analysis & Smith Chart):** 3 dedicated sub-tabs (Reflection, Impedance, Smith Chart) render with zero matplotlib backend conflicts.
4. **View 4 (Fault Diagnosis Engine):** Evidence, rules fired, electromagnetic justifications, and diagnostic report download working.
5. **View 5 (Fault Location: Phase-Slope & IFFT):** Phase-slope formula callout, IFFT echo profile, dual-method comparison, and resolution hierarchy display correctly.
6. **View 6 (Quarter-Wave Matching Studio):** Design inputs, metric cards, and before/after frequency comparison plots functioning.
7. **View 7 (Independent Validation Lab):** Live Monte Carlo test button executed successfully, producing all 4 evaluation dataframes in-browser.
8. **View 8 (Theory & Hand Calculations):** Formatted KaTeX formulas matching `HAND_CALCULATIONS.md`.

**Zero Python exceptions, zero unhandled errors, and zero broken links observed.**

---

## 10. Summary of Limitations & Disclaimers

To maintain strict academic integrity during faculty review, the following limitations are preserved in the application and documentation:
1. **Lossless Model Assumption:** Line attenuation is assumed to be zero ($\alpha = 0$). Conductor skin-effect and dielectric losses are neglected.
2. **Single-Port Reflection Only:** Classifier operates strictly on $S_{11}(\omega)$ without peeking at ground truth.
3. **Single Dominant Reflector:** Dual-method distance localization assumes one dominant reflector or discontinuity along the line.
4. **Purely Real Quarter-Wave Loads:** Quarter-wave transformers match purely real load resistances ($R_L > 0$). Complex loads are explicitly flagged as requiring stub tuning.
5. **Simulation-Based Validation:** All experimental data is numerically generated with complex Gaussian noise; no physical VNA hardware measurements are claimed.
