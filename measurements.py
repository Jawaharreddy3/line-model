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
    "reflection_coefficient",
    "vswr",
    "return_loss_db",
    "sweep",
    "smith_plot",
]


def reflection_coefficient(Z, Z0):
    """
    Complex reflection coefficient:
        Gamma = (Z - Z0) / (Z + Z0)

    Handles Z = np.inf (open circuit) exactly -> +1.0 + 0.0j.
    Supports scalar and array inputs via NumPy broadcasting.
    """
    Z_arr = np.asarray(Z, dtype=complex)
    Z0_arr = np.asarray(Z0, dtype=complex)
    Z_b, Z0_b = np.broadcast_arrays(Z_arr, Z0_arr)

    out = np.empty(Z_b.shape, dtype=complex)
    inf_mask = ~np.isfinite(Z_b)
    out[inf_mask] = 1.0 + 0.0j

    fin_mask = ~inf_mask
    denom = Z_b[fin_mask] + Z0_b[fin_mask]
    singular = np.abs(denom) < 1e-15

    # Safe division
    out_fin = np.empty(denom.shape, dtype=complex)
    out_fin[singular] = 1.0 + 0.0j
    ok = ~singular
    out_fin[ok] = (Z_b[fin_mask][ok] - Z0_b[fin_mask][ok]) / denom[ok]

    out[fin_mask] = out_fin
    return out if out.ndim else out.item()


def vswr(gamma):
    """
    Voltage Standing Wave Ratio (VSWR):
        VSWR = (1 + |Gamma|) / (1 - |Gamma|)

    Returns np.inf when |Gamma| == 1.0 (or within numerical tolerance 1e-12).
    Raises ValueError for non-passive loads |Gamma| > 1.0 + 1e-6.
    """
    g = np.asarray(gamma, dtype=complex)
    mag = np.abs(g)

    # Check for active / non-passive values
    if np.any(mag > 1.0 + 1e-6):
        raise ValueError("VSWR requires passive reflection coefficient |Gamma| <= 1")

    # Clip slight numerical overshoots (e.g., 1.000000000000001)
    mag_clipped = np.clip(mag, 0.0, 1.0)

    out = np.empty(mag_clipped.shape, dtype=float)
    total_reflection = np.isclose(mag_clipped, 1.0, atol=1e-12)
    out[total_reflection] = np.inf

    normal = ~total_reflection
    out[normal] = (1.0 + mag_clipped[normal]) / (1.0 - mag_clipped[normal])

    return out if out.ndim else out.item()


def return_loss_db(gamma):
    """
    Return Loss in dB:
        RL = -20 * log10(|Gamma|)

    Returns np.inf when matched (|Gamma| == 0).
    Guards against divide-by-zero warnings.
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
    dict with exact contract keys:
        'f'     : frequency array [Hz]
        'zin'   : input impedance array [ohm]
        'gamma' : input reflection coefficient array
        'vswr'  : VSWR array
        'rl_db' : Return loss array [dB]
    """
    f_arr = np.asarray(f_array, dtype=float)
    zin = lm.input_impedance_at_freq(Z0, ZL, f_arr, length, vf=vf)
    gamma = reflection_coefficient(zin, Z0)
    swr = vswr(gamma)
    rl = return_loss_db(gamma)

    return {
        "f": f_arr,
        "zin": zin,
        "gamma": gamma,
        "vswr": swr,
        "rl_db": rl,
    }


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
        # Clip inside unit circle (|Gamma| <= 1.001)
        inside = (xc**2 + yc**2) <= 1.001
        ax.plot(
            xc[inside],
            yc[inside],
            color="forestgreen",
            linewidth=0.5,
            alpha=0.35,
            zorder=1,
        )

    # Horizontal center line (real axis)
    ax.axhline(0, color="black", linewidth=0.8, alpha=0.5, zorder=1)

    # Plot input reflection trajectory
    g = np.asarray(gamma_array, dtype=complex)
    default_kw = {"color": "crimson", "linewidth": 1.8, "label": "Gamma"}
    default_kw.update(kw)
    ax.plot(g.real, g.imag, **default_kw)

    # Mark starting frequency point
    if len(g) > 0:
        ax.scatter([g.real[0]], [g.imag[0]], color="crimson", s=30, zorder=5)

    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-1.15, 1.15)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Re(Gamma)")
    ax.set_ylabel("Im(Gamma)")
    ax.set_title("Normalized Smith Chart")
    ax.grid(False)

    return ax
