"""
tests/test_classification_labels.py -- Verification of All 5 Classification Labels.

Strictly verifies that `diagnosis.classify(sweep_dict, Z0)` satisfies the frozen
public contract by returning one of the five canonical classification labels:
  - "healthy"
  - "open"
  - "short"
  - "mismatch"
  - "unknown"
"""

import pytest
import numpy as np
import line_model as lm
import measurements as meas
import fault_simulation as fs
import diagnosis as diag


def test_label_healthy():
    """Verify 'healthy' classification label and subtype."""
    f = np.linspace(500e6, 3000e6, 200)
    sw = meas.sweep(50.0, 50.0, 1.0, f, vf=0.66)
    res = diag.classify(sw, 50.0)

    assert res == "healthy"
    assert isinstance(res, str)
    assert isinstance(res, diag.DiagnosisResult)
    assert res.subtype == "matched"
    assert res.confidence == "high"
    assert "Near-zero reflection" in res.explanation
    assert "R1_HEALTHY_MATCHED" in res.rules_fired


def test_label_open():
    """Verify 'open' classification label and subtype."""
    f = np.linspace(400e6, 3500e6, 250)
    sw = meas.sweep(50.0, lm.OPEN, 0.9, f, vf=0.66)
    res = diag.classify(sw, 50.0)

    assert res == "open"
    assert isinstance(res, str)
    assert isinstance(res, diag.DiagnosisResult)
    assert res.subtype == "open_circuit"
    assert "Open Circuit" in res.explanation
    assert "R4_OPEN_CIRCUIT" in res.rules_fired


def test_label_short():
    """Verify 'short' classification label and subtype."""
    f = np.linspace(400e6, 3500e6, 250)
    sw = meas.sweep(50.0, 0.0 + 0j, 0.9, f, vf=0.66)
    res = diag.classify(sw, 50.0)

    assert res == "short"
    assert isinstance(res, str)
    assert isinstance(res, diag.DiagnosisResult)
    assert res.subtype == "short_circuit"
    assert "Short Circuit" in res.explanation
    assert "R5_SHORT_CIRCUIT" in res.rules_fired


def test_label_mismatch_resistive():
    """Verify 'mismatch' label for resistive terminations."""
    f = np.linspace(500e6, 2500e6, 200)
    sw = meas.sweep(50.0, 150.0, 1.2, f, vf=0.66)
    res = diag.classify(sw, 50.0)

    assert res == "mismatch"
    assert isinstance(res, str)
    assert isinstance(res, diag.DiagnosisResult)
    assert res.subtype == "resistive_mismatch"
    assert "R6_RESISTIVE_MISMATCH" in res.rules_fired


def test_label_mismatch_series_L():
    """Verify 'mismatch' label for series inductive discontinuity."""
    f = np.linspace(500e6, 3000e6, 250)
    sim = fs.simulate_fault("series_L", 50.0, 1.0, f, vf=0.66, L_val=15e-9, fault_pos=0.4)
    res = diag.classify(sim["sweep"], 50.0)

    assert res == "mismatch"
    assert res.subtype == "series_L"
    assert "Series Inductance Discontinuity" in res.explanation


def test_label_mismatch_shunt_C():
    """Verify 'mismatch' label for shunt capacitive discontinuity."""
    f = np.linspace(500e6, 3000e6, 250)
    sim = fs.simulate_fault("shunt_C", 50.0, 1.0, f, vf=0.66, C_val=15e-12, fault_pos=0.6)
    res = diag.classify(sim["sweep"], 50.0)

    assert res == "mismatch"
    assert res.subtype == "shunt_C"
    assert "Shunt Capacitance Discontinuity" in res.explanation


def test_label_unknown_empty_sweep():
    """Verify 'unknown' label when sweep data is empty."""
    empty_sw = {"f": np.array([]), "gamma": np.array([])}
    res = diag.classify(empty_sw, 50.0)

    assert res == "unknown"
    assert isinstance(res, str)
    assert isinstance(res, diag.DiagnosisResult)
    assert res.subtype == "uncertain"
    assert "Empty" in res.explanation


def test_label_unknown_nan_data():
    """Verify 'unknown' label when sweep data contains NaNs."""
    nan_sw = {
        "f": np.linspace(500e6, 1000e6, 10),
        "gamma": np.array([0.1, np.nan, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]),
    }
    res = diag.classify(nan_sw, 50.0)

    assert res == "unknown"
    assert res.subtype == "uncertain"
    assert "non-finite" in res.explanation


def test_label_mismatch_extreme_finite_loads():
    """Verify extreme finite mismatches (500 ohm and 5 ohm) yield 'mismatch' label."""
    f = np.linspace(500e6, 2500e6, 200)
    for zl in [500.0, 5.0, 1000.0, 2.5]:
        sw = meas.sweep(50.0, zl, 1.2, f, vf=0.66)
        res = diag.classify(sw, 50.0)
        assert res == "mismatch", f"ZL={zl} returned {res}"
        assert res.subtype == "resistive_mismatch"


def test_label_unknown_abstention_conditions():
    """Verify 'unknown' label across all abstention challenge types."""
    # 1. Insufficient points
    res_pts = diag.classify({"f": np.array([1e9, 2e9]), "gamma": np.array([0.5, 0.5])}, 50.0)
    assert res_pts == "unknown"
    assert "R_INSUFFICIENT_POINTS" in res_pts.rules_fired

    # 2. Insufficient bandwidth (< 5 MHz)
    f_narrow = np.linspace(100e6, 101e6, 10)
    res_bw = diag.classify({"f": f_narrow, "gamma": np.full(10, 0.5)}, 50.0)
    assert res_bw == "unknown"
    assert "R_INSUFFICIENT_BANDWIDTH" in res_bw.rules_fired

    # 3. Ambiguous total reflection
    f_band = np.linspace(500e6, 2000e6, 100)
    res_amb = diag.classify({"f": f_band, "gamma": np.full(100, 1j)}, 50.0)
    assert res_amb == "unknown"
    assert "R4_AMBIGUOUS_TOTAL_REFL" in res_amb.rules_fired


def test_all_five_labels_exhaustively_covered():
    """Ensure all 5 labels from CLASSIFICATION_LABELS are verified."""
    assert set(diag.CLASSIFICATION_LABELS) == {"healthy", "open", "short", "mismatch", "unknown"}
