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
- **Physical Justification:** 
  1. For short educational laboratory cables ($\ell \le 2.5\text{ m}$) at VHF/UHF frequencies, total cable insertion loss is typically $< 0.3\text{ dB}$, which has negligible impact on reflection magnitude ($|\Gamma|$) and resonant impedance peaks.
  2. Mandated by the frozen project specification (`INTERFACES.md`, line 4) and EC-3104 undergraduate syllabus to maintain mathematical clarity and tractability.
- **Literature Reference:** Pozar (4th ed.), Section 2.3, p. 57; Collin (2nd ed.), Section 3.1.
- **Limitation:** On long cables ($\ell > 50\text{ m}$), conductor skin effect ($R' \propto \sqrt{f}$) and dielectric loss ($G' \propto f$) attenuate the reflected wave by $e^{-2\alpha d}$, causing reflections to appear weaker and the Smith-chart locus to spiral inward toward the center.

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
- **Assumption:** Measurement noise is modeled as complex additive Gaussian noise with equal variance $\sigma^2/2$ on real (in-phase) and imaginary (quadrature) S-parameter channels.
- **Physical Justification:** VNAs use heterodyne receivers with quadrature downconversion (I/Q mixers) and digital filtering. By the Central Limit Theorem, the combination of thermal noise, local oscillator phase jitter, and quantization noise produces circular complex Gaussian noise.
- **Literature Reference:** NIST Technical Note 1511; Stumper (2005); Ridler & Salter (2007).
- **Limitation:** In environments with heavy external impulsive electromagnetic interference (EMI) or power electronics arcing, noise may exhibit heavy-tailed non-Gaussian (Laplacian or impulsive) distributions.

---

### ASM-08: Unclipped Noise and Non-Passive Metric Handling
- **Assumption:** Measurement noise is not artificially clipped to $|\Gamma| \le 1.0$. Observed samples where $|\Gamma| > 1.0$ are preserved, and non-passive VSWR evaluates to NaN.
- **Physical Justification:** Metrologically, artificial clipping introduces downward statistical bias into reflection magnitude and distorts the Gaussian noise profile. Passive-line VSWR is physically defined as $(1+|\Gamma|)/(1-|\Gamma|)$, which is singular at $|\Gamma|=1$ and physically meaningless (negative) for $|\Gamma|>1$. Returning NaN preserves mathematical integrity while notifying the engineer via UI alerts.
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
