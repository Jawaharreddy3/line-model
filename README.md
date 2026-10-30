# RF LINE DOCTOR

An autonomous virtual diagnostics and impedance matching system for RF and microwave transmission lines.

---

## 1. Overview

**RF LINE DOCTOR** provides a modular, production-grade simulation, diagnostics, and matching platform for RF transmission lines based on classical electromagnetic theory.

- **Authoritative Physical Model:** Lossless uniform transmission lines ($e^{j\omega t}$ convention), closed-form input impedance, and cascaded 2-port ABCD matrix formulations.
- **Six Canonical Fault Scenarios:**
  1. `healthy`: Perfectly matched line ($Z_L = Z_0$).
  2. `mismatch`: Pure resistive mismatch ($Z_L = R_L \ne Z_0$).
  3. `open`: Open-circuit termination ($Z_L = \infty$).
  4. `short`: Short-circuit termination ($Z_L = 0$).
  5. `series_L`: Intermediate series inductive discontinuity ($Z_s = j\omega L$) at distance $d$.
  6. `shunt_C`: Intermediate shunt capacitive discontinuity ($Y_p = j\omega C$) at distance $d$.
- **Rule-Based Single-Port Classifier:** Diagnostic classifier operating solely on single-port reflection data ($S_{11}$, frequency, $Z_0$) without peeking at ground truth. Maps strictly to 5 frozen contract labels (`healthy`, `open`, `short`, `mismatch`, `unknown`) while carrying rich internal subtype details.
- **IFFT Pseudo-Time Reflectometry (TDR):** Hann-windowed, zero-padded inverse FFT reflectometry detecting physical fault position with millimeter precision and validating frequency grid uniformity.
- **Quarter-Wave Matching Studio:** Exact synthesis of quarter-wave transformers ($Z_t = \sqrt{Z_0 R_L}$) with exact cancellation at design frequency $f_0$ ($\text{VSWR}=1.0, \text{RL}=\infty$) and passband evaluation ($\text{RL} \ge 20\text{ dB}$).
- **Interactive Streamlit Web Dashboard:** Full GUI featuring live Smith charts, multi-parameter sweeps, fault injection, and matching comparison.

---

## 2. Repository Layout & Interface Architecture

All module interfaces adhere strictly to the frozen contract in [`INTERFACES.md`](INTERFACES.md):

```
line-model/
├── line_model.py            # Core lossless transmission-line model (Member 1)
├── measurements.py          # Reflection coeff, VSWR, return loss, sweeps & Smith charts (Member 2)
├── fault_simulation.py      # 6 canonical fault scenarios & cascaded ABCD modeling
├── diagnosis.py             # Rule-based fault classifier & IFFT distance localization (Member 3)
├── matching.py              # Quarter-wave transformer design & bandwidth evaluator (Member 3)
├── app.py                   # Streamlit web dashboard (Member 4)
├── reproducible_examples.py # Script generating publication figures (F1-F4) & terminal report
├── INTERFACES.md            # Frozen team interface contract (27 Oct 2026)
├── HAND_CALCULATIONS.md     # 7 analytical verification benchmarks
├── PROGRESS.md              # Long-running recovery and milestone log
├── IMPLEMENTATION_STATUS.md # Live interface compliance matrix
├── TECHNICAL_DECISIONS.md   # Architectural design and singularity handling record
├── tests/
│   ├── test_line_model.py       # Core physics and boundary condition tests (27 tests)
│   ├── test_measurements.py     # Measurement functions and array broadcasting (9 tests)
│   ├── test_fault_simulation.py # Discontinuity cascading & scenario tests (10 tests)
│   ├── test_matching.py         # Quarter-wave matching and bandwidth tests (6 tests)
│   ├── test_diagnosis.py        # Fault classification & IFFT TDR tests (10 tests)
│   ├── test_app.py              # Streamlit headless integration tests (2 tests)
│   └── test_integration.py      # End-to-end hand-calculation benchmark suite (8 tests)
└── figures/                 # Generated publication-quality figures
    ├── 1_scenario_sweeps.png
    ├── 2_smith_chart_overlay.png
    ├── 3_matching_before_after.png
    └── 4_tdr_localization.png
```

---

## 3. Quick Start

### Run the Complete Test Suite
```bash
python -m pytest -v
```
*(All 72 tests pass in < 3 seconds)*

### Run End-to-End Verification & Generate Publication Figures
```bash
python reproducible_examples.py
```

### Launch the Interactive Web Dashboard
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

## 4. Verification Against Hand Calculations (`HAND_CALCULATIONS.md`)

All 7 analytical scenarios from `HAND_CALCULATIONS.md` ($Z_0 = 50\,\Omega, f = 100\text{ MHz}, \text{vf} = 1.0$) are automated in the test suite:

1. **Matched Line ($Z_L = 50\,\Omega$):** $\Gamma_L = 0, Z_{\text{in}} = 50\,\Omega$ for any length.
2. **Short Circuit at $\lambda/8$:** $Z_{\text{in}} = +j50\,\Omega$ (purely inductive).
3. **Open Circuit at $\lambda/8$:** $Z_{\text{in}} = -j50\,\Omega$ (purely capacitive).
4. **Quarter-Wave Line ($Z_L = 100\,\Omega$):** $Z_{\text{in}} = 25\,\Omega, |\Gamma_L| = 1/3, \text{VSWR} = 2.0, \text{RL} = 9.542\text{ dB}$.
5. **Half-Wave Line ($Z_L = 30 + j40\,\Omega$):** $Z_{\text{in}} = Z_L$ (repeats every $\lambda/2$).
6. **Quarter-Wave Transformer ($50 \to 200\,\Omega$):** $Z_t = \sqrt{50 \times 200} = 100\,\Omega, l_t = 0.75\text{ m}$.
7. **Singular Cases:** Short at $\lambda/4 \implies Z_{\text{in}} = \infty$; Open at $\lambda/4 \implies Z_{\text{in}} = 0$.

---

## 5. Theory & Core Equations

### Transmission Line Core Equations
- **Phase Velocity:** $v_p = \text{vf} \cdot c_0$
- **Wavelength & Phase Constant:** $\lambda = \frac{v_p}{f}, \quad \beta = \frac{2\pi}{\lambda}$
- **Input Impedance:**
  $$Z_{\text{in}} = Z_0 \frac{1 + \Gamma(l)}{1 - \Gamma(l)}, \quad \Gamma(l) = \Gamma_L e^{-2j\beta l}$$
- **Reflection Coefficient & Metrics:**
  $$\Gamma = \frac{Z - Z_0}{Z + Z_0}, \quad \text{VSWR} = \frac{1 + |\Gamma|}{1 - |\Gamma|}, \quad \text{RL} = -20 \log_{10}(|\Gamma|)$$

### Time Domain Reflectometry (TDR) via IFFT
- **Range Resolution:** $\Delta R = \frac{v_p}{2 B}$, where $B = f_{\text{max}} - f_{\text{min}}$.
- **Unambiguous Range:** $R_{\text{max}} = \frac{v_p}{2 \Delta f}$.
- **Fault Distance:** $d = \frac{v_p \cdot t_{\text{peak}}}{2}$.

### Quarter-Wave Impedance Matching
- **Characteristic Impedance:** $Z_t = \sqrt{Z_0 R_L}$
- **Physical Length:** $l_t = \frac{\lambda_t}{4} = \frac{v_p}{4 f_0}$
- **Passband:** Contiguous frequency band where $\text{RL} \ge 20\text{ dB}$ ($\text{VSWR} \le 1.222$).
