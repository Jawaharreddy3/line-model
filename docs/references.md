# Academic References & Licencing Notices — RF LINE DOCTOR

## 1. Academic & Technical References

1. **Pozar, David M.** *Microwave Engineering*, 4th Edition. John Wiley & Sons, 2012.
   - Chapter 2: Transmission Line Theory, Telegrapher's Equations, Input Impedance, Reflection Coefficient, and Standing Waves.
   - Chapter 4: Microwave Network Analysis, 2-Port ABCD Parameters, Matrix Cascading.
   - Chapter 5: Impedance Matching and Tuning, Quarter-Wave Transformers, Fractional Bandwidth Formulations.
2. **Hewlett-Packard Company.** *Time Domain Reflectometry Theory*, Application Note 1304-2, 1988.
   - Mathematical principles of TDR, impulse/step response synthesis via IFFT, range resolution, and windowing functions.
3. **Smith, Phillip H.** "Transmission Line Calculator," *Electronics*, vol. 12, no. 1, pp. 29–31, Jan. 1939.
   - Conformal bilinear mapping of normalized impedance $z = r + jx$ onto the complex reflection coefficient plane $\Gamma = (z-1)/(z+1)$.
4. **Harris, Fredric J.** "On the Use of Windows for Harmonic Analysis with the Discrete Fourier Transform," *Proceedings of the IEEE*, vol. 66, no. 1, pp. 51–83, Jan. 1978.
   - Sidelobe suppression, coherent gain, and equivalent noise bandwidth of the Hann (Hanning) window.

---

## 2. Technical Reference Attribution & Licencing

This software was engineered as part of the EC-3104 undergraduate engineering curriculum. 

Portions of the simulation architecture, diagnostic rules, and TDR concepts were inspired by the open-source engineering reference:
- **Repository:** `https://github.com/Hackhash07/Transmission-Line-Fault-Diagnosis`
- **Original Authors:** Hackhash07 and contributors.
- **Licence:** MIT License.

### MIT Licence Notice for Adapted Concepts
```text
MIT License

Copyright (c) 2026 Hackhash07 and contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 3. Independent Software Identity

**RF LINE DOCTOR** is an independently designed software suite featuring:
- Strict compatibility with our team's frozen interface contract (`INTERFACES.md`).
- Exact mathematical handling of open circuit terminations ($Z_L = \infty$) via bilinear reflection mapping rather than artificial finite $10^9\,\Omega$ shunts.
- Independent validation pipeline generating empirical performance data and confusion matrices from documented random seeds.
- Comprehensive 8-section interactive laboratory dashboard with dark navy/charcoal engineering UI, live Smith charts, and quarter-wave matching synthesis.
