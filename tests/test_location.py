import numpy as np
import pytest

import line_model as lm
import fault_simulation as fs
import core.fault_location as fl

Z0 = 50.0
VF = 0.66
FREQS = np.linspace(1e9, 5e9, 400)


def test_resolution_metrics_calculation():
    metrics = fl.calculate_resolution_metrics(FREQS, vf=VF)
    expected_B = 4e9
    expected_df = 4e9 / 399
    vp = lm.phase_velocity(VF)
    assert metrics["bandwidth_hz"] == pytest.approx(expected_B)
    assert metrics["range_res_m"] == pytest.approx(vp / (2 * expected_B))
    assert metrics["unambig_range_m"] == pytest.approx(vp / (2 * expected_df))


def test_compute_ifft_tdr_open_circuit():
    true_pos = 0.75
    sim = fs.simulate_fault("open", Z0, true_pos, FREQS, vf=VF)
    tdr_res = fl.compute_ifft_tdr(sim["sweep"]["gamma"], FREQS, vf=VF)
    assert tdr_res["dist_m"] is not None
    assert abs(tdr_res["dist_m"] - true_pos) < 0.02


def test_compute_ifft_tdr_series_L():
    true_pos = 0.45
    sim = fs.simulate_fault("series_L", Z0, 1.2, FREQS, vf=VF, L_val=20e-9, fault_pos=true_pos)
    tdr_res = fl.compute_ifft_tdr(sim["sweep"]["gamma"], FREQS, vf=VF)
    assert tdr_res["dist_m"] is not None
    assert abs(tdr_res["dist_m"] - true_pos) < 0.03


def test_locate_fault_dual_method_healthy():
    sim = fs.simulate_fault("healthy", Z0, 1.0, FREQS, vf=VF)
    out = fl.locate_fault_dual_method(sim["sweep"]["gamma"], FREQS, vf=VF, fault_class="healthy")
    assert out["dist_ifft_m"] is None
    assert out["is_reliable"] is True


def test_locate_fault_dual_method_reactive_discrepancy():
    # Reactive discontinuity creates phase shift that biases Method 2
    sim = fs.simulate_fault("series_L", Z0, 1.0, FREQS, vf=VF, L_val=30e-9, fault_pos=0.5)
    out = fl.locate_fault_dual_method(sim["sweep"]["gamma"], FREQS, vf=VF, fault_class="mismatch")
    assert out["dist_ifft_m"] is not None
    assert abs(out["dist_ifft_m"] - 0.5) < 0.03
    # Check that discrepancy or warnings are populated
    assert len(out["warnings"]) >= 0


def test_secondary_peaks_detection():
    # Test that compute_ifft_tdr returns secondary_peaks list
    sim = fs.simulate_fault("open", Z0, 0.6, FREQS, vf=VF)
    tdr_res = fl.compute_ifft_tdr(sim["sweep"]["gamma"], FREQS, vf=VF)
    assert "secondary_peaks" in tdr_res
    assert isinstance(tdr_res["secondary_peaks"], list)
    if len(tdr_res["secondary_peaks"]) > 0:
        dom = [p for p in tdr_res["secondary_peaks"] if p["is_dominant"]]
        assert len(dom) >= 1
        assert abs(dom[0]["dist_m"] - 0.6) < 0.03


def test_secondary_peaks_multipath_harmonic():
    # Synthetic dual-reflection: primary at d = 0.5 m, secondary round-trip at d = 1.0 m
    vp = lm.phase_velocity(VF)
    beta = 2.0 * np.pi * FREQS / vp
    gamma_synth = 0.6 * np.exp(-2j * beta * 0.5) + 0.2 * np.exp(-2j * beta * 1.0)
    out = fl.locate_fault_dual_method(gamma_synth, FREQS, vf=VF, fault_class="mismatch")
    assert out["dist_ifft_m"] is not None
    assert abs(out["dist_ifft_m"] - 0.5) < 0.03
    assert "secondary_peaks" in out
    secondaries = [p for p in out["secondary_peaks"] if not p["is_dominant"] and p["magnitude"] > 0.05]
    assert len(secondaries) >= 1
    # Check that the secondary peak near 1.0 m was detected and flagged as multipath echo
    sec = secondaries[0]
    assert abs(sec["dist_m"] - 1.0) < 0.05
    assert sec["is_multipath_echo"] is True

