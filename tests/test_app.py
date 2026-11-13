import os
import sys
import numpy as np
import pytest

import line_model as lm
import measurements as meas
import fault_simulation as fs
import diagnosis as diag
import matching as match


def test_app_core_integration_pipeline():
    """
    Test the entire computation pipeline that app.py executes.
    Verifies that all modules integrate seamlessly without UI dependency.
    """
    Z0 = 50.0
    length = 1.2
    vf = 0.66
    freqs = np.linspace(500e6, 3000e6, 200)

    # 1. Simulate fault
    sim = fs.simulate_fault("mismatch", Z0, length, freqs, vf=vf, ZL_mismatch=100.0)
    sweep_dict = sim["sweep"]

    # 2. Check measurement keys
    for k in ["f", "zin", "gamma", "vswr", "rl_db"]:
        assert k in sweep_dict

    # 3. Classify
    res = diag.classify(sweep_dict, Z0)
    assert res == "mismatch"
    assert res.subtype == "resistive_mismatch"
    assert res.confidence in ["high", "medium", "low"]

    # 4. Estimate distance
    d_est = diag.estimate_distance(sweep_dict, vf, res)
    assert d_est is not None
    assert abs(d_est - length) < 0.15

    # 5. Range resolution
    res_info = diag.distance_resolution(sweep_dict, vf=vf)
    assert res_info["range_res"] > 0
    assert res_info["unambig_range"] > 0

    # 6. Matching Studio
    matched = match.compare_matching(Z0, 100.0, freqs, vf=vf)
    assert matched["Zt"] == pytest.approx(np.sqrt(50 * 100))
    assert matched["at_f_design"]["vswr"] == pytest.approx(1.0, abs=1e-12)


def test_app_imports_cleanly():
    import app
    assert app is not None
