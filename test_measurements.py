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


def test_vswr_rejects_active_loads():
    with pytest.raises(ValueError):
        meas.vswr(1.5)


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
