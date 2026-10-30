# RF LINE DOCTOR — Final Project Demonstration Guide

**Project Title:** RF Line Doctor: Virtual Transmission-Line Fault Diagnosis, Fault Location and Impedance-Matching System Using Smith-Chart Analysis  
**Course:** EC-3104 Microwave Engineering  
**Prepared for:** Faculty Evaluation and Undergraduate Classroom Demonstration  
**Target Application:** Streamlit Interactive Laboratory (`app.py`)  
**Development Branch:** `rf-line-doctor-build`

---

## 1. Demonstration Setup & What to Open First

### Step 1: Open Terminal & Launch Application
In the project root directory, launch the virtual laboratory using:

```bash
python -m streamlit run app.py
```

The application will launch in your default web browser at `http://localhost:8501`.

### Step 2: What to Show First (View 1: System Overview)
1. **Start on "1. Overview & System Status":**
   - Point out the **Header & Subtitle**: Emphasize that this is an EC-3104 educational virtual prototype designed to demonstrate transmission-line wave propagation, boundary conditions, automated single-port fault diagnosis, and impedance matching.
   - Point out the **KPI Cards**: Note that the top cards dynamically update to display the currently inferred diagnosis, physical subtype, estimated fault location, and physical Rayleigh range resolution.
   - Point out the **End-to-End Operational Pipeline**: Explain the data flow:
     $$\text{User Inputs} \longrightarrow \text{Lossless Transmission Line Model} \longrightarrow \text{Frequency Sweep} \longrightarrow \text{Smith Chart} \longrightarrow \text{Rule-Based Classifier} \longrightarrow \text{Dual-Method Location} \longrightarrow \text{Matching Studio}$$

---

## 2. Standard Baseline Input Parameters

In the sidebar, configure the standard baseline parameters:

1. **Characteristic Impedance ($Z_0$):** Set to `50.0 Ω` (or demonstrate `75.0 Ω` for CATV lines).
2. **Physical Line Length ($\ell$):** Set to `1.0 m`.
3. **Velocity Factor ($\text{vf}$):** Set to `0.66` (explain that solid polyethylene dielectric has $\epsilon_r \approx 2.3 \implies \text{vf} = 1/\sqrt{\epsilon_r} \approx 0.66$, giving $v_p = 1.98 \times 10^8\text{ m/s}$).
4. **Frequency Sweep:**
   - $f_{\text{start}} = 500\text{ MHz}$
   - $f_{\text{stop}} = 4000\text{ MHz}$ ($4.0\text{ GHz}$)
   - Points $= 400$ (uniform grid spacing $\Delta f = 8.77\text{ MHz}$)
5. **Measurement Noise ($\sigma$):** Start with `0.00` (ideal noiseless baseline), then show `0.02` to demonstrate robustness against complex Gaussian measurement noise.

---

## 3. How to Demonstrate the Six Proposed Scenarios

Cycle through the **Fault Preset Scenario** dropdown in the sidebar and navigate between **View 3 (Signal Analysis & Smith Chart)**, **View 4 (Fault Diagnosis Engine)**, and **View 5 (Fault Location)**:

### Scenario 1: Healthy Matched Line ($Z_L = Z_0$)
- **Select:** `Case 1: Healthy Matched (ZL = Z0)`
- **What to Show:**
  - View 3: Flat reflection $|\Gamma| = 0.000$, $\text{VSWR} = 1.000$, $\text{Return Loss} = \infty\text{ dB}$, input impedance $Z_{\text{in}} = 50 + j0\,\Omega$.
  - View 3 (Smith Chart): Trajectory is a single stationary dot at the exact center $(0, 0)$.
  - View 4: Classifier returns contract class `healthy`, subtype `matched` with `HIGH` confidence.
  - View 5: Localization reports `None` with the note `"Line is healthy/matched; no reflection echo present."`

### Scenario 2: Resistive Impedance Mismatch ($Z_L = R_L \ne Z_0$)
- **Select:** `Case 2: Resistive Mismatch (ZL = RL != Z0)`
- **Set:** Load Resistance $R_L = 120.0\,\Omega$.
- **What to Show:**
  - View 3: Flat $|\Gamma| = (120-50)/(120+50) = 0.412$, $\text{VSWR} = 2.400$, $\text{RL} = 7.71\text{ dB}$.
  - View 3 (Smith Chart): Perfect circular trajectory with radius $\rho = 0.412$ centered on the origin.
  - View 4: Classifier returns contract class `mismatch`, subtype `resistive_mismatch` via Rule `R6_RESISTIVE_MISMATCH`.
  - View 5: Distance estimation reports $1.000\text{ m}$ (Phase-Slope) and $1.004\text{ m}$ (IFFT), matching the physical line termination.

### Scenario 3: Open-Circuit Termination ($Z_L = \infty$)
- **Select:** `Case 3: Open Circuit (ZL = ∞)`
- **What to Show:**
  - View 3: Total reflection $|\Gamma| = 1.000$, $\text{VSWR} = \infty$, $\text{Return Loss} = 0.00\text{ dB}$.
  - View 3 (Smith Chart): Trajectory tracks along the outer boundary circle ($|\Gamma| = 1.0$), intersecting the open-circuit pole $(+1, 0)$ at $f \to 0$.
  - View 4: Classifier returns contract class `open`, subtype `open_circuit`. Explain the **DC Phase Intercept**: $\cos(\phi_0) = +1.000 > 0.1$, which distinguishes open from short without guessing.
  - View 5: Distance estimation detects fault at $1.000\text{ m}$.

### Scenario 4: Short-Circuit Termination ($Z_L = 0$)
- **Select:** `Case 4: Short Circuit (ZL = 0)`
- **What to Show:**
  - View 3: Total reflection $|\Gamma| = 1.000$, $\text{VSWR} = \infty$, $\text{Return Loss} = 0.00\text{ dB}$.
  - View 3 (Smith Chart): Trajectory tracks along the outer boundary circle ($|\Gamma| = 1.0$), intersecting the short-circuit pole $(-1, 0)$ at $f \to 0$.
  - View 4: Classifier returns contract class `short`, subtype `short_circuit`. Explain that $\cos(\phi_0) = -1.000 < -0.1$ uniquely confirms short-circuit termination.
  - View 5: Distance estimation detects fault at $1.000\text{ m}$.

### Scenario 5: Series Inductive Discontinuity (Connector Inductance)
- **Select:** `Case 5: Series Inductive Discontinuity (Series L)`
- **Set:** Inductance $L = 15.0\text{ nH}$, Discontinuity Position $d = 0.40\text{ m}$.
- **What to Show:**
  - View 3: $|\Gamma|$ rises with frequency ($0.43$ at $500\text{ MHz} \to 0.97$ at $4.0\text{ GHz}$).
  - View 3 (Smith Chart): Trajectory spirals toward the inductive upper half-plane ($\text{Im} > 0$).
  - View 4: Classifier identifies contract class `mismatch`, subtype `series_L`. Explain the physical rule: rising frequency trend ($> 0.010$) with inductive de-embedded phase ($+0.76 > 0$).
  - View 5: Both methods detect the discontinuity position at $0.402\text{ m}$ (true $= 0.400\text{ m}$).

### Scenario 6: Shunt Capacitive Discontinuity (Connector Capacitance)
- **Select:** `Case 6: Shunt Capacitive Discontinuity (Shunt C)`
- **Set:** Capacitance $C = 15.0\text{ pF}$, Discontinuity Position $d = 0.60\text{ m}$.
- **What to Show:**
  - View 3: $|\Gamma|$ rises with frequency ($0.76 \to 0.99$).
  - View 3 (Smith Chart): Trajectory spirals toward the capacitive lower half-plane ($\text{Im} < 0$).
  - View 4: Classifier identifies contract class `mismatch`, subtype `shunt_C`. Explain the rule: rising reflection trend with capacitive de-embedded phase ($-0.56 < 0$).
  - View 5: Both methods locate the discontinuity at $0.603\text{ m}$ (true $= 0.600\text{ m}$).

---

## 4. Key Electromagnetic Equations to Explain to the Professor

When navigating to **View 8: Theory & Hand Calculations**, explain these core equations:

1. **Input Impedance of Lossless Transmission Line:**
   $$Z_{\text{in}}(d) = Z_0 \frac{Z_L + j Z_0 \tan(\beta d)}{Z_0 + j Z_L \tan(\beta d)} = Z_0 \frac{1 + \Gamma(d)}{1 - \Gamma(d)}$$
   *Explain why the $\Gamma$-based formulation is numerically superior: it avoids division by zero for open circuits ($Z_L = \infty$) and quarter-wave singularities.*

2. **Phase Velocity and Phase Constant:**
   $$v_p = \text{vf} \times c_0, \quad \beta = \frac{2\pi}{\lambda} = \frac{2\pi f}{v_p}$$

3. **Voltage Standing Wave Ratio (VSWR) & Return Loss:**
   $$\text{VSWR} = \frac{1 + |\Gamma|}{1 - |\Gamma|}, \quad \text{RL} = -20 \log_{10}(|\Gamma|)\text{ dB}$$

4. **Phase-Slope Fault Distance Estimation:**
   $$\phi(f) \approx \phi_0 - \frac{4\pi d}{v_p} f \implies d = -\frac{v_p}{4\pi} \frac{d\phi}{df}$$
   *Explain that round-trip travel introduces $2d$; the unwrapped phase slope across frequency directly yields physical distance.*

5. **Rayleigh Physical Range Resolution vs Zero-Padding:**
   $$\Delta R = \frac{v_p}{2B}$$
   *Emphasize that zero-padding interpolates the peak position between bins ($\delta d = 0.35\text{ cm}$), but cannot resolve two distinct reflectors closer than $\Delta R = 2.83\text{ cm}$.*

---

## 5. How to Demonstrate Quarter-Wave Matching (View 6)

1. Select **View 6: Quarter-Wave Matching Studio**.
2. Note that the studio automatically detects real load resistance ($R_L = 120\,\Omega$).
3. Enter Design Frequency $f_0 = 2250\text{ MHz}$ ($2.25\text{ GHz}$, center of the band).
4. **Point out the synthesized parameters:**
   - Characteristic Impedance: $Z_t = \sqrt{Z_0 R_L} = \sqrt{50 \times 120} = 77.46\,\Omega$.
   - Physical Length: $\ell_t = \frac{v_p}{4 f_0} = \frac{1.979 \times 10^8}{4 \times 2.25 \times 10^9} = 22.0\text{ mm}$.
5. **Show the Before vs After Comparison Plots:**
   - **At $f_0 = 2.25\text{ GHz}$:** Show that VSWR drops from $2.40$ (red dashed line) to exactly $1.000$ (blue solid curve), and Return Loss reaches $\infty\text{ dB}$.
   - **Bandwidth Demonstration:** Point out the metric card showing the contiguous usable bandwidth where $\text{RL} \ge 20\text{ dB}$ ($498.7\text{ MHz}$). Explain that quarter-wave transformers are inherently narrow-band matching networks.
6. **Negative Test (Robustness):** Switch sidebar scenario to "Custom Complex Load" ($75 + j35\,\Omega$) and return to View 6. Show the professor that the application refuses to synthesize an invalid quarter-wave transformer for complex loads and displays an educational warning explaining that complex loads require stub matching.

---

## 6. How to Demonstrate the Validation Laboratory (View 7)

1. Select **View 7: Independent Validation Lab**.
2. Click the button: **`🚀 Run Live Monte Carlo Validation Test (N = 120 Trials)`**.
3. **Walk through the generated results:**
   - **Contract Confusion Matrix ($5 \times 5$):** Show $100\%$ accuracy across the 4 generated target classes (`healthy`, `open`, `short`, `mismatch`; 120/120 samples). Point out frankly to the professor that the evaluation suite generates scenarios from the 6 canonical classes only, so no true unknown cases are included (support = 0 for `unknown`); thus unknown-class rejection remains unvalidated in this test cohort.
   - **Physical Subtype Confusion Matrix ($6 \times 6$):** Show that the classifier accurately resolves intermediate series inductors and shunt capacitors based solely on their reflection signatures.
   - **Fault Location Metrics:** Show the reported MAE ($\approx 0.22\text{ cm}$) and RMSE ($\approx 0.28\text{ cm}$) on simulated reflection data.
4. **Reference the Standalone Batch Validation:**
   - Explain to the professor that a larger standalone batch evaluation with $N = 240$ randomized trials ($40$ per scenario) was executed via `validation/run_validation.py`, achieving $99.58\%$ overall accuracy and generating permanent CSV records in `results/csv/`.
   - Explain the **Noise Sensitivity Study**: Point out that `results/csv/noise_sensitivity.csv` records scalar classification accuracy across discrete noise levels $\sigma \in \{0.0, 0.02, 0.05, 0.08, 0.12, 0.18\}$. Report that observed accuracy drops to $50.0\%$ under higher noise ($\sigma \ge 0.08$). Clarify that while $50\%$ numerically coincides with the proportion of mismatch-mapped cases ($60/120 = 50\%$), the exported CSV logs overall accuracy only (not per-class predictions or confusion matrices for each noise level), so this $50\%$ figure is presented strictly as the empirical overall accuracy under strong noise rather than asserted as proof of a majority-class predictor mode.

---

## 7. How to Acknowledge Academic Limitations Frankly

To ensure maximum academic credibility, conclude the demonstration by highlighting the documented simulation boundaries:
1. **Lossless Line Assumption ($\alpha = 0$):** We deliberately chose a lossless model to keep the mathematics transparent for EC-3104; line attenuation and dielectric dispersion are documented extensions.
2. **Single-Port Reflection Only:** All classification and location algorithms operate strictly on $S_{11}(\omega)$ without peeking at simulation ground truth.
3. **Single Dominant Reflector:** The distance estimation algorithms assume a single primary reflector along the line.
4. **Educational Prototype:** We do not claim this software is a physical VNA hardware instrument; it is an academic simulation tool designed for controlled classroom experimentation.
