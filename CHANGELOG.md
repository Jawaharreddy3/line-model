# Changelog — RF LINE DOCTOR

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.2.2] - 2026-11-14

### Changed
- **Right-Side Navigation Sidebar Layout:**
  - Repositioned the entire Streamlit navigation sidebar to the **right edge of the screen** on desktop views (`flex-direction: row-reverse !important` on `stAppViewContainer`), with main application content on the left.
  - Preserved full sidebar height, vertical alignment, width, typography, light theme (`#f8fafc` background, `#e2e8f0` left border), and clean zero-emoji styling.
  - Maintained the top "RF Line Doctor" title, subtitle, and all 5 navigation radio options in strict vertical order: Simulation, Diagnosis, Fault Location, Impedance Matching, Results.
  - Positioned the sidebar collapse/expand controls on the top-right corner with flipped chevron indicators matching right-side collapse behavior.
  - Added dedicated regression test `test_right_sidebar_layout_styling` verifying right-side layout rules, expanding automated test suite to 183 passed tests.

---

## [2.2.1] - 2026-11-14

### Fixed
- **Simulation Metric Cards Responsiveness & Typography:**
  - Replaced rigid 6-column layout with a fully responsive CSS Grid (`.metrics-grid`), rendering 6 columns on ultra-wide desktop screens (> 1380px), 3 columns on standard laptops/desktops (769px–1380px), 2 columns on tablets (481px–768px), and 1 column on mobile (<= 480px).
  - Enforced `word-break: normal !important; overflow-wrap: normal !important; hyphens: none !important;` to eliminate awkward word splitting (e.g. "inductanc / e") and character fragmentation.
  - Implemented modular, reusable helper functions `render_metric_card` and `render_metrics_grid`.
  - Standardized visual hierarchy: medium-weight labels (~15px), prominent bold metric values (~26px), and supporting text (~14px).
  - Fixed complex impedance formatting for negative reactance values (`R - jX` instead of `R + j-X`).
  - Added dedicated regression test `test_metric_cards_rendering_and_styling`, expanding test suite to 182 passed tests.

---

## [2.2.0] - 2026-11-14

### Changed
- **Complete Website Simplification & UI Redesign:** Redesigned the Streamlit application from a theory-heavy academic interface into a streamlined, results-focused 5-page simulation tool:
  - Page 1: **Simulation** (Primary interactive workspace with 6 physical conditions, conditional inputs, 6 key metric cards, 5 publication-ready plots including Smith chart).
  - Page 2: **Diagnosis** (Plain-language fault classification preserving all 5 public labels, subtype, confidence, measured evidence, and actionable troubleshooting steps).
  - Page 3: **Fault Location** (Physical TDR localization showing estimated distance, range resolution, unambiguous range, and impulse reflection profile).
  - Page 4: **Impedance Matching** (Practical quarter-wave transformer design with design frequency optimization, bandwidth calculations, and before/after comparison plots).
  - Page 5: **Results** (Searchable and sortable numerical table with CSV export and simulation parameters summary).
- **Zero-Emoji Policy:** Completely removed all emojis, decorative symbols, animated badges, and all-caps styling from the UI, buttons, alerts, and navigation.
- **Clean Light Theme:** Configured a modern, light interface (`#ffffff` / `#f8fafc` background, dark slate `#0f172a` text, subtle `#e2e8f0` borders) in `.streamlit/config.toml` and custom CSS.
- **Test Suite Expansion:** Expanded automated regression suite to 181 tests (including 14 comprehensive Streamlit headless AppTests and zero-emoji verification).

---

## [2.1.0] - 2026-11-14

### Added
- **Dedicated Abstention Challenge Suite:** Integrated a 70-case unclassifiable test suite across 7 categories (U1–U7) evaluating classifier abstention (`unknown`) with 98.57% recall.
- **GitHub Actions Continuous Integration:** Created `.github/workflows/tests.yml` with multi-version Python matrix testing (Python 3.10, 3.11, 3.12, 3.13) on `ubuntu-latest`.
- **Extreme Finite Mismatch Validation:** Added dedicated unit tests for extreme loads ($500\,\Omega, 5\,\Omega, 1000\,\Omega, 2.5\,\Omega, 2000\,\Omega, 1.25\,\Omega$).
- **Deployment Operations Guide:** Added `docs/deployment.md` covering Streamlit Community Cloud and Docker containerization.
- **Documentation Synchronizations:** Created `docs/technical_decisions.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, and `FINAL_QA_REPORT.md`.

### Fixed
- **VSWR Numerical Tolerance:** Fixed `np.isclose` comparison in `measurements.py` by explicitly controlling `rtol=1e-12, atol=1e-12`, preventing false infinite VSWR on reflections slightly below unity ($|\Gamma| = 0.99999$).
- **Extreme Finite Mismatch Separation:** Raised near-total reflection threshold in `diagnosis.py` to $\text{mean}(|\Gamma|) \ge 0.975$ with phase intercept and de-embedded real reflection confirmation, eliminating false `open` and `short` misclassifications on extreme resistive mismatches.
- **Qucsator Portability:** Replaced machine-specific hardcoded paths in `Qucs_Cross_Validation/run_qucs_cross_validation.py` with dynamic executable discovery and reference dataset fallback.

---

## [2.0.0] - 2026-11-13

### Added
- **Professional Scientific UI Redesign:** Replaced student dashboard aesthetics with dark-theme scientific styling (`#00d4aa` primary teal, `#07090f` background, `#0d131f` card surfaces).
- **Dual-Method Fault Localization:** Hann-windowed zero-padded IFFT pseudo-TDR combined with linear unwrapped phase-slope reflectometry.
- **Quarter-Wave Impedance Matching Studio:** Automated Pozar $\lambda/4$ transformer synthesis with before-and-after frequency sweep comparisons and 20 dB contiguous passband evaluation.
- **Smith Chart Visualization:** Interactive polar Smith charts rendered via Matplotlib with constant resistance circles and reactance arcs.
- **Independent Qucs-S Cross-Validation:** Touchstone S11 verification against native Qucsator simulation kernel confirming $|\Delta S_{11}| < 8.23 \times 10^{-14}$.

### Changed
- **Test Suite Modernization:** Reorganized tests into dedicated `tests/` directory with 169 passing test cases and zero warnings.
- **Unclipped Noise Modeling:** Replaced artificial $|\Gamma| \le 1.0$ clipping with realistic unclipped complex Gaussian noise and non-passive NaN VSWR handling.

---

## [1.0.0] - 2026-10-27

### Added
- Initial implementation of lossless and lossy Telegrapher transmission-line models (`line_model.py`).
- Frequency sweep calculations: complex $S_{11}$, VSWR, return loss, and input impedance (`measurements.py`).
- 6 canonical physical fault simulation scenarios (`fault_simulation.py`).
- 5-class rule-based diagnostic engine (`diagnosis.py`).
- Initial Streamlit user interface (`app.py`).
- Baseline frozen interface contracts (`INTERFACES.md`).
