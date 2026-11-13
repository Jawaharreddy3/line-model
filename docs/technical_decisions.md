# RF LINE DOCTOR — Technical Decisions & Architecture Record

## 1. Architectural Principles
- **No Overwriting / Preserving Core Model:** `line_model.py` and `test_line_model.py` represent verified baseline physics. No signatures, docstrings, or tests will be altered.
- **Strict Adherence to Contract:** All function signatures and dictionary return keys defined in `INTERFACES.md` are frozen and non-negotiable.
- **Dual-Layer Diagnostic Reporting:** 
  - Public contract: Exactly 5 frozen strings (`"healthy"`, `"open"`, `"short"`, `"mismatch"`, `"unknown"`).
  - Extended metadata: Rich internal attributes (`series_L`, `shunt_C`, `resistive_mismatch`, confidence level, rule activations) are returned in attached diagnostic structures for detailed UI display without altering the public classification string.

---

## 2. Handling Singularities & Open Circuits
- In the reference repository (`Transmission-Line-Fault-Diagnosis`), open circuits were simulated using an artificial finite resistance $Z_L = 10^9\,\Omega$ to prevent division by zero in $\tanh(\gamma l)$.
- In RF LINE DOCTOR, open circuit is mathematically represented by `ZL = np.inf`.
- The input impedance formulation in `line_model.py` maps $Z_L = \infty$ to reflection coefficient $\Gamma_L = +1.0$, evaluating $Z_{\text{in}} = Z_0 \frac{1+\Gamma}{1-\Gamma}$ without numeric overflow.
- `measurements.reflection_coefficient` explicitly checks for infinite load impedance, returning $+1.0 + 0j$.
- Return Loss for $\Gamma = 0$: Evaluates cleanly to `np.inf` using numerical masks to prevent standard `RuntimeWarning: divide by zero encountered in log10`.
- VSWR for $|\Gamma| \ge 1$: Evaluates cleanly to `np.inf` with explicit `rtol=1e-12, atol=1e-12` tolerance control.

---

## 3. Time Domain Reflectometry (TDR via IFFT)
- **Windowing:** Hann (Hanning) window applied across frequency points prior to IFFT to suppress spectral leakage sidelobes by $>31\text{ dB}$.
- **Zero-Padding:** Zero-padding by a factor of 8 ($N_{\text{pad}} \ge 2048$) for fine temporal interpolation of peak position.
- **Grid Uniformity Check:** Validate that $\Delta f_i = f_{i+1} - f_i$ is uniform within $10^{-6}$ relative tolerance. If non-uniform, resample onto a uniform linear grid.
- **Metric Formulation:**
  - Range resolution: $\Delta R = \frac{v_p}{2 B}$, where $B = f_{\text{max}} - f_{\text{min}}$.
  - Unambiguous distance: $R_{\text{max}} = \frac{v_p}{2 \Delta f}$.
  - Peak location: $d_{\text{est}} = \frac{v_p \cdot t_{\text{peak}}}{2}$.

---

## 4. Distinction Between $R_L$ and Return Loss
- **$R_L$:** Load resistance in Ohms ($\Omega$). Real part of termination impedance.
- **$\text{RL}$ / $\text{RL}_{\text{dB}}$:** Return loss in decibels ($\text{dB}$), defined as $-20 \log_{10}(|\Gamma|)$.
- Clear nomenclature maintained throughout code, docstrings, and UI to eliminate any ambiguity.

---

## 5. Post-Build Engineering Audit Refinements

### 5.1 Velocity Factor Propagation
- `extract_features(sweep_dict, Z0, vf=1.0)` is provided the actual line velocity factor $\text{vf}$. `SweepResult(dict)` subclass in `measurements.py` retains `vf`, `Z0`, and `length` as metadata attributes while maintaining 100% dictionary compatibility.

### 5.2 Unclipped Noise Simulation & Physical VSWR Handling
- Measurement noise is modeled as complex zero-mean Gaussian noise without artificial clipping. Passive-line VSWR for noisy non-passive points ($|S_{11}| > 1.0$) evaluates to `np.nan` rather than throwing exceptions or returning invalid negative numbers.

### 5.3 Physics-Based Resolution of Open vs Short Circuit
- Linear unwrapped phase fit $\phi(f) = \phi_0 + m f$ extrapolated to $f \to 0$ ($\phi_0 = \lim_{f \to 0}\angle \Gamma(f)$) yields the DC reflection angle where line rotation $\beta l \to 0$ vanishes completely. Combined with de-embedded real reflection sign, this achieves 100% open vs short disambiguation.

### 5.4 Extreme Finite Mismatch Separation
- Near-total reflection threshold is set to $\text{mean}(|\Gamma|) \ge 0.975$. Finite resistive loads ($500\,\Omega, 5\,\Omega, 1000\,\Omega, 2.5\,\Omega$) have $|\Gamma| \le 0.952$ and are strictly classified as `mismatch` (`resistive_mismatch`), never misclassified as `open` or `short`.

### 5.5 Defensible Abstention Methodology
- The `unknown` label is explicitly treated as an abstention/rejection class for corrupt, out-of-distribution, or insufficient data, verified via a separate 70-case challenge suite across 7 distinct categories (U1–U7).
