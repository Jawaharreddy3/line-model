import numpy as np
import pytest

import line_model as lm
import measurements as meas
import fault_simulation as fs
import diagnosis as diag
import matching as match

Z0 = 50.0
F0 = 100e6
VF = 1.0
LAM = lm.wavelength(F0, VF)
BETA = lm.phase_constant(F0, VF)


def test_hand_calc_item_1_matched():
    # Item 1: Matched, ZL = 50 -> Gamma_L = 0, Zin = 50 for any length
    for frac in [0.0, 0.125, 0.25, 0.5, 1.0]:
        zin = lm.input_impedance(Z0, 50.0, BETA, frac * LAM)
        gamma = meas.reflection_coefficient(zin, Z0)
        assert zin == pytest.approx(50.0, abs=1e-9)
        assert gamma == pytest.approx(0.0, abs=1e-9)
        assert meas.vswr(gamma) == pytest.approx(1.0, abs=1e-9)
        assert np.isinf(meas.return_loss_db(gamma))


def test_hand_calc_item_2_short_eighth_wave():
    # Item 2: Short, l = lambda/8 (beta*l = 45 deg): Zin = +j50 ohm (inductive)
    l = LAM / 8.0
    zin = lm.input_impedance(Z0, 0.0, BETA, l)
    assert zin == pytest.approx(1j * 50.0, rel=1e-9)


def test_hand_calc_item_3_open_eighth_wave():
    # Item 3: Open, l = lambda/8: Zin = -j50 ohm (capacitive)
    l = LAM / 8.0
    zin = lm.input_impedance(Z0, lm.OPEN, BETA, l)
    assert zin == pytest.approx(-1j * 50.0, rel=1e-9)


def test_hand_calc_item_4_quarter_wave_100():
    # Item 4: Quarter-wave, ZL = 100: Zin = 25 ohm, Gamma_in = -1/3, VSWR = 2.0
    l = LAM / 4.0
    zin = lm.input_impedance(Z0, 100.0, BETA, l)
    assert zin == pytest.approx(25.0, rel=1e-9)
    gamma_in = meas.reflection_coefficient(zin, Z0)
    assert abs(gamma_in) == pytest.approx(1.0 / 3.0, rel=1e-9)
    assert meas.vswr(gamma_in) == pytest.approx(2.0, rel=1e-9)
    assert meas.return_loss_db(gamma_in) == pytest.approx(20.0 * np.log10(3.0), rel=1e-9)


def test_hand_calc_item_5_half_wave_repetition():
    # Item 5: Half-wave, ZL = 30 + j40: Zin = ZL
    ZL = 30.0 + 40j
    zin = lm.input_impedance(Z0, ZL, BETA, LAM / 2.0)
    assert zin == pytest.approx(ZL, rel=1e-9)


def test_hand_calc_item_6_transformer_50_to_200():
    # Item 6: Transformer, 50 -> 200 ohm: Zt = 100 ohm, length = 0.75 m at 100 MHz, vf=1
    des = match.design_quarter_wave(Z0, 200.0, F0, vf=VF)
    assert des["Zt"] == pytest.approx(100.0, rel=1e-9)
    assert des["length_m"] == pytest.approx(0.75, rel=1e-3)


def test_hand_calc_item_7_singular_quarter_wave():
    # Item 7: Short at lambda/4 -> Zin -> infinity (looks open); Open at lambda/4 -> 0 (looks short)
    l = LAM / 4.0
    zin_short = lm.input_impedance(Z0, 0.0, BETA, l)
    zin_open = lm.input_impedance(Z0, lm.OPEN, BETA, l)
    assert np.isinf(abs(zin_short))
    assert zin_open == pytest.approx(0.0, abs=1e-9)


def test_interface_compliance_and_types():
    freqs = np.linspace(100e6, 2e9, 50)
    sw = meas.sweep(Z0, 100.0, 1.0, freqs, vf=VF)

    # Required contract keys
    assert set(sw.keys()) == {"f", "zin", "gamma", "vswr", "rl_db"}

    # Diagnosis contract return
    diag_res = diag.classify(sw, Z0)
    assert isinstance(diag_res, str)
    assert diag_res in ["healthy", "open", "short", "mismatch", "unknown"]

    # Distance estimation return
    d_est = diag.estimate_distance(sw, VF, diag_res)
    assert isinstance(d_est, float)

    # Matching contract return
    des = match.design_quarter_wave(Z0, 100.0, 1e9, vf=VF)
    assert set(des.keys()) == {"Zt", "length_m"}
