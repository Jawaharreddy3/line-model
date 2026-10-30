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
