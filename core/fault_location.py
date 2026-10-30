"""
core/fault_location.py -- Advanced fault distance estimation engine.

Implements two complementary localization techniques:
  1. Method 1 (Primary): Windowed IFFT pseudo-Time-Domain Reflectometry (TDR)
     - Validates uniform frequency spacing (resamples linearly if non-uniform).
     - Applies a Hann window to suppress sidelobes.
     - Zero-pads to interpolate the time-domain peak position.
     - Evaluates peak round-trip echo time: d = vp * t_peak / 2.
  2. Method 2 (Cross-Check): Unwrapped phase slope vs frequency
     - d = -(vp / (4*pi)) * (d(phi)/df).
     - Biased for reactive discontinuities due to internal phase shift.

Physical Metrics:
  - Range Resolution: delta_d = vp / (2 * B)
  - Unambiguous Range: d_max = vp / (2 * delta_f)
"""

import numpy as np
import line_model as lm

__all__ = [
    "locate_fault_dual_method",
    "compute_ifft_tdr",
    "compute_phase_slope_distance",
    "calculate_resolution_metrics",
]


def calculate_resolution_metrics(freqs, vf=1.0, pad_factor=8, min_pad=2048):
    """
    Compute physical distance resolution and unambiguous range.

    Distinguishes:
      - Physical Rayleigh range resolution: delta_R = vp / (2 * B)
        Fundamental physical limit. Discontinuities separated by less than delta_R
        cannot be distinguished as two distinct reflection peaks.
      - Zero-padded interpolation step: delta_d = vp / (2 * N_pad * delta_f)
        Bin spacing in interpolated time/distance domain. Improves peak centroid
        estimation for an isolated discontinuity, but does NOT improve physical
        Rayleigh resolution limit.

    Parameters
    ----------
    freqs      : 1-D array of frequencies [Hz]
    vf         : velocity factor (0 < vf <= 1.0)
    pad_factor : zero-padding multiplier
    min_pad    : minimum FFT padding size

    Returns
    -------
    dict:
        bandwidth_hz    : total sweep bandwidth B [Hz]
        delta_f_hz      : frequency step delta_f [Hz]
        range_res_m     : theoretical physical Rayleigh range resolution [m]
        interp_step_m   : zero-padded IFFT interpolation bin resolution [m]
        unambig_range_m : maximum unambiguous measurement range [m]
        vp_m_s          : propagation phase velocity [m/s]
        resolution_note : physical explanation of Rayleigh vs interpolation step
    """
    f = np.asarray(freqs, dtype=float)
    N = len(f)
    if N < 2:
        return {
            "bandwidth_hz": 0.0,
            "delta_f_hz": 0.0,
            "range_res_m": float("nan"),
            "interp_step_m": float("nan"),
            "unambig_range_m": float("nan"),
            "vp_m_s": lm.phase_velocity(vf),
            "resolution_note": "Insufficient frequency points for range metrics.",
        }

    vp = lm.phase_velocity(vf)
    B = float(f[-1] - f[0])
    df = float(B / (N - 1))
    Npad = max(int(N * pad_factor), min_pad)

    range_res = float(vp / (2.0 * B)) if B > 0 else float("nan")
    interp_step = float(vp / (2.0 * Npad * df)) if (Npad * df) > 0 else float("nan")
    unambig_range = float(vp / (2.0 * df)) if df > 0 else float("nan")

    note = (
        f"Rayleigh resolution limit is {range_res*100:.2f} cm (vp / 2B). "
        f"Zero-padded interpolation step is {interp_step*100:.2f} cm (vp / 2*N_pad*df). "
        "Zero-padding interpolates peak position between bins but cannot resolve "
        "two distinct discontinuities separated by less than the Rayleigh limit."
    )

    return {
        "bandwidth_hz": B,
        "delta_f_hz": df,
        "range_res_m": range_res,
        "interp_step_m": interp_step,
        "unambig_range_m": unambig_range,
        "vp_m_s": vp,
        "resolution_note": note,
    }


def compute_ifft_tdr(gamma, freqs, vf=1.0, pad_factor=8, min_pad=2048):
    """
    Method 1: Compute windowed IFFT pseudo-time domain reflectometry profile.

    Parameters
    ----------
    gamma      : complex array of reflection coefficients
    freqs      : array of frequencies [Hz]
    vf         : velocity factor
    pad_factor : zero-padding multiplier for time-grid interpolation
    min_pad    : minimum FFT size

    Returns
    -------
    dict:
        dist_m       : estimated distance to dominant peak [m] (or None if matched)
        peak_idx     : index of peak in time array
        peak_val     : magnitude of dominant peak
        t_axis_s     : time axis array [seconds]
        d_axis_m     : physical distance axis [metres]
        tdr_mag      : IFFT impulse response magnitude array
        was_resampled: bool, whether non-uniform grid was resampled
    """
    g = np.asarray(gamma, dtype=complex)
    f = np.asarray(freqs, dtype=float)
    N = len(f)

    if N < 4:
        return {"dist_m": None, "tdr_mag": np.array([]), "d_axis_m": np.array([]), "was_resampled": False}

    # Validate uniform frequency spacing
    diffs = np.diff(f)
    df_mean = float(np.mean(diffs))
    if df_mean <= 0:
        return {"dist_m": None, "tdr_mag": np.array([]), "d_axis_m": np.array([]), "was_resampled": False}

    is_uniform = np.all(np.abs(diffs - df_mean) / df_mean < 1e-4)
    was_resampled = False

    if not is_uniform:
        was_resampled = True
        f_uniform = np.linspace(f[0], f[-1], N)
        g_re = np.interp(f_uniform, f, np.real(g))
        g_im = np.interp(f_uniform, f, np.imag(g))
        g_proc = g_re + 1j * g_im
        df = (f_uniform[-1] - f_uniform[0]) / (N - 1)
    else:
        g_proc = g
        df = df_mean

    # Apply Hann window
    window = np.hanning(N)
    g_win = g_proc * window

    # Zero-padding for temporal interpolation
    Npad = max(int(N * pad_factor), min_pad)
    g_pad = np.zeros(Npad, dtype=complex)
    g_pad[:N] = g_win

    # Compute IFFT with normalization
    time_response = np.fft.ifft(g_pad) * (float(Npad) / float(N))
    tdr_mag = np.abs(time_response)

    # Time and distance axes
    t_axis_s = np.arange(Npad) / (Npad * df)
    vp = lm.phase_velocity(vf)
    d_axis_m = vp * t_axis_s / 2.0

    # Search dominant peak in causal region, skipping DC feed-through (bins 0..2)
    search_mag = tdr_mag.copy()
    search_mag[:3] = 0.0
    search_mag[Npad // 2 :] = 0.0

    peak_idx = int(np.argmax(search_mag))
    peak_val = float(search_mag[peak_idx])

    # Threshold for physical echo detection
    if peak_val < 0.01:
        dist_m = None
    else:
        dist_m = float(d_axis_m[peak_idx])

    return {
        "dist_m": dist_m,
        "peak_idx": peak_idx,
        "peak_val": peak_val,
        "t_axis_s": t_axis_s,
        "d_axis_m": d_axis_m,
        "tdr_mag": tdr_mag,
        "was_resampled": was_resampled,
    }


def compute_phase_slope_distance(gamma, freqs, vf=1.0):
    """
    Method 2: Estimate fault distance from unwrapped phase slope.

    d = - (vp / (4*pi)) * (d(phi) / df)

    Note: Biased when discontinuity introduces frequency-dependent phase.
    """
    g = np.asarray(gamma, dtype=complex)
    f = np.asarray(freqs, dtype=float)
    if len(f) < 2:
        return None

    mag = np.abs(g)
    if np.mean(mag) < 0.05:
        return None

    phase_unwrapped = np.unwrap(np.angle(g))
    pfit = np.polyfit(f, phase_unwrapped, 1)
    slope = float(pfit[0])  # rad/Hz

    vp = lm.phase_velocity(vf)
    d_slope = float(-(vp / (4.0 * np.pi)) * slope)

    return d_slope if d_slope >= 0 else None


def locate_fault_dual_method(gamma, freqs, vf=1.0, fault_class="mismatch"):
    """
    Execute full fault localization with dual-method cross-check and reliability flags.

    Parameters
    ----------
    gamma       : complex array of reflection coefficients
    freqs       : array of frequencies [Hz]
    vf          : velocity factor (0 < vf <= 1.0)
    fault_class : str, one of "healthy", "open", "short", "mismatch", "unknown"

    Returns
    -------
    dict with:
        dist_ifft_m       : Method 1 distance estimate [m] (primary)
        dist_phase_m      : Method 2 distance estimate [m] (cross-check)
        discrepancy_m     : difference between methods [m]
        range_res_m       : physical range resolution [m]
        unambig_range_m   : unambiguous range [m]
        is_reliable       : bool
        warnings          : list of warning strings
        tdr_data          : dict from compute_ifft_tdr
    """
    warnings = []
    if str(fault_class).lower() == "healthy":
        return {
            "dist_ifft_m": None,
            "dist_phase_m": None,
            "discrepancy_m": None,
            "range_res_m": None,
            "interp_step_m": None,
            "unambig_range_m": None,
            "is_reliable": True,
            "warnings": ["Line is healthy/matched; no reflection echo present."],
            "tdr_data": {},
        }

    res_metrics = calculate_resolution_metrics(freqs, vf=vf)
    tdr_out = compute_ifft_tdr(gamma, freqs, vf=vf)
    d1 = tdr_out["dist_m"]
    d2 = compute_phase_slope_distance(gamma, freqs, vf=vf)

    if tdr_out.get("was_resampled", False):
        warnings.append("Non-uniform frequency grid detected; resampled linearly.")

    discrepancy = None
    is_reliable = True

    if d1 is not None and d2 is not None:
        discrepancy = abs(d1 - d2)
        # Check if discrepancy is large
        if discrepancy > 3.0 * res_metrics["range_res_m"]:
            is_reliable = False
            warnings.append(
                f"Dual-method discrepancy ({discrepancy:.3f} m) exceeds 3x Rayleigh resolution "
                f"({3 * res_metrics['range_res_m']:.3f} m). Discontinuity is likely reactive "
                "(series L or shunt C), which introduces an internal phase-slope bias."
            )
    elif d1 is None:
        is_reliable = False
        warnings.append("No dominant reflection peak detected above noise floor.")

    return {
        "dist_ifft_m": d1,
        "dist_phase_m": d2,
        "discrepancy_m": discrepancy,
        "range_res_m": res_metrics["range_res_m"],
        "interp_step_m": res_metrics["interp_step_m"],
        "unambig_range_m": res_metrics["unambig_range_m"],
        "is_reliable": is_reliable,
        "warnings": warnings,
        "tdr_data": tdr_out,
    }
