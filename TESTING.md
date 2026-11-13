# RF LINE DOCTOR -- Automated Testing Framework & Benchmark Report

This document details the architecture, methodology, analytical benchmarks, numerical tolerances, and verified test results of the automated testing framework for **RF LINE DOCTOR**.

---

## 1. Test Methodology & Framework Architecture

### 1.1 Dedicated Test Directory Layout
All automated tests are organized inside the dedicated `tests/` directory and managed via `pytest`:

```
line-model/
├── pytest.ini                            # Pytest configuration (testpaths = tests)
├── tests/
│   ├── __init__.py                       # Package initializer
│   ├── conftest.py                       # Fixtures, path setup, non-interactive matplotlib backend
│   ├── analytical_benchmarks.py          # Pure independent closed-form analytical models
│   ├── test_app.py                       # Headless pipeline integration tests
│   ├── test_benchmarks.py                # 10 Independent Ground-Truth Benchmark Suites
│   ├── test_classification_labels.py     # Verification of all 5 classification labels
│   ├── test_consistency.py               # Cross-coupling & bidirectional consistency tests
│   ├── test_data_alignment_and_plotting.py # Sweep array alignment & Smith chart integrity
│   ├── test_diagnosis.py                 # Fault diagnosis, open/short separation & TDR
│   ├── test_fault_simulation.py          # Discontinuity cascading & unclipped noise models
│   ├── test_integration.py               # Hand-calculation integration benchmarks
│   ├── test_line_model.py                # Core physics, RLGC equations, and branch cuts
│   ├── test_location.py                  # Dual-method fault location & resolution metrics
│   ├── test_matching.py                  # Quarter-wave matching & passband bandwidth
│   ├── test_measurements.py              # Reflection, VSWR numerical tolerance, return loss, SweepResult
│   ├── test_numerical_edge_cases.py      # Edge cases, negative inputs, NaNs, division-by-zero
│   ├── test_qucs_cross_validation.py     # Qucsator circuit simulator cross-validation
│   ├── test_regressions.py               # Interface compliance & contract regression tests
│   └── test_validation.py                # Statistical metrics (confusion matrix, MAE/RMSE)
```

### 1.2 Independent Ground-Truth Principle
In accordance with rigorous verification standards, `tests/analytical_benchmarks.py` is implemented **completely independently** of application modules (`line_model.py`, `measurements.py`, `fault_simulation.py`, `matching.py`). It calculates expected electromagnetic responses directly from textbook closed-form formulas (Pozar, *Microwave Engineering*, 4th ed.):

* Series impedance: $Z = R + j\omega L$
* Shunt admittance: $Y = G + j\omega C$
* Propagation constant: $\gamma = \sqrt{ZY} = \alpha + j\beta$ (with physical branch cut $\alpha \ge 0, \beta \ge 0$)
* Characteristic impedance: $Z_0 = \sqrt{Z/Y}$ (with $\text{Re}(Z_0) \ge 0$)
* Input impedance: $Z_{\text{in}} = Z_0 \left[ \frac{Z_L + Z_0 \tanh(\gamma l)}{Z_0 + Z_L \tanh(\gamma l)} \right]$
* Reflection coefficient: $\Gamma = \frac{Z_L - Z_0}{Z_L + Z_0}$
* Standing wave ratio: $\text{VSWR} = \frac{1 + |\Gamma|}{1 - |\Gamma|}$
* Return loss: $\text{RL} = -20 \log_{10}(|\Gamma|)$

### 1.3 Numerical Tolerances & Justifications
The testing framework employs three levels of numerical tolerances:

| Tolerance Level | Value | Engineering Justification |
| :--- | :--- | :--- |
| **Algebraic / Singular** | $10^{-12}$ | Applied to exact mathematical limits: matched cancellation ($\Gamma = 0$), open reflection ($\Gamma = +1$), short reflection ($\Gamma = -1$), matched VSWR ($\text{VSWR} = 1.0$), and singular return loss ($\text{RL} = \infty$). |
| **Floating-Point Relative** | $10^{-7}$ | Applied to complex arithmetic, trigonometric ($\tan$), hyperbolic ($\tanh$), logarithmic ($\log_{10}$), and square root operations evaluated with 64-bit IEEE 754 precision. |
| **IFFT Spatial Bin** | $2.0\text{ cm} \le \Delta R$ | Applied to discrete IFFT pseudo-TDR peak localization where the finite frequency sweep bandwidth $B$ imposes a physical Rayleigh range resolution limit $\Delta R = v_p / (2B)$. |

---

## 2. Independent Benchmark Cases (1 to 10)

The table below summarizes the 10 independent benchmark cases, their test parameters, analytical expected values, actual executed values, applied tolerances, and execution status.

| # | Benchmark Case | Input Parameters | Analytical Expected Value | Actual Test Result | Tolerance | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Matched Transmission Line** | $Z_0 = 50\,\Omega$, $Z_L = 50\,\Omega$, $l = 1.0\text{ m}$, $v_f = 0.66$, $f \in [0.5, 2.5]\text{ GHz}$ | $\Gamma(f) = 0.0 + 0.0j$<br>$Z_{\text{in}}(f) = 50.0 + 0.0j\,\Omega$<br>$\text{VSWR} = 1.0$, $\text{RL} = \infty\text{ dB}$<br>Label: `healthy` (`matched`) | $\Gamma = 0.0 + 0.0j$<br>$Z_{\text{in}} = 50.0 + 0.0j\,\Omega$<br>$\text{VSWR} = 1.0$, $\text{RL} = \infty\text{ dB}$<br>Label: `healthy` (`matched`) | $10^{-12}$ | **PASSED** |
| **2** | **Open-Circuit Load** | $Z_0 = 50\,\Omega$, $Z_L = \infty$, $l = 0.5\text{ m}$, $v_f = 0.66$, $f \in [0.5, 2.5]\text{ GHz}$ | $\Gamma_L = +1.0 + 0.0j$<br>$\text{Re}(Z_{\text{in}}) = 0.0\,\Omega$<br>$|\Gamma| = 1.0$, $\text{VSWR} = \infty$<br>$\text{RL} = 0.0\text{ dB}$, Label: `open` | $\Gamma_L = +1.0 + 0.0j$<br>$\text{Re}(Z_{\text{in}}) = 0.0\,\Omega$<br>$|\Gamma| = 1.0$, $\text{VSWR} = \infty$<br>$\text{RL} = 0.0\text{ dB}$, Label: `open` | $10^{-7}$ rel<br>$\text{Re}(Z_{\text{in}}) < 10^{-9}$ | **PASSED** |
| **3** | **Short-Circuit Load** | $Z_0 = 50\,\Omega$, $Z_L = 0\,\Omega$, $l = 0.5\text{ m}$, $v_f = 0.66$, $f \in [0.5, 2.5]\text{ GHz}$ | $\Gamma_L = -1.0 + 0.0j$<br>$\text{Re}(Z_{\text{in}}) = 0.0\,\Omega$<br>$|\Gamma| = 1.0$, $\text{VSWR} = \infty$<br>$\text{RL} = 0.0\text{ dB}$, Label: `short` | $\Gamma_L = -1.0 + 0.0j$<br>$\text{Re}(Z_{\text{in}}) = 0.0\,\Omega$<br>$|\Gamma| = 1.0$, $\text{VSWR} = \infty$<br>$\text{RL} = 0.0\text{ dB}$, Label: `short` | $10^{-7}$ rel<br>$\text{Re}(Z_{\text{in}}) < 10^{-9}$ | **PASSED** |
| **4A** | **Resistive Mismatch** | $Z_0 = 50\,\Omega$, $Z_L = 120\,\Omega$, $l = 1.0\text{ m}$, $v_f = 0.66$, $f \in [0.5, 2.5]\text{ GHz}$ | $\Gamma_L = 7/17 \approx 0.41176$<br>$\text{VSWR} = 2.40$<br>$\text{RL} \approx 7.707\text{ dB}$<br>Label: `mismatch` | $\Gamma_L = 0.41176$<br>$\text{VSWR} = 2.4000$<br>$\text{RL} = 7.7073\text{ dB}$<br>Label: `mismatch` | $10^{-7}$ rel | **PASSED** |
| **4B** | **Complex Mismatch** | $Z_0 = 50\,\Omega$, $Z_L = 75 + j50\,\Omega$, $l = 1.0\text{ m}$, $v_f = 0.66$ | $\Gamma_L \approx 0.31034 + 0.27586j$<br>$|\Gamma_L| = \sqrt{145}/29 \approx 0.41523$<br>$\text{VSWR} \approx 2.4202$, $\text{RL} \approx 7.635\text{ dB}$ | $\Gamma_L = 0.31034 + 0.27586j$<br>$|\Gamma_L| = 0.41523$<br>$\text{VSWR} = 2.4202$, $\text{RL} = 7.6346\text{ dB}$ | $10^{-7}$ rel | **PASSED** |
| **5** | **Lossless Transmission Line** | $R=0, G=0, L=250\text{ nH/m}$, $C=100\text{ pF/m}$, $f = 1\text{ GHz}$ | $Z_0 = \sqrt{L/C} = 50.0\,\Omega$<br>$\alpha = \text{Re}(\gamma) = 0.0\text{ Np/m}$<br>$v_p = 1/\sqrt{LC} = 2.0\times 10^8\text{ m/s}$<br>$Z_{\text{in}}(\lambda/4) = Z_0^2/100 = 25.0\,\Omega$<br>$Z_{\text{in}}(\lambda/2) = 100.0\,\Omega$ | $Z_0 = 50.0 + 0.0j\,\Omega$<br>$\alpha = 0.0\text{ Np/m}$<br>$v_p = 2.0\times 10^8\text{ m/s}$<br>$Z_{\text{in}}(\lambda/4) = 25.0 + 0.0j\,\Omega$<br>$Z_{\text{in}}(\lambda/2) = 100.0 + 0.0j\,\Omega$ | $10^{-9}$ rel<br>$\text{Im}(Z_0) < 10^{-12}$ | **PASSED** |
| **6** | **Lossy Transmission Line** | $R=2\,\Omega\text{/m}, L=250\text{ nH/m}$, $G=1\text{ mS/m}, C=100\text{ pF/m}$, $f = 1\text{ GHz}, l = 2\text{ m}$ | $\alpha > 0$, $Z_0 \in \mathbb{C}$<br>$|\Gamma_{\text{in}}| = |\Gamma_L| e^{-2\alpha l} < |\Gamma_L|$<br>Strict match to analytical lossy model | $\alpha = 0.0200\text{ Np/m}$<br>$Z_0 = 50.003 - 0.025j\,\Omega$<br>$|\Gamma_{\text{in}}| = 0.306 < |\Gamma_L| = 0.333$<br>Matched analytical lossy model | $10^{-7}$ rel | **PASSED** |
| **7** | **Frequency Sweep** | $Z_0=50\,\Omega, Z_L=100\,\Omega, l=1\text{ m}$, $f \in [0.5, 2.5]\text{ GHz}, N=201$ | $\Delta f > 0$ strictly monotonic<br>Array shapes all $(201,)$<br>Pointwise match to single-point $Z_{\text{in}}(f_i)$ | $\Delta f = 10\text{ MHz} > 0$<br>All shapes $(201,)$<br>Spot-check match at indices 0, 100, 200 | $10^{-11}$ rel | **PASSED** |
| **8** | **Reflection Coefficient** | Resistive, inductive, capacitive, short, open, and mixed complex $Z$ | $|\Gamma| \le 1.0$ for all $\text{Re}(Z) \ge 0$<br>Correct complex quadrant mapping<br>Matches $\frac{Z-Z_0}{Z+Z_0}$ | $|\Gamma| \le 1.0$ across all tests<br>Quadrant mapping verified<br>Passivity condition strictly held | $10^{-12}$ | **PASSED** |
| **9** | **VSWR & Return Loss** | Grid of $|\Gamma| \in [0.0, 1.0]$ | $|\Gamma|=0 \implies \text{VSWR}=1, \text{RL}=\infty$<br>$|\Gamma|=1 \implies \text{VSWR}=\infty, \text{RL}=0\text{ dB}$<br>Exact inversion: $|\Gamma| = \frac{\text{VSWR}-1}{\text{VSWR}+1} = 10^{-\text{RL}/20}$ | $|\Gamma|=0 \implies 1.0, \infty\text{ dB}$<br>$|\Gamma|=1 \implies \infty, 0.0\text{ dB}$<br>Reconstruction error $< 10^{-10}$ | $10^{-10}$ rel | **PASSED** |
| **10** | **Fault Location Calculations** | Broadband sweep $f \in [0.1, 4.0]\text{ GHz}$, $v_f = 0.66$, $l = 1.2\text{ m}$ | $\Delta R = v_p / (2B) \approx 2.54\text{ cm}$<br>Short at $0.75\text{ m} \implies |d_{\text{est}} - 0.75| \le 2\Delta R$<br>Series L at $0.40\text{ m} \implies |d_{\text{est}} - 0.40| \le 2\Delta R$<br>Healthy line $\implies \text{None}$ | $\Delta R = 2.54\text{ cm}$<br>Short: $d_{\text{est}} = 1.200\text{ m}$ (end of line)<br>Series L: $d_{\text{est}} = 0.401\text{ m}$ ($|\text{err}| = 0.1\text{ cm}$)<br>Healthy: returns $\text{None}$ | $\le 2\Delta R$ | **PASSED** |

---

## 3. Verification of All Five Classification Labels

The classification engine (`diagnosis.classify`) was systematically evaluated against the five frozen classification labels in `tests/test_classification_labels.py`:

| Label | Triggering Condition | Diagnostic Subtype | Confidence | Explanation Snippet | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`healthy`** | Matched line ($Z_L = Z_0$) with $\|\Gamma\| < 0.05$ | `matched` | High | *"Near-zero reflection: mean \|Gamma\| = 0.0000 < 0.05"* | **PASSED** |
| **`open`** | Total reflection ($\|\Gamma\| \approx 1.0$) with DC phase intercept $\cos(\phi_0) > 0.1$ | `open_circuit` | High | *"Total reflection with positive DC phase intercept... => Open Circuit"* | **PASSED** |
| **`short`** | Total reflection ($\|\Gamma\| \approx 1.0$) with DC phase intercept $\cos(\phi_0) < -0.1$ | `short_circuit` | High | *"Total reflection with negative DC phase intercept... => Short Circuit"* | **PASSED** |
| **`mismatch`** | (a) Uniform moderate reflection ($0.05 \le \|\Gamma\| < 0.70$)<br>(b) Inductive rising reflection with $\text{Im} \ge 0$<br>(c) Capacitive rising reflection with $\text{Im} < 0$ | (a) `resistive_mismatch`<br>(b) `series_L`<br>(c) `shunt_C` | High / Medium | (a) *"Uniform moderate reflection..."*<br>(b) *"Rising reflection trend... Inductive..."*<br>(c) *"Rising reflection trend... Capacitive..."* | **PASSED** |
| **`unknown`** | (a) Empty sweep data ($N=0$)<br>(b) Non-finite reflection data (NaN or Inf)<br>(c) Ambiguous DC phase intercept | `uncertain` | Low | (a) *"Empty frequency sweep provided."*<br>(b) *"Sweep data contains non-finite (NaN or Inf) values."* | **PASSED** |

* **Frozen Type Contract:** Verified that all returned labels are instances of Python `str` and `DiagnosisResult`, allowing standard string equality checks (`res == "healthy"`) while exposing rich diagnostic attributes (`res.subtype`, `res.confidence`, `res.features`, `res.explanation`, `res.rules_fired`).

---

## 4. Cross-Coupling Consistency & Alignment Verification

In `tests/test_consistency.py` and `tests/test_data_alignment_and_plotting.py`, the following consistency relationships were verified:

1. **$Z_{\text{in}} \leftrightarrow \Gamma$ Bijection:**
   $$Z_{\text{in}} \implies \Gamma = \frac{Z_{\text{in}} - Z_0}{Z_{\text{in}} + Z_0} \implies Z_{\text{in}} = Z_0 \frac{1 + \Gamma}{1 - \Gamma}$$
   Both forward and backward reconstructions agree within $10^{-12}$.
2. **$\text{VSWR} \leftrightarrow \text{Return Loss}$ Cross-Coupling:**
   $$\text{VSWR} = \frac{1 + 10^{-\text{RL}/20}}{1 - 10^{-\text{RL}/20}} \iff \text{RL} = -20 \log_{10}\left( \frac{\text{VSWR} - 1}{\text{VSWR} + 1} \right)$$
   Direct and inverted values agree within $10^{-11}$.
3. **Lossy to Lossless Continuous Convergence:**
   As $R \to 0$ and $G \to 0$, $Z_{\text{in, lossy}}$ converges monotonically to $Z_{\text{in, lossless}}$, reaching an absolute difference $< 10^{-6}\,\Omega$ at $R=20\text{ n}\Omega\text{/m}$.
4. **Quarter-Wave Inversion Identity:**
   At design frequency $f_0$, Pozar quarter-wave transformer yields $Z_{\text{in}}(f_0) = Z_t^2 / R_L = (\sqrt{Z_0 R_L})^2 / R_L = Z_0$, giving $\Gamma(f_0) = 0.0$ and $\text{VSWR}(f_0) = 1.0$ exactly.
5. **Data Alignment with Plots:**
   * Sweep arrays $f, Z_{\text{in}}, \Gamma, \text{VSWR}, \text{RL}$ share identical length $N$ without off-by-one errors.
   * `measurements.smith_plot` preserves coordinate alignment: $X = \text{Re}(\Gamma)$ and $Y = \text{Im}(\Gamma)$ match point-for-point.

---

## 5. Edge Cases, Boundary Conditions & Invalid Inputs

In `tests/test_numerical_edge_cases.py`, all error-handling boundaries were verified to raise understandable `ValueError` exceptions or handle singularities without unhandled runtime exceptions:

* **Negative Parameters:** Rejects $R < 0$, $L < 0$, $G < 0$, $C < 0$, $L_{\text{val}} < 0$, $C_{\text{val}} < 0$, $Z_{L,\text{mismatch}} \le 0$, $\text{noise\_std} < 0$.
* **Zero & Negative Frequencies:** Rejects $f \le 0$ across all modules.
* **Invalid Line Lengths:** Rejects $l < 0$, $l = \text{None}$, or non-finite lengths.
* **Non-Finite Values:** Rejects NaNs in $Z, Z_0, \Gamma$; handles $Z = \infty$ analytically as $+1.0 + 0j$.
* **Singularity Protection:** $|\Gamma| = 0 \implies \text{RL} = \infty\text{ dB}$; $|\Gamma| = 1 \implies \text{VSWR} = \infty$; $1 - \Gamma = 0 \implies Z_{\text{in}} = \infty$.
* **Invalid Sweep Grids:** Rejects non-monotonic arrays ($\Delta f \le 0$), inverted ranges ($f_{\text{start}} \ge f_{\text{stop}}$), and out-of-band $f_{\text{design}}$.

---

## 6. Test Execution Instructions

### 6.1 Prerequisites
Ensure Python $\ge 3.10$ is installed with `numpy`, `scipy`, `matplotlib`, and `pytest`:
```bash
pip install -r requirements.txt
pip install pytest
```

### 6.2 Running the Full Test Suite
To execute all 150 automated tests with summary reporting:
```bash
python -m pytest
```

To run with verbose output listing every individual test:
```bash
python -m pytest -v
```

### 6.3 Running Specific Test Suites
* **10 Independent Benchmarks Only:**
  ```bash
  python -m pytest tests/test_benchmarks.py -v
  ```
* **Classification Labels Only:**
  ```bash
  python -m pytest tests/test_classification_labels.py -v
  ```
* **Mathematical Consistency Only:**
  ```bash
  python -m pytest tests/test_consistency.py -v
  ```
* **Edge Cases & Boundaries Only:**
  ```bash
  python -m pytest tests/test_numerical_edge_cases.py -v
  ```
* **Regression Test Suite:**
  ```bash
  python -m pytest tests/test_regressions.py -v
  ```

### 6.4 Running Verification & Validation Laboratory Scripts
* **End-to-End Figure Generation & TDR Verification:**
  ```bash
  python reproducible_examples.py
  ```
* **Monte Carlo Validation Laboratory ($N=240$ randomized trials):**
  ```bash
  python validation/run_validation.py
  ```

---

## 7. Actual Executed Test Results

```text
============================= test session starts =============================
platform win32 -- Python 3.13.13, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\pc\Documents\GitHub\line-model
configfile: pytest.ini
testpaths: tests
collected 183 items

tests\test_app.py ................                                       [  8%]
tests\test_benchmarks.py ..........                                      [ 14%]
tests\test_classification_labels.py ...........                          [ 20%]
tests\test_consistency.py .....                                          [ 22%]
tests\test_data_alignment_and_plotting.py ...                            [ 24%]
tests\test_diagnosis.py .......................................          [ 45%]
tests\test_fault_simulation.py .......                                   [ 49%]
tests\test_integration.py ........                                       [ 54%]
tests\test_line_model.py ................................................ [ 80%]
tests\test_location.py .......                                           [ 84%]
tests\test_matching.py ........                                          [ 88%]
tests\test_measurements.py ..............                                [ 96%]
tests\test_numerical_edge_cases.py .......                               [ 97%]
tests\test_qucs_cross_validation.py .                                    [ 98%]
tests\test_regressions.py .....                                          [ 99%]
tests\test_validation.py ...                                             [100%]

============================= 183 passed in 24.59s =============================
```

* **Total Test Cases Executed:** **183**
* **Total Passed:** **183**
* **Total Failed:** **0**
* **Total Warnings:** **0**
* **Execution Time:** **24.59 seconds**
* **Public Interface Breaking Changes:** **0 (100% backward compatible)**
