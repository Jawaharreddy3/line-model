# Physical and Mathematical Assumption Register

**Project:** RF LINE DOCTOR — Virtual Transmission-Line Fault Diagnosis & Matching  
**Course:** EC-3104 (Electromagnetic Waves and Transmission Lines)  

---

## 1. Purpose of the Register

This register documents every foundational physical, mathematical, and numerical assumption embedded in the **RF LINE DOCTOR** architecture. Each assumption is explicitly justified against microwave engineering literature, its domain of validity is specified, its impact on simulation results is quantified, and its physical limitations are clearly stated for defense before academic faculty.

---

## 2. Comprehensive Assumption Matrix

### ASM-01: Transverse Electromagnetic (TEM) Mode Dominance
- **Assumption:** Electromagnetic propagation along the coaxial transmission line occurs purely in the fundamental TEM mode. Higher-order waveguide modes ($TE_{11}$, $TM_{01}$) are evanescent and carry zero active power.
- **Physical Justification:** Coaxial cables are designed to operate strictly below the cutoff frequency of the $TE_{11}$ mode:
  $$f_c \approx \frac{c_0}{\pi (a + b) \sqrt{\varepsilon_r}}$$
  For standard RG-58 coaxial cable ($a = 0.45\text{ mm}, b = 1.47\text{ mm}, \varepsilon_r \approx 2.3$), $f_c \approx 33\text{ GHz}$. The operating frequency range of RF Line Doctor ($1\text{ MHz} - 5\text{ GHz}$) lies well below $f_c$ ($f \le 0.15 f_c$).
- **Literature Reference:** Pozar (4th ed.), Section 3.4, pp. 114–116; Collin (2nd ed.), Section 3.3.
- **Limitation:** In millimeter-wave applications ($f > 30\text{ GHz}$) or oversized coaxial lines, higher-order mode excitation at discontinuities would invalidate scalar TEM transmission-line equations.

---

### ASM-02: Lossless Transmission Line Baseline ($\alpha = 0$)
- **Assumption:** Conductor series resistance ($R' = 0$) and dielectric shunt conductance ($G' = 0$) are assumed zero in the baseline model, yielding zero attenuation constant ($\alpha = 0$).
- **Physical Justification & Educational Baseline:** 
  1. Mandated by the frozen project specification (`INTERFACES.md`, line 4) and the EC-3104 undergraduate syllabus to maintain mathematical transparency, analytical solvability, and exact alignment with closed-form hand calculations.
  2. Setting $\alpha = 0$ provides an essential benchmark reference against which students and researchers can isolate reactive and resistive discontinuity phenomena without confounding attenuation decay.
- **Physical Reality & High-Frequency Limitations:**
  In real physical coaxial cables (e.g., RG-58, RG-214), attenuation is frequency-dependent due to conductor skin effect ($R'(f) \propto \sqrt{f}$) and dielectric loss tangent ($G'(f) = \omega C' \tan\delta \propto f$):
  $$\alpha(f) = \alpha_c(f) + \alpha_d(f) = \frac{R_s(f)}{2 Z_0} \left( \frac{1}{2\pi a} + \frac{1}{2\pi b} \right) + \frac{1}{2}\omega\sqrt{\mu\varepsilon}\tan\delta$$
  While attenuation is modest at low frequencies ($< 0.1\text{ dB/m}$ at $100\text{ MHz}$), at $5\text{ GHz}$ a standard RG-58 cable exhibits attenuation of $\approx 1.6 - 2.0\text{ dB/m}$. For a $2.5\text{ m}$ cable, round-trip attenuation reaches $8 - 10\text{ dB}$, which noticeably depresses peak reflection amplitudes and causes the open-circuit/short-circuit reflection coefficient locus on the Smith chart to spiral inward toward the center. This attenuation must be accounted for in Phase II lossy modeling.
- **Literature Reference:** Pozar (4th ed.), Section 2.3, p. 57; Collin (2nd ed.), Section 3.1; Ramo, Whinnery, & Van Duzer (3rd ed.), Section 5.2.

---

### ASM-03: Non-Dispersive Dielectric Medium ($\varepsilon_r = \text{const}$)
- **Assumption:** The dielectric permittivity $\varepsilon_r$ and velocity factor $\text{vf} = 1/\sqrt{\varepsilon_r}$ are constant across the frequency sweep. Phase velocity $v_p$ is non-dispersive ($d v_p / df = 0$).
- **Physical Justification:** Standard high-quality cable dielectrics (solid Polyethylene, PTFE/Teflon, and foamed PE) have essentially flat real permittivity from $1\text{ MHz}$ to $10\text{ GHz}$.
- **Literature Reference:** Ramo, Whinnery, & Van Duzer (3rd ed.), Section 5.3; Pozar (4th ed.), Section 3.1.
- **Limitation:** In severely aged, water-tree degraded, or moisture-ingress cables, dipolar relaxation causes $\varepsilon_r(f)$ to vary with frequency, introducing phase dispersion and pulse broadening.

---

### ASM-04: Time-Harmonic Phasor Convention ($e^{j\omega t}$)
- **Assumption:** All voltages, currents, impedances, and scattering parameters are defined under the engineering phasor convention $e^{j\omega t}$.
- **Physical Justification:** Standard in IEEE, Pozar, Collin, and Keysight technical documentation. Under this convention:
  - Inductive reactance: $Z_L = +j\omega L$ (positive imaginary impedance, upper half of Smith chart).
  - Capacitive reactance: $Z_C = \frac{1}{j\omega C} = -j \frac{1}{\omega C}$ (negative imaginary impedance, lower half of Smith chart).
  - Forward-propagating wave: $e^{-j\beta z}$.
  - Backward-propagating wave: $e^{+j\beta z}$.
  - De-embedding reflection to fault plane: $\Gamma_{\text{fault}} = \Gamma_{\text{in}} e^{+2j\beta d}$.
- **Literature Reference:** Pozar (4th ed.), Section 1.3, p. 8; INTERFACES.md, line 4.
- **Limitation:** Physics literature occasionally adopts $e^{-i\omega t}$, which conjugates all reactances and S-parameters. Mixing conventions must be strictly avoided.

---

### ASM-05: Lumped Discontinuity Approximation for Connectors & Pinches
- **Assumption:** Mechanical connector defects and localized pinches are modeled as point-like lumped 2-port networks (series inductance $Z_s = j\omega L$ or shunt capacitance $Y_p = j\omega C$) embedded between two uniform line sections.
- **Physical Justification:** A typical BNC/SMA connector or crimp defect has an axial extent of $\Delta z \approx 2 - 10\text{ mm}$. At $1\text{ GHz}$, the wavelength is $\lambda \approx 200\text{ mm}$, so $\Delta z \le \lambda / 20$. In this sub-wavelength regime, quasistatic field analysis rigorously proves that excess magnetic energy storage behaves as an equivalent lumped series inductance and excess electric field fringe capacitance behaves as an equivalent lumped shunt capacitance.
- **Literature Reference:** Pozar (4th ed.), Section 4.5, pp. 195–198; Collin (2nd ed.), Section 4.8.
- **Limitation:** For extended, distributed impedance variations (e.g., periodic water logging over several meters), a distributed Telegrapher model or stepped cascaded transmission-line profile is required.

---

### ASM-06: Single-Port S-Parameter Diagnostic Constraint
- **Assumption:** The fault diagnosis engine operates exclusively on near-end reflection data ($S_{11}(f)$ and nominal $Z_0$), without access to the far-end port ($S_{21}$) or simulation ground truth.
- **Physical Justification:** Replicates real-world field conditions where installed transmission lines (e.g., tower-mounted antenna feeds, buried power feeders, aircraft wire bundles) cannot have their far end instrumented without disconnecting equipment or taking systems offline.
- **Literature Reference:** Furse et al. (2021), Section III; Anritsu AN 11410-00373.
- **Limitation:** Single-port measurements cannot distinguish between an internal short circuit and a distant zero-ohm load termination without spatial distance estimation.

---

### ASM-07: Complex Circular Gaussian Measurement Noise ($\mathcal{CN}(0, \sigma^2)$)
- **Assumption:** Measurement noise is modeled as complex additive zero-mean circular Gaussian noise with equal variance $\sigma^2/2$ on real (in-phase) and imaginary (quadrature) S-parameter channels:
  $$S_{11,\text{meas}}(f_k) = S_{11,\text{true}}(f_k) + n_I(f_k) + j n_Q(f_k), \quad n_I, n_Q \sim \mathcal{N}(0, \sigma^2/2)$$
- **Physical Justification:** Modern Vector Network Analyzers use dual-channel heterodyne receivers with quadrature (I/Q) downconversion mixers followed by digital IF bandpass filtering. By the Central Limit Theorem, the superposition of thermal Johnson-Nyquist noise, mixer shot noise, local oscillator phase noise, and ADC quantization noise converges asymptotically to a circularly symmetric complex Gaussian distribution.
- **Metrological Distinction — Systematic VNA Errors vs Random Receiver Noise:**
  - *Systematic Metrological Calibration:* Real VNA measurements are subject to systematic hardware imperfections removed via standard calibration standards (Short-Open-Load / SOLT):
    - **1-Port VNA Model:** Calibrating $S_{11}$ requires a **3-term error model** accounting for directivity ($e_{00}$), source match ($e_{11}$), and reflection tracking ($e_{10}e_{01}$).
    - **Full 2-Port VNA Model:** Calibrating all 4 S-parameters requires a **12-term error model** (or 8-term leaky model) accounting for forward/reverse directivity, crosstalk, source match, load match, and transmission/reflection tracking.
  - *Residual Stochastic Noise:* After systematic vector calibration, the residual uncertainty is dominated by random thermal receiver noise, modeled here by $\mathcal{CN}(0, \sigma^2)$. Formal metrological uncertainty analysis propagates this through calibration matrices (Williams, Wang, & Arz 2003, Marks 1991, Stumper 2005, Ridler & Salter 2007).
- **Literature Reference:** Williams, Wang, & Arz (2003); Marks (1991); Stumper (2005); Ridler & Salter (2007). *(Note: NIST Technical Note 1511 covers waveguide microwave power standards by Allen et al. (1999) and is distinct from VNA reflection uncertainty).*
- **Limitation:** In harsh industrial environments with switching converters or power electronics arcing, electromagnetic interference exhibits impulsive, heavy-tailed non-Gaussian characteristics.

---

### ASM-08: Unclipped Noise and Non-Passive Metric Handling
- **Assumption:** Measurement noise is not artificially clipped to the passive unit circle ($|\Gamma| \le 1.0$). Observed samples where $|\Gamma| > 1.0$ due to additive noise perturbations are preserved, and non-passive VSWR evaluates to NaN.
- **Physical Justification:** Metrologically, artificial clipping ($\Gamma \mapsto \Gamma / |\Gamma|$) introduces downward statistical bias into reflection magnitude and distorts the Gaussian noise profile. Passive-line VSWR is physically defined as $(1+|\Gamma|)/(1-|\Gamma|)$, which is singular at $|\Gamma|=1$ and physically meaningless (negative) for $|\Gamma|>1$. Returning NaN preserves mathematical integrity while notifying the engineer via UI alerts.
- **Literature Reference:** Keysight AN 1287-1; Stumper (2005).
- **Limitation:** Downstream algorithms expecting finite scalars must explicitly handle NaN values.

---

### ASM-09: Pure Real Termination Resistance for Quarter-Wave Matching
- **Assumption:** Quarter-wave transformer synthesis assumes that the load impedance to be matched is purely real: $Z_L = R_L \in \mathbb{R}^+$.
- **Physical Justification:** A quarter-wave transformer transforms impedance according to $Z_{\text{in}} = Z_t^2 / Z_L$. If $Z_L$ has an imaginary part $X_L \ne 0$, $Z_{\text{in}}$ will also possess a reactive component, preventing a pure real match to $Z_0$ without prior reactive cancellation. Complex loads require either stub tuning or an L-network.
- **Literature Reference:** Pozar (4th ed.), Section 5.4, p. 246.
- **Limitation:** If a user specifies a complex load $R + jX$, a single quarter-wave transformer cannot eliminate the reactive reflection unless preceded by a length of line that transforms the impedance to a pure real value.

---

### ASM-10: Uniform Frequency Spacing for IFFT Reflectometry
- **Assumption:** Frequency sweep data is sampled on a uniform grid with constant step $\Delta f = (f_{\text{max}} - f_{\text{min}}) / (N - 1)$.
- **Physical Justification:** Standard Fast Fourier Transform algorithms assume uniform spectral sampling. Non-uniform frequency spacing distorts the Fourier basis functions, producing severe phase jitter and false ghost peaks in the time domain. If non-uniform data is supplied, linear resampling is required.
- **Literature Reference:** Harris (1978); Keysight AN 5989-5723EN.
- **Limitation:** Linear interpolation of sparse or highly non-uniform frequency grids introduces high-frequency smoothing and slight attenuation of peak reflection magnitude.

---

### ASM-11: Coaxial Characteristic Impedance Optima ($30\,\Omega, 50\,\Omega, 60\,\Omega, 77\,\Omega$)
- **Assumption:** Standard coaxial systems operate at specific standardized characteristic impedances, primarily $50\,\Omega$ and $75\,\Omega$, which are rigorously rooted in physical electromagnetic optimization for coaxial geometry.
- **Physical Derivation & Optimality Proofs:**
  For a coaxial line with inner conductor radius $a$, outer conductor inner radius $b$, and dielectric relative permittivity $\varepsilon_r$:
  $$Z_0 = \frac{\eta_0}{2\pi\sqrt{\varepsilon_r}} \ln\left(\frac{b}{a}\right) \approx \frac{59.95}{\sqrt{\varepsilon_r}} \ln\left(\frac{b}{a}\right)\,\Omega$$
  1. **Maximum Peak RF Power Capacity ($30\,\Omega$):**
     Dielectric breakdown is initiated when the peak radial electric field at the inner conductor surface $E_{\text{max}} = V_0 / [a \ln(b/a)]$ exceeds the dielectric strength $E_d$. The transmitted power is $P = V_0^2 / (2 Z_0) \propto a^2 \ln(b/a)$. For a fixed outer radius $b$, setting $x = b/a$ and maximizing $f(x) = \frac{\ln x}{x^2}$ yields:
     $$\frac{d}{dx}\left[\frac{\ln x}{x^2}\right] = \frac{1 - 2\ln x}{x^3} = 0 \implies \ln x = \frac{1}{2} \implies \frac{b}{a} = \sqrt{e} \approx 1.649$$
     In air dielectric ($\varepsilon_r = 1$), this optimum impedance is:
     $$Z_{0,\text{opt-power}} = 59.95 \cdot \frac{1}{2} \approx 29.98\,\Omega \approx 30\,\Omega$$
  2. **Maximum DC / RF Voltage Rating ($60\,\Omega$):**
     To sustain the highest breakdown voltage $V_0$ for a given maximum allowable surface electric field $E_{\text{max}}$ and outer radius $b$, we maximize $V_0 = E_{\text{max}} a \ln(b/a) \propto \frac{\ln(b/a)}{b/a}$. Maximizing $g(x) = \frac{\ln x}{x}$ yields:
     $$\frac{d}{dx}\left[\frac{\ln x}{x}\right] = \frac{1 - \ln x}{x^2} = 0 \implies \ln x = 1 \implies \frac{b}{a} = e \approx 2.718$$
     In air dielectric ($\varepsilon_r = 1$), this optimum impedance is:
     $$Z_{0,\text{opt-voltage}} = 59.95 \cdot 1.0 \approx 59.95\,\Omega \approx 60\,\Omega$$
  3. **Minimum Conductor Attenuation ($77\,\Omega$ in air $\to 50.5\,\Omega$ in PE):**
     Conductor attenuation due to skin effect is governed by the surface resistance $R_s$:
     $$\alpha_c = \frac{R_s}{2 Z_0} \left(\frac{1}{2\pi a} + \frac{1}{2\pi b}\right) \propto \frac{1 + b/a}{b \ln(b/a)}$$
     Setting $x = b/a$ and minimizing $h(x) = \frac{1 + x}{\ln x}$ gives:
     $$\frac{d}{dx}\left[\frac{1 + x}{\ln x}\right] = \frac{\ln x - (1 + 1/x)}{\ln^2 x} = 0 \implies \ln x = 1 + \frac{1}{x}$$
     This transcendental equation solves numerically to $x = b/a \approx 3.5911$. In air ($\varepsilon_r = 1$):
     $$Z_{0,\text{min-loss, air}} = 59.95 \ln(3.5911) \approx 76.64\,\Omega \approx 75 - 77\,\Omega$$
     When filled with solid polyethylene dielectric ($\varepsilon_r \approx 2.26 - 2.3$), the minimum-attenuation characteristic impedance shifts downward by $1/\sqrt{\varepsilon_r}$:
     $$Z_{0,\text{min-loss, PE}} = \frac{76.64\,\Omega}{\sqrt{2.3}} \approx 50.5\,\Omega$$
  4. **The Standard $50\,\Omega$ Engineering Compromise:**
     Standardized during World War II radar and microwave development, $50\,\Omega$ represents an optimal practical engineering compromise between peak power capacity ($30\,\Omega$) and air attenuation ($77\,\Omega$). Coincidentally, $50\,\Omega$ almost exactly matches the minimum attenuation point for polyethylene coaxial cables ($50.5\,\Omega$), making it the universal standard for RF/microwave instrumentation. (It is not the arithmetic mean of $30\,\Omega$ and $77\,\Omega$, which would be $53.5\,\Omega$).
- **Literature Reference:** Pozar (4th ed.), Section 2.1; Collin (2nd ed.), Section 3.4; Ramo, Whinnery, & Van Duzer (3rd ed.), Section 5.3.

---

### ASM-12: Physical DC Phase Intercept ($\phi_0$) for Terminal Open/Short Classification
- **Assumption:** At DC ($f \to 0$), the electrical length of any finite uniform transmission line vanishes identically ($\beta(f)\ell = \frac{2\pi f}{v_p}\ell \to 0$). The unwrapped phase intercept $\phi_0 = \lim_{f \to 0} \text{unwrap}(\angle \Gamma(f))$ directly equals the intrinsic reflection angle $\angle \Gamma_L$, providing an analytical discriminator between open circuits ($\cos\phi_0 = +1.0$) and short circuits ($\cos\phi_0 = -1.0$).
- **Conditions and Operational Limits:**
  1. *Dominant Single Reflection:* The model assumes a single dominant terminal reflection without overlapping multiple echoes.
  2. *Phase-Unwrapping Sampling Limit:* To prevent $2\pi$ spatial phase aliasing during numerical phase unwrapping, the phase change between adjacent frequency samples must satisfy:
     $$\Delta \phi = \frac{4\pi d}{v_p} \Delta f < \pi \implies \Delta f < \frac{v_p}{4 d_{\text{max}}}$$
     For $d_{\text{max}} = 2.5\text{ m}$ and $\text{vf} = 0.66$, this requires frequency sampling step $\Delta f < 19.8\text{ MHz}$. Sweeps violating this condition experience unwrapping cycle slips.
  3. *Low-Frequency Extrapolation Noise Sensitivity:* Because microwave VNA sweeps begin at $f_{\text{min}} > 0$ (e.g., $200\text{ MHz} - 500\text{ MHz}$), $\phi_0$ is evaluated by linear regression extrapolation across $[0, f_{\text{min}}]$. Extrapolation uncertainty scales with the lever arm $f_{\text{min}} / \Delta f$. High receiver noise ($\sigma > 0.05$) induces slope jitter that can corrupt the sign of $\cos\phi_0$.
  4. *Goodness-of-Fit Verification ($R^2$):* Linear phase regression strictly assumes a single non-dispersive reflection. In the current implementation (`diagnosis.py:extract_features`), $\phi_0$ is estimated via first-order linear regression (`np.polyfit`) without evaluating or enforcing an $R^2$ threshold at runtime. Enforcing an $R^2 \ge 0.95$ threshold is a **recommended future safeguard** to flag non-linear phase distortion from severe dispersion or multi-fault reflections, but is not currently enforced as a runtime rejection criterion in the existing codebase.
  5. *Tested Parameter Range:* Validated in automated Monte Carlo testing across line lengths $\ell \in [0.5, 2.5]\text{ m}$, frequency bands $f_{\text{start}} \in [200, 600]\text{ MHz}$ to $f_{\text{stop}} \in [3000, 5000]\text{ MHz}$ ($N = 300$ points), discrete velocity factors $\text{vf} \in \{0.66, 0.70, 1.0\}$, and noise $\sigma = 0.02$.
- **Literature Reference:** Collin (2001), Ch. 3; Pozar (4th ed.), Sec. 2.3; Chang et al. (2026).

---

### ASM-13: Range Resolution Hierarchy and Zero-Padding
- **Assumption:** Fault location using IFFT-based Distance-to-Fault reflects a rigorous distinction between physical bandwidth resolution, effective windowed resolution, and display bin spacing:
  1. *Nominal Physical Resolution:* $\Delta R_{\text{nom}} = \frac{v_p}{2 B} = \frac{c_0 \cdot \text{vf}}{2 (f_{\text{max}} - f_{\text{min}})}$.
  2. *Windowed Effective Resolution:* Application of a Hann window broadens the impulse response mainlobe:
     - Under the **$-3\text{ dB}$ (half-power) pulse width** metric, the unwindowed rectangular width $\tau_{-3\text{dB}} \approx 0.886/B$ ($\Delta R_{-3\text{dB}} \approx 0.89 \Delta R_{\text{nom}}$) broadens to $\tau_{-3\text{dB}} \approx 1.437/B$ ($\Delta R_{-3\text{dB}} \approx 1.44 \Delta R_{\text{nom}}$), representing a broadening ratio of $\frac{1.437}{0.886} \approx 1.62$.
     - Under the **Equivalent Noise Bandwidth (ENBW)** metric, the Hann window expansion factor is $1.50$.
     - In exchange, windowing achieves $-31.5\text{ dB}$ sidelobe suppression, preventing spectral leakage from masking small nearby defects.
  3. *Display Interpolation Step:* Zero-padding to $N_{\text{pad}} \ge 4N$ points produces a display sampling grid $\delta d = \frac{v_p}{2 N_{\text{pad}} \Delta f}$.
- **Metrological Principle:** Zero-padding in the frequency domain is mathematically equivalent to bandlimited sinc interpolation in the spatial domain. It reduces visual discretization and peak scallop loss, but does **NOT** improve the physical two-fault resolution. Two physical discontinuities separated by less than the effective mainlobe width merge into a single broad peak that cannot be separated by zero-padding.
- **Literature Reference:** Keysight AN 5989-5723EN; Anritsu AN 11410-00373; Harris (1978).

---

## 3. Verified Reference Citations

1. **Pozar, D. M.** (2012). *Microwave Engineering*, 4th ed., John Wiley & Sons, Hoboken, NJ. ISBN: 978-0-470-63155-3.
2. **Collin, R. E.** (2001). *Foundations for Microwave Engineering*, 2nd ed., IEEE Press / Wiley-Interscience, New York. ISBN: 978-0-7803-6031-0.
3. **Ramo, S., Whinnery, J. R., & Van Duzer, T.** (1994). *Fields and Waves in Communication Electronics*, 3rd ed., John Wiley & Sons, New York. ISBN: 978-0-471-58551-0.
4. **Furse, C. M., Kafal, M., Razzaghi, R., & Shin, Y.-J.** (2021). "Fault Diagnosis for Electrical Systems and Power Networks: A Review," *IEEE Sensors Journal*, vol. 21, no. 2, pp. 888–906, Jan. 2021. DOI: [10.1109/JSEN.2020.2987321](https://doi.org/10.1109/JSEN.2020.2987321).
5. **Chang, K., Xu, Z., Zhang, G., & Wang, L.** (2026). "Fault Location and Evaluation in Coaxial Cables Based on Stepped Frequency Waveform Reflectometry and Electromagnetic Time Reversal," *IEEE Transactions on Instrumentation and Measurement*, vol. 75, Art. no. 3503811, pp. 1–11, Jan. 2026. DOI: [10.1109/TIM.2026.3657555](https://doi.org/10.1109/TIM.2026.3657555).
6. **Liu, C., Hou, Y., Duan, Z., Shang, R., Wang, K., & Chen, D.** (2024). "Underground Power Cable Fault Detection and Localization Based on the Spectrum of Propagation Functions," *IEEE Transactions on Instrumentation and Measurement*, vol. 73, Art. no. 3530211, pp. 1–11, 2024. DOI: [10.1109/TIM.2024.3453315](https://doi.org/10.1109/TIM.2024.3453315).
7. **Shi, X., Li, R., Zhang, H., & Liu, Y.** (2022). "Application of Augmented Spread Spectrum Time Domain Reflectometry for Detection and Localization of Soft Faults on a Coaxial Cable," *IEEE Transactions on Aerospace and Electronic Systems*, vol. 58, no. 6, pp. 4891–4901, Dec. 2022. DOI: [10.1109/TAES.2022.3184913](https://doi.org/10.1109/TAES.2022.3184913).
8. **Song, C., Mu, H., Zou, X., & Zhang, G.** (2025). "Application of stepped-frequency waveform reflectometry to locating and characterizing line-like aging faults in cables," *Measurement*, vol. 254, Art. no. 117866, pp. 1–12, Oct. 2025. DOI: [10.1016/j.measurement.2025.117866](https://doi.org/10.1016/j.measurement.2025.117866).
9. **Rao, X., Xu, Z., Guan, H., Ding, Y., Yang, X., & Yang, Y.** (2023). "Cable Defect Location by Using Frequency Domain Reflectometry With Synchrosqueezing Generalized S-Transform," in *2023 Panda Forum on Power and Energy (PandaFPE)*, pp. 1178–1182, 2023. DOI: [10.1109/PandaFPE57779.2023.10140514](https://doi.org/10.1109/PandaFPE57779.2023.10140514).
10. **Song, E.-S., Shin, Y.-J., Stone, P. E., Wang, J., Choe, T.-S., Yook, J.-G., & Park, J.-B.** (2009). "Detection and Location of Multiple Wiring Faults via Time–Frequency-Domain Reflectometry," *IEEE Transactions on Electromagnetic Compatibility*, vol. 51, no. 1, pp. 131–138, Feb. 2009. DOI: [10.1109/TEMC.2008.2007964](https://doi.org/10.1109/TEMC.2008.2007964).
11. **Kingston, S., Benoit, E., Edun, A. S., et al.** (2021). "A SSTDR Methodology, Implementations, and Challenges," *Sensors*, vol. 21, no. 16, p. 5268, Aug. 2021. DOI: [10.3390/s21165268](https://doi.org/10.3390/s21165268).
12. **Williams, D. F., Wang, J. C. M., & Arz, U.** (2003). "An Optimal Vector-Network-Analyzer Calibration Algorithm," *IEEE Transactions on Microwave Theory and Techniques*, vol. 51, no. 12, pp. 2391–2401, Dec. 2003. DOI: [10.1109/TMTT.2003.819211](https://doi.org/10.1109/TMTT.2003.819211).
13. **Marks, R. B.** (1991). "A Multiline Method of Network Analyzer Calibration," *IEEE Transactions on Microwave Theory and Techniques*, vol. 39, no. 7, pp. 1205–1215, July 1991. DOI: [10.1109/22.85388](https://doi.org/10.1109/22.85388).
14. **Stumper, U.** (2005). "Uncertainty of VNA S-Parameter Measurement Due to Nonideal TRL Calibration Items," *IEEE Transactions on Instrumentation and Measurement*, vol. 54, no. 2, pp. 676–679, Apr. 2005. DOI: [10.1109/TIM.2005.843521](https://doi.org/10.1109/TIM.2005.843521).
15. **Ridler, N. M., & Salter, M. J.** (2007). "Evaluating and Expressing Uncertainty in S-Parameter Measurements," *Metrologia*, vol. 44, no. 4, pp. 292–299, 2007. DOI: [10.1088/0026-1394/44/4/007](https://doi.org/10.1088/0026-1394/44/4/007).
16. **Harris, F. J.** (1978). "On the Use of Windows for Harmonic Analysis with the Discrete Fourier Transform," *Proceedings of the IEEE*, vol. 66, no. 1, pp. 51–83, Jan. 1978. DOI: [10.1109/PROC.1978.10837](https://doi.org/10.1109/PROC.1978.10837).
17. **Keysight Technologies** (2020). *Time Domain Analysis Using a Network Analyzer*, Application Note 5989-5723EN, Keysight Technologies, Santa Rosa, CA.
18. **Keysight Technologies** (2021). *Understanding the Fundamental Principles of Vector Network Analysis*, Application Note 1287-1, Keysight Technologies, Santa Rosa, CA.
19. **Anritsu Company** (2018). *Distance-to-Fault (DTF) Measurement Fundamentals*, Application Note 11410-00373, Anritsu Company, Morgan Hill, CA.