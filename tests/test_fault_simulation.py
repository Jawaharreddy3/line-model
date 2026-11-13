import numpy as np
import pytest

import line_model as lm
import measurements as meas
import fault_simulation as fs

Z0 = 50.0
FREQ = np.linspace(100e6, 2e9, 50)
LENGTH = 1.0
VF = 0.66


def test_scenario_names():
    assert len(fs.FAULT_SCENARIOS) == 6
    assert set(fs.FAULT_SCENARIOS) == {
        "healthy",
        "mismatch",
        "open",
        "short",
        "series_L",
        "shunt_C",
    }


def test_healthy_scenario():
    sim = fs.simulate_fault("healthy", Z0, LENGTH, FREQ, vf=VF)
    sw = sim["sweep"]
    assert np.allclose(sw["gamma"], 0.0, atol=1e-12)
    assert np.allclose(sw["vswr"], 1.0, atol=1e-12)
    assert np.all(np.isinf(sw["rl_db"]))
    assert sim["truth"]["fault_pos"] is None


def test_mismatch_scenario():
    sim = fs.simulate_fault(
        "mismatch", Z0, LENGTH, FREQ, vf=VF, ZL_mismatch=100.0
    )
    sw = sim["sweep"]
    expected_gamma_mag = (100.0 - 50.0) / (100.0 + 50.0)  # 1/3
    assert np.allclose(np.abs(sw["gamma"]), expected_gamma_mag, rtol=1e-9)
    assert np.allclose(sw["vswr"], 2.0, rtol=1e-9)


def test_open_scenario():
    sim = fs.simulate_fault("open", Z0, LENGTH, FREQ, vf=VF)
    sw = sim["sweep"]
    assert np.allclose(np.abs(sw["gamma"]), 1.0, atol=1e-12)
    assert np.all(np.isinf(sw["vswr"]))
    assert np.allclose(sw["rl_db"], 0.0, atol=1e-12)


def test_short_scenario():
    sim = fs.simulate_fault("short", Z0, LENGTH, FREQ, vf=VF)
    sw = sim["sweep"]
    assert np.allclose(np.abs(sw["gamma"]), 1.0, atol=1e-12)
    assert np.all(np.isinf(sw["vswr"]))
    assert np.allclose(sw["rl_db"], 0.0, atol=1e-12)


def test_series_L_zero_limit_is_healthy():
    # When L -> 0, series discontinuity vanishes -> matched line
    sim = fs.simulate_fault(
        "series_L", Z0, LENGTH, FREQ, vf=VF, L_val=0.0, fault_pos=0.4
    )
    sw = sim["sweep"]
    assert np.allclose(sw["gamma"], 0.0, atol=1e-10)
    assert np.allclose(sw["vswr"], 1.0, atol=1e-10)


def test_shunt_C_zero_limit_is_healthy():
    # When C -> 0, shunt admittance vanishes -> matched line
    sim = fs.simulate_fault(
        "shunt_C", Z0, LENGTH, FREQ, vf=VF, C_val=0.0, fault_pos=0.4
    )
    sw = sim["sweep"]
    assert np.allclose(sw["gamma"], 0.0, atol=1e-10)
    assert np.allclose(sw["vswr"], 1.0, atol=1e-10)


def test_reactive_discontinuity_trend():
    # For reactive discontinuities, |Gamma| rises with frequency
    sim_L = fs.simulate_fault(
        "series_L", Z0, LENGTH, FREQ, vf=VF, L_val=15e-9, fault_pos=0.5
    )
    mag_L = np.abs(sim_L["sweep"]["gamma"])
    assert mag_L[-1] > mag_L[0]  # rises with frequency

    sim_C = fs.simulate_fault(
        "shunt_C", Z0, LENGTH, FREQ, vf=VF, C_val=15e-12, fault_pos=0.5
    )
    mag_C = np.abs(sim_C["sweep"]["gamma"])
    assert mag_C[-1] > mag_C[0]  # rises with frequency


def test_noisy_simulation_unclipped_and_reproducible():
    # Fixed random seeds ensure reproducible noise
    rng1 = np.random.default_rng(12345)
    rng2 = np.random.default_rng(12345)

    sim1 = fs.simulate_fault("open", Z0, LENGTH, FREQ, vf=VF, noise_std=0.10, rng=rng1)
    sim2 = fs.simulate_fault("open", Z0, LENGTH, FREQ, vf=VF, noise_std=0.10, rng=rng2)

    # 1. Reproducibility
    assert np.allclose(sim1["sweep"]["gamma"], sim2["sweep"]["gamma"])

    # 2. Ideal response remains perfectly unity and passive
    assert "gamma_ideal" in sim1["truth"]
    assert np.allclose(np.abs(sim1["truth"]["gamma_ideal"]), 1.0)

    # 3. Noisy response can exceed unity (|S11| > 1) without silent clipping
    noisy_mag = np.abs(sim1["sweep"]["gamma"])
    assert np.any(noisy_mag > 1.0)

    # 4. For samples where |S11| > 1, VSWR is np.nan (handled gracefully without crashing)
    over_unity_mask = noisy_mag > 1.0
    vswr_vals = sim1["sweep"]["vswr"]
    assert np.all(np.isnan(vswr_vals[over_unity_mask]))

    # 5. Metadata preserved in SweepResult
    assert sim1["sweep"].vf == pytest.approx(VF)
    assert sim1["sweep"].Z0 == 50.0


def test_invalid_scenario_raises():
    with pytest.raises(ValueError):
        fs.simulate_fault("invalid_scenario", Z0, LENGTH, FREQ)


def test_simulate_fault_input_validations():
    # Invalid Z0
    with pytest.raises(ValueError, match="characteristic impedance Z0"):
        fs.simulate_fault("healthy", -50.0, LENGTH, FREQ)
    with pytest.raises(ValueError, match="characteristic impedance Z0"):
        fs.simulate_fault("healthy", 0.0, LENGTH, FREQ)

    # Invalid length
    with pytest.raises(ValueError, match="Physical line length"):
        fs.simulate_fault("healthy", Z0, -1.0, FREQ)
    with pytest.raises(ValueError, match="Physical line length"):
        fs.simulate_fault("healthy", Z0, 0.0, FREQ)

    # Invalid frequencies
    with pytest.raises(ValueError, match="at least 2 points"):
        fs.simulate_fault("healthy", Z0, LENGTH, np.array([100e6]))
    with pytest.raises(ValueError, match="strictly positive"):
        fs.simulate_fault("healthy", Z0, LENGTH, np.array([0.0, 100e6]))
    with pytest.raises(ValueError, match="strictly monotonically increasing"):
        fs.simulate_fault("healthy", Z0, LENGTH, np.array([200e6, 100e6]))

    # Negative reactive / mismatch values
    with pytest.raises(ValueError, match="L_val must be non-negative"):
        fs.simulate_fault("series_L", Z0, LENGTH, FREQ, L_val=-1e-9)
    with pytest.raises(ValueError, match="C_val must be non-negative"):
        fs.simulate_fault("shunt_C", Z0, LENGTH, FREQ, C_val=-1e-12)
    with pytest.raises(ValueError, match="ZL_mismatch must be strictly positive"):
        fs.simulate_fault("mismatch", Z0, LENGTH, FREQ, ZL_mismatch=-10.0)
    with pytest.raises(ValueError, match="noise_std must be non-negative"):
        fs.simulate_fault("healthy", Z0, LENGTH, FREQ, noise_std=-0.05)

    # Discontinuity position out of bounds
    with pytest.raises(ValueError, match="fault_pos must be within"):
        fs.simulate_fault("series_L", Z0, LENGTH, FREQ, fault_pos=-0.1)
    with pytest.raises(ValueError, match="fault_pos must be within"):
        fs.simulate_fault("series_L", Z0, LENGTH, FREQ, fault_pos=1.5)

