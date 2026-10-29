"""
line_model.py -- Lossless transmission-line core model (Member 1).

Conventions (see INTERFACES.md):
  * SI units: ohm, metre, Hz, radian.
  * Impedances are Python/NumPy complex numbers. An open circuit is ZL = np.inf.
  * Inputs may be scalars or NumPy arrays (broadcasting works).
  * Time convention e^{j w t}; Gamma(d) = Gamma_L * exp(-2j*beta*d).
"""
import numpy as np

C0 = 299_792_458.0  # speed of light in vacuum [m/s]

__all__ = [
    "C0", "OPEN", "velocity_factor_from_er", "phase_velocity", "wavelength",
    "phase_constant", "load_reflection", "reflection_at_distance",
    "input_impedance", "input_impedance_at_freq", "quarter_wave_zin",
    "quarter_wave_impedance", "electrical_length_deg",
]

OPEN = np.inf


def velocity_factor_from_er(er_eff):
    """Velocity factor vf = 1/sqrt(effective relative permittivity)."""
    er_eff = np.asarray(er_eff, dtype=float)
    if np.any(er_eff <= 0):
        raise ValueError("er_eff must be > 0")
    return 1.0 / np.sqrt(er_eff)


def phase_velocity(vf=1.0):
    """v = vf * c0  [m/s]."""
    _check_vf(vf)
    return np.asarray(vf, dtype=float) * C0


def wavelength(f, vf=1.0):
    """lambda = v / f  [m]."""
    f = np.asarray(f, dtype=float)
    if np.any(f <= 0):
        raise ValueError("frequency must be > 0")
    return phase_velocity(vf) / f


def phase_constant(f, vf=1.0):
    """beta = 2*pi / lambda = 2*pi*f / v  [rad/m] (lossless line)."""
    return 2.0 * np.pi / wavelength(f, vf)


def electrical_length_deg(f, length, vf=1.0):
    """Electrical length beta*l in degrees."""
    return np.degrees(phase_constant(f, vf) * np.asarray(length, dtype=float))


def load_reflection(Z0, ZL):
    """Gamma_L = (ZL - Z0)/(ZL + Z0). ZL = inf (open) -> +1."""
    Z0 = np.asarray(Z0, dtype=complex)
    ZL = np.asarray(ZL, dtype=complex)
    ZL_b, Z0_b = np.broadcast_arrays(ZL, Z0)
    out = np.empty(ZL_b.shape, dtype=complex)
    inf = ~np.isfinite(ZL_b)
    out[inf] = 1.0
    fin = ~inf
    out[fin] = (ZL_b[fin] - Z0_b[fin]) / (ZL_b[fin] + Z0_b[fin])
    return out if out.ndim else out.item()


def reflection_at_distance(Z0, ZL, beta, d):
    """Gamma(d) = Gamma_L * exp(-2j*beta*d), d measured from the load toward source."""
    return load_reflection(Z0, ZL) * np.exp(-2j * np.asarray(beta) * np.asarray(d))


def input_impedance(Z0, ZL, beta, length):
    """
    Input impedance of a lossless line of given length terminated in ZL:
        Zin = Z0 * (ZL + j Z0 tan(bl)) / (Z0 + j ZL tan(bl))
    Evaluated via Gamma so open (inf) and short (0) loads are handled exactly:
        Zin = Z0 * (1 + G) / (1 - G),  G = Gamma_L * exp(-2j*beta*length)
    Returns complex (np.inf where the impedance is infinite).
    """
    Z0c = np.asarray(Z0, dtype=complex)
    G = reflection_at_distance(Z0, ZL, beta, length)
    num = 1.0 + G
    den = 1.0 - G
    num, den, Z0b = np.broadcast_arrays(np.asarray(num), np.asarray(den), Z0c)
    out = np.empty(num.shape, dtype=complex)
    singular = np.abs(den) < 1e-12
    out[singular] = np.inf
    ok = ~singular
    out[ok] = Z0b[ok] * num[ok] / den[ok]
    return out if out.ndim else out.item()


def input_impedance_at_freq(Z0, ZL, f, length, vf=1.0):
    """Convenience: Zin for a line of physical `length` at frequency f."""
    return input_impedance(Z0, ZL, phase_constant(f, vf), length)


def quarter_wave_zin(Z0, ZL):
    """Zin of an exactly quarter-wave line: Z0^2 / ZL (analytic cross-check)."""
    return np.asarray(Z0, dtype=complex) ** 2 / np.asarray(ZL, dtype=complex)


def quarter_wave_impedance(Z_in_line, R_load):
    """
    Characteristic impedance of a quarter-wave transformer matching a real
    load R_load to a real line impedance Z_in_line:  Zt = sqrt(Z_in_line * R_load).
    (Member 3 builds the full matching module on top of this.)
    """
    if np.imag(Z_in_line) != 0 or np.imag(R_load) != 0:
        raise ValueError("Quarter-wave transformer requires real impedances")
    return float(np.sqrt(np.real(Z_in_line) * np.real(R_load)))


def _check_vf(vf):
    vf = np.asarray(vf, dtype=float)
    if np.any(vf <= 0) or np.any(vf > 1):
        raise ValueError("velocity factor must satisfy 0 < vf <= 1")
