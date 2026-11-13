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

Preserves:
  - SweepResult object containing actual velocity factor (vf), Z0, and length metadata.
  - Noiseless ideal response ('gamma_ideal') separated from noisy observed response ('gamma').
  - Unclipped noise modeling: samples with |S11| > 1.0 are preserved; VSWR returns NaN.
"""

import numpy as np
import line_model as lm
import measurements as meas
from measurements import SweepResult

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
    ABCD 2-port transmission matrix for a uniform lossless line section.

    Electromagnetic Theory:
      For a transmission line section of length l with propagation constant gamma = alpha + j*beta:
          [ V1 ] = [ cosh(gamma*l)       Z0*sinh(gamma*l) ] [ V2 ]
          [ I1 ]   [ Y0*sinh(gamma*l)    cosh(gamma*l)    ] [ I2 ]
      In the lossless limit (alpha = 0, gamma = j*beta):
          cosh(j*beta*l) = cos(beta*l)
          sinh(j*beta*l) = j * sin(beta*l)
      giving:
          A = cos(beta*l),       B = j * Z0 * sin(beta*l)
          C = j * sin(beta*l)/Z0, D = cos(beta*l)
      Reciprocity condition: A*D - B*C = cos^2(beta*l) + sin^2(beta*l) == 1.
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
    ABCD matrix for a series lumped impedance:
        [ [1, Z],
          [0, 1] ]
    where for series inductance Z = j * omega * L [ohm].
    """
    Z = np.asarray(Z, dtype=complex)
    ones = np.ones_like(Z, dtype=complex)
    zeros = np.zeros_like(Z, dtype=complex)
    return ones, Z, zeros, ones


def abcd_shunt_admittance(Y):
    """
    ABCD matrix for a shunt lumped admittance:
        [ [1, 0],
          [Y, 1] ]
    where for shunt capacitance Y = j * omega * C [S].
    """
    Y = np.asarray(Y, dtype=complex)
    ones = np.ones_like(Y, dtype=complex)
    zeros = np.zeros_like(Y, dtype=complex)
    return ones, zeros, Y, ones


def multiply_abcd(M1, M2):
    """
    Multiply two 2-port ABCD matrices:
        M_total = M1 @ M2
    where M = (A, B, C, D).
    """
    A1, B1, C1, D1 = M1
    A2, B2, C2, D2 = M2
    A = A1 * A2 + B1 * C2
    B = A1 * B2 + B1 * D2
    C = C1 * A2 + D1 * C2
    D = C1 * B2 + D1 * D2
    return A, B, C, D


def zin_from_abcd(ABCD, ZL):
    """
    Input impedance Zin from cascaded 2-port ABCD matrix and termination ZL:
        Zin = Vin / Iin = (A * ZL + B) / (C * ZL + D)

    Boundary Conditions:
      * Open circuit (ZL -> inf): Zin = A / C
      * Short circuit (ZL = 0):   Zin = B / D
    """
    A, B, C, D = ABCD
    ZL_val = complex(ZL)

    if np.isinf(abs(ZL_val)):
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

    Returns
    -------
    dict with:
        'sweep': SweepResult with keys ('f', 'zin', 'gamma', 'vswr', 'rl_db')
                 plus metadata attributes .vf, .Z0, .length, .gamma_ideal
        'truth': ground truth metadata dict
    """
    if scenario not in FAULT_SCENARIOS:
        raise ValueError(
            f"Unknown scenario '{scenario}'. Choose from {FAULT_SCENARIOS}"
        )

    Z0_val = float(np.real(Z0))
    if not np.isfinite(Z0_val) or Z0_val <= 0:
        raise ValueError(f"Line characteristic impedance Z0 must be finite and > 0 (got {Z0})")

    len_val = float(length)
    if not np.isfinite(len_val) or len_val <= 0:
        raise ValueError(f"Physical line length must be finite and > 0 (got {length})")

    f_arr = np.asarray(f_array, dtype=float)
    if f_arr.size < 2:
        raise ValueError("Frequency array must contain at least 2 points")
    if np.any(~np.isfinite(f_arr)) or np.any(f_arr <= 0):
        raise ValueError("Frequencies must be finite and strictly positive (> 0)")
    if len(f_arr) > 1 and np.any(np.diff(f_arr) <= 0):
        raise ValueError("Frequency array must be strictly monotonically increasing")

    lm._check_vf(vf)

    if not np.isfinite(L_val) or L_val < 0:
        raise ValueError(f"Discontinuity inductance L_val must be non-negative (>= 0), got {L_val}")
    if not np.isfinite(C_val) or C_val < 0:
        raise ValueError(f"Discontinuity capacitance C_val must be non-negative (>= 0), got {C_val}")
    if not np.isfinite(ZL_mismatch) or ZL_mismatch <= 0:
        raise ValueError(f"Mismatch resistance ZL_mismatch must be strictly positive (> 0), got {ZL_mismatch}")
    if not np.isfinite(noise_std) or noise_std < 0:
        raise ValueError(f"Measurement noise noise_std must be non-negative (>= 0), got {noise_std}")

    if fault_pos is None:
        fault_pos = len_val / 2.0
    else:
        fp_val = float(fault_pos)
        if not np.isfinite(fp_val) or fp_val < 0 or fp_val > len_val:
            raise ValueError(f"Discontinuity position fault_pos must be within [0, {len_val}] (got {fault_pos})")
        fault_pos = fp_val

    beta = lm.phase_constant(f_arr, vf=vf)
    omega = 2.0 * np.pi * f_arr

    truth = {
        "scenario": scenario,
        "Z0": float(Z0_val),
        "length": float(len_val),
        "fault_pos": fault_pos,
        "L_val": float(L_val),
        "C_val": float(C_val),
        "vf": float(vf),
        "noise_std": float(noise_std),
    }

    if scenario == "healthy":
        ZL = complex(Z0)
        truth["ZL"] = ZL
        truth["fault_pos"] = None
        zin_ideal = lm.input_impedance_at_freq(Z0, ZL, f_arr, length, vf=vf)

    elif scenario == "mismatch":
        ZL = complex(ZL_mismatch)
        truth["ZL"] = ZL
        truth["fault_pos"] = float(length)
        zin_ideal = lm.input_impedance_at_freq(Z0, ZL, f_arr, length, vf=vf)

    elif scenario == "open":
        ZL = lm.OPEN
        truth["ZL"] = ZL
        truth["fault_pos"] = float(length)
        zin_ideal = lm.input_impedance_at_freq(Z0, ZL, f_arr, length, vf=vf)

    elif scenario == "short":
        ZL = 0.0 + 0j
        truth["ZL"] = ZL
        truth["fault_pos"] = float(length)
        zin_ideal = lm.input_impedance_at_freq(Z0, ZL, f_arr, length, vf=vf)

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
        zin_ideal = zin_from_abcd(M_total, ZL)

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
        zin_ideal = zin_from_abcd(M_total, ZL)

    gamma_ideal = meas.reflection_coefficient(zin_ideal, Z0)

    # Realistic measurement noise modeling (UNCLIPPED)
    num_non_passive = 0
    if noise_std > 0.0:
        if rng is None:
            rng = np.random.default_rng(42)
        sigma_1d = noise_std / np.sqrt(2.0)
        noise = rng.normal(0, sigma_1d, len(f_arr)) + 1j * rng.normal(0, sigma_1d, len(f_arr))
        # Additive noise without silent clipping
        gamma_observed = gamma_ideal + noise
        non_passive_mask = np.abs(gamma_observed) > 1.0
        num_non_passive = int(np.sum(non_passive_mask))
    else:
        gamma_observed = gamma_ideal.copy()

    truth["num_non_passive_samples"] = num_non_passive

    # Compute observed measurement metrics
    vswr_arr = meas.vswr(gamma_observed)
    rl_arr = meas.return_loss_db(gamma_observed)

    # Zin calculated from observed S11
    # Guard against singular points (1 - Gamma == 0)
    denom = 1.0 - gamma_observed
    singular = np.abs(denom) < 1e-15
    zin_observed = np.empty_like(gamma_observed, dtype=complex)
    zin_observed[singular] = np.inf
    ok = ~singular
    zin_observed[ok] = Z0 * (1.0 + gamma_observed[ok]) / denom[ok]

    sweep_res = SweepResult(
        {
            "f": f_arr,
            "zin": zin_observed,
            "gamma": gamma_observed,
            "vswr": vswr_arr,
            "rl_db": rl_arr,
        },
        vf=vf,
        Z0=Z0,
        length=length,
    )
    # Store ideal noiseless reflection for verification
    truth["gamma_ideal"] = gamma_ideal
    sweep_res.gamma_ideal = gamma_ideal
    sweep_res.s11 = gamma_observed

    return {
        "sweep": sweep_res,
        "truth": truth,
    }
