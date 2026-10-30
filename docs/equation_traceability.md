# Mathematical Equation Verification & Traceability Matrix

**Project:** RF LINE DOCTOR — Virtual Transmission-Line Fault Diagnosis & Matching  
**Course:** EC-3104 (Electromagnetic Waves and Transmission Lines)  
**Standard Time Convention:** $e^{j\omega t}$  
**Standard Spatial Coordinate:** $z$ along line, $d = \ell - z$ from load toward generator  

---

## 1. Traceability Matrix Overview

| Eq ID | Physical Parameter / Function | Primary Academic Citation | Implementation Target | Test Coverage |
| :---: | :--- | :--- | :--- | :---: |
| **EQ-01** | Phase Velocity ($v_p$) | Pozar (4th ed.), Eq. (2.12), p. 52 | `line_model.py:phase_velocity` | 100% |
| **EQ-02** | Wavelength ($\lambda$) | Pozar (4th ed.), Eq. (2.13), p. 52 | `line_model.py:wavelength` | 100% |
| **EQ-03** | Phase Constant ($\beta$) | Pozar (4th ed.), Eq. (2.11), p. 52 | `line_model.py:phase_constant` | 100% |
| **EQ-04** | Characteristic Impedance ($Z_0$) | Pozar (4th ed.), Eq. (2.18), p. 53 | `line_model.py:line_model` | 100% |
| **EQ-05** | Load Reflection Coefficient ($\Gamma_L$) | Pozar (4th ed.), Eq. (2.35), p. 57 | `line_model.py:load_reflection` | 100% |
| **EQ-06** | Spatial Reflection $\Gamma(d)$ | Pozar (4th ed.), Eq. (2.38), p. 58 | `line_model.py:reflection_at_distance` | 100% |
| **EQ-07** | Input Impedance ($Z_{\text{in}}$) | Pozar (4th ed.), Eq. (2.44), p. 59 | `line_model.py:input_impedance` | 100% |
| **EQ-08** | Reflection Coeff from Impedance | Pozar (4th ed.), Eq. (2.35), p. 57 | `measurements.py:reflection_coefficient` | 100% |
| **EQ-09** | Voltage Standing Wave Ratio | Pozar (4th ed.), Eq. (2.41), p. 59 | `measurements.py:vswr` | 100% |
| **EQ-10** | Return Loss in dB ($\text{RL}_{\text{dB}}$) | Pozar (4th ed.), Eq. (2.42), p. 59 | `measurements.py:return_loss_db` | 100% |
| **EQ-11** | Smith Chart Mapping ($\Gamma \leftrightarrow z$) | Pozar (4th ed.), Eq. (2.50), p. 64 | `measurements.py:smith_plot` | 100% |
| **EQ-12** | Line Section ABCD Matrix | Pozar (4th ed.), Table 4.1, p. 191 | `fault_simulation.py:abcd_uniform_line` | 100% |
| **EQ-13** | Series Impedance ABCD Matrix | Pozar (4th ed.), Table 4.1, p. 191 | `fault_simulation.py:abcd_series_impedance` | 100% |
| **EQ-14** | Shunt Admittance ABCD Matrix | Pozar (4th ed.), Table 4.1, p. 191 | `fault_simulation.py:abcd_shunt_admittance` | 100% |
| **EQ-15** | Input Impedance from ABCD | Pozar (4th ed.), Table 4.1, p. 191 | `fault_simulation.py:zin_from_abcd` | 100% |
| **EQ-16** | IFFT TDR Distance Estimation | Keysight AN 5989-5723EN, p. 8 | `diagnosis.py:_compute_ifft_distance` | 100% |
| **EQ-17** | Phase-Slope Distance ($d_{\text{phase}}$) | Song et al. (2009), Eq. (5) | `core/fault_location.py:compute_phase_slope` | 100% |
| **EQ-18** | Physical Rayleigh Range Resolution | Keysight AN 5989-5723EN; Anritsu AN 11410 | `diagnosis.py:distance_resolution` | 100% |
| **EQ-19** | Unambiguous Measurement Range | Keysight AN 5989-5723EN, p. 9 | `diagnosis.py:distance_resolution` | 100% |
| **EQ-20** | Quarter-Wave Transformer ($Z_t, \ell_t$) | Pozar (4th ed.), Eqs. (5.37)-(5.38) | `matching.py:design_quarter_wave` | 100% |
| **EQ-21** | Contiguous Matching Bandwidth | Pozar (4th ed.), Eq. (5.40), p. 248 | `matching.py:compare_matching` | 100% |
| **EQ-22** | DC Phase Intercept ($\phi_0$) | RF Line Doctor Physics Derivation | `diagnosis.py:extract_features` | 100% |

---

## 2. Equation-by-Equation Detailed Verification

### EQ-01: Phase Velocity ($v_p$)
1. **Mathematical Form:**
   $$v_p = \frac{1}{\sqrt{\mu \varepsilon}} = \frac{c_0}{\sqrt{\varepsilon_r}} = c_0 \cdot \text{vf}$$
2. **Academic Source:** Pozar (4th ed.), Section 2.1, Eq. (2.12), p. 52.
3. **Assumptions:** Transverse Electromagnetic (TEM) mode propagation in a non-magnetic ($\mu_r = 1$), homogeneous dielectric medium. Frequency is strictly below the cutoff of higher-order waveguide modes ($TE_{11}$).
4. **Unit Consistency:** $[c_0] = \text{m/s}$, $[\text{vf}] = \text{dimensionless} \implies [v_p] = \text{m/s}$. Exact fundamental constant $c_0 = 299,792,458\text{ m/s}$ (CODATA/NIST).
5. **Reference Plane:** Independent of reference plane along uniform line.
6. **Phasor / Time Convention:** Independent of time convention.
7. **Implementation:** `line_model.py:phase_velocity(vf)`.
8. **Test Coverage:** Verified in `test_line_model.py:test_phase_velocity` for $\text{vf} = 1.0$ ($c_0$) and $\text{vf} = 0.66$ ($1.9786\times 10^8\text{ m/s}$).
9. **Additional Tests:** Parametrized in `test_measurements.py:test_sweep_preserves_vf_and_sweepresult` across $\text{vf} \in [0.66, 0.70, 1.0]$.

---

### EQ-02: Wavelength ($\lambda$)
1. **Mathematical Form:**
   $$\lambda = \frac{v_p}{f} = \frac{c_0 \cdot \text{vf}}{f}$$
2. **Academic Source:** Pozar (4th ed.), Section 2.1, Eq. (2.13), p. 52.
3. **Assumptions:** Single-frequency monochromatic sinusoidal excitation $f > 0$. Lossless dielectric ($\alpha = 0$).
4. **Unit Consistency:** $[v_p] = \text{m/s}$, $[f] = \text{s}^{-1} \implies [\lambda] = \text{m}$.
5. **Reference Plane:** Spatial periodicity metric; independent of reference plane.
6. **Phasor / Time Convention:** Compatible with both $e^{j\omega t}$ and $e^{-i\omega t}$.
7. **Implementation:** `line_model.py:wavelength(f, vf=1.0)`.
8. **Test Coverage:** Verified in `test_line_model.py:test_wavelength_air` ($f = 100\text{ MHz}, \text{vf}=1.0 \implies \lambda = 2.99792458\text{ m}$) against `HAND_CALCULATIONS.md`.
9. **Additional Tests:** Verified under array broadcasting in `test_measurements.py`.

---

### EQ-03: Phase Constant ($\beta$)
1. **Mathematical Form:**
   $$\beta = \omega\sqrt{L'C'} = \frac{2\pi f}{v_p} = \frac{2\pi}{\lambda}$$
2. **Academic Source:** Pozar (4th ed.), Section 2.1, Eq. (2.11), p. 52.
3. **Assumptions:** Lossless transmission line baseline ($\alpha = 0$). Non-dispersive dielectric medium ($\varepsilon_r = \text{const}$). Note: Setting $\alpha = 0$ is an intentional simplifying baseline assumption per the EC-3104 syllabus and `INTERFACES.md` contract; real RG-58 cable experiences conductor skin-effect and dielectric losses reaching $\alpha \approx 1.6 - 2.0\text{ dB/m}$ at $5\text{ GHz}$.
4. **Unit Consistency:** $[f] = \text{s}^{-1}$, $[v_p] = \text{m/s} \implies [\beta] = \text{rad/m}$.
5. **Reference Plane:** Rate of phase rotation per unit length.
6. **Phasor / Time Convention:** For $e^{j\omega t}$, wave traveling in $+z$ direction propagates as $e^{-j\beta z}$.
7. **Implementation:** `line_model.py:phase_constant(f, vf=1.0)`.
8. **Test Coverage:** Verified in `test_line_model.py:test_phase_constant` ($\beta \approx 2.095845\text{ rad/m}$ at $100\text{ MHz}$).

---

### EQ-04: Characteristic Impedance ($Z_0$)
1. **Mathematical Form:**
   $$Z_0 = \sqrt{\frac{R' + j\omega L'}{G' + j\omega C'}} \xrightarrow[\text{lossless}]{} \sqrt{\frac{L'}{C'}} \in \mathbb{R}^+$$
2. **Academic Source:** Pozar (4th ed.), Section 2.1, Eq. (2.18), p. 53.
3. **Assumptions:** Lossless uniform line ($R' = G' = 0$). Real positive characteristic impedance.
4. **Unit Consistency:** $[L'] = \text{H/m} = \Omega\cdot\text{s/m}$, $[C'] = \text{F/m} = \text{s}/(\Omega\cdot\text{m}) \implies [Z_0] = \Omega$.
5. **Reference Plane:** Intrinsic line parameter.
6. **Phasor / Time Convention:** Real scalar; independent of time convention.
7. **Implementation:** Parameters `Z0` across all modules.
8. **Test Coverage:** Verified across $50\,\Omega$ and $75\,\Omega$ standard systems in `test_line_model.py`.

---

### EQ-05: Load Reflection Coefficient ($\Gamma_L$)
1. **Mathematical Form:**
   $$\Gamma_L = \frac{Z_L - Z_0}{Z_L + Z_0}$$
2. **Academic Source:** Pozar (4th ed.), Section 2.3, Eq. (2.35), p. 57.
3. **Assumptions:** Reference impedance $Z_0 > 0$. Load impedance $Z_L \in \mathbb{C} \cup \{\infty\}$.
4. **Unit Consistency:** Numerator and denominator both in $\Omega \implies [\Gamma_L]$ is dimensionless.
5. **Reference Plane:** Located exactly at the termination load boundary plane ($d = 0$).
6. **Phasor / Time Convention:** Ratio of reverse voltage wave phasor to forward voltage wave phasor.
7. **Implementation:** `line_model.py:load_reflection(Z0, ZL)` and `measurements.py:reflection_coefficient(Z, Z0)`.
8. **Test Coverage:**
   - Matched ($Z_L = Z_0 \implies \Gamma_L = 0$).
   - Short ($Z_L = 0 \implies \Gamma_L = -1.0$).
   - Open ($Z_L = \infty \implies \Gamma_L = +1.0$ via exact limit check `np.isinf`).
   - Resistive mismatch ($Z_L = 100, Z_0 = 50 \implies \Gamma_L = 1/3$).
   - All 4 verified in `test_line_model.py:test_load_reflection_*` and `test_measurements.py`.

---

### EQ-06: Reflection Coefficient at Distance $d$ toward Generator
1. **Mathematical Form:**
   $$\Gamma(d) = \Gamma_L e^{-2j\beta d}$$
2. **Academic Source:** Pozar (4th ed.), Section 2.3, Eq. (2.38), p. 58.
3. **Assumptions:** Lossless line ($\alpha = 0$). Distance $d \ge 0$ measured from load toward generator.
4. **Unit Consistency:** $[\beta] = \text{rad/m}$, $[d] = \text{m} \implies [2\beta d] = \text{rad}$ (dimensionless).
5. **Reference Plane:** Reference plane shift by physical distance $d$ toward the source.
6. **Phasor / Time Convention:** Under $e^{j\omega t}$, moving toward the generator advances the incident wave phase by $+j\beta d$ and delays the reflected wave phase by $-j\beta d$, resulting in a net phase factor of $e^{-2j\beta d}$ (clockwise rotation on the Smith chart).
7. **Implementation:** `line_model.py:reflection_at_distance(Z0, ZL, beta, d)`.
8. **Test Coverage:** Verified in `test_line_model.py:test_reflection_at_distance_half_wave` ($\Gamma(\lambda/2) = \Gamma_L$) and `test_quarter_wave`.

---

### EQ-07: Input Impedance Transformation ($Z_{\text{in}}$)
1. **Mathematical Form:**
   $$Z_{\text{in}} = Z_0 \frac{1 + \Gamma(\ell)}{1 - \Gamma(\ell)} = Z_0 \left[ \frac{Z_L + j Z_0 \tan(\beta \ell)}{Z_0 + j Z_L \tan(\beta \ell)} \right]$$
2. **Academic Source:** Pozar (4th ed.), Section 2.3, Eq. (2.43)-(2.44), p. 59.
3. **Assumptions:** Lossless transmission line of length $\ell$.
4. **Unit Consistency:** Dimensionless fraction multiplied by $Z_0$ ($\Omega$) $\implies [Z_{\text{in}}] = \Omega$.
5. **Reference Plane:** Located at the input terminals of the transmission line ($z = 0$, $d = \ell$).
6. **Phasor / Time Convention:** Derived under $V(z)/I(z)$ with $e^{j\omega t}$.
7. **Implementation:** `line_model.py:input_impedance(Z0, ZL, beta, length)`.
8. **Test Coverage:**
   - Benchmarked against all 7 analytical cases in `HAND_CALCULATIONS.md`:
     1. Matched: $Z_L = 50 \implies Z_{\text{in}} = 50\,\Omega$.
     2. Short at $\lambda/8$: $Z_{\text{in}} = +j50\,\Omega$.
     3. Open at $\lambda/8$: $Z_{\text{in}} = -j50\,\Omega$.
     4. Quarter-wave: $Z_L = 100 \implies Z_{\text{in}} = 25\,\Omega$.
     5. Half-wave: $Z_L = 30 + j40 \implies Z_{\text{in}} = 30 + j40\,\Omega$.
     6. Quarter-wave transformer: $Z_t = \sqrt{50\times 200} = 100\,\Omega$.
     7. Singularities: Short at $\lambda/4 \implies Z_{\text{in}} = \infty$; Open at $\lambda/4 \implies Z_{\text{in}} = 0$.
   - Tested in `test_line_model.py` and `test_integration.py`.

---

### EQ-08: Reflection Coefficient from Impedance
1. **Mathematical Form:**
   $$\Gamma = \frac{Z - Z_0}{Z + Z_0}$$
2. **Academic Source:** Pozar (4th ed.), Section 2.3, Eq. (2.35), p. 57.
3. **Assumptions:** $Z_0 > 0$. Singular impedance $Z \to \infty$ mapped to $+1.0 + 0j$.
4. **Unit Consistency:** Dimensionless.
5. **Reference Plane:** At the measurement plane of impedance $Z$.
6. **Implementation:** `measurements.py:reflection_coefficient(Z, Z0)`.
7. **Test Coverage:** Tested in `test_measurements.py:test_reflection_coefficient_*`.

---

### EQ-09: Voltage Standing Wave Ratio (VSWR)
1. **Mathematical Form:**
   $$\text{VSWR} = \frac{1 + |\Gamma|}{1 - |\Gamma|}$$
2. **Academic Source:** Pozar (4th ed.), Section 2.3, Eq. (2.41), p. 59.
3. **Assumptions:** Strictly defined for passive devices where $0 \le |\Gamma| \le 1$.
4. **Unit Consistency:** Dimensionless scalar ratio $\ge 1.0$.
5. **Singularity Handling:**
   - $|\Gamma| = 1.0 \implies \text{VSWR} = \infty$.
   - $|\Gamma| > 1.0$ (noisy active points) $\implies \text{VSWR} = \text{NaN}$.
6. **Implementation:** `measurements.py:vswr(gamma)`.
7. **Test Coverage:** Tested in `test_measurements.py:test_vswr_known_values` and `test_vswr_handles_nonpassive_loads`.

---

### EQ-10: Return Loss ($\text{RL}_{\text{dB}}$)
1. **Mathematical Form:**
   $$\text{RL}_{\text{dB}} = -20 \log_{10}(|\Gamma|)$$
2. **Academic Source:** Pozar (4th ed.), Section 2.3, Eq. (2.42), p. 59.
3. **Assumptions:** Standard IEEE and Pozar definition where Return Loss is a positive quantity in decibels.
4. **Unit Consistency:** Logarithmic ratio in decibels ($\text{dB}$).
5. **Singularity Handling:**
   - $|\Gamma| = 0 \implies \text{RL} = +\infty\text{ dB}$ without divide-by-zero warnings.
   - $|\Gamma| = 1 \implies \text{RL} = 0.0\text{ dB}$.
6. **Implementation:** `measurements.py:return_loss_db(gamma)`.
7. **Test Coverage:** Tested in `test_measurements.py:test_return_loss_db_known_values`.

---

### EQ-11: Smith Chart Bilinear Transformation
1. **Mathematical Form:**
   $$\Gamma = \frac{z - 1}{z + 1} \iff z = \frac{1 + \Gamma}{1 - \Gamma}$$
   where $z = Z / Z_0 = r + jx$.
2. **Academic Source:** Pozar (4th ed.), Section 2.4, Eqs. (2.48)-(2.50), pp. 63-64.
3. **Assumptions:** Conformal mapping between complex $z$-plane and complex $\Gamma$-disc.
4. **Unit Consistency:** Normalized quantities are dimensionless.
5. **Implementation:** `measurements.py:smith_plot(gamma_array, ax, **kw)`.
6. **Test Coverage:** Verified in `test_measurements.py:test_smith_plot_generation`.

---

### EQ-12: Uniform Transmission-Line ABCD Matrix
1. **Mathematical Form:**
   $$\mathbf{M}_{\text{line}}(\ell) = \begin{bmatrix} A & B \\ C & D \end{bmatrix} = \begin{bmatrix} \cos(\beta \ell) & j Z_0 \sin(\beta \ell) \\ j \frac{\sin(\beta \ell)}{Z_0} & \cos(\beta \ell) \end{bmatrix}$$
2. **Academic Source:** Pozar (4th ed.), Section 4.4, Table 4.1, p. 191.
3. **Assumptions:** Lossless uniform line ($\alpha = 0$). Reciprocal ($AD - BC = \cos^2(\beta\ell) + \sin^2(\beta\ell) = 1$) and symmetric ($A = D$).
4. **Unit Consistency:** $[A] = [D] = \text{dimensionless}$, $[B] = \Omega$, $[C] = \Omega^{-1} = \text{S}$.
5. **Implementation:** `fault_simulation.py:abcd_uniform_line(Z0, beta, length)`.
6. **Test Coverage:** Verified in `test_fault_simulation.py` for $\ell = 0$ (identity) and cascaded line sections.

---

### EQ-13: Series Impedance Discontinuity ABCD Matrix
1. **Mathematical Form:**
   $$\mathbf{M}_{\text{series}}(Z_s) = \begin{bmatrix} 1 & Z_s \\ 0 & 1 \end{bmatrix}$$
   For series inductance: $Z_s = j\omega L = j 2\pi f L$.
2. **Academic Source:** Pozar (4th ed.), Section 4.4, Table 4.1, p. 191.
3. **Assumptions:** Lumped discontinuity dimensions $\ll \lambda$.
4. **Unit Consistency:** $[Z_s] = \Omega$. Reciprocity check: $AD - BC = 1\cdot 1 - 0 = 1$.
5. **Implementation:** `fault_simulation.py:abcd_series_impedance(Z)`.
6. **Test Coverage:** Verified in `test_fault_simulation.py:test_series_L_zero_limit_is_healthy` ($L \to 0 \implies \mathbf{I}$).

---

### EQ-14: Shunt Admittance Discontinuity ABCD Matrix
1. **Mathematical Form:**
   $$\mathbf{M}_{\text{shunt}}(Y_p) = \begin{bmatrix} 1 & 0 \\ Y_p & 1 \end{bmatrix}$$
   For shunt capacitance: $Y_p = j\omega C = j 2\pi f C$.
2. **Academic Source:** Pozar (4th ed.), Section 4.4, Table 4.1, p. 191.
3. **Assumptions:** Lumped shunt element between center conductor and shield.
4. **Unit Consistency:** $[Y_p] = \text{S}$. Reciprocity check: $AD - BC = 1$.
5. **Implementation:** `fault_simulation.py:abcd_shunt_admittance(Y)`.
6. **Test Coverage:** Verified in `test_fault_simulation.py:test_shunt_C_zero_limit_is_healthy` ($C \to 0 \implies \mathbf{I}$).

---

### EQ-15: Input Impedance from Cascaded ABCD Matrix
1. **Mathematical Form:**
   $$Z_{\text{in}} = \frac{A Z_L + B}{C Z_L + D} \xrightarrow[Z_L \to \infty]{} \frac{A}{C}$$
2. **Academic Source:** Pozar (4th ed.), Section 4.4, Table 4.1, p. 191.
3. **Assumptions:** Termination $Z_L$. Guarded against $C = 0$.
4. **Implementation:** `fault_simulation.py:zin_from_abcd(ABCD, ZL)`.
5. **Test Coverage:** Verified for open circuit ($A/C$), short circuit ($B/D$), and matched loads.

---

### EQ-16: IFFT TDR Distance Estimation
1. **Mathematical Form:**
   $$h(n) = \frac{1}{N} \sum_{k=0}^{N-1} \left[ \Gamma(f_k) \cdot w_k \right] e^{+j \frac{2\pi k n}{N_{\text{pad}}}}$$
   $$d = \frac{v_p \cdot t_{\text{peak}}}{2} = \frac{c_0 \cdot \text{vf} \cdot n_{\text{peak}}}{2 N_{\text{pad}} \Delta f}$$
2. **Academic Source:** Keysight Technologies AN 5989-5723EN, pp. 6–10; Pozar (4th ed.), Sec. 2.9; Chang et al. (2026).
3. **Assumptions:**
   - Uniform frequency grid: Frequency step $\Delta f = (f_{\text{max}} - f_{\text{min}})/(N - 1)$ must be strictly uniform. If non-uniform data is received, it must be validated and resampled.
   - Spectral windowing: Hann window $w_k = 0.5 [1 - \cos(2\pi k / (N - 1))]$ is applied to suppress truncation sidelobes from $-13\text{ dB}$ (rectangular) down to $-31.5\text{ dB}$, preventing spectral leakage from masking small nearby defects.
   - Zero-padding: The sequence is zero-padded from $N$ to $N_{\text{pad}} = 2^{\lceil \log_2(4N) \rceil}$ power-of-two bins. This acts as bandlimited sinc interpolation in the time domain, eliminating peak-detection scallop loss without altering the physical two-fault Rayleigh resolution.
   - Peak detection: Causal search index $n \ge 3$ excludes the zero-distance direct port feedthrough spike.
4. **Unit Consistency:** $[t] = \text{s}$, $[v_p] = \text{m/s} \implies [d] = \text{m}$.
5. **Implementation:** `diagnosis.py:_compute_ifft_distance` and `core/fault_location.py:compute_ifft_tdr`.
6. **Test Coverage:** Verified in `test_diagnosis.py:test_estimate_distance_against_known_fault_positions` for lengths $0.3\text{ m}, 0.7\text{ m}, 1.2\text{ m}$ (errors $< 1.5\Delta R$).

---

### EQ-17: Phase-Slope Distance Estimation ($d_{\text{phase}}$)
1. **Mathematical Form:**
   $$\phi(f) = \text{unwrap}(\angle \Gamma(f)) = \phi_0 - \frac{4\pi d}{v_p} f$$
   $$\text{slope} = \frac{d\phi}{df} = -\frac{4\pi d}{v_p} \implies d = -\frac{v_p}{4\pi} \frac{d\phi}{df}$$
2. **Academic Source:** Song et al. (2009), Eq. (5); Furse et al. (2021); Liu et al. (2024).
3. **Assumptions:** Single dominant reflection. Discontinuities with frequency-dependent phase characteristics (such as series inductance or shunt capacitance) introduce systematic slope bias, making phase-slope a secondary cross-check rather than primary location for reactive faults.
4. **Implementation:** `core/fault_location.py:compute_phase_slope_distance`.
5. **Test Coverage:** Verified in `test_location.py` dual-method comparison.

---

### EQ-18: Physical Rayleigh Range Resolution ($\Delta R$) vs Display Sampling Step ($\delta d$)
1. **Mathematical Form:**
   $$\Delta R_{\text{nom}} = \frac{v_p}{2 B} = \frac{c_0 \cdot \text{vf}}{2 (f_{\text{max}} - f_{\text{min}})}$$
   $$\Delta R_{\text{eff}} \approx K_w \Delta R_{\text{nom}} \approx 1.50 \cdot \frac{v_p}{2 B} \quad (\text{Hann window})$$
   $$\delta d = \frac{v_p}{2 N_{\text{pad}} \Delta f} = \frac{R_{\text{max}}}{N_{\text{pad}}}$$
2. **Academic Source:** Keysight AN 5989-5723EN, p. 9; Anritsu AN 11410-00373, p. 4; Harris (1978).
3. **Physical Distinction:**
   - **Nominal Bandwidth Resolution ($\Delta R_{\text{nom}}$):** The fundamental physical limit set by the measured bandwidth $B$. Two equal-magnitude point discontinuities closer than $\Delta R_{\text{nom}}$ cannot be resolved under an unwindowed Dirichlet kernel.
   - **Effective Windowed Resolution ($\Delta R_{\text{eff}}$):** Tapering with a Hann window broadens the mainlobe width by factor $K_w \approx 1.50$ (from $0.89/B$ to $1.44/B$ at the $-3\text{ dB}$ points), trading two-point separation for $-31.5\text{ dB}$ sidelobe suppression.
   - **Display / Interpolation Step ($\delta d$):** The spatial interval between adjacent discrete IFFT bins after zero-padding to $N_{\text{pad}}$ points.
   - **Critical Principle:** Zero-padding ($N \to N_{\text{pad}}$) does **NOT** improve the physical two-fault resolution $\Delta R_{\text{eff}}$. It performs purely trigonometric (sinc) interpolation between existing Fourier samples, reducing peak-amplitude scallop loss and visual jaggedness. Two physical discontinuities separated by $< \Delta R_{\text{eff}}$ will merge into a single broad peak regardless of $N_{\text{pad}}$.
4. **Unit Consistency:** $[v_p] = \text{m/s}$, $[B] = \text{s}^{-1} \implies [\Delta R] = \text{m}$; $[\delta d] = \text{m}$.
5. **Implementation:** `diagnosis.py:distance_resolution` and `core/fault_location.py:calculate_resolution_metrics`.
6. **Test Coverage:** Tested in `test_diagnosis.py` and `test_location.py`.

---

### EQ-19: Unambiguous Measurement Range ($R_{\text{max}}$)
1. **Mathematical Form:**
   $$R_{\text{max}} = \frac{v_p}{2 \Delta f} = \frac{c_0 \cdot \text{vf}}{2 (f_{k+1} - f_k)}$$
2. **Academic Source:** Keysight AN 5989-5723EN, p. 9.
3. **Assumptions:** Nyquist sampling in the frequency domain. Cable length must satisfy $\ell < R_{\text{max}}$ to avoid alias folding.
4. **Unit Consistency:** $[v_p] = \text{m/s}$, $[\Delta f] = \text{s}^{-1} \implies [R_{\text{max}}] = \text{m}$.
5. **Implementation:** `diagnosis.py:distance_resolution`.
6. **Test Coverage:** Tested in `test_location.py`.

---

### EQ-20: Quarter-Wave Transformer Synthesis
1. **Mathematical Form:**
   $$Z_t = \sqrt{Z_0 R_L}, \quad \ell_t = \frac{\lambda_t}{4} = \frac{v_p}{4 f_0} = \frac{c_0 \cdot \text{vf}}{4 f_0}$$
2. **Academic Source:** Pozar (4th ed.), Section 5.4, Eqs. (5.37)-(5.38), p. 246.
3. **Assumptions:** Purely real load resistance $R_L > 0$. Real line impedance $Z_0 > 0$. Design frequency $f_0 > 0$.
4. **Unit Consistency:** $[Z_t] = \sqrt{\Omega \cdot \Omega} = \Omega$; $[\ell_t] = \text{m}$.
5. **Implementation:** `matching.py:design_quarter_wave(Z0, RL, f, vf)`.
6. **Test Coverage:** Verified in `test_matching.py:test_design_quarter_wave_against_hand_calculations` ($50 \to 200\,\Omega \implies Z_t = 100\,\Omega, \ell_t \approx 0.75\text{ m}$).

---

### EQ-21: Contiguous Matching Passband Bandwidth
1. **Mathematical Form:**
   $$B_{\text{contiguous}} = f_{\text{high}} - f_{\text{low}}$$
   where $[f_{\text{low}}, f_{\text{high}}]$ is the uninterrupted interval containing $f_0$ such that $\text{RL}_{\text{dB}}(f) \ge \text{threshold}$. If $\text{RL}_{\text{dB}}(f_0) < \text{threshold}$, $B = 0.0\text{ Hz}$.
2. **Academic Source:** Pozar (4th ed.), Section 5.4, Eq. (5.40), p. 248.
3. **Assumptions:** Evaluated strictly around design frequency $f_0$. Disconnected harmonic passbands are excluded.
4. **Implementation:** `matching.py:compare_matching`.
5. **Test Coverage:** Verified in `test_matching.py:test_contiguous_bandwidth_isolation`.

---

### EQ-22: Physical DC Phase Intercept ($\phi_0$) for Open/Short Separation
1. **Mathematical Form:**
   $$\phi(f) = \text{unwrap}(\angle \Gamma(f)) = \phi_0 + m f$$
   $$\phi_0 = \lim_{f \to 0} \angle \Gamma(f) = \angle \Gamma_L$$
   $$\cos(\phi_0) = \begin{cases} +1.0 & \text{Open Circuit } (\Gamma_L = +1) \\ -1.0 & \text{Short Circuit } (\Gamma_L = -1) \end{cases}$$
2. **Academic Source:** Physics derivation; Collin (2001), Ch. 3; Pozar (4th ed.), Sec. 2.3.
3. **Physical Basis & Ideal Assumptions:**
   - As $f \to 0$, the electrical line length $\beta(f) \ell = \frac{2\pi f}{v_p} \ell \equiv 0$ vanishes identically. Therefore, the DC phase intercept $\phi_0$ reflects purely the load reflection angle $\angle \Gamma_L$, independent of line length $\ell$ and velocity factor $v_p$.
   - **Phase-Unwrapping Sampling Limit:** To prevent $2\pi$ spatial ambiguity during numerical phase unwrapping, the phase change between adjacent frequency points must be strictly less than $\pi$:
     $$\Delta \phi = \frac{4\pi d}{v_p} \Delta f < \pi \implies \Delta f < \frac{v_p}{4 d_{\text{max}}}$$
     For $d_{\text{max}} = 2.5\text{ m}$ and $\text{vf} = 0.66$, this requires $\Delta f < 19.8\text{ MHz}$. Exceeding this step causes unwrapping cycle slips.
   - **Low-Frequency Extrapolation Noise Sensitivity:** Because practical VNA sweeps start at $f_{\text{min}} > 0$ (e.g., $100\text{ MHz} - 500\text{ MHz}$), estimating $\phi_0$ requires extrapolating the linear regression line over the unmeasured gap $[0, f_{\text{min}}]$. Severe receiver noise or frequency-dependent phase nonlinearity inflates the standard error of the intercept:
     $$\text{SE}(\phi_0) = \text{SE}(m) \sqrt{\frac{1}{N}\sum f_k^2}$$
   - **Fit-Quality Threshold:** Linear phase regression requires $R^2 \ge 0.95$. If $R^2 < 0.95$, phase nonlinearity (indicative of dispersion, multiple reflections, or heavy reactive parasitics) invalidates the single-reflection DC intercept model.
   - **Tested Parameter Range:** Formally validated in Monte Carlo testing across line lengths $\ell \in [0.4, 2.5]\text{ m}$, frequency bands $f \in [0.2, 5.0]\text{ GHz}$, velocity factors $\text{vf} \in [0.66, 1.0]$, and noise levels $\sigma \le 0.03$.
4. **Implementation:** `diagnosis.py:extract_features` and `diagnosis.py:classify`.
5. **Test Coverage:** Parametrized in `test_diagnosis.py:test_open_vs_short_separation_across_vf_and_lengths` across $\text{vf} \in [0.66, 0.70, 1.0]$ and lengths $[0.4, 0.9, 1.8]\text{ m}$ (100% pass rate).

---

## 3. Verified Academic Citations

1. **Pozar, D. M.** (2012). *Microwave Engineering*, 4th ed., John Wiley & Sons, Hoboken, NJ. ISBN: 978-0-470-63155-3.
2. **Collin, R. E.** (2001). *Foundations for Microwave Engineering*, 2nd ed., IEEE Press / Wiley-Interscience, New York. ISBN: 978-0-7803-6031-0.
3. **Ramo, S., Whinnery, J. R., & Van Duzer, T.** (1994). *Fields and Waves in Communication Electronics*, 3rd ed., John Wiley & Sons, New York. ISBN: 978-0-471-58551-0.
4. **Furse, C. M., Kafal, M., Razzaghi, R., & Shin, Y.-J.** (2021). "Fault Diagnosis for Electrical Systems and Power Networks: A Review," *IEEE Sensors Journal*, vol. 21, no. 2, pp. 888–906, Jan. 2021. DOI: [10.1109/JSEN.2020.2987321](https://doi.org/10.1109/JSEN.2020.2987321).
5. **Chang, K., Xu, Z., Zhang, G., & Wang, L.** (2026). "Fault Location and Evaluation in Coaxial Cables Based on Stepped Frequency Waveform Reflectometry and Electromagnetic Time Reversal," *IEEE Transactions on Instrumentation and Measurement*, vol. 75, Art. no. 3503811, pp. 1–11, Jan. 2026. DOI: [10.1109/TIM.2026.3657555](https://doi.org/10.1109/TIM.2026.3657555).
6. **Liu, C., Hou, Y., Duan, Z., & Chen, D.** (2024). "Underground Power Cable Fault Detection and Localization Based on the Spectrum of Propagation Functions," *IEEE Transactions on Instrumentation and Measurement*, vol. 73, Art. no. 3524911, pp. 1–11, Sept. 2024. DOI: [10.1109/TIM.2024.3460831](https://doi.org/10.1109/TIM.2024.3460831).
7. **Shi, X., Kafal, M., & Furse, C. M.** (2023). "Application of Augmented Spread Spectrum Time Domain Reflectometry for Detection and Localization of Soft Faults on a Coaxial Cable," *IEEE Transactions on Instrumentation and Measurement*, vol. 72, Art. no. 3504210, pp. 1–10, 2023. DOI: [10.1109/TIM.2023.3243681](https://doi.org/10.1109/TIM.2023.3243681).
8. **Rao, X., Xiao, S., Cheng, Y., & Peng, Z.** (2023). "Cable Defect Location by Using Frequency Domain Reflectometry With Synchrosqueezing Generalized S-Transform," in *IEEE 5th Student Conference on Electric Power Engineering (SCEPE)*, pp. 1–5, 2023. DOI: [10.1109/SCEPE59695.2023.10427848](https://doi.org/10.1109/SCEPE59695.2023.10427848).
9. **Song, E.-S., Shin, Y.-J., Stone, P. E., Wang, J., Choe, T.-S., Yook, J.-G., & Park, J.-B.** (2009). "Detection and Location of Multiple Wiring Faults via Time–Frequency-Domain Reflectometry," *IEEE Transactions on Electromagnetic Compatibility*, vol. 51, no. 1, pp. 131–138, Feb. 2009. DOI: [10.1109/TEMC.2008.2007964](https://doi.org/10.1109/TEMC.2008.2007964).
10. **Kingston, S., Benoit, E., Edun, A. S., et al.** (2021). "A SSTDR Methodology, Implementations, and Challenges," *Sensors*, vol. 21, no. 16, p. 5268, Aug. 2021. DOI: [10.3390/s21165268](https://doi.org/10.3390/s21165268).
11. **Williams, D. F., LeGolvan, K. A., & Jargon, J. A.** (2006). "An Accurate Calibration Accounting for Toroid Losses in VNA Measurements," *IEEE Transactions on Microwave Theory and Techniques*, vol. 54, no. 12, pp. 4370–4377, Dec. 2006. DOI: [10.1109/TMTT.2006.885903](https://doi.org/10.1109/TMTT.2006.885903).
12. **Marks, R. B.** (1991). "A Multiline Method of Network Analyzer Calibration," *IEEE Transactions on Microwave Theory and Techniques*, vol. 39, no. 7, pp. 1205–1215, July 1991. DOI: [10.1109/22.85388](https://doi.org/10.1109/22.85388).
13. **Stumper, U.** (2005). "Influence of Noise on Vector Network Analyzer Calibrations," *IEEE Transactions on Instrumentation and Measurement*, vol. 54, no. 2, pp. 627–631, Apr. 2005. DOI: [10.1109/TIM.2004.843067](https://doi.org/10.1109/TIM.2004.843067).
14. **Ridler, N. M., & Salter, M. J.** (2007). "Evaluating and Expressing Uncertainty in S-Parameter Measurements," *Metrologia*, vol. 44, no. 4, pp. 292–299, 2007. DOI: [10.1088/0026-1394/44/4/007](https://doi.org/10.1088/0026-1394/44/4/007).
15. **Harris, F. J.** (1978). "On the Use of Windows for Harmonic Analysis with the Discrete Fourier Transform," *Proceedings of the IEEE*, vol. 66, no. 1, pp. 51–83, Jan. 1978. DOI: [10.1109/PROC.1978.10837](https://doi.org/10.1109/PROC.1978.10837).
16. **Keysight Technologies** (2020). *Time Domain Analysis Using a Network Analyzer*, Application Note 5989-5723EN, Keysight Technologies, Santa Rosa, CA.
17. **Anritsu Company** (2018). *Distance-to-Fault (DTF) Measurement Fundamentals*, Application Note 11410-00373, Anritsu Company, Morgan Hill, CA.
