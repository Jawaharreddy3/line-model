import sys
import pathlib
import numpy as np
import pytest
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import line_model as lm
import measurements as meas

Z0 = 50.0
F = 100e6
VF = 1.0
LAM = lm.wavelength(F, VF)
BETA = lm.phase_constant(F, VF)


def test_matched_reflection_and_metrics():
    # HAND_CALCULATIONS: Item 1 (ZL = 50 -> Gamma = 0, VSWR = 1, RL = inf)
    gamma = meas.reflection_coefficient(50.0, Z0)
    assert gamma == pytest.approx(0.0)
    assert meas.vswr(gamma) == pytest.approx(1.0)
    assert np.isinf(meas.return_loss_db(gamma))


def test_short_circuit_metrics():
    # Short circuit (Gamma = -1, VSWR = inf, RL = 0 dB)
    gamma = meas.reflection_coefficient(0.0, Z0)
    assert gamma == pytest.approx(-1.0 + 0j)
    assert np.isinf(meas.vswr(gamma))
    assert meas.return_loss_db(gamma) == pytest.approx(0.0, abs=1e-12)


def test_open_circuit_metrics():
    # Open circuit (ZL = np.inf -> Gamma = +1, VSWR = inf, RL = 0 dB)
    gamma = meas.reflection_coefficient(np.inf, Z0)
    assert gamma == pytest.approx(1.0 + 0j)
    assert np.isinf(meas.vswr(gamma))
    assert meas.return_loss_db(gamma) == pytest.approx(0.0, abs=1e-12)


def test_hand_calculation_quarter_wave_100_ohm():
    # HAND_CALCULATIONS: Item 4 (ZL = 100 -> Zin = 25 ohm, Gamma_in = -1/3, VSWR = 2.0, RL ~ 9.542 dB)
    zin = lm.input_impedance(Z0, 100.0, BETA, LAM / 4)
    assert zin == pytest.approx(25.0, rel=1e-9)

    gamma_in = meas.reflection_coefficient(zin, Z0)
    assert gamma_in == pytest.approx(-1.0 / 3.0, rel=1e-9)
    assert meas.vswr(gamma_in) == pytest.approx(2.0, rel=1e-9)
    expected_rl = 20.0 * np.log10(3.0)  # ~9.5424 dB
    assert meas.return_loss_db(gamma_in) == pytest.approx(expected_rl, rel=1e-9)


def test_reactive_loads_vswr_and_rl():
    # Pure reactive load: Zin = +j50 (HAND_CALCULATIONS: Item 2, short at lambda/8)
    zin = 1j * 50.0
    gamma = meas.reflection_coefficient(zin, Z0)
    assert abs(gamma) == pytest.approx(1.0, rel=1e-9)
    assert np.isinf(meas.vswr(gamma))
    assert meas.return_loss_db(gamma) == pytest.approx(0.0, abs=1e-12)


def test_array_broadcasting():
    z_array = np.array([50.0, 100.0, 0.0, np.inf])
    gamma_arr = meas.reflection_coefficient(z_array, Z0)
    assert gamma_arr.shape == (4,)
    assert gamma_arr[0] == pytest.approx(0.0)
    assert gamma_arr[1] == pytest.approx(1.0 / 3.0)
    assert gamma_arr[2] == pytest.approx(-1.0)
    assert gamma_arr[3] == pytest.approx(1.0)

    vswr_arr = meas.vswr(gamma_arr)
    assert vswr_arr[0] == pytest.approx(1.0)
    assert vswr_arr[1] == pytest.approx(2.0)
    assert np.isinf(vswr_arr[2])
    assert np.isinf(vswr_arr[3])

    rl_arr = meas.return_loss_db(gamma_arr)
    assert np.isinf(rl_arr[0])
    assert rl_arr[1] == pytest.approx(20.0 * np.log10(3.0))
    assert rl_arr[2] == pytest.approx(0.0, abs=1e-12)
    assert rl_arr[3] == pytest.approx(0.0, abs=1e-12)


def test_sweep_contract_keys_and_shapes():
    freqs = np.linspace(50e6, 200e6, 21)
    res = meas.sweep(Z0, 100.0, 1.5, freqs, vf=VF)

    # Check exact contract keys: f, zin, gamma, vswr, rl_db
    for key in ["f", "zin", "gamma", "vswr", "rl_db"]:
        assert key in res
        assert len(res[key]) == 21

    # Lossless line: |Gamma| magnitude must be constant along frequency for real load
    # |Gamma_in| = |Gamma_L| = |(100-50)/(100+50)| = 1/3
    assert np.allclose(np.abs(res["gamma"]), 1.0 / 3.0, rtol=1e-9)
    assert np.allclose(res["vswr"], 2.0, rtol=1e-9)
    assert np.allclose(res["rl_db"], 20.0 * np.log10(3.0), rtol=1e-9)


def test_vswr_handles_nonpassive_loads():
    # Passive-line VSWR is physically undefined for |Gamma| > 1; returns np.nan
    val = meas.vswr(1.5)
    assert np.isnan(val)

    arr = meas.vswr(np.array([0.5, 1.0, 1.2]))
    assert np.isclose(arr[0], 3.0)
    assert np.isinf(arr[1])
    assert np.isnan(arr[2])


def test_vswr_numerical_tolerance_and_boundary_cases():
    """
    Regression test for VSWR numerical tolerance:
    Ensures relative tolerance is explicitly controlled (rtol=1e-12, atol=1e-12)
    so values slightly below unity (e.g. 0.99999) are never misclassified as exactly 1.0 (inf).
    """
    # 1. Gamma magnitude 0: VSWR = 1.0
    assert meas.vswr(0.0) == pytest.approx(1.0, abs=1e-15)
    assert meas.vswr(0.0 + 0.0j) == pytest.approx(1.0, abs=1e-15)

    # 2. Gamma magnitude 0.5: VSWR = (1 + 0.5) / (1 - 0.5) = 3.0
    expected_vswr_05 = 3.0
    assert meas.vswr(0.5) == pytest.approx(expected_vswr_05, rel=1e-14)
    assert meas.vswr(-0.5) == pytest.approx(expected_vswr_05, rel=1e-14)
    assert meas.vswr(0.5j) == pytest.approx(expected_vswr_05, rel=1e-14)
    assert meas.vswr(-0.5j) == pytest.approx(expected_vswr_05, rel=1e-14)
    # Complex point with |Gamma| = 0.5
    gamma_05_complex = 0.3 + 0.4j
    assert np.isclose(np.abs(gamma_05_complex), 0.5)
    assert meas.vswr(gamma_05_complex) == pytest.approx(expected_vswr_05, rel=1e-14)

    # 3. Gamma magnitude 0.99999: Analytical VSWR = (1 + 0.99999) / (1 - 0.99999) = 1.99999 / 1e-5 = 199999.0
    expected_vswr_099999 = (1.0 + 0.99999) / (1.0 - 0.99999)  # 199999.0
    vswr_099999 = meas.vswr(0.99999)
    assert np.isfinite(vswr_099999), "VSWR for |Gamma|=0.99999 must be finite, not infinite!"
    assert vswr_099999 == pytest.approx(expected_vswr_099999, rel=1e-14)

    # Complex with magnitude 0.99999 (pure imaginary and rotated)
    assert meas.vswr(0.0 + 0.99999j) == pytest.approx(expected_vswr_099999, rel=1e-14)
    assert meas.vswr(-0.99999 + 0.0j) == pytest.approx(expected_vswr_099999, rel=1e-14)
    gamma_099999_complex = 0.99999 * (np.cos(np.pi / 4) + 1j * np.sin(np.pi / 4))
    expected_rotated = (1.0 + np.abs(gamma_099999_complex)) / (1.0 - np.abs(gamma_099999_complex))
    assert meas.vswr(gamma_099999_complex) == pytest.approx(expected_rotated, rel=1e-14)

    # 4. Gamma magnitude exactly 1: VSWR = infinity
    assert np.isinf(meas.vswr(1.0)) and meas.vswr(1.0) > 0
    assert np.isinf(meas.vswr(-1.0))
    assert np.isinf(meas.vswr(1.0j))
    assert np.isinf(meas.vswr(-1.0j))
    gamma_unit_complex = (1.0 + 1.0j) / np.sqrt(2.0)
    assert np.isclose(np.abs(gamma_unit_complex), 1.0)
    assert np.isinf(meas.vswr(gamma_unit_complex))

    # 5. Gamma magnitude 1.0001: Non-passive (|Gamma| > 1) -> NaN
    assert np.isnan(meas.vswr(1.0001))
    assert np.isnan(meas.vswr(-1.0001))
    assert np.isnan(meas.vswr(1.0001j))
    gamma_nonpassive_complex = 1.0001 * (0.6 + 0.8j)
    assert np.isnan(meas.vswr(gamma_nonpassive_complex))

    # 6. Array broadcasting (1-D and 2-D)
    gamma_1d = np.array([0.0, 0.5, 0.99999, 1.0, 1.0001])
    vswr_1d = meas.vswr(gamma_1d)
    assert vswr_1d.shape == (5,)
    assert vswr_1d[0] == pytest.approx(1.0, abs=1e-15)
    assert vswr_1d[1] == pytest.approx(3.0, rel=1e-14)
    assert vswr_1d[2] == pytest.approx(expected_vswr_099999, rel=1e-14)
    assert np.isinf(vswr_1d[3])
    assert np.isnan(vswr_1d[4])

    # 2-D array with complex numbers and broadcasting
    gamma_2d = np.array([
        [0.0 + 0j, 0.3 + 0.4j],
        [0.0 - 0.99999j, -1.0 + 0j],
        [1.0001j, np.nan]
    ])
    vswr_2d = meas.vswr(gamma_2d)
    assert vswr_2d.shape == (3, 2)
    assert vswr_2d[0, 0] == pytest.approx(1.0, abs=1e-15)
    assert vswr_2d[0, 1] == pytest.approx(3.0, rel=1e-14)
    assert vswr_2d[1, 0] == pytest.approx(expected_vswr_099999, rel=1e-14)
    assert np.isinf(vswr_2d[1, 1])
    assert np.isnan(vswr_2d[2, 0])
    assert np.isnan(vswr_2d[2, 1])



@pytest.mark.parametrize("vf_test", [0.66, 0.70, 1.0])
def test_sweep_preserves_vf_and_sweepresult(vf_test):
    freqs = np.linspace(100e6, 500e6, 11)
    res = meas.sweep(50.0, 75.0, 1.2, freqs, vf=vf_test)
    assert isinstance(res, meas.SweepResult)
    assert isinstance(res, dict)
    assert res.vf == pytest.approx(vf_test)
    assert res.Z0 == 50.0
    assert res.length == pytest.approx(1.2)
    # Dictionary access
    assert "f" in res
    assert "gamma" in res
    assert "vswr" in res
    assert "rl_db" in res
    assert "zin" in res


def test_smith_plot_generation():
    freqs = np.linspace(50e6, 150e6, 31)
    res = meas.sweep(Z0, 25.0 + 35j, 1.0, freqs, vf=VF)

    fig, ax = plt.subplots()
    ret_ax = meas.smith_plot(res["gamma"], ax=ax)
    assert ret_ax is ax
    assert len(ax.lines) > 0
    plt.close(fig)

    # Test default ax=None
    ret_ax2 = meas.smith_plot(res["gamma"])
    assert ret_ax2 is not None
    plt.close(ret_ax2.figure)


def test_measurements_validation_and_boundary_conditions():
    # 1. Invalid Z0 with non-positive real part
    with pytest.raises(ValueError, match="strictly positive real part"):
        meas.reflection_coefficient(50.0, -50.0)

    with pytest.raises(ValueError, match="strictly positive real part"):
        meas.reflection_coefficient(50.0, 0.0)

    # 2. NaN inputs to reflection_coefficient
    with pytest.raises(ValueError, match="cannot contain NaN"):
        meas.reflection_coefficient(np.nan, 50.0)

    with pytest.raises(ValueError, match="cannot contain NaN"):
        meas.reflection_coefficient(50.0, np.nan)

    # 3. Sweep invalid line length
    freqs = np.linspace(100e6, 200e6, 11)
    with pytest.raises(ValueError, match="Line length must be provided"):
        meas.sweep(50.0, 50.0, None, freqs)

    with pytest.raises(ValueError, match="Line length must be a finite, non-negative number"):
        meas.sweep(50.0, 50.0, -1.0, freqs)

    with pytest.raises(ValueError, match="Line length must be a finite, non-negative number"):
        meas.sweep(50.0, 50.0, np.nan, freqs)

    # 4. Sweep empty and invalid frequency array
    with pytest.raises(ValueError, match="Frequency array cannot be empty"):
        meas.sweep(50.0, 50.0, 1.0, np.array([]))

    with pytest.raises(ValueError, match="strictly positive"):
        meas.sweep(50.0, 50.0, 1.0, np.array([0.0, 100e6]))

    with pytest.raises(ValueError, match="strictly positive"):
        meas.sweep(50.0, 50.0, 1.0, np.array([-10e6, 100e6]))

    with pytest.raises(ValueError, match="strictly monotonically increasing"):
        meas.sweep(50.0, 50.0, 1.0, np.array([200e6, 100e6]))

    with pytest.raises(ValueError, match="strictly monotonically increasing"):
        meas.sweep(50.0, 50.0, 1.0, np.array([100e6, 100e6]))

    # 5. Invalid velocity factor
    with pytest.raises(ValueError, match="velocity factor"):
        meas.sweep(50.0, 50.0, 1.0, freqs, vf=0.0)

    with pytest.raises(ValueError, match="velocity factor"):
        meas.sweep(50.0, 50.0, 1.0, freqs, vf=1.5)

