# Theoretical Foundations — RF LINE DOCTOR

This document presents the complete mathematical formulations, derivations, boundary conditions, and analytical proofs underlying the **RF LINE DOCTOR** software architecture.

---

## 1. Transmission-Line Telegrapher's Equations & Wave Solutions

For a uniform, distributed transmission line oriented along the $z$-axis with series inductance per unit length $L'$ ($\text{H/m}$), series resistance $R'$ ($\Omega/\text{m}$), shunt capacitance $C'$ ($\text{F/m}$), and shunt conductance $G'$ ($\text{S/m}$), the governing differential equations in the frequency domain with $e^{j\omega t}$ time convention are:

$$\frac{dV(z)}{dz} = -(R' + j\omega L') I(z)$$

$$\frac{dI(z)}{dz} = -(G' + j\omega C') V(z)$$

Differentiating yields the uncoupled Helmholtz wave equations:

$$\frac{d^2 V(z)}{dz^2} - \gamma^2 V(z) = 0, \quad \frac{d^2 I(z)}{dz^2} - \gamma^2 I(z) = 0$$

where $\gamma = \alpha + j\beta = \sqrt{(R' + j\omega L')(G' + j\omega C')}$ is the complex propagation constant.

### Lossless Approximation ($\alpha = 0$)
In a lossless line ($R' = 0, G' = 0$):
$$\gamma = j\beta = j\omega\sqrt{L'C'}$$
$$\alpha = 0, \quad \beta = \omega\sqrt{L'C'} = \frac{2\pi f}{v_p}$$

The characteristic impedance is real and positive:
$$Z_0 = \sqrt{\frac{L'}{C'}} \in \mathbb{R}^+$$

Phase velocity $v_p$ and wavelength $\lambda$:
$$v_p = \text{vf} \cdot c_0 = \frac{1}{\sqrt{\mu \varepsilon}} = \frac{c_0}{\sqrt{\varepsilon_{r,\text{eff}}}}$$
$$\lambda = \frac{v_p}{f}$$

---

## 2. Voltage, Current, and Reflection Coefficient

The general solutions for the forward-traveling wave ($V_0^+ e^{-j\beta z}$) and reverse-traveling wave ($V_0^- e^{+j\beta z}$) are:
$$V(z) = V_0^+ e^{-j\beta z} + V_0^- e^{+j\beta z}$$
$$I(z) = \frac{V_0^+}{Z_0} e^{-j\beta z} - \frac{V_0^-}{Z_0} e^{+j\beta z}$$

Defining the coordinate $d = l - z$ measured from the load ($d = 0$) toward the source ($d = l$):
$$V(d) = V_0^+ e^{-j\beta l} \left( e^{j\beta d} + \Gamma_L e^{-j\beta d} \right)$$
$$I(d) = \frac{V_0^+}{Z_0} e^{-j\beta l} \left( e^{j\beta d} - \Gamma_L e^{-j\beta d} \right)$$

### Load Reflection Coefficient ($\Gamma_L$)
At the load boundary ($d = 0$), $Z_L = V(0) / I(0)$:
$$\Gamma_L = \frac{V_0^-}{V_0^+} = \frac{Z_L - Z_0}{Z_L + Z_0}$$

### Generalized Reflection Coefficient at Distance $d$
$$\Gamma(d) = \frac{V_{\text{reflected}}(d)}{V_{\text{incident}}(d)} = \Gamma_L e^{-2j\beta d}$$

---

## 3. Input Impedance Derivation & Boundary Formulations

The input impedance at distance $d = l$ from the termination is:
$$Z_{\text{in}} = \frac{V(l)}{I(l)} = Z_0 \frac{e^{j\beta l} + \Gamma_L e^{-j\beta l}}{e^{j\beta l} - \Gamma_L e^{-j\beta l}} = Z_0 \frac{1 + \Gamma(l)}{1 - \Gamma(l)}$$

Substituting $\Gamma_L = \frac{Z_L - Z_0}{Z_L + Z_0}$ yields the classic Euler form:
$$Z_{\text{in}} = Z_0 \left[ \frac{Z_L + j Z_0 \tan(\beta l)}{Z_0 + j Z_L \tan(\beta l)} \right]$$

### Exact Boundary Limits
1. **Matched Load ($Z_L = Z_0$):**
   $$\Gamma_L = 0 \implies Z_{\text{in}} = Z_0 \quad (\forall l, \beta)$$
2. **Short Circuit ($Z_L = 0$):**
   $$\Gamma_L = -1 \implies Z_{\text{in}} = +j Z_0 \tan(\beta l)$$
   - At $l = \lambda/8$ ($\beta l = \pi/4$): $Z_{\text{in}} = +j Z_0$ (pure inductive reactance).
   - At $l = \lambda/4$ ($\beta l = \pi/2$): $Z_{\text{in}} \to \infty$ (parallel resonant tank / virtual open).
   - At $l = \lambda/2$ ($\beta l = \pi$): $Z_{\text{in}} = 0$ (short circuit reproduced).
3. **Open Circuit ($Z_L = \infty$):**
   $$\Gamma_L = +1 \implies Z_{\text{in}} = -j Z_0 \cot(\beta l)$$
   - At $l = \lambda/8$ ($\beta l = \pi/4$): $Z_{\text{in}} = -j Z_0$ (pure capacitive reactance).
   - At $l = \lambda/4$ ($\beta l = \pi/2$): $Z_{\text{in}} = 0$ (series resonant tank / virtual short).
   - At $l = \lambda/2$ ($\beta l = \pi$): $Z_{\text{in}} \to \infty$ (open circuit reproduced).
4. **Quarter-Wave Transformer Inversion ($l = \lambda/4$):**
   $$Z_{\text{in}}\left(\frac{\lambda}{4}\right) = \frac{Z_0^2}{Z_L}$$

---

## 4. Derived Reflection Metrics

### Voltage Standing Wave Ratio (VSWR)
$$V_{\text{max}} = |V_0^+|(1 + |\Gamma|), \quad V_{\text{min}} = |V_0^+|(1 - |\Gamma|)$$
$$\text{VSWR} = \frac{V_{\text{max}}}{V_{\text{min}}} = \frac{1 + |\Gamma|}{1 - |\Gamma|}, \quad 1 \le \text{VSWR} \le \infty$$

### Return Loss (RL in dB)
$$\text{RL}_{\text{dB}} = -20 \log_{10}(|\Gamma|)$$
- $\Gamma = 0 \implies \text{RL} = +\infty\text{ dB}$ (ideal transmission).
- $|\Gamma| = 1 \implies \text{RL} = 0\text{ dB}$ (total reflection).

---

## 5. ABCD 2-Port Cascading for Intermediate Discontinuities

A composite transmission line containing an internal discontinuity at physical position $d_1$ from the source is partitioned into two uniform transmission-line segments separated by a lumped 2-port network:

$$\begin{bmatrix} V_1 \\ I_1 \end{bmatrix} = \mathbf{M}_1 \begin{bmatrix} V_{\text{disc}} \\ I_{\text{disc}} \end{bmatrix}, \quad \begin{bmatrix} V_{\text{disc}} \\ I_{\text{disc}} \end{bmatrix} = \mathbf{M}_{\text{disc}} \begin{bmatrix} V_2 \\ I_2 \end{bmatrix}, \quad \begin{bmatrix} V_2 \\ I_2 \end{bmatrix} = \mathbf{M}_2 \begin{bmatrix} V_L \\ I_L \end{bmatrix}$$

The total system ABCD matrix is given by matrix multiplication:
$$\mathbf{M}_{\text{total}} = \mathbf{M}_1(d_1) \cdot \mathbf{M}_{\text{disc}} \cdot \mathbf{M}_2(l - d_1) = \begin{bmatrix} A & B \\ C & D \end{bmatrix}$$

### Elementary ABCD Matrices
1. **Uniform Lossless Section of Length $d$:**
   $$\mathbf{M}_{\text{line}}(d) = \begin{bmatrix} \cos(\beta d) & j Z_0 \sin(\beta d) \\ j \frac{\sin(\beta d)}{Z_0} & \cos(\beta d) \end{bmatrix}$$
2. **Series Inductive Discontinuity ($Z_s = j\omega L$):**
   $$\mathbf{M}_{\text{series}} = \begin{bmatrix} 1 & j\omega L \\ 0 & 1 \end{bmatrix}$$
3. **Shunt Capacitive Discontinuity ($Y_p = j\omega C$):**
   $$\mathbf{M}_{\text{shunt}} = \begin{bmatrix} 1 & 0 \\ j\omega C & 1 \end{bmatrix}$$

### Input Impedance from ABCD Matrix
$$Z_{\text{in}} = \frac{A Z_L + B}{C Z_L + D}$$

For an open circuit ($Z_L \to \infty$):
$$Z_{\text{in}} = \lim_{Z_L \to \infty} \frac{A + B/Z_L}{C + D/Z_L} = \frac{A}{C}$$

---

## 6. Time Domain Reflectometry (TDR) via Inverse FFT

Given single-port frequency-domain reflection measurements $S_{11}(f_n)$ uniformly spaced at intervals $\Delta f$:
$$f_n = f_0 + n \Delta f, \quad n = 0, 1, \dots, N-1$$

A reflection originating from a localized discontinuity at round-trip time $\tau = 2d / v_p$ contributes a phase ramp:
$$S_{11}(f) \approx \Gamma_{\text{fault}} \exp(-j 2\pi f \tau)$$

### Sidelobe Suppression & Zero-Padding
To prevent Gibbs spectral leakage from masking small echoes, a symmetric Hann window $w[n]$ is applied:
$$w[n] = 0.5 \left[ 1 - \cos\left(\frac{2\pi n}{N-1}\right) \right]$$

The sequence is zero-padded to length $N_{\text{pad}} \ge 2048$ to interpolate the discrete time grid without altering physical resolution:
$$h[k] = \frac{N_{\text{pad}}}{N} \sum_{n=0}^{N-1} \left( w[n] S_{11}[n] \right) e^{j 2\pi k n / N_{\text{pad}}}$$

### Resolution and Unambiguous Distance
1. **Range Resolution ($\Delta R$):** The minimum distance between two separable reflectors:
   $$\Delta R = \frac{v_p}{2 B} = \frac{v_p}{2(f_{\text{max}} - f_{\text{min}})}$$
2. **Unambiguous Range ($R_{\text{max}}$):** The maximum distance before temporal aliasing occurs:
   $$R_{\text{max}} = \frac{v_p}{2 \Delta f}$$

---

## 7. Quarter-Wave Impedance Matching Theory

To match a real load resistance $R_L \ne Z_0$ to a feed line $Z_0$ at frequency $f_0$:
A quarter-wave transformer section is inserted with electrical length:
$$\theta = \beta_t l_t = \frac{\pi}{2} \implies l_t = \frac{\lambda_t}{4} = \frac{v_p}{4 f_0}$$

The input impedance looking into the quarter-wave section loaded by $R_L$ is:
$$Z_{\text{in}}(f_0) = \frac{Z_t^2}{R_L}$$

Enforcing perfect match $Z_{\text{in}}(f_0) = Z_0$:
$$Z_0 = \frac{Z_t^2}{R_L} \implies Z_t = \sqrt{Z_0 R_L}$$

### Fractional Bandwidth (Lossless Line)
From Pozar eq. (5.11), for an allowable reflection magnitude $|\Gamma_m|$ (corresponding to Return Loss threshold $\text{RL}_{\text{th}} = -20\log_{10}|\Gamma_m|$):
$$\frac{\Delta f}{f_0} = 2 - \frac{4}{\pi} \arccos\left[ \frac{|\Gamma_m|}{\sqrt{1 - |\Gamma_m|^2}} \frac{2\sqrt{Z_0 R_L}}{|R_L - Z_0|} \right]$$

Notice: As mismatch $|R_L - Z_0|$ increases, the usable matching bandwidth $\Delta f$ narrows monotonically.
