"""
matching.py -- Quarter-wave impedance matching module (Member 3).

Reference: Pozar, "Microwave Engineering", 4th ed., Section 5.1.

Conventions & Terminology:
  * RL: Load resistance [ohm] (purely real, positive).
  * RL_dB: Return loss [dB] (must never be confused with load resistance RL).
  * Evaluates matching exactly at design frequency f0 (Gamma = 0, VSWR = 1).
  * Usable bandwidth defined where Return Loss >= rl_threshold (default 20 dB).
"""

import numpy as np
import line_model as lm
import measurements as meas

__all__ = [
    "design_quarter_wave",
    "compare_matching",
]


def design_quarter_wave(Z0, RL, f, vf=1.0):
    """
    Design a quarter-wave transformer matching real load resistance RL to line Z0.

    Parameters
    ----------
    Z0 : characteristic impedance of line [ohm], real > 0
    RL : load resistance [ohm], real > 0 (not return loss!)
    f  : design frequency [Hz], > 0
    vf : velocity factor (0 < vf <= 1.0)

    Returns
    -------
    dict with exact contract keys:
        'Zt'       : characteristic impedance of transformer section [ohm]
        'length_m' : physical length of transformer section [m]
    """
    Z0_val = float(np.real(Z0))
    RL_val = float(np.real(RL))
    f_val = float(f)
    vf_val = float(vf)

    if np.imag(Z0) != 0 or np.imag(RL) != 0:
        raise ValueError(
            "Quarter-wave transformer requires purely real impedances: "
            f"Z0={Z0}, RL={RL}"
        )
    if Z0_val <= 0:
        raise ValueError(f"Line impedance Z0 must be > 0 (got {Z0_val})")
    if RL_val <= 0:
        raise ValueError(f"Load resistance RL must be > 0 (got {RL_val})")
    if f_val <= 0:
        raise ValueError(f"Design frequency must be > 0 (got {f_val})")

    Zt = float(np.sqrt(Z0_val * RL_val))
    vp = lm.phase_velocity(vf_val)
    length_m = float(vp / (4.0 * f_val))

    return {
        "Zt": Zt,
        "length_m": length_m,
    }


def compare_matching(
    Z0,
    ZL,
    f_array,
    vf=1.0,
    f_design=None,
    rl_threshold=20.0,
):
    """
    Compare line performance before and after inserting a quarter-wave transformer.

    Parameters
    ----------
    Z0           : characteristic impedance of source/feed line [ohm]
    ZL           : load impedance [ohm] (must be real resistance RL for quarter-wave)
    f_array      : frequency array [Hz]
    vf           : velocity factor of transformer section
    f_design     : design center frequency [Hz] (defaults to mid-band if None)
    rl_threshold : return loss threshold [dB] defining usable bandwidth (default: 20 dB)

    Returns
    -------
    dict containing:
        'before'       : sweep dict (f, zin, gamma, vswr, rl_db) without transformer
        'after'        : sweep dict (f, zin, gamma, vswr, rl_db) with transformer
        'Zt'           : transformer characteristic impedance [ohm]
        'length_m'     : transformer physical length [m]
        'f_design'     : design frequency [Hz]
        'bandwidth_hz' : frequency span [Hz] where return loss >= rl_threshold
        'rl_threshold' : threshold in dB used for bandwidth
        'at_f_design'  : dict of exact metrics evaluated at f_design
    """
    ZL_c = complex(ZL)
    if abs(ZL_c.imag) > 1e-6 * max(abs(ZL_c.real), 1e-9):
        raise ValueError(
            f"Quarter-wave matching requires real load resistance RL. "
            f"Received complex load ZL = {ZL_c}."
        )
    RL = ZL_c.real

    f_arr = np.asarray(f_array, dtype=float)
    if f_design is None:
        f_design = float(np.mean(f_arr))

    # Design quarter-wave transformer at exact f_design
    design = design_quarter_wave(Z0, RL, f_design, vf=vf)
    Zt = design["Zt"]
    lt = design["length_m"]

    # BEFORE: Direct connection of ZL to Z0 line
    # Zin at load plane is simply ZL across all frequencies
    zin_before = np.full_like(f_arr, ZL_c, dtype=complex)
    gamma_before = meas.reflection_coefficient(zin_before, Z0)
    vswr_before = meas.vswr(gamma_before)
    rl_before = meas.return_loss_db(gamma_before)

    before_dict = {
        "f": f_arr,
        "zin": zin_before,
        "gamma": gamma_before,
        "vswr": vswr_before,
        "rl_db": rl_before,
    }

    # AFTER: Quarter-wave transformer inserted between Z0 line and ZL
    # Looking into transformer input:
    zin_after = lm.input_impedance_at_freq(Zt, ZL_c, f_arr, lt, vf=vf)
    gamma_after = meas.reflection_coefficient(zin_after, Z0)
    vswr_after = meas.vswr(gamma_after)
    rl_after = meas.return_loss_db(gamma_after)

    after_dict = {
        "f": f_arr,
        "zin": zin_after,
        "gamma": gamma_after,
        "vswr": vswr_after,
        "rl_db": rl_after,
    }

    # Evaluate exact performance at f_design
    zin_f0 = lm.input_impedance_at_freq(Zt, ZL_c, f_design, lt, vf=vf)
    gamma_f0 = meas.reflection_coefficient(zin_f0, Z0)
    vswr_f0 = meas.vswr(gamma_f0)
    rl_f0 = meas.return_loss_db(gamma_f0)

    # Compute usable bandwidth (contiguous band around f_design where RL >= threshold)
    bw_mask = rl_after >= float(rl_threshold)
    if np.any(bw_mask):
        bw_freqs = f_arr[bw_mask]
        bandwidth_hz = float(bw_freqs[-1] - bw_freqs[0])
    else:
        bandwidth_hz = 0.0

    return {
        "before": before_dict,
        "after": after_dict,
        "Zt": Zt,
        "length_m": lt,
        "f_design": f_design,
        "bandwidth_hz": bandwidth_hz,
        "rl_threshold": float(rl_threshold),
        "at_f_design": {
            "zin": zin_f0,
            "gamma": gamma_f0,
            "vswr": vswr_f0,
            "rl_db": rl_f0,
        },
    }
