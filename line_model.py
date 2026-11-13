"""
line_model.py -- Transmission-line electromagnetic model (Member 1).

Theory & Equations (Distributed Transmission-Line Telegrapher Model):
---------------------------------------------------------------------
1. Series impedance per unit length:
       Z = R + j*omega*L  [ohm/m]
   where omega = 2*pi*f [rad/s], R is conductor resistance [ohm/m],
   and L is loop inductance [H/m].

2. Shunt admittance per unit length:
       Y = G + j*omega*C  [S/m]
   where G is dielectric conductance [S/m] and C is capacitance [F/m].

3. Complex propagation constant:
       gamma = sqrt(Z * Y) = alpha + j*beta  [1/m]
   Branch selection: alpha >= 0 (attenuation constant [Np/m]),
                     beta >= 0 (phase constant [rad/m]).
   In the lossless limit (R = 0, G = 0):
       alpha = 0, beta = omega * sqrt(L * C) = 2*pi*f / vp = 2*pi / lambda.

4. Complex characteristic impedance:
       Z0 = sqrt(Z / Y)  [ohm]
   Branch selection: Re(Z0) >= 0 (passive transmission line).
   In the lossless limit:
       Z0 = sqrt(L / C) (purely real and positive).

5. Phase velocity:
       vp = omega / beta = 1 / sqrt(L * C) = vf * c0  [m/s]
   where vf = 1 / sqrt(er_eff) is the velocity factor (0 < vf <= 1).

6. Input impedance:
       Zin = Z0 * [ (ZL + Z0 * tanh(gamma*l)) / (Z0 + ZL * tanh(gamma*l)) ]
   Evaluated numerically via the reflection coefficient:
       Gamma(l) = Gamma_L * exp(-2*gamma*l)
       Zin = Z0 * (1 + Gamma(l)) / (1 - Gamma(l))
   so singular open-circuit (ZL = inf -> Gamma_L = +1.0) and short-circuit
   (ZL = 0 -> Gamma_L = -1.0) boundaries are handled without indeterminate forms.

Conventions (see INTERFACES.md):
  * SI units: ohm, metre, Hz, radian, S/m, H/m, F/m.
  * Impedances are Python/NumPy complex numbers. An open circuit is ZL = np.inf.
  * Inputs may be scalars or NumPy arrays (NumPy broadcasting supported).
  * Time convention e^{j w t}; Gamma(d) = Gamma_L * exp(-2j*beta*d).
"""
import numpy as np

C0 = 299_792_458.0  # speed of light in vacuum [m/s] (NIST/CODATA)
MU0 = 4.0 * np.pi * 1e-7  # permeability of free space [H/m]
SIGMA_COPPER = 5.80e7  # annealed standard copper electrical conductivity [S/m]

__all__ = [
    "C0", "MU0", "SIGMA_COPPER", "OPEN", "velocity_factor_from_er", "phase_velocity", "wavelength",
    "phase_constant", "load_reflection", "reflection_at_distance",
    "input_impedance", "input_impedance_at_freq", "quarter_wave_zin",
    "quarter_wave_impedance", "electrical_length_deg",
    "series_impedance", "shunt_admittance", "propagation_constant",
    "characteristic_impedance_rlgc", "phase_velocity_rlgc", "input_impedance_lossy",
    "skin_depth", "surface_resistance", "coaxial_skin_resistance", "frequency_dependent_resistance",
]

OPEN = np.inf


# ── Distributed Telegrapher Primary Parameter Equations ───────────────────────

def series_impedance(R, L, f):
    """
    Equation 1: Series impedance per unit length:
        Z = R + j * omega * L  [ohm/m]
    where omega = 2*pi*f [rad/s].
    """
    f_arr = np.asarray(f, dtype=float)
    if np.any(f_arr <= 0):
        raise ValueError("Frequency must be > 0")
    omega = 2.0 * np.pi * f_arr
    R_arr = np.asarray(R, dtype=complex)
    L_arr = np.asarray(L, dtype=complex)
    if np.any(np.real(R_arr) < 0) or np.any(np.real(L_arr) < 0):
        raise ValueError("R and L per unit length must be non-negative (passive media)")
    Z = R_arr + 1j * omega * L_arr
    return Z if Z.ndim else Z.item()


def shunt_admittance(G, C, f):
    """
    Equation 2: Shunt admittance per unit length:
        Y = G + j * omega * C  [S/m]
    where omega = 2*pi*f [rad/s].
    """
    f_arr = np.asarray(f, dtype=float)
    if np.any(f_arr <= 0):
        raise ValueError("Frequency must be > 0")
    omega = 2.0 * np.pi * f_arr
    G_arr = np.asarray(G, dtype=complex)
    C_arr = np.asarray(C, dtype=complex)
    if np.any(np.real(G_arr) < 0) or np.any(np.real(C_arr) < 0):
        raise ValueError("G and C per unit length must be non-negative (passive media)")
    Y = G_arr + 1j * omega * C_arr
    return Y if Y.ndim else Y.item()


def propagation_constant(R, L, G, C, f):
    """
    Equation 3: Complex propagation constant:
        gamma = sqrt(Z * Y) = alpha + j * beta  [1/m]

    Branch selection:
      alpha = Re(gamma) >= 0 (attenuation constant [Np/m])
      beta  = Im(gamma) >= 0 (phase constant [rad/m])
    """
    Z = np.asarray(series_impedance(R, L, f), dtype=complex)
    Y = np.asarray(shunt_admittance(G, C, f), dtype=complex)
    gamma = np.sqrt(Z * Y)

    # Physical branch selection for forward wave attenuation/phase progression
    # Ensure Re(gamma) = alpha >= 0 and Im(gamma) = beta >= 0
    gamma = np.where(np.real(gamma) < 0, -gamma, gamma)
    gamma = np.where((np.real(gamma) == 0) & (np.imag(gamma) < 0), -gamma, gamma)
    return gamma if gamma.ndim else gamma.item()


def characteristic_impedance_rlgc(R, L, G, C, f):
    """
    Equation 4: Characteristic impedance of distributed line:
        Z0 = sqrt(Z / Y)  [ohm]

    Branch selection:
      Re(Z0) >= 0 (passive transmission line).
    """
    Z = np.asarray(series_impedance(R, L, f), dtype=complex)
    Y = np.asarray(shunt_admittance(G, C, f), dtype=complex)
    Z0 = np.sqrt(Z / Y)

    # Physical branch selection: Re(Z0) >= 0 for passive media
    Z0 = np.where(np.real(Z0) < 0, -Z0, Z0)
    return Z0 if Z0.ndim else Z0.item()


def phase_velocity_rlgc(R, L, G, C, f):
    """
    Equation 5: Phase velocity:
        vp = omega / beta  [m/s]
    """
    f_arr = np.asarray(f, dtype=float)
    omega = 2.0 * np.pi * f_arr
    gamma = np.asarray(propagation_constant(R, L, G, C, f_arr), dtype=complex)
    beta = np.imag(gamma)
    singular = np.isclose(beta, 0.0, atol=1e-15)
    out = np.empty(beta.shape, dtype=float)
    out[singular] = np.inf
    ok = ~singular
    out[ok] = omega[ok] / beta[ok]
    return out if out.ndim else out.item()


def input_impedance_lossy(Z0, ZL, gamma, length):
    """
    Equation 6: Input impedance of general lossy transmission line:
        Zin = Z0 * [ (ZL + Z0*tanh(gamma*l)) / (Z0 + ZL*tanh(gamma*l)) ]

    Evaluated via spatial reflection shift Gamma(l) = Gamma_L * exp(-2*gamma*l):
        Zin = Z0 * (1 + Gamma(l)) / (1 - Gamma(l))
    Exact at open (inf) and short (0) boundaries without 0/0 or inf/inf indeterminate forms.
    """
    l_arr = np.asarray(length, dtype=float)
    if np.any(~np.isfinite(l_arr)) or np.any(l_arr < 0):
        raise ValueError("Line length must be finite and non-negative (>= 0)")
    Z0c = np.asarray(Z0, dtype=complex)
    ZL_arr = np.asarray(ZL, dtype=complex)
    gamma_arr = np.asarray(gamma, dtype=complex)
    if np.any(~np.isfinite(gamma_arr)):
        raise ValueError("Propagation constant gamma must be finite")

    # Gamma_L boundary condition
    GL = load_reflection(Z0c, ZL_arr)
    # Spatial shift by distance l toward generator: exp(-2 * gamma * l)
    G = GL * np.exp(-2.0 * gamma_arr * l_arr)

    num = 1.0 + G
    den = 1.0 - G
    num, den, Z0b = np.broadcast_arrays(np.asarray(num), np.asarray(den), Z0c)
    out = np.empty(num.shape, dtype=complex)
    singular = np.abs(den) < 1e-12
    out[singular] = np.inf
    ok = ~singular
    out[ok] = Z0b[ok] * num[ok] / den[ok]
    return out if out.ndim else out.item()


# ── Lossless Transmission Line Core Functions (Member 1 Frozen Contracts) ────


def velocity_factor_from_er(er_eff):
    """Velocity factor vf = 1/sqrt(effective relative permittivity)."""
    er_eff = np.asarray(er_eff, dtype=float)
    if np.any(~np.isfinite(er_eff)) or np.any(er_eff <= 0):
        raise ValueError("er_eff must be finite and > 0")
    return 1.0 / np.sqrt(er_eff)


def phase_velocity(vf=1.0):
    """v = vf * c0  [m/s]."""
    _check_vf(vf)
    return np.asarray(vf, dtype=float) * C0


def wavelength(f, vf=1.0):
    """lambda = v / f  [m]."""
    f = np.asarray(f, dtype=float)
    if np.any(~np.isfinite(f)) or np.any(f <= 0):
        raise ValueError("frequency must be finite and > 0")
    return phase_velocity(vf) / f


def phase_constant(f, vf=1.0):
    """beta = 2*pi / lambda = 2*pi*f / v  [rad/m] (lossless line)."""
    return 2.0 * np.pi / wavelength(f, vf)


def electrical_length_deg(f, length, vf=1.0):
    """Electrical length beta*l in degrees."""
    l_arr = np.asarray(length, dtype=float)
    if np.any(~np.isfinite(l_arr)) or np.any(l_arr < 0):
        raise ValueError("length must be finite and non-negative (>= 0)")
    return np.degrees(phase_constant(f, vf) * l_arr)


def load_reflection(Z0, ZL):
    """Gamma_L = (ZL - Z0)/(ZL + Z0). ZL = inf (open) -> +1."""
    Z0 = np.asarray(Z0, dtype=complex)
    ZL = np.asarray(ZL, dtype=complex)
    if np.any(np.isnan(Z0)) or np.any(np.isnan(ZL)):
        raise ValueError("Impedances Z0 and ZL cannot contain NaN")
    if np.any(np.real(Z0) <= 0):
        raise ValueError("Line impedance Z0 must have strictly positive real part")
    ZL_b, Z0_b = np.broadcast_arrays(ZL, Z0)
    out = np.empty(ZL_b.shape, dtype=complex)
    inf = ~np.isfinite(ZL_b)
    out[inf] = 1.0 + 0j
    fin = ~inf
    out[fin] = (ZL_b[fin] - Z0_b[fin]) / (ZL_b[fin] + Z0_b[fin])
    return out if out.ndim else out.item()


def reflection_at_distance(Z0, ZL, beta, d):
    """Gamma(d) = Gamma_L * exp(-2j*beta*d), d measured from the load toward source."""
    d_arr = np.asarray(d, dtype=float)
    if np.any(~np.isfinite(d_arr)) or np.any(d_arr < 0):
        raise ValueError("Distance d must be finite and non-negative (>= 0)")
    b_arr = np.asarray(beta, dtype=float)
    if np.any(~np.isfinite(b_arr)):
        raise ValueError("Phase constant beta must be finite")
    return load_reflection(Z0, ZL) * np.exp(-2j * b_arr * d_arr)


def input_impedance(Z0, ZL, beta, length):
    """
    Input impedance of a lossless line of given length terminated in ZL:
        Zin = Z0 * (ZL + j Z0 tan(bl)) / (Z0 + j ZL tan(bl))
    Evaluated via Gamma so open (inf) and short (0) loads are handled exactly:
        Zin = Z0 * (1 + G) / (1 - G),  G = Gamma_L * exp(-2j*beta*length)
    Returns complex (np.inf where the impedance is infinite).
    """
    l_arr = np.asarray(length, dtype=float)
    if np.any(~np.isfinite(l_arr)) or np.any(l_arr < 0):
        raise ValueError("Line length must be finite and non-negative (>= 0)")
    Z0c = np.asarray(Z0, dtype=complex)
    G = reflection_at_distance(Z0, ZL, beta, l_arr)
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
    Z0_arr = np.asarray(Z0, dtype=complex)
    ZL_arr = np.asarray(ZL, dtype=complex)
    if np.any(np.isnan(Z0_arr)) or np.any(np.isnan(ZL_arr)):
        raise ValueError("Impedances cannot contain NaN")
    Z0_b, ZL_b = np.broadcast_arrays(Z0_arr, ZL_arr)
    out = np.empty(ZL_b.shape, dtype=complex)
    zero_mask = np.isclose(np.abs(ZL_b), 0.0, atol=1e-15)
    out[zero_mask] = np.inf
    inf_mask = np.isinf(np.abs(ZL_b))
    out[inf_mask] = 0.0 + 0.0j
    normal_mask = ~zero_mask & ~inf_mask
    out[normal_mask] = (Z0_b[normal_mask] ** 2) / ZL_b[normal_mask]
    return out if out.ndim else out.item()


def quarter_wave_impedance(Z_in_line, R_load):
    """
    Characteristic impedance of a quarter-wave transformer matching a real
    load R_load to a real line impedance Z_in_line:  Zt = sqrt(Z_in_line * R_load).
    (Member 3 builds the full matching module on top of this.)
    """
    if np.imag(Z_in_line) != 0 or np.imag(R_load) != 0:
        raise ValueError("Quarter-wave transformer requires real impedances")
    if np.real(Z_in_line) <= 0 or np.real(R_load) <= 0:
        raise ValueError("Quarter-wave transformer requires strictly positive real impedances")
    return float(np.sqrt(np.real(Z_in_line) * np.real(R_load)))


def _check_vf(vf):
    vf = np.asarray(vf, dtype=float)
    if np.any(~np.isfinite(vf)) or np.any(vf <= 0) or np.any(vf > 1):
        raise ValueError("velocity factor must be finite and satisfy 0 < vf <= 1")


# ── Skin-Effect & High-Frequency Loss Models ──────────────────────────────────

def skin_depth(f, sigma=SIGMA_COPPER, mu_r=1.0):
    """
    Skin depth in a good conductor:
        delta_s = 1 / sqrt(pi * f * mu * sigma)  [m]
    where mu = MU0 * mu_r [H/m].

    Parameters
    ----------
    f     : frequency [Hz] (must be strictly positive and finite)
    sigma : conductivity [S/m] (default: copper = 5.80e7 S/m)
    mu_r  : relative permeability (default: 1.0 for non-magnetic conductor)

    Returns
    -------
    float or ndarray : skin depth in metres [m]
    """
    f_arr = np.asarray(f, dtype=float)
    if np.any(~np.isfinite(f_arr)) or np.any(f_arr <= 0):
        raise ValueError("Frequency must be strictly positive and finite")
    if sigma <= 0 or not np.isfinite(sigma):
        raise ValueError("Conductivity sigma must be strictly positive and finite")
    if mu_r <= 0 or not np.isfinite(mu_r):
        raise ValueError("Relative permeability mu_r must be strictly positive and finite")
    
    mu = MU0 * float(mu_r)
    delta = 1.0 / np.sqrt(np.pi * f_arr * mu * float(sigma))
    return delta if delta.ndim else delta.item()


def surface_resistance(f, sigma=SIGMA_COPPER, mu_r=1.0):
    """
    Surface resistance (real part of surface impedance):
        Rs = 1 / (sigma * delta_s) = sqrt(pi * f * mu / sigma)  [ohm/square]

    Parameters
    ----------
    f     : frequency [Hz]
    sigma : conductivity [S/m]
    mu_r  : relative permeability

    Returns
    -------
    float or ndarray : surface resistance in ohms [ohm]
    """
    delta = skin_depth(f, sigma=sigma, mu_r=mu_r)
    Rs = 1.0 / (float(sigma) * np.asarray(delta, dtype=float))
    return Rs if Rs.ndim else Rs.item()


def coaxial_skin_resistance(f, a, b, sigma=SIGMA_COPPER, mu_r=1.0):
    """
    Skin-effect series resistance per unit length for a coaxial line:
        R_skin(f) = (Rs / (2*pi)) * (1/a + 1/b)  [ohm/m]
    where a is inner conductor radius and b is outer conductor radius (b > a > 0).

    Parameters
    ----------
    f     : frequency [Hz]
    a     : inner conductor radius [m]
    b     : outer conductor shield inner radius [m]
    sigma : conductor conductivity [S/m]
    mu_r  : conductor relative permeability

    Returns
    -------
    float or ndarray : series skin resistance in ohm/m [ohm/m]
    """
    if a <= 0 or not np.isfinite(a):
        raise ValueError("Inner conductor radius 'a' must be strictly positive and finite")
    if b <= a or not np.isfinite(b):
        raise ValueError("Outer conductor radius 'b' must be strictly greater than inner radius 'a'")
    
    Rs = surface_resistance(f, sigma=sigma, mu_r=mu_r)
    geom_factor = (1.0 / float(a) + 1.0 / float(b)) / (2.0 * np.pi)
    R_skin = np.asarray(Rs, dtype=float) * geom_factor
    return R_skin if R_skin.ndim else R_skin.item()


def frequency_dependent_resistance(f, R_dc, f_ref=1e6):
    """
    Continuous transition model for frequency-dependent conductor resistance:
        R(f) = R_dc * sqrt(1 + f / f_ref)  [ohm/m]
    Provides smooth transition from DC resistance at low frequencies to
    classical sqrt(f) skin-depth behavior at frequencies f >> f_ref.

    Parameters
    ----------
    f     : frequency [Hz]
    R_dc  : DC resistance per unit length [ohm/m]
    f_ref : reference transition frequency [Hz] (default: 1.0 MHz)

    Returns
    -------
    float or ndarray : total resistance per unit length [ohm/m]
    """
    f_arr = np.asarray(f, dtype=float)
    if np.any(~np.isfinite(f_arr)) or np.any(f_arr <= 0):
        raise ValueError("Frequency must be strictly positive and finite")
    if R_dc < 0 or not np.isfinite(R_dc):
        raise ValueError("R_dc must be non-negative and finite")
    if f_ref <= 0 or not np.isfinite(f_ref):
        raise ValueError("f_ref must be strictly positive and finite")
    
    R_total = float(R_dc) * np.sqrt(1.0 + f_arr / float(f_ref))
    return R_total if R_total.ndim else R_total.item()

