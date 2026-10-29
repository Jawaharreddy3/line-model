# Interface contract (frozen 27 Oct 2026 — change only after telling the lead)

**Units:** ohm, metre, Hz, radian. **Impedances:** complex numbers. **Open circuit:** `ZL = np.inf`.
**Inputs:** scalars or NumPy arrays. **Line:** lossless (alpha = 0). Time convention e^{jwt}.

## line_model.py — Member 1 (done)
| Function | Returns |
|---|---|
| `wavelength(f, vf=1.0)` | lambda [m] |
| `phase_constant(f, vf=1.0)` | beta [rad/m] |
| `load_reflection(Z0, ZL)` | Gamma_L (complex) |
| `reflection_at_distance(Z0, ZL, beta, d)` | Gamma(d), d from load toward source |
| `input_impedance(Z0, ZL, beta, length)` | Zin (complex; inf at singular cases) |
| `input_impedance_at_freq(Z0, ZL, f, length, vf=1.0)` | Zin for a frequency sweep |
| `quarter_wave_zin(Z0, ZL)` | Z0^2/ZL |
| `quarter_wave_impedance(Zline, R_load)` | transformer Zt = sqrt(Zline*R) |

## measurements.py — Member 2
| Function | Returns |
|---|---|
| `reflection_coefficient(Z, Z0)` | Gamma = (Z - Z0)/(Z + Z0) |
| `vswr(gamma)` | (1+abs(G))/(1-abs(G)); inf when abs(G)=1 |
| `return_loss_db(gamma)` | -20*log10(abs(G)); inf when matched |
| `sweep(Z0, ZL, length, f_array, vf)` | dict: f, zin, gamma, vswr, rl_db |
| `smith_plot(gamma_array, ax=None, **kw)` | matplotlib Axes (normalised chart) |

## diagnosis.py / matching.py — Member 3
| Function | Returns |
|---|---|
| `classify(sweep_dict, Z0)` | one of `"healthy" "open" "short" "mismatch" "unknown"` |
| `estimate_distance(sweep_dict, vf, fault_class)` | metres, or `None` if not applicable |
| `design_quarter_wave(Z0, RL, f, vf)` | dict: Zt, length_m |
| `compare_matching(Z0, ZL, f_array, ...)` | dict: before / after sweep results |

## app.py — Member 4
Streamlit UI. Only calls the functions above; inputs: Z0, ZL (R, X), length, frequency range, vf, fault type.
