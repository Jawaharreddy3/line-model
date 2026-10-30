"""
diagnosis.py -- Fault diagnosis and IFFT distance localization (Member 3).

Conventions (see INTERFACES.md):
  * classify(sweep_dict, Z0):
      Returns strictly one of: "healthy", "open", "short", "mismatch", "unknown"
      Exposes rich internal diagnostic subtypes via attributes without breaking
      the public string return contract.
  * estimate_distance(sweep_dict, vf, fault_class):
      Returns physical fault distance [m] as float, or None if not applicable
      (e.g., for "healthy" line). Validates uniform frequency grid; resamples
      with documented warnings if non-uniform.
"""

import numpy as np
import line_model as lm
import measurements as meas

CLASSIFICATION_LABELS = [
    "healthy",
    "open",
    "short",
    "mismatch",
    "unknown",
]

__all__ = [
    "CLASSIFICATION_LABELS",
    "DiagnosisResult",
    "classify",
    "estimate_distance",
    "distance_resolution",
    "extract_features",
]


class DiagnosisResult(str):
    """
    Subclass of str representing the frozen classification label.
    Supports equality checks like `res == "healthy"` while carrying rich
    metadata attributes for detailed diagnostic display in app.py.
    """

    def __new__(
        cls,
        value,
        subtype=None,
        confidence="high",
        features=None,
        explanation="",
        rules_fired=None,
    ):
        if value not in CLASSIFICATION_LABELS:
            raise ValueError(
                f"Classification must be one of {CLASSIFICATION_LABELS}, got '{value}'"
            )
        obj = str.__new__(cls, value)
        obj.label = value
        obj.subtype = subtype or value
        obj.confidence = confidence
        obj.features = features or {}
        obj.explanation = explanation
        obj.rules_fired = rules_fired or []
        return obj


def extract_features(sweep_dict, Z0, vf=1.0):
    """
    Extract diagnostic features from reflection coefficient sweep.
    Operates strictly on single-port reflection data (Gamma / S11).
    """
    gamma = np.asarray(sweep_dict["gamma"], dtype=complex)
    freqs = np.asarray(sweep_dict["f"], dtype=float)
    N = len(gamma)

    mag = np.abs(gamma)
    mag_mean = float(np.mean(mag))
    mag_std = float(np.std(mag))
    mag_max = float(np.max(mag)) if N > 0 else 0.0

    quarter = max(1, N // 4)
    mag_low = float(np.mean(mag[:quarter])) if N > 0 else 0.0
    mag_high = float(np.mean(mag[-quarter:])) if N > 0 else 0.0
    trend = mag_high - mag_low

    phase_unwrapped = np.unwrap(np.angle(gamma)) if N > 0 else np.array([])
    phase_first = float(np.angle(gamma[0])) if N > 0 else 0.0

    # Low-frequency real/imag reflection (reflects load behavior before line rotation)
    lf_real = float(np.real(gamma[0])) if N > 0 else 0.0
    lf_imag = float(np.imag(gamma[0])) if N > 0 else 0.0

    # Estimate distance via IFFT for de-embedding
    d_est = None
    deembedded_real = lf_real
    deembedded_imag = lf_imag

    if N >= 4 and (freqs[-1] - freqs[0]) > 1e4:
        d_est = _compute_ifft_distance(gamma, freqs, vf)
        if d_est is not None and d_est > 0:
            vp = lm.phase_velocity(vf)
            beta = 2.0 * np.pi * freqs / vp
            gamma_deembedded = gamma * np.exp(2j * beta * d_est)
            deembedded_real = float(np.mean(gamma_deembedded.real))
            deembedded_imag = float(np.mean(gamma_deembedded.imag))

    return {
        "mag_mean": mag_mean,
        "mag_std": mag_std,
        "mag_max": mag_max,
        "mag_low": mag_low,
        "mag_high": mag_high,
        "trend": trend,
        "phase_first": phase_first,
        "lf_real": lf_real,
        "lf_imag": lf_imag,
        "deembedded_real": deembedded_real,
        "deembedded_imag": deembedded_imag,
        "d_est": d_est,
    }


def classify(sweep_dict, Z0):
    """
    Classify transmission-line fault from sweep data.

    Parameters
    ----------
    sweep_dict : dict containing 'f' and 'gamma' (from measurements.sweep)
    Z0         : characteristic impedance of the line [ohm]

    Returns
    -------
    DiagnosisResult (str) : one of "healthy", "open", "short", "mismatch", "unknown"
    """
    feat = extract_features(sweep_dict, Z0)
    mm = feat["mag_mean"]
    ms = feat["mag_std"]
    tr = feat["trend"]
    de_re = feat["deembedded_real"]
    de_im = feat["deembedded_imag"]
    lf_re = feat["lf_real"]

    rules = []

    # Rule 1: Healthy Matched Line
    # Negligible reflection across all frequencies
    if mm < 0.05 and feat["mag_max"] < 0.10:
        rules.append("R1_HEALTHY_MATCHED")
        return DiagnosisResult(
            "healthy",
            subtype="matched",
            confidence="high",
            features=feat,
            explanation=f"Near-zero reflection: mean |Gamma| = {mm:.4f} < 0.05",
            rules_fired=rules,
        )

    # Rule 2: Reactive Discontinuity (Series L or Shunt C)
    # Reflection magnitude rises significantly with frequency (trend > 0.005 or std > 0.035)
    if tr > 0.005 or ms > 0.035:
        if de_im >= 0:
            rules.append("R2_SERIES_L_MISMATCH")
            return DiagnosisResult(
                "mismatch",
                subtype="series_L",
                confidence="medium" if mm > 0.15 else "low",
                features=feat,
                explanation=(
                    f"Rising reflection trend ({tr:+.3f}) with inductive phase "
                    f"(Im={de_im:+.2f}) => Series Inductance Discontinuity"
                ),
                rules_fired=rules,
            )
        else:
            rules.append("R3_SHUNT_C_MISMATCH")
            return DiagnosisResult(
                "mismatch",
                subtype="shunt_C",
                confidence="medium" if mm > 0.15 else "low",
                features=feat,
                explanation=(
                    f"Rising reflection trend ({tr:+.3f}) with capacitive phase "
                    f"(Im={de_im:+.2f}) => Shunt Capacitance Discontinuity"
                ),
                rules_fired=rules,
            )

    # Rule 3: Total Reflection (Open vs Short Circuit)
    # Mean |Gamma| near 1.0 and flat frequency trend
    if mm >= 0.70:
        # Distinguish open vs short via de-embedded reflection or low-frequency real part
        if de_re >= 0 or lf_re >= 0:
            rules.append("R4_OPEN_CIRCUIT")
            return DiagnosisResult(
                "open",
                subtype="open_circuit",
                confidence="high" if ms < 0.05 else "medium",
                features=feat,
                explanation=(
                    f"Total reflection with positive real reflection "
                    f"(|Gamma|={mm:.3f}, Re={de_re:+.2f}) => Open Circuit"
                ),
                rules_fired=rules,
            )
        else:
            rules.append("R5_SHORT_CIRCUIT")
            return DiagnosisResult(
                "short",
                subtype="short_circuit",
                confidence="high" if ms < 0.05 else "medium",
                features=feat,
                explanation=(
                    f"Total reflection with negative real reflection "
                    f"(|Gamma|={mm:.3f}, Re={de_re:+.2f}) => Short Circuit"
                ),
                rules_fired=rules,
            )

    # Rule 4: Steady Resistive Mismatch
    if 0.05 <= mm < 0.70:
        rules.append("R6_RESISTIVE_MISMATCH")
        return DiagnosisResult(
            "mismatch",
            subtype="resistive_mismatch",
            confidence="high" if ms < 0.05 else "medium",
            features=feat,
            explanation=f"Uniform moderate reflection: mean |Gamma| = {mm:.3f}, std = {ms:.3f}",
            rules_fired=rules,
        )

    # Rule 5: Fallback / Ambiguous
    rules.append("R7_UNKNOWN")
    return DiagnosisResult(
        "unknown",
        subtype="uncertain",
        confidence="low",
        features=feat,
        explanation="Sweep metrics did not cleanly match canonical fault signatures.",
        rules_fired=rules,
    )


def distance_resolution(sweep_dict, vf=1.0):
    """
    Compute physical range resolution and unambiguous range for the given sweep.

    Returns
    -------
    dict:
        'range_res': range resolution delta_R [m] (vp / (2 * B))
        'unambig_range': unambiguous range R_max [m] (vp / (2 * df))
        'bandwidth_hz': frequency sweep bandwidth B [Hz]
    """
    freqs = np.asarray(sweep_dict["f"], dtype=float)
    N = len(freqs)
    if N < 2:
        return {"range_res": np.nan, "unambig_range": np.nan, "bandwidth_hz": 0.0}

    vp = lm.phase_velocity(vf)
    B = freqs[-1] - freqs[0]
    df = B / (N - 1)

    range_res = float(vp / (2.0 * B)) if B > 0 else np.nan
    unambig_range = float(vp / (2.0 * df)) if df > 0 else np.nan

    return {
        "range_res": range_res,
        "unambig_range": unambig_range,
        "bandwidth_hz": float(B),
    }


def estimate_distance(sweep_dict, vf, fault_class):
    """
    Estimate physical distance to fault in metres using Hann-windowed IFFT TDR.

    Parameters
    ----------
    sweep_dict  : dict containing 'f' and 'gamma' arrays
    vf          : velocity factor (0 < vf <= 1.0)
    fault_class : str, one of "healthy", "open", "short", "mismatch", "unknown"

    Returns
    -------
    float : distance to fault in metres, or None if not applicable / undetectable
    """
    # Matched / healthy line has no fault reflection echo
    if str(fault_class).lower() == "healthy":
        return None

    gamma = np.asarray(sweep_dict["gamma"], dtype=complex)
    freqs = np.asarray(sweep_dict["f"], dtype=float)

    if len(freqs) < 4:
        return None

    return _compute_ifft_distance(gamma, freqs, vf)


def _compute_ifft_distance(gamma, freqs, vf):
    """Internal IFFT TDR peak detection with grid uniformity validation."""
    N = len(freqs)
    if N < 4:
        return None

    # Step 1: Validate frequency spacing uniformity
    df_diffs = np.diff(freqs)
    df_mean = float(np.mean(df_diffs))
    if df_mean <= 0:
        return None

    relative_deviations = np.abs(df_diffs - df_mean) / df_mean
    is_uniform = np.all(relative_deviations < 1e-4)

    if not is_uniform:
        # Resample onto a uniform linear grid
        f_uniform = np.linspace(freqs[0], freqs[-1], N)
        gamma_real = np.interp(f_uniform, freqs, np.real(gamma))
        gamma_imag = np.interp(f_uniform, freqs, np.imag(gamma))
        gamma_proc = gamma_real + 1j * gamma_imag
        df = (f_uniform[-1] - f_uniform[0]) / (N - 1)
    else:
        gamma_proc = gamma
        df = df_mean

    B = freqs[-1] - freqs[0]
    if B <= 1e3:
        return None

    # Step 2: Apply Hann window to suppress sidelobes
    window = np.hanning(N)
    gamma_win = gamma_proc * window

    # Step 3: Zero-padding for fine temporal interpolation
    Npad = max(N * 8, 2048)
    gamma_pad = np.zeros(Npad, dtype=complex)
    gamma_pad[:N] = gamma_win

    # Step 4: Inverse FFT to pseudo-time domain
    # Scale by (Npad / N) so peak amplitude reflects windowed reflection magnitude
    time_response = np.fft.ifft(gamma_pad) * (float(Npad) / float(N))
    mag_time = np.abs(time_response)

    # Time axis: t_k = k / (Npad * df)
    t_axis = np.arange(Npad) / (Npad * df)

    # Suppress DC / direct port feed (bins 0..2) and non-causal second half
    search_mag = mag_time.copy()
    search_mag[:3] = 0.0
    search_mag[Npad // 2 :] = 0.0

    peak_idx = int(np.argmax(search_mag))
    peak_val = search_mag[peak_idx]

    # If peak is too weak (< 0.01), no clear echo detected
    if peak_val < 0.01:
        return None

    t_peak = t_axis[peak_idx]
    vp = lm.phase_velocity(vf)
    d_est = float(vp * t_peak / 2.0)

    return d_est
