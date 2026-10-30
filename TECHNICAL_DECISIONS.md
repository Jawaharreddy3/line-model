# RF LINE DOCTOR — Technical Decisions & Architecture Record

## 1. Architectural Principles
- **No Overwriting / Preserving Core Model:** `line_model.py` and `test_line_model.py` represent verified baseline physics (Member 1). No signatures, docstrings, or tests will be altered.
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
- VSWR for $|\Gamma| \ge 1$: Evaluates cleanly to `np.inf`.

---

## 3. Time Domain Reflectometry (TDR via IFFT)
- **Windowing:** Hann (Hanning) window applied across frequency points prior to IFFT to suppress spectral leakage sidelobes by $>31\text{ dB}$.
- **Zero-Padding:** Zero-padding by a factor of 8 ($N_{\text{pad}} \ge 2048$) for fine temporal interpolation of peak position.
- **Grid Uniformity Check:** Validate that $\Delta f_i = f_{i+1} - f_i$ is uniform within $10^{-6}$ relative tolerance. If non-uniform, reject or resample onto a uniform linear grid.
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
- **Problem:** `extract_features(sweep_dict, Z0, vf=1.0)` was previously called inside `classify(sweep_dict, Z0)` without passing the actual velocity factor. For lines with $\text{vf} \ne 1.0$ (e.g. RG-58 with $\text{vf}=0.66$), de-embedding phase rotation $\exp(2j\beta d)$ used incorrect phase velocity, corrupting the de-embedded reflection plane.
- **Solution:** Created `SweepResult(dict)` subclass in `measurements.py`. Retains `vf`, `Z0`, and `length` as metadata attributes while maintaining 100% standard dictionary semantics and frozen keys (`f`, `zin`, `gamma`, `vswr`, `rl_db`). `classify` extracts `vf` dynamically via `getattr(sweep_dict, 'vf', sweep_dict.get('vf', 1.0))` and propagates it to `extract_features` and de-embedding. Legacy plain dictionaries remain fully supported with documented fallback to 1.0.

### 5.2 Unclipped Noise Simulation & Physical VSWR Handling
- **Problem:** Measurement noise was previously clipped to $|\Gamma| \le 1.0$, which is unphysical for noisy receiver observations and distorts noise statistics.
- **Solution:** Preserved noisy complex reflection samples even when $|S_{11}| > 1.0$. Separated ideal noiseless response (`gamma_ideal`) from noisy observed response (`gamma`). Because passive-line VSWR is physically undefined for $|S_{11}| > 1.0$, `measurements.vswr()` evaluates non-passive noisy points as `np.nan` rather than throwing exceptions or returning negative numbers. The classifier operates on the unclipped noisy data, and the UI displays explanatory warning banners.

### 5.3 Physics-Based Resolution of Open vs Short Circuit
- **Problem:** At microwave frequencies (e.g. 4 GHz), $\lambda/4 \approx 1.8\text{ cm}$. Any slight discretization error in high-frequency phase de-embedding rotates phase by $\approx 180^\circ$, causing short circuits to be confused with open circuits (previously 18/40 short cases were misclassified as open).
- **Solution:** Evaluated the linear unwrapped phase fit $\phi(f) = \phi_0 + m f$. The intercept at $f \to 0$ ($\phi_0 = \lim_{f \to 0}\angle \Gamma(f)$) represents the reflection angle at DC, where electrical line length $\beta l \to 0$ vanishes completely regardless of line length or frequency:
  $$\cos(\phi_0) = \begin{cases} +1.0 & \text{Open Circuit } (\Gamma_L = +1) \\ -1.0 & \text{Short Circuit } (\Gamma_L = -1) \end{cases}$$
  Corroborated by actual de-embedded real reflection with true $v_p$, this achieved **100% recall** (40/40 open, 40/40 short) with 0 misclassifications.

### 5.4 Contiguous Matching Bandwidth
- **Problem:** `bw_freqs[-1] - bw_freqs[0]` spanned across disconnected harmonic bands if the return loss threshold was met in multiple regions.
- **Solution:** Identified the array index closest to $f_{\text{design}}$ and expanded left and right along contiguous points satisfying $\text{RL} \ge \text{threshold}$. If threshold is not met at $f_0$, bandwidth is reported as $0.0\text{ Hz}$.

### 5.5 Physical Rayleigh Resolution vs Interpolation Bin Spacing
- **Rayleigh Physical Limit:** $\Delta R = \frac{v_p}{2 B}$. Two distinct physical discontinuities separated by $< \Delta R$ merge into a single impulse peak and cannot be resolved.
- **Interpolation Bin Step:** $\delta d = \frac{v_p}{2 N_{\text{pad}} \Delta f}$. Zero-padding interpolates the peak centroid between coarse FFT bins, but does not improve the physical Rayleigh resolution limit $\Delta R$.
- Both metrics and the physical phase-slope bias introduced by reactive discontinuities (series L and shunt C) are explicitly reported in code, validation outputs, and UI.
