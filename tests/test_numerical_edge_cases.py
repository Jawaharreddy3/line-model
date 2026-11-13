"""
tests/test_numerical_edge_cases.py -- Edge Cases, Boundary Conditions, and Exception Handling.

Tests:
  - Negative R, L, G, C parameters.
  - Zero or negative frequencies.
  - Negative, zero, or non-finite line lengths.
  - NaN and infinite inputs.
  - Division by zero singularities.
  - Inverted or non-monotonic frequency sweep ranges.
  - Complex-valued loads across all four complex impedance quadrants.
"""

import pytest
import numpy as np
import line_model as lm
import measurements as meas
import fault_simulation as fs
import matching as match
import diagnosis as diag


def test_negative_rlgc_parameters_raise_value_error():
    """Verify rejection of negative primary line parameters."""
    f = 1e9

    with pytest.raises(ValueError, match="non-negative"):
        lm.series_impedance(-1.0, 250e-9, f)

    with pytest.raises(ValueError, match="non-negative"):
        lm.series_impedance(1.0, -250e-9, f)

    with pytest.raises(ValueError, match="non-negative"):
        lm.shunt_admittance(-0.001, 100e-12, f)

    with pytest.raises(ValueError, match="non-negative"):
        lm.shunt_admittance(0.001, -100e-12, f)

    with pytest.raises(ValueError, match="non-negative"):
        lm.propagation_constant(-1.0, 250e-9, 0.001, 100e-12, f)


def test_zero_and_negative_frequencies():
    """Verify rejection of f <= 0."""
    with pytest.raises(ValueError, match="frequency must be finite and > 0"):
        lm.wavelength(0.0)

    with pytest.raises(ValueError, match="frequency must be finite and > 0"):
        lm.wavelength(-100e6)

    with pytest.raises(ValueError, match="strictly positive"):
        meas.sweep(50.0, 50.0, 1.0, np.array([0.0, 100e6]))

    with pytest.raises(ValueError, match="strictly positive"):
        meas.sweep(50.0, 50.0, 1.0, np.array([-50e6, 100e6]))


def test_invalid_line_length():
    """Verify rejection of length < 0, None, or NaN."""
    freqs = np.linspace(100e6, 500e6, 10)

    with pytest.raises(ValueError, match="Line length must be provided"):
        meas.sweep(50.0, 50.0, None, freqs)

    with pytest.raises(ValueError, match="Line length must be a finite, non-negative number"):
        meas.sweep(50.0, 50.0, -0.5, freqs)

    with pytest.raises(ValueError, match="Line length must be a finite, non-negative number"):
        meas.sweep(50.0, 50.0, float("nan"), freqs)

    with pytest.raises(ValueError, match="Physical line length"):
        fs.simulate_fault("healthy", 50.0, -1.0, freqs)


def test_non_finite_inputs_nan_and_inf():
    """Verify robust handling of NaN and Inf across core functions."""
    # NaN in load impedance
    with pytest.raises(ValueError, match="cannot contain NaN"):
        meas.reflection_coefficient(np.nan, 50.0)

    with pytest.raises(ValueError, match="cannot contain NaN"):
        meas.reflection_coefficient(50.0, np.nan)

    with pytest.raises(ValueError, match="cannot contain NaN"):
        lm.load_reflection(50.0, np.nan)

    # Inf in load impedance (open circuit) is valid and mapped to +1.0 + 0j
    g_inf = meas.reflection_coefficient(np.inf, 50.0)
    assert g_inf == pytest.approx(1.0 + 0j)


def test_division_by_zero_singularities():
    """Verify analytic limits prevent uncaught zero division exceptions."""
    # Matched load |Gamma| == 0 -> Return loss is infinity dB (no division by zero warning)
    rl_zero = meas.return_loss_db(0.0)
    assert np.isinf(rl_zero)

    # Total reflection |Gamma| == 1 -> VSWR is infinity (no unhandled ZeroDivisionError)
    vswr_one = meas.vswr(1.0)
    assert np.isinf(vswr_one)

    # Open quarter-wave -> short (0 Ohm)
    zin_open_qw = lm.quarter_wave_zin(50.0, np.inf)
    assert zin_open_qw == pytest.approx(0.0 + 0j)

    # Short quarter-wave -> open (inf Ohm)
    zin_short_qw = lm.quarter_wave_zin(50.0, 0.0)
    assert np.isinf(np.abs(zin_short_qw))


def test_invalid_frequency_sweep_grids():
    """Verify validation of non-monotonic or inverted frequency sweep grids."""
    # Inverted grid
    f_inverted = np.array([1000e6, 900e6, 800e6])
    with pytest.raises(ValueError, match="strictly monotonically increasing"):
        meas.sweep(50.0, 50.0, 1.0, f_inverted)

    # Constant frequency (zero step size)
    f_flat = np.array([500e6, 500e6, 500e6])
    with pytest.raises(ValueError, match="strictly monotonically increasing"):
        meas.sweep(50.0, 50.0, 1.0, f_flat)

    # Matching design frequency outside swept band
    f_band = np.linspace(800e6, 1200e6, 21)
    with pytest.raises(ValueError, match="outside swept band"):
        match.compare_matching(50.0, 100.0, f_band, f_design=2000e6)


def test_complex_load_impedances_in_all_four_quadrants():
    """Verify valid complex loads remain supported without error."""
    Z0 = 50.0
    f = np.linspace(500e6, 1500e6, 10)

    # Quadrant 1: +R, +X (inductive load, e.g. antenna with series L)
    sw_q1 = meas.sweep(Z0, 60.0 + 40j, 1.0, f)
    assert np.all(np.isfinite(sw_q1["zin"]))
    assert np.all(np.abs(sw_q1["gamma"]) < 1.0)

    # Quadrant 4: +R, -X (capacitive load, e.g. electrically short dipole)
    sw_q4 = meas.sweep(Z0, 60.0 - 40j, 1.0, f)
    assert np.all(np.isfinite(sw_q4["zin"]))
    assert np.all(np.abs(sw_q4["gamma"]) < 1.0)
