# Research Gap Analysis and Benchmarking Report

**Project:** RF LINE DOCTOR — Virtual Transmission-Line Fault Diagnosis & Matching  
**Course:** EC-3104 (Electromagnetic Waves and Transmission Lines)  

---

## 1. Executive Summary

This document presents a structured engineering comparison and critical literature benchmarking between:
1. **The Reference Project:** The Hackhash07 GitHub repository (`Transmission-Line-Fault-Diagnosis`), representative of existing open-source undergraduate implementations.
2. **Commercial RF Test Instruments:** Industry-standard portable cable and antenna analyzers (e.g., Keysight FieldFox N9918B, Anritsu Site Master S331L, Rohde & Schwarz Cable Rider ZPH).
3. **Peer-Reviewed State of the Art (2022–2026):** Contemporary reflectometry and cable diagnostic literature (e.g., Chang et al. 2026, Liu et al. 2024, Shi et al. 2022, Song et al. 2025, Rao et al. 2023, Furse et al. 2021, Kingston et al. 2021, Song et al. 2009).
4. **RF LINE DOCTOR (This Work):** Our verified virtual software diagnostic platform.

---

## 2. Multi-Dimensional Comparison Matrix

| Evaluation Dimension | Reference Project (`Hackhash07`) | Commercial Instruments (Keysight / Anritsu / R&S) | Academic Research Literature (2022–2026) | RF LINE DOCTOR (Current Implementation) |
| :--- | :--- | :--- | :--- | :--- |
| **Transmission Line Model** | Ideal lossless line with numerical approximations | Calibrated real lines with loss, dispersion, and phase-velocity tables | Lossy, dispersive, frequency-dependent Telegrapher models ($\alpha(f), \beta(f)$) | Exact lossless model ($\alpha = 0, \beta = 2\pi f / v_p$) benchmarked to analytical theory |
| **Open Circuit Simulation** | Artificial finite load ($Z_L = 10^9\,\Omega$) to avoid zero-division in $\tanh$ | Physical open-circuit calibration standard | Exact analytical limit: $Z_L \to \infty \implies \Gamma_L = +1.0$ | Exact mathematical limit $Z_L = \infty \implies \Gamma_L = +1.0$ and $Z_{\text{in}} = -j Z_0 \cot(\beta\ell)$ |
| **Discontinuity Simulation** | Basic terminal load variations only | Time-domain gating of physical connectors and adapters | 2-port ABCD cascading and transmission-line matrix (TLM) | Cascaded 2-port ABCD formulation for intermediate series $L$ and shunt $C$ discontinuities |
| **Measurement Noise Modeling** | None (ideal noiseless waveforms only) | Hardware noise floor (DANL $\approx -140\text{ dBm}$), trace noise, receiver dynamic range | Complex additive Gaussian or measured industrial noise profiles | Complex circular Gaussian noise $\mathcal{CN}(0, \sigma^2)$ without artificial clipping; NaN VSWR |
| **Open vs Short Classification** | Prone to phase ambiguity (fails at high frequencies) | High-accuracy polar display; calibrated phase reference planes | Machine learning classifiers; time-domain peak polarity; phase-slope analysis | **Physics-Based DC Phase Intercept ($\cos\phi_0$):** 100% recall (40/40 open, 40/40 short) |
| **Fault Localization** | Basic heuristic peak detection | Chirp-Z Transform (CZT) / Windowed IFFT DTF with gating | SSTDR, TFDR, EM Time Reversal, Generalized S-Transforms | Dual-Method: Hann-windowed IFFT pseudo-TDR + unwrapped phase slope cross-check |
| **Resolution Reporting** | Unclear distinction between FFT bins and resolution | Rigorous separation of resolution $\Delta R$ and display points | Theoretical Cramer-Rao Lower Bounds and Rayleigh limits | Clear distinction: Rayleigh limit $\Delta R_{\text{nom}} = v_p / 2B$, windowed $\Delta R_{\text{eff}}$, vs display step $\delta d$ |
| **Impedance Matching** | Basic single-frequency formula | VNA Smith chart marker readouts | Multi-section broadband matching, Chebychev/Binomial | Exact $\lambda/4$ synthesis with contiguous passband evaluation ($\text{RL} \ge 20\text{ dB}$) |
| **User Interface** | Basic Streamlit script with minimal interactive controls | Dedicated embedded instrument firmware | Custom MATLAB/Python research scripts | 8-section dark-themed engineering Streamlit dashboard with live validation lab |
| **Test & Validation Suite** | No formal automated test suite | Metrology laboratory calibration standards (ISO 17025) | Monte Carlo simulations on synthetic/measured datasets | 102 automated pytest unit/integration tests + automated simulation validation lab |

---

## 3. The Eight Canonical Reflectometry Paradigms

In modern microwave engineering and cable diagnostics, reflectometry methods are classified into eight distinct operational paradigms (Furse et al. 2021, Kingston et al. 2021, Chang et al. 2026):

1. **Continuous-Wave Frequency-Domain Reflectometry (CW FDR-IFFT):**
   - Sweeps continuous sinusoidal tones across bandwidth $B$, measures complex reflection coefficient $S_{11}(f)$, applies windowing, and computes inverse FFT to synthesize the spatial impulse response.
   - *Status in RF Line Doctor:* Fully implemented as the primary Distance-to-Fault localization engine (`diagnosis.py`, `core/fault_location.py`).
2. **Phase-Slope Analysis / Phase Gradient Reflectometry:**
   - Evaluates the derivative of the unwrapped reflection phase with respect to frequency: $d\phi / df = -4\pi d / v_p$.
   - *Status in RF Line Doctor:* Implemented as an independent analytical cross-check (`core/fault_location.py`).
3. **Pulse Time-Domain Reflectometry (Pulse TDR):**
   - Injects a high-speed sub-nanosecond baseband step or impulse voltage into the cable and records reflected echoes directly on a high-bandwidth equivalent-time sampling oscilloscope.
   - *Status in RF Line Doctor:* Emulated mathematically via IFFT synthesization (synthetic TDR).
4. **Spread-Spectrum Time-Domain Reflectometry (SSTDR):**
   - Modulates pseudo-noise (PN) digital sequences onto high-frequency sinusoidal carriers, allowing live in-situ testing on energized cables carrying live signals (Kingston et al. 2021, Shi et al. 2022).
   - *Status in RF Line Doctor:* Documented as a specialized industrial extension for energized wiring.
5. **Time-Frequency Domain Reflectometry (TFDR):**
   - Transmits Gaussian-enveloped linear chirp pulses and computes cross-time-frequency distributions (Wigner-Ville distribution) to provide optimal localization under heavy cable dispersion and attenuation (Song et al. 2009).
   - *Status in RF Line Doctor:* Positioned in the research roadmap (Phase III).
6. **Noise-Domain Reflectometry (NDR):**
   - Transmits pseudorandom thermal noise sequences and computes cross-correlation with returning reflections, maximizing electromagnetic compatibility (EMC) and low probability of intercept.
   - *Status in RF Line Doctor:* Documented in literature taxonomy.
7. **Multiple-Reflection Analysis & Matrix Pencil De-embedding:**
   - Evaluates iterative multi-echo reverberations between cascaded discontinuities using transmission-line scattering matrices or Prony/Matrix-Pencil spectral estimation to reconstruct full spatial impedance profiles (Liu et al. 2024, Chang et al. 2026).
   - *Status in RF Line Doctor:* ABCD forward modeling implemented; full spatial inverse de-embedding positioned for future research.
8. **Frequency-Domain Impedance Spectroscopy (FDIS):**
   - Measures complex terminal impedance over broadband spectra to identify distributed aging phenomena, water ingress, or chemical dielectric insulation breakdown (Song et al. 2025).
   - *Status in RF Line Doctor:* Covered via wideband input impedance transformation analysis.

---

## 4. Analysis of Critical Technical Gaps & Solutions

### 4.1 The High-Frequency Phase De-Embedding Breakdown
- **Defect in Existing Tools:** Most existing educational implementations de-embed the reflection coefficient to the estimated fault plane by multiplying by $\exp(+2j\beta d_{\text{est}})$. However, at microwave frequencies (e.g., $4\text{ GHz}$ in a polyethylene cable with $\text{vf} = 0.66$), the guided wavelength is only $\lambda \approx 4.95\text{ cm}$. A quarter-wavelength is a mere $1.24\text{ cm}$. If the estimated distance $d_{\text{est}}$ has a discretization error of just $6\text{ mm}$ (a fraction of an FFT bin), the round-trip phase rotates by $\approx 180^\circ$. This flips the sign of $\text{Re}(\Gamma_{\text{de-embedded}})$, causing short circuits ($\Gamma_L = -1$) to be erroneously classified as open circuits ($\Gamma_L = +1$). In the initial baseline audit, this caused 18 of 40 short cases to fail.
- **RF Line Doctor Solution:** Rather than relying on microwave phase de-embedding, we formulated the **DC Phase Intercept Principle**:
  $$\phi(f) = \text{unwrap}(\angle \Gamma(f)) = \phi_0 + m f$$
  $$\phi_0 = \lim_{f \to 0} \angle \Gamma(f) = \angle \Gamma_L$$
  As frequency approaches zero, the electrical line length $\beta(f)\ell = \frac{2\pi f}{v_p}\ell \equiv 0$ vanishes identically. The phase intercept $\phi_0$ at DC is completely immune to distance discretization errors and line length, providing an exact analytical discriminator: $\cos(\phi_0) = +1.0$ for open circuits and $\cos(\phi_0) = -1.0$ for short circuits.
- **Implementation Reality & Future Safeguard:** In the current implementation (`diagnosis.py:extract_features`), $\phi_0$ is estimated via first-order linear regression (`np.polyfit`) without evaluating or enforcing an $R^2$ threshold at runtime. Enforcing an $R^2 \ge 0.95$ threshold is a **recommended future safeguard** to flag non-linear phase distortion from severe dispersion or multi-fault reflections, but is not currently enforced as a runtime rejection criterion in the existing codebase.

### 4.2 Artificial Noise Clipping vs Metrological Noise Handling
- **Defect in Existing Tools:** Academic software frequently enforces $|\Gamma| \le 1.0$ by clipping noisy vectors: $\Gamma_{\text{clipped}} = \Gamma / |\Gamma|$. This is unphysical, distorts noise statistics, and masks receiver noise.
- **RF Line Doctor Solution:** Retains unclipped complex circular Gaussian noise $\Gamma_{\text{meas}} = \Gamma_{\text{ideal}} + \mathcal{CN}(0, \sigma^2)$. Evaluates non-passive noisy points ($|\Gamma| > 1.0$) as `np.nan` in the VSWR equation, avoiding runtime crashes while notifying the engineer via descriptive UI warnings.

### 4.3 Artificial Discontinuity Workarounds vs Cascaded ABCD Matrices
- **Defect in Existing Tools:** Intermediate connector discontinuities are either ignored entirely or modeled as an artificial termination resistance (e.g., $10^9\,\Omega$ for open).
- **RF Line Doctor Solution:** Formulated true 2-port ABCD matrix cascading:
  $$\mathbf{M}_{\text{total}} = \mathbf{M}_{\text{line}}(d) \cdot \mathbf{M}_{\text{disc}} \cdot \mathbf{M}_{\text{line}}(\ell - d)$$
  This accommodates intermediate series inductance ($Z_s = j\omega L$) and shunt capacitance ($Y_p = j\omega C$) with exact boundary evaluation for open ($A/C$) and short ($B/D$) terminations.

### 4.4 Discontinuous Passband Aggregation vs Contiguous Bandwidth
- **Defect in Existing Tools:** In quarter-wave matching modules, passband bandwidth is commonly calculated as `f[mask][-1] - f[mask][0]` across any frequency where $\text{RL} \ge 20\text{ dB}$. If the frequency sweep spans higher harmonic frequencies ($3f_0, 5f_0$), the transformer exhibits recurring harmonic passbands. The conventional formula spans across the stopbands, erroneously reporting a massive, unphysical bandwidth.
- **RF Line Doctor Solution:** Locates the exact design frequency index $k_0 = \arg\min |f - f_0|$ and expands contiguous boundaries left and right while $\text{RL}(f) \ge \text{threshold}$. If the threshold is not satisfied at $f_0$, the returned bandwidth is reported as $0.0\text{ Hz}$.

---

## 5. Simulation-Based Validation & Robustness Analysis

### 5.1 Monte Carlo Simulation Validation Benchmarking
The classification engine was evaluated using an automated Monte Carlo simulation test bench (`validation/run_validation.py`) consisting of **$N = 240$ randomized synthetic transmission-line trials** across six distinct physical fault scenarios (40 samples per scenario). The simulation parameters were:
- Swept Frequency Band: $f_{\text{start}} \in [200, 600]\text{ MHz}$ to $f_{\text{stop}} \in [3000, 5000]\text{ MHz}$ ($N_{\text{pts}} = 300$ points)
- Cable Length: $\ell \in [0.5, 2.5]\text{ m}$
- Velocity Factor: Discrete values $\text{vf} \in \{0.66, 0.70, 1.0\}$
- Characteristic Impedance: $Z_0 \in \{50.0, 75.0\}\,\Omega$
- Intermediate Discontinuity Parameters: $L \in [2, 40]\text{ nH}$, $C \in [2, 40]\text{ pF}$
- Terminal Mismatch Impedance: $Z_L \in \{0.4 Z_0, 0.7 Z_0, 1.5 Z_0, 2.5 Z_0\}$
- Measurement Noise Level: $\sigma = 0.02$

#### Empirical Results at $\sigma = 0.02$
- **5-Class Public Contract Accuracy:** **99.58%** (239 / 240 correct)
- **6-Scenario Physical Subtype Accuracy:** **99.58%** (239 / 240 correct)
- **Fault Location Mean Absolute Error (MAE):** **0.16 cm** (1.6 mm)
- **Fault Location RMSE:** **0.22 cm** (2.2 mm)

#### Empirical Contract Confusion Matrix ($N = 240$, $\sigma = 0.02$)
*(Exported from `results/csv/confusion_matrix.csv`)*

| True Class \ Predicted Class | Healthy | Open | Short | Mismatch | Unknown | Total | Recall |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Healthy** | **40** | 0 | 0 | 0 | 0 | 40 | **100.0%** |
| **Open** | 0 | **40** | 0 | 0 | 0 | 40 | **100.0%** |
| **Short** | 0 | 0 | **40** | 0 | 0 | 40 | **100.0%** |
| **Mismatch** (Cluster: Mismatch + Series L + Shunt C) | 0 | 0 | 1 | **119** | 0 | 120 | **99.2%** |
| **Unknown** | 0 | 0 | 0 | 0 | 0 | 0 | N/A |
| **Total** | 40 | 40 | 41 | 119 | 0 | 240 | **99.58%** |

### 5.2 Full Noise-Sensitivity Degradation Analysis

To establish empirical operating boundaries, tests were executed across six discrete complex noise standard deviations: $\sigma \in \{0.0, 0.02, 0.05, 0.08, 0.12, 0.18\}$.

#### Empirical Accuracy vs Noise Profile
*(Exported directly from `results/csv/noise_sensitivity.csv`)*

| Complex Noise Std Dev ($\sigma$) | Classification Accuracy (%) | Operational Status |
| :---: | :---: | :--- |
| **0.00** | **98.33%** | Fully Operational (Minor noiseless boundary artifact in healthy class) |
| **0.02** | **100.00%** | Fully Operational (Nominal Operating Baseline) |
| **0.05** | **61.67%** | Degraded (Reactive trend threshold breakdown) |
| **0.08** | **50.00%** | Severely Degraded (Majority-class baseline) |
| **0.12** | **50.00%** | Non-operational (Majority-class baseline) |
| **0.18** | **50.00%** | Non-operational (Majority-class baseline) |

#### Methodological Structure & Physical Mechanisms:
1. **Cohort Structure (Not Paired Experiments):** At each noise level, 20 samples per physical scenario across 6 scenarios were generated ($N = 120$ samples per noise level). Each noise level uses a distinct random seed (`seed = 100 + int(n_sigma * 100)`). Therefore, these are **not paired experiments** on identical cables, but independent randomized cohorts evaluated at each discrete noise standard deviation.
2. **Omission of Noise-Dependent MAE:** The validation runner exports classification accuracy vs noise into `results/csv/noise_sensitivity.csv`. Because noise-dependent fault location MAE is not computed across the noise sweep, unsupported numerical distance error claims have been omitted.
3. **Physical Degradation Mechanism:** The degradation at $\sigma \ge 0.05$ occurs because additive circular Gaussian receiver noise distorts the subtle monotonic reflection magnitude trend ($\Delta |\Gamma| / \Delta f$) and phase signatures produced by intermediate reactances ($L \in [2, 40]\text{ nH}$, $C \in [2, 40]\text{ pF}$), causing reactive rules to fail and default to healthy or mismatch.
4. **Explanation of the 50.0% Asymptotic Floor:** The 50.0% high-noise result is **not** a random-guessing baseline (which would be 20% for 5 classes). Instead, it reflects class imbalance in the frozen contract mapping: three physical scenarios (`mismatch`, `series_L`, `shunt_C`) are all mapped to the contract target label `"mismatch"`. Because each scenario comprises 20 samples, `"mismatch"` accounts for $60 / 120 = 50.0\%$ of the generated dataset. When high noise obscures subtle reactive and healthy signatures, predictions collapse toward `"mismatch"`, resulting in a 50.0% accuracy that represents the majority-class baseline of this 3-scenario contract mapping.

### 5.3 Critical Evaluation of Unknown-Class Rejection Limitation
> [!WARNING]
> **Validation Boundary on Unknown-Class Rejection:**
> In the Monte Carlo validation suite above, all $N = 240$ test samples belonged to one of the six modeled physical classes. Consequently, the rejection rate for truly unmodeled anomalies (e.g., distributed multi-faults, non-TEM waveguide modes, or nonlinear active reflections) has **not been experimentally or numerically validated ($N = 0$ true unknown samples)**. While the software architecture contains an internal anomaly threshold (`UNKNOWN` fallback when feature confidence is below threshold), formal validation of this boundary requires future generation of out-of-distribution physical test datasets.

---

## 6. Range Resolution Hierarchy and Zero-Padding Principles

To prevent confusion between physical instrument resolution and digital display sampling, RF Line Doctor enforces the following formal definitions:

1. **Nominal Bandwidth Resolution (Rayleigh Limit, $\Delta R_{\text{nom}}$):**
   $$\Delta R_{\text{nom}} = \frac{v_p}{2 B} = \frac{c_0 \cdot \text{vf}}{2 (f_{\text{max}} - f_{\text{min}})}$$
   This represents the fundamental physical resolution limit set by the swept bandwidth $B$.
2. **Effective Windowed Resolution ($\Delta R_{\text{eff}}$):**
   Applying a Hann window suppresses sidelobes from $-13\text{ dB}$ down to $-31.5\text{ dB}$, trading two-point separation for spectral dynamic range:
   - Under the **$-3\text{ dB}$ (half-power) mainlobe pulse width** metric, an unwindowed rectangular impulse has temporal width $\tau_{-3\text{dB}} \approx 0.886 / B$ ($\Delta R_{-3\text{dB}} \approx 0.89 \Delta R_{\text{nom}}$), whereas a Hann-windowed impulse has width $\tau_{-3\text{dB}} \approx 1.437 / B$ ($\Delta R_{-3\text{dB}} \approx 1.44 \Delta R_{\text{nom}}$). The window broadening ratio is $\frac{1.437}{0.886} \approx 1.62$.
   - Under the **Equivalent Noise Bandwidth (ENBW)** metric, the Hann window expansion factor is exactly $1.50$.
   - Therefore, depending on whether measured by half-power mainlobe width ($1.62$ factor) or noise equivalence ($1.50$ factor), windowing broadens the effective resolution cell beyond $\Delta R_{\text{nom}}$.
3. **Display Sampling Step ($\delta d$):**
   $$\delta d = \frac{v_p}{2 N_{\text{pad}} \Delta f} = \frac{R_{\text{max}}}{N_{\text{pad}}}$$
   This is the distance interval between adjacent output points of the zero-padded IFFT ($N_{\text{pad}} \ge 4N$).
4. **Physical Limitation of Zero-Padding:**
   Zero-padding in the frequency domain is mathematically identical to trigonometric (sinc) interpolation in the spatial domain. It smooths the visual waveform, reduces display binning jitter, and eliminates peak scallop amplitude errors. **However, zero-padding does NOT improve physical two-fault resolution.** If two physical discontinuities are separated by less than $\Delta R_{\text{eff}}$, their responses merge into a single overlapping mainlobe that cannot be resolved into two peaks by zero-padding.

---

## 7. Scope Boundaries & Future Research Roadmap

### 7.1 Educational Baseline Justification
- **Lossless Line Baseline ($\alpha = 0$):**
  Mandated by `INTERFACES.md` and the EC-3104 undergraduate syllabus to maintain mathematical clarity and alignment with analytical hand calculations. While short laboratory cables at VHF frequencies exhibit low insertion loss, high-frequency real cables (e.g., RG-58 at $5\text{ GHz}$) exhibit attenuation of $\approx 1.6 - 2.0\text{ dB/m}$, which depresses reflection peaks and spirals the Smith chart locus inward.
- **Single Dominant Discontinuity:**
  Focuses on the primary impedance discontinuity or terminal fault. Multi-fault reverberations are intentionally isolated for advanced coursework.

### 7.2 Post-Course Research & Development Roadmap
1. **Phase II (Dispersive & Lossy Line Modeling):**
   Incorporate frequency-dependent skin effect $R'(f) \propto \sqrt{f}$ and dielectric loss tangent $G'(f) = \omega C' \tan\delta$, evaluating the complex propagation constant $\gamma(f) = \alpha(f) + j\beta(f)$ and frequency-dependent characteristic impedance $Z_0(f)$.
2. **Phase III (Time-Frequency Domain Reflectometry - TFDR):**
   Implement Gaussian chirp excitation with Wigner-Ville distribution cross-correlation as formulated by Song et al. (2009) to provide optimal fault localization under severe cable dispersion.
3. **Phase IV (Hardware-in-the-Loop VNA Integration):**
   Connect the Streamlit interface via PyVISA and SCPI commands to physical benchtop VNAs (Keysight E5063A, Rohde & Schwarz ZND) or USB instruments (NanoVNA) to ingest live Touchstone (`.s1p`) measurements.

---

## 8. Complete Verified References

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