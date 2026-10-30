import numpy as np
import pytest

import line_model as lm
import measurements as meas
import fault_simulation as fs
import diagnosis as diag

Z0 = 50.0
VF = 0.66
FREQS = np.linspace(500e6, 4e9, 400)


def test_classify_healthy_matched():
    sim = fs.simulate_fault("healthy", Z0, 1.0, FREQS, vf=VF)
    res = diag.classify(sim["sweep"], Z0)
    assert res == "healthy"
    assert res in diag.CLASSIFICATION_LABELS
    assert res.subtype == "matched"
    assert res.confidence == "high"


def test_classify_resistive_mismatch():
    sim = fs.simulate_fault("mismatch", Z0, 1.0, FREQS, vf=VF, ZL_mismatch=120.0)
    res = diag.classify(sim["sweep"], Z0)
    assert res == "mismatch"
    assert res in diag.CLASSIFICATION_LABELS
    assert res.subtype == "resistive_mismatch"


def test_classify_open_circuit():
    sim = fs.simulate_fault("open", Z0, 1.0, FREQS, vf=VF)
    res = diag.classify(sim["sweep"], Z0)
    assert res == "open"
    assert res in diag.CLASSIFICATION_LABELS
    assert res.subtype == "open_circuit"


def test_classify_short_circuit():
    sim = fs.simulate_fault("short", Z0, 1.0, FREQS, vf=VF)
    res = diag.classify(sim["sweep"], Z0)
    assert res == "short"
    assert res in diag.CLASSIFICATION_LABELS
    assert res.subtype == "short_circuit"


def test_classify_series_inductive_discontinuity():
    sim = fs.simulate_fault(
        "series_L", Z0, 1.0, FREQS, vf=VF, L_val=15e-9, fault_pos=0.4
    )
    res = diag.classify(sim["sweep"], Z0)
    assert res == "mismatch"
    assert res in diag.CLASSIFICATION_LABELS
    assert res.subtype == "series_L"


def test_classify_shunt_capacitive_discontinuity():
    sim = fs.simulate_fault(
        "shunt_C", Z0, 1.0, FREQS, vf=VF, C_val=15e-12, fault_pos=0.6
    )
    res = diag.classify(sim["sweep"], Z0)
    assert res == "mismatch"
    assert res in diag.CLASSIFICATION_LABELS
    assert res.subtype == "shunt_C"


def test_estimate_distance_healthy_returns_none():
    sim = fs.simulate_fault("healthy", Z0, 1.0, FREQS, vf=VF)
    d = diag.estimate_distance(sim["sweep"], VF, "healthy")
    assert d is None


def test_estimate_distance_against_known_fault_positions():
    # Sweep from 1 GHz to 5 GHz (B = 4 GHz)
    # Range resolution delta_R = vp / (2 * B) = (0.66 * 3e8) / (2 * 4e9) = 0.02475 m (~2.5 cm)
    freqs = np.linspace(1e9, 5e9, 500)
    res_info = diag.distance_resolution({"f": freqs}, vf=VF)
    delta_r = res_info["range_res"]
    assert delta_r < 0.03  # better than 3 cm resolution

    test_lengths = [0.3, 0.7, 1.2]
    for true_pos in test_lengths:
        sim = fs.simulate_fault("open", Z0, true_pos, freqs, vf=VF)
        d_est = diag.estimate_distance(sim["sweep"], VF, "open")
        assert d_est is not None
        abs_error = abs(d_est - true_pos)
        # Error must be within range resolution
        assert abs_error <= 1.5 * delta_r, (
            f"True {true_pos} m vs Est {d_est} m: error {abs_error:.4f} m > 1.5*delta_r ({delta_r:.4f} m)"
        )


def test_estimate_distance_series_L_intermediate():
    freqs = np.linspace(1e9, 5e9, 500)
    res_info = diag.distance_resolution({"f": freqs}, vf=VF)
    delta_r = res_info["range_res"]

    true_fault_pos = 0.45
    sim = fs.simulate_fault(
        "series_L", Z0, 1.0, freqs, vf=VF, L_val=20e-9, fault_pos=true_fault_pos
    )
    d_est = diag.estimate_distance(sim["sweep"], VF, "mismatch")
    assert d_est is not None
    assert abs(d_est - true_fault_pos) <= 2.0 * delta_r


def test_non_uniform_frequency_resampling():
    # Construct non-uniform frequency grid
    f_uniform = np.linspace(1e9, 5e9, 400)
    jitter = np.sin(np.linspace(0, 10, 400)) * 5e6
    f_non_uniform = f_uniform + jitter
    f_non_uniform = np.sort(f_non_uniform)

    sim = fs.simulate_fault("short", Z0, 0.8, f_non_uniform, vf=VF)
    d_est = diag.estimate_distance(sim["sweep"], VF, "short")
    assert d_est is not None
    # Still resolves close to 0.8 m
    assert abs(d_est - 0.8) < 0.08
