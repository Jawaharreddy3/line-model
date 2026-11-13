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


def test_series_impedance_and_shunt_admittance():
    f = 1e9
    omega = 2.0 * np.pi * f
    R = 0.5
    L = 250e-9
    G = 1e-4
    C = 100e-12

    Z = lm.series_impedance(R, L, f)
    assert Z == pytest.approx(R + 1j * omega * L)

    Y = lm.shunt_admittance(G, C, f)
    assert Y == pytest.approx(G + 1j * omega * C)

    with pytest.raises(ValueError):
        lm.series_impedance(-1.0, L, f)
    with pytest.raises(ValueError):
        lm.shunt_admittance(-1.0, C, f)


def test_propagation_constant_lossless_reduction():
    f = 500e6
    omega = 2.0 * np.pi * f
    L = 250e-9
    C = 100e-12

    # In lossless limit (R=0, G=0): gamma = j * omega * sqrt(L * C)
    gamma_lossless = lm.propagation_constant(0.0, L, 0.0, C, f)
    assert np.isclose(gamma_lossless.real, 0.0, atol=1e-12)
    expected_beta = omega * np.sqrt(L * C)
    assert np.isclose(gamma_lossless.imag, expected_beta, rtol=1e-9)


def test_characteristic_impedance_lossless_reduction():
    f = 1e9
    L = 250e-9
    C = 100e-12

    # In lossless limit: Z0 = sqrt(L / C) = sqrt(250e-9 / 100e-12) = 50 ohm
    Z0 = lm.characteristic_impedance_rlgc(0.0, L, 0.0, C, f)
    assert np.isclose(Z0.real, 50.0, rtol=1e-9)
    assert np.isclose(Z0.imag, 0.0, atol=1e-12)


def test_phase_velocity_rlgc():
    f = 1e9
    L = 250e-9
    C = 100e-12
    vp = lm.phase_velocity_rlgc(0.0, L, 0.0, C, f)
    expected_vp = 1.0 / np.sqrt(L * C)  # 2.0e8 m/s
    assert np.isclose(vp, expected_vp, rtol=1e-9)


def test_input_impedance_lossy_matches_lossless():
    f = 100e6
    vf = 1.0
    beta = lm.phase_constant(f, vf)
    gamma = 1j * beta
    Z0 = 50.0
    lam = lm.wavelength(f, vf)

    for length in [0.0, 0.125 * lam, 0.25 * lam, 0.5 * lam]:
        for ZL in [50.0, 100.0, 0.0, lm.OPEN, 30.0 + 40.0j]:
            z_lossless = lm.input_impedance(Z0, ZL, beta, length)
            z_lossy = lm.input_impedance_lossy(Z0, ZL, gamma, length)
            if np.isinf(abs(z_lossless)):
                assert np.isinf(abs(z_lossy))
            else:
                assert np.isclose(z_lossless, z_lossy, atol=1e-11)


def test_quarter_wave_impedance_rejects_negative_real():
    with pytest.raises(ValueError):
        lm.quarter_wave_impedance(-50, 100)
    with pytest.raises(ValueError):
        lm.quarter_wave_impedance(50, -100)
    with pytest.raises(ValueError):
        lm.quarter_wave_impedance(0, 100)


def test_skin_depth_analytical():
    # Benchmark: Copper at 1 GHz has skin depth ~ 2.09 um
    f = 1e9
    delta = lm.skin_depth(f)
    expected_delta = 1.0 / np.sqrt(np.pi * f * lm.MU0 * lm.SIGMA_COPPER)
    assert np.isclose(delta, expected_delta, rtol=1e-12)
    assert np.isclose(delta, 2.0898e-6, rtol=1e-3)

    # Scaling with frequency: delta(4f) = delta(f) / 2
    delta_4f = lm.skin_depth(4.0 * f)
    assert np.isclose(delta_4f, delta / 2.0, rtol=1e-12)

    # Invalid inputs
    with pytest.raises(ValueError):
        lm.skin_depth(-1e6)
    with pytest.raises(ValueError):
        lm.skin_depth(1e9, sigma=-10)


def test_surface_resistance_and_coaxial_skin():
    f = 1e9
    Rs = lm.surface_resistance(f)
    expected_Rs = np.sqrt(np.pi * f * lm.MU0 / lm.SIGMA_COPPER)
    assert np.isclose(Rs, expected_Rs, rtol=1e-12)

    # Coaxial line: a = 0.5 mm, b = 1.75 mm
    a, b = 0.5e-3, 1.75e-3
    R_coax = lm.coaxial_skin_resistance(f, a, b)
    expected_R = (Rs / (2.0 * np.pi)) * (1.0 / a + 1.0 / b)
    assert np.isclose(R_coax, expected_R, rtol=1e-12)
    assert R_coax > 0.0

    # Geometric checks
    with pytest.raises(ValueError):
        lm.coaxial_skin_resistance(f, a=1.0e-3, b=0.5e-3)  # b <= a
    with pytest.raises(ValueError):
        lm.coaxial_skin_resistance(f, a=-0.5e-3, b=1.5e-3)


def test_frequency_dependent_resistance():
    R_dc = 0.1  # ohm/m
    f_ref = 1e6
    assert np.isclose(lm.frequency_dependent_resistance(1e6, R_dc, f_ref), R_dc * np.sqrt(2.0), rtol=1e-12)
    # High frequency asymptotic: R(100 MHz) ~ R_dc * sqrt(101)
    assert np.isclose(lm.frequency_dependent_resistance(100e6, R_dc, f_ref), R_dc * np.sqrt(101.0), rtol=1e-12)

    with pytest.raises(ValueError):
        lm.frequency_dependent_resistance(-1.0, R_dc)
    with pytest.raises(ValueError):
        lm.frequency_dependent_resistance(1e6, -0.5)

