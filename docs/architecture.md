# Architecture & Module Specifications — RF LINE DOCTOR

## 1. System Architecture & Design Principles

**RF LINE DOCTOR** is designed according to three core software engineering principles:
1. **Separation of Simulation Ground Truth vs Inferred Diagnosis:** The diagnosis and localization engines receive only measured frequency sweep data ($S_{11}$, frequency array, and line characteristic impedance $Z_0$). They never access internal scenario metadata, true load values, or physical fault positions.
2. **Strict Preservation of Frozen Interface Contracts:** All function signatures, parameter names, argument ordering, and return dictionaries defined in `INTERFACES.md` are frozen and non-negotiable.
3. **Dual-Layer Diagnostic Architecture:** The public contract return string strictly adheres to one of five frozen labels (`"healthy"`, `"open"`, `"short"`, `"mismatch"`, `"unknown"`), while providing rich diagnostic metadata (`subtype`, `confidence`, `features`, `explanation`, `rules_fired`) for academic presentation.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        line_model.py (Member 1)                        │
│   • wavelength(f, vf=1.0)              • phase_constant(f, vf=1.0)     │
│   • load_reflection(Z0, ZL)            • reflection_at_distance(...)   │
│   • input_impedance(Z0, ZL, beta, l)   • input_impedance_at_freq(...)  │
│   • quarter_wave_zin(Z0, ZL)           • quarter_wave_impedance(...)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
         ┌──────────────────────────┴──────────────────────────┐
         ▼                                                     ▼
┌──────────────────────────────────┐      ┌──────────────────────────────────┐
│    measurements.py (Member 2)    │      │  diagnosis.py / matching.py (M3) │
│ • reflection_coefficient(Z, Z0)  │      │ • classify(sweep_dict, Z0)       │
│ • vswr(gamma)                    │      │ • estimate_distance(sweep, vf, c)│
│ • return_loss_db(gamma)          │      │ • design_quarter_wave(Z0, RL, ..)│
│ • sweep(Z0, ZL, length, f_arr,vf)│      │ • compare_matching(Z0, ZL, ...)  │
│ • smith_plot(gamma_arr, ax, **kw)│      └────────────────┬─────────────────┘
└────────────────┬─────────────────┘                       │
                 └──────────────────┬──────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                            app.py (Member 4)                           │
│ • Streamlit Web Dashboard: Inputs (Z0, ZL, length, f_range, vf, fault) │
│ • S11, VSWR, Return Loss sweeps, Smith Chart, Diagnosis & Matching      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Directory Layout

```
line-model/
├── app.py                      # Streamlit interactive application (Member 4)
├── line_model.py               # Core electromagnetic model (Member 1)
├── measurements.py             # Measurement helpers & Smith chart (Member 2)
├── diagnosis.py                # Rule-based classifier & IFFT TDR locator (Member 3)
├── matching.py                 # Quarter-wave transformer matching studio (Member 3)
├── fault_simulation.py         # Dedicated 6-scenario fault simulation engine
│
├── core/                       # Internal algorithm modules
│   ├── __init__.py
│   ├── signal_analysis.py      # Spectral features, impedance decomposition, noise
│   ├── fault_location.py       # IFFT TDR & phase slope cross-check
│   ├── fault_simulator.py      # Cascaded 2-port ABCD fault simulation
│   └── diagnostic_explanations.py # Physics explanation & corrective actions
│
├── validation/                 # Experimental validation framework
│   ├── __init__.py
│   ├── classification_metrics.py # Confusion matrix, precision, recall, F1
│   ├── location_metrics.py     # MAE, RMSE, location error curves
│   └── run_validation.py       # Automated Monte Carlo experiment runner
│
├── tests/                      # Automated Pytest suite (176 passing tests)
│   ├── __init__.py
│   ├── conftest.py             # Fixtures, path setup, non-interactive matplotlib backend
│   ├── analytical_benchmarks.py # Independent closed-form textbook models
│   ├── test_app.py             # Streamlit headless integration tests
│   ├── test_benchmarks.py      # 10 canonical benchmark suites
│   ├── test_classification_labels.py # Verification of all 5 frozen labels & extreme loads
│   ├── test_consistency.py     # Cross-coupling & bidirectional consistency tests
│   ├── test_data_alignment_and_plotting.py # Sweep array alignment & Smith chart integrity
│   ├── test_diagnosis.py       # Fault diagnosis, open/short separation & TDR
│   ├── test_fault_simulation.py# 6 scenarios & ABCD cascading tests
│   ├── test_integration.py     # Hand-calculation integration benchmarks
│   ├── test_line_model.py      # Core physics, RLGC equations, branch cuts, skin effect
│   ├── test_location.py        # Dual-method fault location & resolution metrics
│   ├── test_matching.py        # Quarter-wave matching & passband bandwidth
│   ├── test_measurements.py    # Reflection, VSWR numerical tolerance, return loss, SweepResult
│   ├── test_numerical_edge_cases.py # Edge cases, negative inputs, NaNs, division-by-zero
│   ├── test_qucs_cross_validation.py # Qucsator circuit simulator cross-validation
│   ├── test_regressions.py     # Interface compliance & contract regression tests
│   └── test_validation.py      # Statistical metrics (confusion matrix, MAE/RMSE)
│
├── results/                    # Validation outputs (Real experimental data)
│   ├── csv/                    # Confusion matrix, classification metrics, location errors, challenge results
│   └── figures/                # Publication-quality PNG plots & heatmaps
│
├── Qucs_Cross_Validation/      # Independent circuit simulator cross-validation
│   ├── run_qucs_cross_validation.py
│   ├── qucs_mismatch.sch       # Native schematic
│   ├── qucs_mismatch.net       # Native netlist
│   ├── qucs_mismatch.s1p       # Standard Touchstone S-parameter file
│   ├── comparison_table.csv    # 201-point comparative verification data
│   └── Qucs_Cross_Validation_Report.md
│
├── .github/
│   └── workflows/
│       └── tests.yml           # GitHub Actions CI matrix (Python 3.10-3.13)
│
├── .streamlit/
│   └── config.toml             # Streamlit server & theme configuration
│
├── docs/                       # Technical documentation suite
│   ├── theory.md               # Mathematical foundations & derivations
│   ├── architecture.md         # Architecture, interface contracts & data flow
│   ├── validation.md           # Empirical validation report & error analysis
│   ├── assumption_register.md  # Comprehensive model assumption register
│   ├── equation_traceability.md# Mathematical equation traceability matrix
│   ├── technical_decisions.md  # Architectural design record
│   ├── deployment.md           # Streamlit Community Cloud & local deployment guide
│   └── final_software_verification_report.md # Final software verification report
│
├── figures/                    # Reproducible demonstration figures
├── reproducible_examples.py    # End-to-end demonstration & verification script
├── INTERFACES.md               # Frozen team contract
├── HAND_CALCULATIONS.md        # Canonical hand-calculation benchmarks
├── FINAL_QA_REPORT.md          # Comprehensive quality assurance audit report
├── TECHNICAL_DOCUMENTATION.md  # 585-line academic reference manual
├── TESTING.md                  # Detailed testing guide and benchmark tolerances
├── requirements.txt            # Python dependencies
└── .gitignore                  # Git ignore rules
```

---

## 3. Module Interface Contracts

### 3.1 `line_model.py` (Member 1)
- `wavelength(f, vf=1.0) -> float`
- `phase_constant(f, vf=1.0) -> float`
- `load_reflection(Z0, ZL) -> complex` (Handles `ZL = np.inf` $\to +1.0 + 0j$)
- `reflection_at_distance(Z0, ZL, beta, d) -> complex`
- `input_impedance(Z0, ZL, beta, length) -> complex` (Singularities return `np.inf`)
- `input_impedance_at_freq(Z0, ZL, f, length, vf=1.0) -> complex`
- `quarter_wave_zin(Z0, ZL) -> complex`
- `quarter_wave_impedance(Zline, R_load) -> float`

### 3.2 `measurements.py` (Member 2)
- `reflection_coefficient(Z, Z0) -> complex`
- `vswr(gamma) -> float` (Returns `np.inf` when $|\Gamma| \ge 1.0$)
- `return_loss_db(gamma) -> float` (Returns `np.inf` when $\Gamma = 0$)
- `sweep(Z0, ZL, length, f_array, vf=1.0) -> dict`
  - Keys: `'f'`, `'zin'`, `'gamma'`, `'vswr'`, `'rl_db'`
- `smith_plot(gamma_array, ax=None, **kw) -> matplotlib.axes.Axes`

### 3.3 `matching.py` (Member 3)
- `design_quarter_wave(Z0, RL, f, vf=1.0) -> dict`
  - Keys: `'Zt'`, `'length_m'`
- `compare_matching(Z0, ZL, f_array, vf=1.0, f_design=None, rl_threshold=20.0) -> dict`
  - Keys: `'before'`, `'after'`, `'Zt'`, `'length_m'`, `'f_design'`, `'bandwidth_hz'`, `'rl_threshold'`, `'at_f_design'`

### 3.4 `diagnosis.py` (Member 3)
- `classify(sweep_dict, Z0) -> DiagnosisResult (str)`
  - Returns strictly one of: `"healthy"`, `"open"`, `"short"`, `"mismatch"`, `"unknown"`
- `estimate_distance(sweep_dict, vf, fault_class) -> float | None`
  - Returns distance in metres, or `None` if `fault_class == "healthy"` or undetectable.
