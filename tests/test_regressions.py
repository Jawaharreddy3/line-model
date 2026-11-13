"""
tests/test_regressions.py -- Comprehensive Regression and Contract Preservation Suite.

Guarantees:
  - Backward compatibility of all frozen public signatures and return types.
  - Verification that new validations do not break valid legacy usage patterns.
  - End-to-end integration and textbook hand-calculation consistency.
"""

import pytest
import numpy as np
import line_model as lm
import measurements as meas
import fault_simulation as fs
import diagnosis as diag
import matching as match
import core.fault_location as fl
import core.signal_analysis as sa


def test_regression_public_module_exports():
    """Verify all public __all__ exports remain available and callable."""
    assert hasattr(lm, "phase_velocity")
    assert hasattr(lm, "wavelength")
    assert hasattr(lm, "phase_constant")
    assert hasattr(lm, "electrical_length_deg")
    assert hasattr(lm, "load_reflection")
    assert hasattr(lm, "reflection_at_distance")
    assert hasattr(lm, "input_impedance")
    assert hasattr(lm, "input_impedance_at_freq")
    assert hasattr(lm, "quarter_wave_zin")
    assert hasattr(lm, "quarter_wave_impedance")
    assert hasattr(lm, "series_impedance")
    assert hasattr(lm, "shunt_admittance")
    assert hasattr(lm, "propagation_constant")
    assert hasattr(lm, "characteristic_impedance_rlgc")
    assert hasattr(lm, "phase_velocity_rlgc")
    assert hasattr(lm, "input_impedance_lossy")

    assert hasattr(meas, "SweepResult")
    assert hasattr(meas, "reflection_coefficient")
    assert hasattr(meas, "vswr")
    assert hasattr(meas, "return_loss_db")
    assert hasattr(meas, "sweep")
    assert hasattr(meas, "smith_plot")

    assert hasattr(fs, "simulate_fault")
    assert hasattr(fs, "FAULT_SCENARIOS")

    assert hasattr(diag, "classify")
    assert hasattr(diag, "estimate_distance")
    assert hasattr(diag, "distance_resolution")
    assert hasattr(diag, "extract_features")
    assert hasattr(diag, "DiagnosisResult")
    assert hasattr(diag, "CLASSIFICATION_LABELS")

    assert hasattr(match, "design_quarter_wave")
    assert hasattr(match, "compare_matching")


def test_regression_sweep_result_dictionary_subclass():
    """Verify SweepResult retains dict behavior, key access, and metadata attributes."""
    f = np.linspace(500e6, 1500e6, 21)
    res = meas.sweep(50.0, 75.0, 1.0, f, vf=0.66)

    assert isinstance(res, dict)
    assert isinstance(res, meas.SweepResult)
    assert res.vf == pytest.approx(0.66)
    assert res.Z0 == pytest.approx(50.0)
    assert res.length == pytest.approx(1.0)

    # Standard dict unpacking
    assert set(res.keys()) == {"f", "zin", "gamma", "vswr", "rl_db"}
    f_arr, zin_arr = res["f"], res["zin"]
    assert len(f_arr) == 21
    assert len(zin_arr) == 21


def test_regression_diagnosis_result_string_subclass():
    """Verify DiagnosisResult inherits from str and maintains equality comparisons."""
    f = np.linspace(500e6, 1500e6, 50)
    res_str = diag.classify({"f": f, "gamma": np.zeros(50)}, 50.0)

    # String equality contract
    assert res_str == "healthy"
    assert "healthy" in res_str
    assert isinstance(res_str, str)
    assert isinstance(res_str, diag.DiagnosisResult)

    # Attribute access
    assert res_str.label == "healthy"
    assert res_str.subtype == "matched"
    assert res_str.confidence == "high"
    assert isinstance(res_str.features, dict)
    assert isinstance(res_str.rules_fired, list)


def test_regression_quarter_wave_transformer_exact_cancellation():
    """Verify that Pozar quarter-wave transformer cancels reflection at f_design."""
    Z0 = 50.0
    RL = 100.0
    f_arr = np.linspace(800e6, 1200e6, 41)
    f0 = 1000e6

    res = match.compare_matching(Z0, RL, f_arr, vf=1.0, f_design=f0)

    # Required contract keys
    assert "before" in res
    assert "after" in res
    assert "Zt" in res
    assert "length_m" in res
    assert "f_design" in res
    assert "bandwidth_hz" in res
    assert "at_f_design" in res

    # Verification of exact matching at design frequency
    at_f0 = res["at_f_design"]
    assert at_f0["gamma"] == pytest.approx(0.0, abs=1e-12)
    assert at_f0["vswr"] == pytest.approx(1.0, abs=1e-12)
    assert np.isinf(at_f0["rl_db"])
