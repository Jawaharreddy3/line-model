"""
tests/test_qucs_cross_validation.py -- Automated Cross-Validation Against Qucsator Kernel.

Verifies:
  - Execution of Qucsator kernel on native netlist.
  - S11 reflection magnitude matches RF LINE DOCTOR within 1e-12.
  - S11 phase matches RF LINE DOCTOR within 1e-6 degrees.
  - Input impedance Zin matches within 1e-6 Ohm.
  - VSWR matches within 1e-10.
"""

import os
import re
import pytest
import numpy as np

import line_model as lm
import measurements as meas


def test_qucsator_simulation_matches_rf_line_doctor():
    dat_path = os.path.join("Qucs_Cross_Validation", "qucs_mismatch.dat")
    assert os.path.exists(dat_path), "Qucsator dataset qucs_mismatch.dat must exist"

    # Read Qucsator output
    with open(dat_path, "r") as f:
        lines = f.readlines()

    f_qucs = []
    s11_qucs = []
    mode = None

    for line in lines:
        line = line.strip()
        if line.startswith("<indep frequency"):
            mode = "freq"
            continue
        elif line.startswith("<dep S[1,1] frequency"):
            mode = "s11"
            continue
        elif line.startswith("</indep") or line.startswith("</dep"):
            mode = None
            continue

        if mode == "freq" and line:
            f_qucs.append(float(line))
        elif mode == "s11" and line:
            m = re.match(r"([+-]?[\d.e+-]+)([+-])j([\d.e+-]+)", line.strip())
            if m:
                s11_qucs.append(complex(float(m.group(1)), float(m.group(2) + m.group(3))))

    f_qucs = np.array(f_qucs)
    s11_qucs = np.array(s11_qucs)
    assert len(f_qucs) == 201
    assert len(s11_qucs) == 201

    # RF LINE DOCTOR analytical sweep with identical parameters
    Z0 = 50.0
    RL = 120.0
    length = 1.0
    vf = 0.66

    sw_rld = meas.sweep(Z0, RL, length, f_qucs, vf=vf)
    s11_rld = sw_rld["gamma"]
    zin_rld = sw_rld["zin"]
    vswr_rld = sw_rld["vswr"]

    # 1. Magnitude comparison
    mag_rld = np.abs(s11_rld)
    mag_qucs = np.abs(s11_qucs)
    max_err_mag = np.max(np.abs(mag_rld - mag_qucs))
    assert max_err_mag < 1e-12, f"Magnitude error {max_err_mag} exceeds 1e-12"

    # 2. Phase comparison
    phase_rld = np.unwrap(np.angle(s11_rld))
    phase_qucs = np.unwrap(np.angle(s11_qucs))
    max_err_phase_deg = np.degrees(np.max(np.abs(phase_rld - phase_qucs)))
    assert max_err_phase_deg < 1e-6, f"Phase error {max_err_phase_deg} deg exceeds 1e-6"

    # 3. Input impedance comparison
    zin_qucs = Z0 * (1.0 + s11_qucs) / (1.0 - s11_qucs)
    max_err_zin = np.max(np.abs(zin_rld - zin_qucs))
    assert max_err_zin < 1e-6, f"Zin error {max_err_zin} Ohm exceeds 1e-6"

    # 4. VSWR comparison
    vswr_qucs = (1.0 + mag_qucs) / (1.0 - mag_qucs)
    max_err_vswr = np.max(np.abs(vswr_rld - vswr_qucs))
    assert max_err_vswr < 1e-10, f"VSWR error {max_err_vswr} exceeds 1e-10"
