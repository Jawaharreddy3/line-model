"""
tests/analytical_benchmarks.py -- Independent analytical reference models.

CRITICAL REQUIREMENT:
This module contains pure, independent textbook closed-form equations from
electromagnetic transmission line theory (Pozar, "Microwave Engineering").
It DOES NOT import from line_model, measurements, fault_simulation, or matching.
It serves as the unbiased ground truth benchmark for all automated tests.
"""

import numpy as np

C0_EXACT = 299792458.0  # Speed of light in vacuum [m/s]


def analytical_phase_velocity(vf):
    """vp = vf * c0 [m/s]."""
    return float(vf) * C0_EXACT


def analytical_series_impedance(R, L, f):
    """Z = R + j*omega*L [ohm/m]."""
    omega = 2.0 * np.pi * np.asarray(f, dtype=float)
    return float(R) + 1j * omega * float(L)


def analytical_shunt_admittance(G, C, f):
    """Y = G + j*omega*C [S/m]."""
    omega = 2.0 * np.pi * np.asarray(f, dtype=float)
    return float(G) + 1j * omega * float(C)


def analytical_propagation_constant(R, L, G, C, f):
    """
    gamma = sqrt(Z * Y) = alpha + j*beta [1/m].
    Principal branch enforces alpha >= 0, beta >= 0 for passive media.
    """
    Z = analytical_series_impedance(R, L, f)
    Y = analytical_shunt_admittance(G, C, f)
    gamma = np.sqrt(Z * Y)
    gamma_arr = np.asarray(gamma, dtype=complex)
    # Ensure passive branch
    real_part = np.abs(np.real(gamma_arr))
    imag_part = np.abs(np.imag(gamma_arr))
    out = real_part + 1j * imag_part
    return out if out.ndim else out.item()


def analytical_characteristic_impedance(R, L, G, C, f):
    """
    Z0 = sqrt(Z / Y) [ohm].
    Branch selection enforces Re(Z0) >= 0.
    """
    Z = analytical_series_impedance(R, L, f)
    Y = analytical_shunt_admittance(G, C, f)
    z0 = np.sqrt(Z / Y)
    z0_arr = np.asarray(z0, dtype=complex)
    neg_real = np.real(z0_arr) < 0
    z0_arr[neg_real] = -z0_arr[neg_real]
    return z0_arr if z0_arr.ndim else z0_arr.item()


def analytical_load_reflection(ZL, Z0):
    """
    Gamma_L = (ZL - Z0) / (ZL + Z0).
    Open circuit (ZL = inf) evaluates to +1.0 + 0j.
    """
    ZL_arr = np.asarray(ZL, dtype=complex)
    Z0_arr = np.asarray(Z0, dtype=complex)
    ZL_b, Z0_b = np.broadcast_arrays(ZL_arr, Z0_arr)
    out = np.empty(ZL_b.shape, dtype=complex)
    inf_mask = ~np.isfinite(ZL_b)
    out[inf_mask] = 1.0 + 0j
    fin_mask = ~inf_mask
    out[fin_mask] = (ZL_b[fin_mask] - Z0_b[fin_mask]) / (ZL_b[fin_mask] + Z0_b[fin_mask])
    return out if out.ndim else out.item()


def analytical_lossless_zin(Z0, ZL, f, length, vf=1.0):
    """
    Independent textbook formula for input impedance of a lossless line:
    Zin = Z0 * [ZL + j*Z0*tan(beta*l)] / [Z0 + j*ZL*tan(beta*l)]
    Computed via reflection coefficient to handle open/short singularities cleanly:
    Gamma_in = Gamma_L * exp(-2j * beta * l)
    Zin = Z0 * (1 + Gamma_in) / (1 - Gamma_in)
    """
    vp = analytical_phase_velocity(vf)
    f_arr = np.asarray(f, dtype=float)
    beta = 2.0 * np.pi * f_arr / vp
    gamma_l = analytical_load_reflection(ZL, Z0)
    gamma_in = gamma_l * np.exp(-2j * beta * float(length))
    
    denom = 1.0 - gamma_in
    singular = np.abs(denom) < 1e-12
    out = np.empty_like(gamma_in, dtype=complex)
    out[singular] = np.inf + 0j
    ok = ~singular
    out[ok] = float(Z0) * (1.0 + gamma_in[ok]) / denom[ok]
    return out if out.ndim else out.item()


def analytical_lossy_zin(Z0_complex, ZL, gamma, length):
    """
    Independent textbook formula for input impedance of a lossy line:
    Zin = Z0 * [ZL + Z0*tanh(gamma*l)] / [Z0 + ZL*tanh(gamma*l)]
    """
    gamma_l = analytical_load_reflection(ZL, Z0_complex)
    gamma_in = gamma_l * np.exp(-2.0 * gamma * float(length))
    denom = 1.0 - gamma_in
    singular = np.abs(denom) < 1e-12
    out = np.empty_like(gamma_in, dtype=complex)
    out[singular] = np.inf + 0j
    ok = ~singular
    out[ok] = Z0_complex * (1.0 + gamma_in[ok]) / denom[ok]
    return out if out.ndim else out.item()


def analytical_vswr(gamma):
    """VSWR = (1 + |Gamma|) / (1 - |Gamma|)."""
    mag = np.abs(np.asarray(gamma, dtype=complex))
    out = np.full(mag.shape, np.nan, dtype=float)
    total_refl = np.isclose(mag, 1.0, atol=1e-12)
    out[total_refl] = np.inf
    valid_passive = (mag >= 0.0) & (mag < 1.0 - 1e-12)
    out[valid_passive] = (1.0 + mag[valid_passive]) / (1.0 - mag[valid_passive])
    return out if out.ndim else out.item()


def analytical_return_loss_db(gamma):
    """RL = -20 * log10(|Gamma|)."""
    mag = np.abs(np.asarray(gamma, dtype=complex))
    out = np.empty(mag.shape, dtype=float)
    zero_mask = mag <= 1e-15
    out[zero_mask] = np.inf
    non_zero = ~zero_mask
    out[non_zero] = -20.0 * np.log10(mag[non_zero])
    return out if out.ndim else out.item()


def analytical_quarter_wave_transformer(Z0, RL, f0, vf=1.0):
    """
    Zt = sqrt(Z0 * RL)
    lt = lambda / 4 = vp / (4 * f0)
    """
    Zt = float(np.sqrt(float(Z0) * float(RL)))
    vp = analytical_phase_velocity(vf)
    lt = float(vp / (4.0 * float(f0)))
    return {"Zt": Zt, "length_m": lt}


def analytical_resolution_metrics(f_array, vf=1.0):
    """
    Physical Rayleigh range resolution: delta_R = vp / (2 * B)
    Unambiguous range: R_max = vp / (2 * delta_f)
    """
    vp = analytical_phase_velocity(vf)
    f = np.asarray(f_array, dtype=float)
    B = float(f[-1] - f[0])
    N = len(f)
    df = float(B / (N - 1)) if N > 1 else 0.0
    range_res = float(vp / (2.0 * B)) if B > 0 else np.nan
    unambig_range = float(vp / (2.0 * df)) if df > 0 else np.nan
    return {"bandwidth_hz": B, "range_res_m": range_res, "unambig_range_m": unambig_range}
