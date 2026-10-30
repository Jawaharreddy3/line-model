# RF LINE DOCTOR

An educational virtual transmission-line diagnostics and impedance matching simulator for RF and microwave engineering courses.

---

## 1. Overview

**RF LINE DOCTOR** is an educational virtual prototype for EC-3104 Microwave Engineering. It implements classical transmission-line theory in a simulation-based environment, covering fault diagnosis, fault location estimation, and impedance matching.

- **Authoritative Physical Model:** Lossless uniform transmission lines ($e^{j\omega t}$ convention), closed-form input impedance, and cascaded 2-port ABCD matrix formulations.
- **Six Canonical Fault Scenarios:**
  1. `healthy`: Perfectly matched line ($Z_L = Z_0$).
  2. `mismatch`: Pure resistive mismatch ($Z_L = R_L \ne Z_0$).
  3. `open`: Open-circuit termination ($Z_L = \infty$).
  4. `short`: Short-circuit termination ($Z_L = 0$).
  5. `series_L`: Intermediate series inductive discontinuity ($Z_s = j\omega L$) at distance $d$.
  6. `shunt_C`: Intermediate shunt capacitive discontinuity ($Y_p = j\omega C$) at distance $d$.
- **Rule-Based Single-Port Classifier:** Diagnostic classifier operating solely on single-port reflection data ($S_{11}$, frequency, $Z_0$) without peeking at ground truth. Maps strictly to 5 frozen contract labels (`healthy`, `open`, `short`, `mismatch`, `unknown`) while carrying rich internal subtype details.
- **IFFT TDR Visualisation (Cross-Check):** Hann-windowed, zero-padded inverse FFT reflectometry used as a supporting cross-check of phase-slope distance estimates. Physical resolution depends on sweep bandwidth: ΔR = vp / (2B). Validating frequency grid uniformity before IFFT is applied.
- **Quarter-Wave Matching Studio:** Exact synthesis of quarter-wave transformers ($Z_t = \sqrt{Z_0 R_L}$) with exact cancellation at design frequency $f_0$ ($\text{VSWR}=1.0, \text{RL}=\infty$) and passband evaluation ($\text{RL} \ge 20\text{ dB}$).
- **Interactive Streamlit Web Dashboard:** Full GUI featuring live Smith charts, multi-parameter sweeps, fault injection, and matching comparison.

---

## 2. Repository Layout & Interface Architecture

All module interfaces adhere strictly to the frozen contract in [`INTERFACES.md`](INTERFACES.md):

```
line-model/
├── line_model.py            # Core lossless transmission-line model (Member 1)
├── measurements.py          # Reflection coeff, VSWR, return loss, sweeps, SweepResult & Smith charts (Member 2)
├── fault_simulation.py      # 6 canonical fault scenarios, cascaded ABCD & unclipped noise modeling
├── diagnosis.py             # Rule-based fault classifier, DC phase intercept & IFFT localization (Member 3)
├── matching.py              # Quarter-wave transformer design & contiguous bandwidth evaluator (Member 3)
├── app.py                   # Streamlit web dashboard with 8 dedicated interactive views (Member 4)
├── reproducible_examples.py # Script generating publication figures (F1-F4) & terminal report
├── core/                    # Advanced academic diagnostic & signal processing engine
│   ├── signal_analysis.py   # Spectral feature extraction & S11 metrics
│   ├── fault_location.py    # Dual-method localization (IFFT TDR + Phase Slope)
│   ├── fault_simulator.py   # High-level simulation interface
│   └── diagnostic_explanations.py # Physical failure mode explanations
├── validation/              # Empirical Monte Carlo validation laboratory
│   ├── classification_metrics.py # Confusion matrix, precision, recall, F1
│   ├── location_metrics.py  # MAE, RMSE, maximum error analysis
│   └── run_validation.py    # Automated test runner exporting CSVs & figures
├── results/                 # Empirical validation artifacts
│   ├── csv/                 # confusion_matrix.csv, subtype_confusion_matrix.csv, etc.
│   └── figures/             # Confusion matrices, noise sensitivity, error histograms
├── docs/                    # Architectural and theoretical documentation
├── INTERFACES.md            # Frozen team interface contract (27 Oct 2026)
├── HAND_CALCULATIONS.md     # 7 analytical verification benchmarks
├── PROGRESS.md              # Long-running recovery and milestone log
├── IMPLEMENTATION_STATUS.md # Live interface compliance matrix
├── TECHNICAL_DECISIONS.md   # Architectural design and singularity handling record
└── tests/                   # 102 comprehensive pytest unit and integration tests
    ├── test_line_model.py       # Core physics and boundary condition tests (27 tests)
    ├── test_measurements.py     # Measurement functions, SweepResult, non-passive VSWR (12 tests)
    ├── test_fault_simulation.py # Discontinuity cascading & unclipped noise tests (10 tests)
    ├── test_matching.py         # Quarter-wave matching and contiguous bandwidth tests (7 tests)
    ├── test_diagnosis.py        # Fault classification, open/short separation & IFFT TDR tests (28 tests)
    ├── test_location.py         # Fault location dual-method & range resolution tests (5 tests)
    ├── test_validation.py       # Statistical validation metric tests (3 tests)
    ├── test_app.py              # Streamlit headless integration tests (2 tests)
    └── test_integration.py      # End-to-end hand-calculation benchmark suite (8 tests)
```

---

## 3. Installation & Running Locally from GitHub

You can run RF LINE DOCTOR on your own computer. Each user runs a local copy of the application; it is not necessary for the project owner's computer to stay online.

### Prerequisites

- Python installed on your computer.
- Git installed on your computer.
- An internet connection for the initial clone and dependency installation.

### Step 1 — Clone the project

Open PowerShell (Windows) or a terminal (macOS/Linux) and run:

```bash
git clone -b rf-line-doctor-build --single-branch https://github.com/Jawaharreddy3/line-model.git
```

This downloads the project from the `rf-line-doctor-build` branch.

### Step 2 — Enter the project folder

```bash
cd line-model
```

### Step 3 — Install the required Python packages

```bash
python -m pip install -r requirements.txt
```

### Step 4 — Start the Streamlit application

```bash
python -m streamlit run app.py
```

### Step 5 — Open the local website

Open your browser and visit:

[`http://localhost:8501`](http://localhost:8501)

The RF LINE DOCTOR dashboard will run on your computer. Keep the terminal window open while using it. To stop the application, press `Ctrl + C` in that terminal.

**Important:** `localhost:8501` is local to the computer running the command. Sharing the GitHub repository lets others download and run their own copy; it does not make your local application directly accessible to them.

---

## 4. Quick Start

### Run the Complete Test Suite
```bash
python -m pytest -v
```
*(All 102 tests pass in < 2 seconds with zero failures)*

### Run Automated Validation Laboratory
```bash
python validation/run_validation.py
```
*(Generates empirical CSV reports in `results/csv/` and publication heatmaps in `results/figures/`)*

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

---

## 6. Empirical Validation Results

From the automated Monte Carlo test suite ($N = 240$ randomized lines, complex noise $\sigma = 0.02$):

| Diagnostic Level | Accuracy | Open Recall | Short Recall | Healthy Recall | Mismatch Recall |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **5-Class Public Contract** | **99.58%** | 100.0% | 100.0% | 100.0% | 99.17% |
| **6-Scenario Physical Subtype** | **99.58%** | 100.0% | 100.0% | 100.0% | 100.0% (mismatch & series L) / 97.5% (shunt C) |

- **Fault Location Accuracy:** Mean Absolute Error (MAE) = **0.16 cm** (1.6 mm), RMSE = **0.22 cm**, Max Error = **0.75 cm** across all 200 faulty transmission lines.
- **Physical Resolution vs Interpolation:** Physical Rayleigh resolution limit $\Delta R = v_p / (2B)$ is rigorously reported alongside zero-padded interpolation step $\delta d = v_p / (2 N_{\text{pad}} \Delta f)$.
- **Unclipped Noise Architecture:** Realistic complex Gaussian noise preserved without artificial clipping; non-passive noisy points correctly return NaN for physical VSWR.
- **Physical DC Phase Intercept:** $\phi_0 = \lim_{f \to 0}\angle \Gamma(f)$ eliminates high-frequency phase wrapping ambiguity, achieving 100% separation between open and short circuit terminations.
