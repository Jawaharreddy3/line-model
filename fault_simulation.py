"""
fault_simulation.py -- Dedicated 6-scenario fault simulation engine.

Simulates transmission lines with:
  1. healthy      : Matched line (ZL = Z0)
  2. mismatch     : Pure resistive mismatch (ZL = RL != Z0)
  3. open         : Open-circuit termination (ZL = np.inf)
  4. short        : Short-circuit termination (ZL = 0.0)
  5. series_L     : Series inductive discontinuity (Zs = j*w*L) at distance d
  6. shunt_C      : Shunt capacitive discontinuity (Yp = j*w*C) at distance d

Discontinuities use 2-port ABCD matrix cascading:
  M_total = M_line(0..d) @ M_discontinuity @ M_line(d..length)
"""

import numpy as np
import line_model as lm
import measurements as meas

FAULT_SCENARIOS = [
    "healthy",
    "mismatch",
    "open",
    "short",
    "series_L",
    "shunt_C",
]

__all__ = [
    "FAULT_SCENARIOS",
    "abcd_uniform_line",
    "abcd_series_impedance",
    "abcd_shunt_admittance",
    "zin_from_abcd",
    "simulate_fault",
]


def abcd_uniform_line(Z0, beta, length):
    """
    ABCD matrix for a lossless uniform transmission-line section.
        [ [cos(beta*l),     j*Z0*sin(beta*l)],
          [j*sin(beta*l)/Z0, cos(beta*l)     ] ]
    Supports scalar or array frequencies.
    """
    bl = np.asarray(beta, dtype=float) * float(length)
    cos_bl = np.cos(bl)
    sin_bl = np.sin(bl)
    Z0c = complex(Z0)

    A = cos_bl
    B = 1j * Z0c * sin_bl
    C = 1j * (sin_bl / Z0c)
    D = cos_bl

    return A, B, C, D


def abcd_series_impedance(Z):
    """
    ABCD matrix for a series impedance:
        [ [1, Z],
          [0, 1] ]
    """
    Z = np.asarray(Z, dtype=complex)
    ones = np.ones_like(Z, dtype=complex)
    zeros = np.zeros_like(Z, dtype=complex)
    return ones, Z, zeros, ones


def abcd_shunt_admittance(Y):
    """
    ABCD matrix for a shunt admittance:
        [ [1, 0],
          [Y, 1] ]
    """
    Y = np.asarray(Y, dtype=complex)
    ones = np.ones_like(Y, dtype=complex)
    zeros = np.zeros_like(Y, dtype=complex)
    return ones, zeros, Y, ones


def multiply_abcd(M1, M2):
    """Multiply two ABCD matrix tuples (A1, B1, C1, D1) @ (A2, B2, C2, D2)."""
    A1, B1, C1, D1 = M1
    A2, B2, C2, D2 = M2
    A = A1 * A2 + B1 * C2
    B = A1 * B2 + B1 * D2
    C = C1 * A2 + D1 * C2
    D = C1 * B2 + D1 * D2
    return A, B, C, D


def zin_from_abcd(ABCD, ZL):
    """
    Input impedance from ABCD matrix and load impedance ZL:
        Zin = (A*ZL + B) / (C*ZL + D)
    Handles ZL = np.inf: Zin = A / C.
    """
    A, B, C, D = ABCD
    ZL_val = complex(ZL)

    if np.isinf(abs(ZL_val)):
        # Limit as ZL -> inf is A / C
        C_safe = np.where(np.abs(C) < 1e-15, 1e-15, C)
        out = A / C_safe
        out[np.abs(C) < 1e-15] = np.inf
        return out

    num = A * ZL_val + B
    den = C * ZL_val + D
    singular = np.abs(den) < 1e-15

    den_safe = np.where(singular, 1e-15, den)
    out = num / den_safe
    out[singular] = np.inf
    return out


def simulate_fault(
    scenario,
    Z0,
    length,
    f_array,
    vf=1.0,
    fault_pos=None,
    L_val=10e-9,
    C_val=10e-12,
    ZL_mismatch=100.0,
    noise_std=0.0,
    rng=None,
):
    """
    Simulate one of the 6 canonical transmission line fault scenarios.

    Parameters
    ----------
    scenario    : str, one of FAULT_SCENARIOS
    Z0          : characteristic impedance [ohm]
    length      : total line length [m]
    f_array     : frequency array [Hz]
    vf          : velocity factor (0 < vf <= 1.0)
    fault_pos   : physical position of fault from input [m] (default: length / 2)
    L_val       : inductance [H] for 'series_L' scenario
    C_val       : capacitance [F] for 'shunt_C' scenario
    ZL_mismatch : load impedance [ohm] for 'mismatch' scenario
    noise_std   : standard deviation of complex Gaussian noise on Gamma
    rng         : np.random.Generator (optional)

    Returns
    -------
    dict with:
        'sweep': dict with keys ('f', 'zin', 'gamma', 'vswr', 'rl_db')
        'truth': ground truth metadata dict
    """
    if scenario not in FAULT_SCENARIOS:
        raise ValueError(
            f"Unknown scenario '{scenario}'. Choose from {FAULT_SCENARIOS}"
        )

    f_arr = np.asarray(f_array, dtype=float)
    if np.any(f_arr <= 0):
        raise ValueError("Frequencies must be > 0")

    if fault_pos is None:
        fault_pos = length / 2.0
    fault_pos = float(np.clip(fault_pos, 0.0, length))

    beta = lm.phase_constant(f_arr, vf=vf)
    omega = 2.0 * np.pi * f_arr

    truth = {
        "scenario": scenario,
        "Z0": float(Z0),
        "length": float(length),
        "fault_pos": fault_pos,
        "L_val": float(L_val),
        "C_val": float(C_val),
        "vf": float(vf),
    }

    if scenario == "healthy":
        ZL = complex(Z0)
        truth["ZL"] = ZL
        truth["fault_pos"] = None
        zin = lm.input_impedance_at_freq(Z0, ZL, f_arr, length, vf=vf)

    elif scenario == "mismatch":
        ZL = complex(ZL_mismatch)
        truth["ZL"] = ZL
        truth["fault_pos"] = float(length)
        zin = lm.input_impedance_at_freq(Z0, ZL, f_arr, length, vf=vf)

    elif scenario == "open":
        ZL = lm.OPEN
        truth["ZL"] = ZL
        truth["fault_pos"] = float(length)
        zin = lm.input_impedance_at_freq(Z0, ZL, f_arr, length, vf=vf)

    elif scenario == "short":
        ZL = 0.0 + 0j
        truth["ZL"] = ZL
        truth["fault_pos"] = float(length)
        zin = lm.input_impedance_at_freq(Z0, ZL, f_arr, length, vf=vf)

    elif scenario == "series_L":
        ZL = complex(Z0)
        truth["ZL"] = ZL
        truth["fault_pos"] = fault_pos
        d1 = fault_pos
        d2 = length - fault_pos

        M1 = abcd_uniform_line(Z0, beta, d1)
        Zs = 1j * omega * L_val
        M_disc = abcd_series_impedance(Zs)
        M2 = abcd_uniform_line(Z0, beta, d2)

        M_total = multiply_abcd(multiply_abcd(M1, M_disc), M2)
        zin = zin_from_abcd(M_total, ZL)

    elif scenario == "shunt_C":
        ZL = complex(Z0)
        truth["ZL"] = ZL
        truth["fault_pos"] = fault_pos
        d1 = fault_pos
        d2 = length - fault_pos

        M1 = abcd_uniform_line(Z0, beta, d1)
        Yp = 1j * omega * C_val
        M_disc = abcd_shunt_admittance(Yp)
        M2 = abcd_uniform_line(Z0, beta, d2)

        M_total = multiply_abcd(multiply_abcd(M1, M_disc), M2)
        zin = zin_from_abcd(M_total, ZL)

    gamma = meas.reflection_coefficient(zin, Z0)

    # Optional noise addition (S11 measurement noise)
    if noise_std > 0.0:
        if rng is None:
            rng = np.random.default_rng(42)
        noise = rng.normal(0, noise_std / np.sqrt(2), len(f_arr)) + \
                1j * rng.normal(0, noise_std / np.sqrt(2), len(f_arr))
        gamma_noisy = gamma + noise
        mag = np.abs(gamma_noisy)
        overshoot = mag > 1.0
        gamma_noisy[overshoot] = gamma_noisy[overshoot] / mag[overshoot]
        gamma = gamma_noisy
        # Recompute Zin from noisy Gamma for consistency
        zin = Z0 * (1.0 + gamma) / (1.0 - gamma)

    vswr_arr = meas.vswr(gamma)
    rl_arr = meas.return_loss_db(gamma)

    sweep_dict = {
        "f": f_arr,
        "zin": zin,
        "gamma": gamma,
        "vswr": vswr_arr,
        "rl_db": rl_arr,
    }

    return {
        "sweep": sweep_dict,
        "truth": truth,
    }
