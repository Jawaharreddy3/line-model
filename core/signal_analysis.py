"""
core/signal_analysis.py -- Spectral, reflection, and impedance analysis tools.

Computes:
  - Complex reflection coefficient S11, magnitude, and unwrapped phase.
  - Input impedance decomposition: Rin (resistance) and Xin (reactance).
  - Normalized impedance coordinates (r + jx) for Smith chart mapping.
  - Complex Gaussian noise modeling with SNR tracking and passivity checks.
  - Frequency derivative metrics: magnitude trend and phase slope.
"""

import numpy as np

__all__ = [
    "decompose_impedance",
    "compute_spectral_features",
    "add_measurement_noise",
    "phase_slope_rad_per_hz",
]


def decompose_impedance(zin):
    """
    Decompose complex input impedance Zin into resistance Rin and reactance Xin.

    Parameters
    ----------
    zin : complex or array of complex [ohm]

    Returns
    -------
    rin : real part [ohm]
    xin : imaginary part [ohm]
    """
    z = np.asarray(zin, dtype=complex)
    rin = np.real(z)
    xin = np.imag(z)
    return (rin, xin) if z.ndim else (float(rin), float(xin))


def compute_spectral_features(gamma, freqs):
    """
    Compute comprehensive scalar and vector features from a frequency sweep.

    Parameters
    ----------
    gamma : complex array of reflection coefficients
    freqs : float array of frequencies [Hz]

    Returns
    -------
    dict of features:
        mag          : array of |Gamma|
        phase_rad    : array of unwrapped phase [rad]
        phase_deg    : array of unwrapped phase [deg]
        mag_mean     : mean reflection magnitude
        mag_std      : standard deviation of reflection magnitude
        trend        : high-freq minus low-freq magnitude difference
        phase_slope  : linear slope of phase vs freq [rad/Hz]
        is_passive   : bool, whether all |Gamma| <= 1.0 + 1e-6
    """
    g = np.asarray(gamma, dtype=complex)
    f = np.asarray(freqs, dtype=float)
    N = len(g)

    mag = np.abs(g)
    is_passive = bool(np.all(mag <= 1.0 + 1e-6))

    if N > 0:
        mag_mean = float(np.mean(mag))
        mag_std = float(np.std(mag))
        quarter = max(1, N // 4)
        mag_low = float(np.mean(mag[:quarter]))
        mag_high = float(np.mean(mag[-quarter:]))
        trend = float(mag_high - mag_low)
        phase_rad = np.unwrap(np.angle(g))
        phase_deg = np.degrees(phase_rad)
    else:
        mag_mean = 0.0
        mag_std = 0.0
        trend = 0.0
        phase_rad = np.array([])
        phase_deg = np.array([])

    slope = 0.0
    phi0 = 0.0
    cos_phi0 = 0.0
    if N > 1:
        try:
            pfit = np.polyfit(f, phase_rad, 1)
            slope = float(pfit[0])
            phi0 = float(pfit[1])
            cos_phi0 = float(np.cos(phi0))
        except Exception:
            slope = phase_slope_rad_per_hz(phase_rad, f)

    return {
        "mag": mag,
        "phase_rad": phase_rad,
        "phase_deg": phase_deg,
        "mag_mean": mag_mean,
        "mag_std": mag_std,
        "trend": trend,
        "phase_slope": slope,
        "phi0": phi0,
        "cos_phi0": cos_phi0,
        "is_passive": is_passive,
    }


def phase_slope_rad_per_hz(phase_unwrapped, freqs):
    """
    Compute linear slope d(phi)/df via least-squares polynomial fit.

    Parameters
    ----------
    phase_unwrapped : float array of unwrapped phase [rad]
    freqs           : float array of frequencies [Hz]

    Returns
    -------
    slope : float, rad/Hz
    """
    p = np.asarray(phase_unwrapped, dtype=float)
    f = np.asarray(freqs, dtype=float)
    if len(f) < 2:
        return 0.0
    pfit = np.polyfit(f, p, 1)
    return float(pfit[0])


def add_measurement_noise(gamma, noise_std, rng=None, clip_passive=False):
    """
    Add complex zero-mean Gaussian noise to reflection coefficient array.

    Parameters
    ----------
    gamma        : complex array of reflection coefficients
    noise_std    : standard deviation of complex noise
    rng          : np.random.Generator (optional)
    clip_passive : if True, clip |Gamma| <= 1.0; if False (recommended per VNA metrology),
                   preserves unclipped noisy samples exceeding unity.

    Returns
    -------
    noisy_gamma : complex array
    info        : dict with 'snr_db', 'num_non_passive'
    """
    if noise_std <= 0.0:
        return gamma.copy(), {"snr_db": float("inf"), "num_non_passive": 0}

    if rng is None:
        rng = np.random.default_rng(42)

    g = np.asarray(gamma, dtype=complex)
    N = len(g)
    sigma_1d = noise_std / np.sqrt(2.0)
    noise = rng.normal(0, sigma_1d, N) + 1j * rng.normal(0, sigma_1d, N)
    g_noisy = g + noise

    # Detect values outside unit circle
    mag_noisy = np.abs(g_noisy)
    non_passive_mask = mag_noisy > 1.0
    num_non_passive = int(np.sum(non_passive_mask))

    if clip_passive and num_non_passive > 0:
        g_noisy[non_passive_mask] = (
            g_noisy[non_passive_mask] / mag_noisy[non_passive_mask]
        )

    # Compute Signal-to-Noise Ratio (SNR) in dB
    sig_pwr = np.mean(np.abs(g) ** 2)
    noise_pwr = noise_std ** 2
    snr_db = (
        float(10.0 * np.log10(sig_pwr / noise_pwr))
        if noise_pwr > 0 and sig_pwr > 0
        else float("inf")
    )

    return g_noisy, {
        "snr_db": snr_db,
        "num_non_passive": num_non_passive,
    }
