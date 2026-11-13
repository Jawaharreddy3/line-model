"""
measurements.py -- Transmission-line measurement helpers (Member 2).

Conventions (see INTERFACES.md):
  * SI units: ohm, metre, Hz, radian.
  * Inputs may be scalars or NumPy arrays (broadcasting supported).
  * Open circuit: ZL = np.inf (reflection coefficient = +1.0).
  * Line is lossless; passive loads satisfy |Gamma| <= 1.
"""

import numpy as np
import line_model as lm

__all__ = [
    "SweepResult",
    "reflection_coefficient",
    "vswr",
    "return_loss_db",
    "sweep",
    "smith_plot",
]


class SweepResult(dict):
    """
    Dictionary-compatible container for frequency sweep results.

    Preserves exact contract keys ('f', 'zin', 'gamma', 'vswr', 'rl_db')
    while retaining line metadata (vf, Z0, length) as accessible attributes.
    Supports standard dictionary access, unpacking, and JSON serialization.
    """

    def __init__(self, *args, vf=1.0, Z0=50.0, length=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.vf = float(vf)
        self.Z0 = complex(Z0)
        self.length = float(length) if length is not None else None

    def __repr__(self):
        keys = list(self.keys())
        return f"<SweepResult keys={keys} vf={self.vf} Z0={self.Z0}>"


def reflection_coefficient(Z, Z0):
    """
    Equation 7: Complex reflection coefficient:
        Gamma = (Z - Z0) / (Z + Z0)

    Electromagnetic Theory & Boundary Conditions:
      * At a termination boundary ZL, Gamma represents the ratio of the reflected
        voltage wave phasor V0^- to incident voltage wave phasor V0^+.
      * For Z = Z0 (matched load): Gamma = 0 (zero reflection, total transmission).
      * For Z = 0 (short circuit): Gamma = -1.0 + 0.0j (180 deg phase reversal).
      * For Z = np.inf (open circuit): Gamma = +1.0 + 0.0j (in-phase reflection).
      * Handles Z = np.inf exactly without numerical overflow -> +1.0 + 0.0j.
      * Supports scalar and array inputs via NumPy broadcasting.
    """
    Z0_arr = np.asarray(Z0, dtype=complex)
    if np.any(np.isnan(Z0_arr)):
        raise ValueError("Reference impedance Z0 cannot contain NaN")
    if np.any(np.real(Z0_arr) <= 0):
        raise ValueError("Reference impedance Z0 must have strictly positive real part")

    Z_arr = np.asarray(Z, dtype=complex)
    if np.any(np.isnan(Z_arr)):
        raise ValueError("Impedance Z cannot contain NaN")

    Z_b, Z0_b = np.broadcast_arrays(Z_arr, Z0_arr)

    out = np.empty(Z_b.shape, dtype=complex)
    inf_mask = ~np.isfinite(Z_b)
    out[inf_mask] = 1.0 + 0.0j

    fin_mask = ~inf_mask
    denom = Z_b[fin_mask] + Z0_b[fin_mask]
    singular = np.abs(denom) < 1e-15

    out_fin = np.empty(denom.shape, dtype=complex)
    out_fin[singular] = 1.0 + 0.0j
    ok = ~singular
    out_fin[ok] = (Z_b[fin_mask][ok] - Z0_b[fin_mask][ok]) / denom[ok]

    out[fin_mask] = out_fin
    return out if out.ndim else out.item()


def vswr(gamma):
    """
    Equation 8: Voltage Standing Wave Ratio (VSWR):
        VSWR = V_max / V_min = (1 + |Gamma|) / (1 - |Gamma|)

    Electromagnetic Theory & Numerical Stability:
      * Defined for passive transmission lines where 0 <= |Gamma| <= 1.0.
      * |Gamma| == 0: VSWR = 1.0 (perfect match, constant voltage envelope).
      * |Gamma| == 1.0: returns np.inf (total reflection, standing wave nodes).
      * 0 <= |Gamma| < 1.0: returns physical ratio in [1.0, inf).
      * |Gamma| > 1.0: returns np.nan for non-passive noisy samples
        rather than crashing or returning negative unphysical values.
      * Controlled tolerance: uses explicit relative (rtol=1e-12) and absolute
        (atol=1e-12) tolerances to avoid misclassifying values near unity
        (e.g., 0.99999) as exactly 1.0.
    """
    g = np.asarray(gamma, dtype=complex)
    mag = np.abs(g)

    out = np.full(mag.shape, np.nan, dtype=float)

    # Total reflection: |Gamma| == 1.0 with explicitly controlled relative and absolute tolerances.
    # Explicitly pass rtol=1e-12 to override NumPy's default rtol=1e-5, which would otherwise
    # misclassify values like 0.99999 as exactly 1.0.
    tol = 1e-12
    total_refl = np.isclose(mag, 1.0, rtol=tol, atol=tol)
    out[total_refl] = np.inf

    # Valid passive transmission line region: 0 <= |Gamma| < 1 (strictly below total reflection tolerance)
    valid_passive = (mag >= 0.0) & (mag < 1.0) & (~total_refl)
    out[valid_passive] = (1.0 + mag[valid_passive]) / (1.0 - mag[valid_passive])

    return out if out.ndim else out.item()


def return_loss_db(gamma):
    """
    Equation 9: Return Loss in dB:
        RL = -20 * log10(|Gamma|) = 10 * log10(P_incident / P_reflected)

    Electromagnetic Theory & Decibel Conversion:
      * Quantifies the power reflected from an impedance discontinuity.
      * Matched load (|Gamma| == 0): returns np.inf without divide-by-zero log warnings.
      * Passive total reflection (|Gamma| == 1.0): returns exactly 0.0 dB.
      * Intermediate passive reflection (0 < |Gamma| < 1): returns positive dB.
      * Non-passive noisy reflection (|Gamma| > 1): returns negative dB without clipping.
    """
    g = np.asarray(gamma, dtype=complex)
    mag = np.abs(g)

    out = np.empty(mag.shape, dtype=float)
    zero_mask = (mag <= 1e-15)
    out[zero_mask] = np.inf

    non_zero = ~zero_mask
    out[non_zero] = -20.0 * np.log10(mag[non_zero])

    return out if out.ndim else out.item()


def sweep(Z0, ZL, length, f_array, vf=1.0):
    """
    Frequency sweep of input impedance, reflection coefficient, VSWR, and return loss.

    Parameters
    ----------
    Z0      : characteristic impedance [ohm], real or complex
    ZL      : load impedance [ohm], complex or np.inf
    length  : physical line length [m]
    f_array : 1-D array of frequencies [Hz]
    vf      : velocity factor (0 < vf <= 1.0)

    Returns
    -------
    SweepResult (dict) with exact contract keys:
        'f'     : frequency array [Hz]
        'zin'   : input impedance array [ohm]
        'gamma' : input reflection coefficient array
        'vswr'  : VSWR array (contains np.nan for non-passive noisy points)
        'rl_db' : Return loss array [dB]
    """
    if length is None:
        raise ValueError("Line length must be provided")
    l_val = float(length)
    if not np.isfinite(l_val) or l_val < 0:
        raise ValueError(f"Line length must be a finite, non-negative number (got {length})")

    f_arr = np.asarray(f_array, dtype=float)
    if f_arr.size == 0:
        raise ValueError("Frequency array cannot be empty")
    if np.any(~np.isfinite(f_arr)) or np.any(f_arr <= 0):
        raise ValueError("Frequencies must be finite and strictly positive (> 0)")
    if len(f_arr) > 1 and np.any(np.diff(f_arr) <= 0):
        raise ValueError("Frequency sweep array must be strictly monotonically increasing")

    lm._check_vf(vf)

    zin = lm.input_impedance_at_freq(Z0, ZL, f_arr, l_val, vf=vf)
    gamma = reflection_coefficient(zin, Z0)
    swr = vswr(gamma)
    rl = return_loss_db(gamma)

    return SweepResult(
        {
            "f": f_arr,
            "zin": zin,
            "gamma": gamma,
            "vswr": swr,
            "rl_db": rl,
        },
        vf=vf,
        Z0=Z0,
        length=l_val,
    )


def smith_plot(gamma_array, ax=None, **kw):
    """
    Plot complex reflection coefficient trajectory on a normalized Smith chart.

    Parameters
    ----------
    gamma_array : complex array of reflection coefficients
    ax          : matplotlib Axes instance (optional; created if None)
    **kw        : keyword arguments passed to ax.plot()

    Returns
    -------
    ax : matplotlib Axes with normalized Smith chart overlay
    """
    import matplotlib.pyplot as plt

    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 6))

    # Draw constant resistance circles (r = R / Z0)
    theta = np.linspace(0, 2 * np.pi, 500)
    r_vals = [0.0, 0.2, 0.5, 1.0, 2.0, 5.0]
    for r in r_vals:
        center_x = r / (1.0 + r)
        radius = 1.0 / (1.0 + r)
        lw = 1.0 if r == 0.0 else 0.5
        alpha = 0.8 if r in [0.0, 1.0] else 0.4
        color = "black" if r == 0.0 else "royalblue"
        ax.plot(
            center_x + radius * np.cos(theta),
            radius * np.sin(theta),
            color=color,
            linewidth=lw,
            alpha=alpha,
            zorder=1,
        )

    # Draw constant reactance arcs (x = X / Z0)
    x_vals = [0.2, 0.5, 1.0, 2.0, 5.0, -0.2, -0.5, -1.0, -2.0, -5.0]
    phi = np.linspace(-np.pi, np.pi, 500)
    for x in x_vals:
        center_x = 1.0
        center_y = 1.0 / x
        radius_a = abs(1.0 / x)
        xc = center_x + radius_a * np.cos(phi)
        yc = center_y + radius_a * np.sin(phi)
        inside = (xc**2 + yc**2) <= 1.001
        ax.plot(
            xc[inside],
            yc[inside],
            color="forestgreen",
            linewidth=0.5,
            alpha=0.35,
            zorder=1,
        )

    ax.axhline(0, color="black", linewidth=0.8, alpha=0.5, zorder=1)

    g = np.asarray(gamma_array, dtype=complex)
    valid = np.isfinite(g.real) & np.isfinite(g.imag)
    g_plot = g[valid]

    default_kw = {"color": "crimson", "linewidth": 1.8, "label": "Gamma"}
    default_kw.update(kw)
    if len(g_plot) > 0:
        ax.plot(g_plot.real, g_plot.imag, **default_kw)
        ax.scatter([g_plot.real[0]], [g_plot.imag[0]], color="crimson", s=30, zorder=5)

    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-1.15, 1.15)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Re(Gamma)")
    ax.set_ylabel("Im(Gamma)")
    ax.set_title("Normalized Smith Chart")
    ax.grid(False)

    return ax
