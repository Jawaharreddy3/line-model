import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np
import pytest
import line_model as lm

Z0 = 50.0
F = 100e6
VF = 1.0
LAM = lm.wavelength(F, VF)
BETA = lm.phase_constant(F, VF)


def test_wavelength_and_beta():
    assert LAM == pytest.approx(2.99792458, rel=1e-9)
    assert BETA == pytest.approx(2 * np.pi / LAM, rel=1e-12)
    assert lm.wavelength(F, 0.66) == pytest.approx(0.66 * LAM)


@pytest.mark.parametrize("frac", [0.0, 0.1, 0.25, 0.37, 0.5, 1.3])
def test_matched_line_is_Z0_for_any_length(frac):
    zin = lm.input_impedance(Z0, Z0, BETA, frac * LAM)
    assert zin == pytest.approx(Z0, abs=1e-9)


@pytest.mark.parametrize("frac", [0.01, 0.1, 0.2, 0.3, 0.45])
def test_short_circuit(frac):
    l = frac * LAM
    expected = 1j * Z0 * np.tan(BETA * l)
    assert lm.input_impedance(Z0, 0.0, BETA, l) == pytest.approx(expected, rel=1e-9, abs=1e-9)


@pytest.mark.parametrize("frac", [0.01, 0.1, 0.2, 0.3, 0.45])
def test_open_circuit(frac):
    l = frac * LAM
    expected = -1j * Z0 / np.tan(BETA * l)
    assert lm.input_impedance(Z0, lm.OPEN, BETA, l) == pytest.approx(expected, rel=1e-9, abs=1e-9)


def test_quarter_wave_inversion():
    ZL = 100.0 + 0j
    zin = lm.input_impedance(Z0, ZL, BETA, LAM / 4)
    assert zin == pytest.approx(lm.quarter_wave_zin(Z0, ZL), rel=1e-9)
    assert zin == pytest.approx(25.0, rel=1e-9)


def test_quarter_wave_short_is_open_and_vice_versa():
    assert np.isinf(abs(lm.input_impedance(Z0, 0.0, BETA, LAM / 4)))
    assert lm.input_impedance(Z0, lm.OPEN, BETA, LAM / 4) == pytest.approx(0, abs=1e-9)


def test_half_wave_repeats_load():
    ZL = 30 + 40j
    assert lm.input_impedance(Z0, ZL, BETA, LAM / 2) == pytest.approx(ZL, rel=1e-9)


def test_matches_textbook_formula_complex_load():
    ZL = 75 + 25j
    l = 0.137 * LAM
    t = np.tan(BETA * l)
    expected = Z0 * (ZL + 1j * Z0 * t) / (Z0 + 1j * ZL * t)
    assert lm.input_impedance(Z0, ZL, BETA, l) == pytest.approx(expected, rel=1e-12)


def test_load_reflection_values():
    assert lm.load_reflection(Z0, Z0) == 0
    assert lm.load_reflection(Z0, 0.0) == pytest.approx(-1)
    assert lm.load_reflection(Z0, lm.OPEN) == pytest.approx(1)
    assert lm.load_reflection(Z0, 100.0) == pytest.approx(1 / 3)


def test_array_inputs():
    l = np.array([0.01, 0.1, 0.2, 0.3, 0.4, 0.49]) * LAM
    z = lm.input_impedance(Z0, 0.0, BETA, l)
    assert z.shape == (6,)
    assert np.allclose(z, 1j * Z0 * np.tan(BETA * l))


def test_frequency_sweep_shape():
    f = np.linspace(50e6, 150e6, 11)
    z = lm.input_impedance_at_freq(Z0, 100 + 0j, f, 1.0, VF)
    assert z.shape == (11,)


def test_lossless_passivity_gamma_magnitude_constant():
    ZL = 20 + 60j
    g0 = abs(lm.load_reflection(Z0, ZL))
    for d in np.linspace(0, 2, 9):
        assert abs(lm.reflection_at_distance(Z0, ZL, BETA, d)) == pytest.approx(g0)


def test_invalid_inputs():
    with pytest.raises(ValueError):
        lm.wavelength(0, 1.0)
    with pytest.raises(ValueError):
        lm.phase_velocity(1.5)
    with pytest.raises(ValueError):
        lm.quarter_wave_impedance(50 + 5j, 100)


def test_quarter_wave_transformer_value():
    assert lm.quarter_wave_impedance(50, 200) == pytest.approx(100.0)
