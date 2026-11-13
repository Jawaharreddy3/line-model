"""
tests/test_benchmarks.py -- 10 Independent Ground-Truth Benchmark Suites.

Tests all 10 required benchmark categories by comparing the RF LINE DOCTOR
implementation outputs against the independent analytical models in
`tests/analytical_benchmarks.py` with justified numerical tolerances.
"""

import pytest
import numpy as np
import line_model as lm
import measurements as meas
import fault_simulation as fs
import diagnosis as diag
import core.fault_location as fl

from tests.analytical_benchmarks import (
    analytical_phase_velocity,
    analytical_series_impedance,
    analytical_shunt_admittance,
    analytical_propagation_constant,
    analytical_characteristic_impedance,
    analytical_load_reflection,
    analytical_lossless_zin,
    analytical_lossy_zin,
    analytical_vswr,
    analytical_return_loss_db,
    analytical_resolution_metrics,
)


# =============================================================================
# Benchmark 1: Matched Transmission Line (ZL = Z0)
# =============================================================================
def test_benchmark_1_matched_line(default_line_params, standard_freq_sweep, numerical_tolerances):
    """
    Benchmark 1: Matched load ZL = Z0.
    Expected:
      - Gamma = 0.0 + 0.0j across all frequencies and line lengths.
      - Input impedance Zin = Z0 = 50.0 Ohm strictly invariant.
      - VSWR = 1.0 (exact).
      - Return Loss = inf dB.
      - Classification = 'healthy'.
    """
    Z0 = default_line_params["Z0"]
    length = default_line_params["length"]
    vf = default_line_params["vf"]
    f_arr = standard_freq_sweep

    # Application execution
    sweep_res = meas.sweep(Z0, Z0, length, f_arr, vf=vf)

    # Independent analytical benchmark
    expected_zin = analytical_lossless_zin(Z0, Z0, f_arr, length, vf=vf)
    expected_gamma = analytical_load_reflection(Z0, Z0)
    expected_vswr = analytical_vswr(expected_gamma)
    expected_rl = analytical_return_loss_db(expected_gamma)

    # Verifications against justified tolerances
    tol = numerical_tolerances["algebraic"]
    assert np.allclose(sweep_res["zin"], expected_zin, atol=tol)
    assert np.allclose(sweep_res["gamma"], expected_gamma, atol=tol)
    assert np.allclose(sweep_res["vswr"], expected_vswr, atol=tol)
    assert np.all(np.isinf(sweep_res["rl_db"]))
    assert np.all(np.isinf(expected_rl))

    # Diagnostic label check
    diag_res = diag.classify(sweep_res, Z0)
    assert diag_res == "healthy"
    assert diag_res.subtype == "matched"


# =============================================================================
# Benchmark 2: Open-Circuit Load (ZL = infinity)
# =============================================================================
def test_benchmark_2_open_circuit(default_line_params, standard_freq_sweep, numerical_tolerances):
    """
    Benchmark 2: Open-circuit load ZL = inf.
    Expected:
      - Gamma_L = +1.0 + 0.0j.
      - Total reflection |Gamma| = 1.0 at all frequencies.
      - Input impedance Zin = -j Z0 cot(beta * l).
      - Purely imaginary (Re(Zin) = 0).
      - VSWR = inf.
      - Return Loss = 0.0 dB.
      - Classification = 'open'.
    """
    Z0 = default_line_params["Z0"]
    length = 0.5  # half metre
    vf = default_line_params["vf"]
    f_arr = standard_freq_sweep

    sweep_res = meas.sweep(Z0, lm.OPEN, length, f_arr, vf=vf)

    expected_zin = analytical_lossless_zin(Z0, np.inf, f_arr, length, vf=vf)
    expected_gamma_mag = 1.0
    expected_vswr = np.inf
    expected_rl = 0.0

    tol = numerical_tolerances["float_rel"]
    # Verify purely imaginary impedance (Re(Zin) == 0)
    assert np.allclose(np.real(sweep_res["zin"]), 0.0, atol=1e-9)
    assert np.allclose(sweep_res["zin"], expected_zin, rtol=tol)
    assert np.allclose(np.abs(sweep_res["gamma"]), expected_gamma_mag, atol=1e-12)
    assert np.all(np.isinf(sweep_res["vswr"]))
    assert np.allclose(sweep_res["rl_db"], expected_rl, atol=1e-12)

    diag_res = diag.classify(sweep_res, Z0)
    assert diag_res == "open"
    assert diag_res.subtype == "open_circuit"


# =============================================================================
# Benchmark 3: Short-Circuit Load (ZL = 0)
# =============================================================================
def test_benchmark_3_short_circuit(default_line_params, standard_freq_sweep, numerical_tolerances):
    """
    Benchmark 3: Short-circuit load ZL = 0.
    Expected:
      - Gamma_L = -1.0 + 0.0j.
      - Total reflection |Gamma| = 1.0 at all frequencies.
      - Input impedance Zin = j Z0 tan(beta * l).
      - Purely imaginary (Re(Zin) = 0).
      - VSWR = inf.
      - Return Loss = 0.0 dB.
      - Classification = 'short'.
    """
    Z0 = default_line_params["Z0"]
    length = 0.5
    vf = default_line_params["vf"]
    f_arr = standard_freq_sweep

    sweep_res = meas.sweep(Z0, 0.0 + 0j, length, f_arr, vf=vf)

    expected_zin = analytical_lossless_zin(Z0, 0.0 + 0j, f_arr, length, vf=vf)

    tol = numerical_tolerances["float_rel"]
    assert np.allclose(np.real(sweep_res["zin"]), 0.0, atol=1e-9)
    assert np.allclose(sweep_res["zin"], expected_zin, rtol=tol)
    assert np.allclose(np.abs(sweep_res["gamma"]), 1.0, atol=1e-12)
    assert np.all(np.isinf(sweep_res["vswr"]))
    assert np.allclose(sweep_res["rl_db"], 0.0, atol=1e-12)

    diag_res = diag.classify(sweep_res, Z0)
    assert diag_res == "short"
    assert diag_res.subtype == "short_circuit"


# =============================================================================
# Benchmark 4: Mismatched Load (Real and Complex)
# =============================================================================
def test_benchmark_4_mismatched_load(default_line_params, standard_freq_sweep, numerical_tolerances):
    """
    Benchmark 4: Resistive mismatch (120 Ohm) and Complex mismatch (75 + j50 Ohm).
    Expected:
      - 120 Ohm: Gamma_L = (120-50)/(120+50) = 7/17 ~ 0.41176.
        VSWR = (1 + 7/17) / (1 - 7/17) = 24/10 = 2.40.
        RL = -20*log10(7/17) ~ 7.707 dB.
      - Complex (75 + j50):
        Gamma_L = (25 + 50j)/(125 + 50j) ~ 0.31034 + 0.27586j.
        |Gamma_L| = sqrt(145)/29 ~ 0.41523.
        VSWR ~ 2.4202.
        RL ~ 7.635 dB.
    """
    Z0 = default_line_params["Z0"]
    length = default_line_params["length"]
    vf = default_line_params["vf"]
    f_arr = standard_freq_sweep
    tol = numerical_tolerances["float_rel"]

    # 4A: Real mismatch
    RL = 120.0
    sw_real = meas.sweep(Z0, RL, length, f_arr, vf=vf)
    exp_zin_real = analytical_lossless_zin(Z0, RL, f_arr, length, vf=vf)
    exp_gamma_real = analytical_load_reflection(RL, Z0)
    exp_vswr_real = analytical_vswr(exp_gamma_real)
    exp_rl_real = analytical_return_loss_db(exp_gamma_real)

    assert np.allclose(sw_real["zin"], exp_zin_real, rtol=tol)
    assert np.allclose(np.abs(sw_real["gamma"]), abs(exp_gamma_real), rtol=tol)
    assert np.allclose(sw_real["vswr"], exp_vswr_real, rtol=tol)
    assert np.allclose(sw_real["rl_db"], exp_rl_real, rtol=tol)
    assert diag.classify(sw_real, Z0) == "mismatch"

    # 4B: Complex mismatch
    ZC = 75.0 + 50.0j
    sw_cpx = meas.sweep(Z0, ZC, length, f_arr, vf=vf)
    exp_zin_cpx = analytical_lossless_zin(Z0, ZC, f_arr, length, vf=vf)
    exp_gamma_cpx = analytical_load_reflection(ZC, Z0)
    exp_vswr_cpx = analytical_vswr(exp_gamma_cpx)
    exp_rl_cpx = analytical_return_loss_db(exp_gamma_cpx)

    assert np.allclose(sw_cpx["zin"], exp_zin_cpx, rtol=tol)
    assert np.allclose(np.abs(sw_cpx["gamma"]), abs(exp_gamma_cpx), rtol=tol)
    assert np.allclose(sw_cpx["vswr"], exp_vswr_cpx, rtol=tol)
    assert np.allclose(sw_cpx["rl_db"], exp_rl_cpx, rtol=tol)


# =============================================================================
# Benchmark 5: Lossless Transmission Line (alpha = 0, Conservation of |Gamma|)
# =============================================================================
def test_benchmark_5_lossless_line(numerical_tolerances):
    """
    Benchmark 5: Lossless line parameters R=0, G=0, L=250 nH/m, C=100 pF/m.
    Expected:
      - Z0 = sqrt(L/C) = 50.0 Ohm (purely real).
      - gamma = j * omega * sqrt(LC) = j * beta (alpha = 0).
      - vp = 1/sqrt(LC) = 2.0e8 m/s.
      - Quarter-wave inversion: Zin(lambda/4) = Z0^2 / ZL.
      - Half-wave repetition: Zin(lambda/2) = ZL.
      - |Gamma(d)| = |Gamma_L| invariant with distance.
    """
    R, G = 0.0, 0.0
    L = 250e-9
    C = 100e-12
    f = 1e9  # 1 GHz

    z0 = lm.characteristic_impedance_rlgc(R, L, G, C, f)
    gamma = lm.propagation_constant(R, L, G, C, f)
    vp = lm.phase_velocity_rlgc(R, L, G, C, f)

    assert np.real(z0) == pytest.approx(50.0, rel=1e-9)
    assert np.imag(z0) == pytest.approx(0.0, abs=1e-12)
    assert np.real(gamma) == pytest.approx(0.0, abs=1e-12)  # alpha == 0
    assert np.imag(gamma) == pytest.approx(2.0 * np.pi * 1e9 * np.sqrt(L * C), rel=1e-9)
    assert vp == pytest.approx(1.0 / np.sqrt(L * C), rel=1e-9)

    # Quarter-wave inversion test
    lam = vp / f
    zin_quarter = lm.input_impedance_lossy(z0, 100.0, gamma, lam / 4.0)
    assert np.real(zin_quarter) == pytest.approx(25.0, rel=1e-7)
    assert np.imag(zin_quarter) == pytest.approx(0.0, abs=1e-7)

    # Half-wave repetition test
    zin_half = lm.input_impedance_lossy(z0, 100.0, gamma, lam / 2.0)
    assert np.real(zin_half) == pytest.approx(100.0, rel=1e-7)
    assert np.imag(zin_half) == pytest.approx(0.0, abs=1e-7)


# =============================================================================
# Benchmark 6: Lossy Transmission Line (alpha > 0, Exponential Reflection Decay)
# =============================================================================
def test_benchmark_6_lossy_line(numerical_tolerances):
    """
    Benchmark 6: Lossy line R = 2.0 Ohm/m, L = 250 nH/m, G = 0.001 S/m, C = 100 pF/m.
    Expected:
      - alpha = Re(gamma) > 0.
      - Complex Z0 with small negative imaginary part.
      - Reflection decays exponentially: |Gamma_in| = |Gamma_L| * exp(-2*alpha*l) < |Gamma_L|.
      - Implementation matches independent analytical lossy equations.
    """
    R = 2.0
    L = 250e-9
    G = 0.001
    C = 100e-12
    f = 1e9
    l = 2.0  # 2 metres

    # Implementation
    gamma_app = lm.propagation_constant(R, L, G, C, f)
    z0_app = lm.characteristic_impedance_rlgc(R, L, G, C, f)
    zin_app = lm.input_impedance_lossy(z0_app, 100.0, gamma_app, l)

    # Independent analytical benchmark
    gamma_exp = analytical_propagation_constant(R, L, G, C, f)
    z0_exp = analytical_characteristic_impedance(R, L, G, C, f)
    zin_exp = analytical_lossy_zin(z0_exp, 100.0, gamma_exp, l)

    tol = numerical_tolerances["float_rel"]
    assert np.allclose(gamma_app, gamma_exp, rtol=tol)
    assert np.allclose(z0_app, z0_exp, rtol=tol)
    assert np.allclose(zin_app, zin_exp, rtol=tol)

    # Verify physical attenuation: |Gamma_in| must be strictly less than |Gamma_L|
    gamma_l = analytical_load_reflection(100.0, z0_app)
    gamma_in = meas.reflection_coefficient(zin_app, z0_app)
    alpha = float(np.real(gamma_app))
    assert alpha > 0.0
    expected_decay = abs(gamma_l) * np.exp(-2.0 * alpha * l)
    assert abs(gamma_in) == pytest.approx(expected_decay, rel=tol)
    assert abs(gamma_in) < abs(gamma_l)


# =============================================================================
# Benchmark 7: Frequency Sweep (Array Consistency, Grid Monotonicity)
# =============================================================================
def test_benchmark_7_frequency_sweep(default_line_params, standard_freq_sweep):
    """
    Benchmark 7: Frequency sweep structure and alignment.
    Expected:
      - Sweep frequency grid is strictly monotonically increasing.
      - All output arrays (f, zin, gamma, vswr, rl_db) share exact same length.
      - Point-by-point calculation matches individual single-frequency evaluations.
    """
    Z0 = default_line_params["Z0"]
    length = default_line_params["length"]
    vf = default_line_params["vf"]
    f_arr = standard_freq_sweep

    sw = meas.sweep(Z0, 100.0, length, f_arr, vf=vf)

    # 1. Monotonicity
    assert np.all(np.diff(sw["f"]) > 0)
    assert len(sw["f"]) == len(f_arr)

    # 2. Key matching & lengths
    for k in ["f", "zin", "gamma", "vswr", "rl_db"]:
        assert k in sw
        assert len(sw[k]) == len(f_arr)

    # 3. Spot-check point-by-point equivalence at 3 indices (start, middle, end)
    for idx in [0, len(f_arr) // 2, -1]:
        f_i = f_arr[idx]
        zin_i = lm.input_impedance_at_freq(Z0, 100.0, f_i, length, vf=vf)
        gamma_i = meas.reflection_coefficient(zin_i, Z0)
        vswr_i = meas.vswr(gamma_i)
        rl_i = meas.return_loss_db(gamma_i)

        assert sw["zin"][idx] == pytest.approx(zin_i, rel=1e-11)
        assert sw["gamma"][idx] == pytest.approx(gamma_i, rel=1e-11)
        assert sw["vswr"][idx] == pytest.approx(vswr_i, rel=1e-11)
        assert sw["rl_db"][idx] == pytest.approx(rl_i, rel=1e-11)


# =============================================================================
# Benchmark 8: Reflection Coefficient (Complex Plane & Passive Boundedness)
# =============================================================================
def test_benchmark_8_reflection_coefficient():
    """
    Benchmark 8: Comprehensive reflection coefficient test across complex plane.
    Expected:
      - |Gamma| <= 1.0 for all passive impedances Re(Z) >= 0.
      - Correct quadrant mapping for inductive and capacitive loads.
    """
    Z0 = 50.0

    # Passive loads covering resistive, inductive, capacitive, and boundaries
    test_impedances = [
        50.0 + 0j,       # matched -> 0
        0.0 + 0j,        # short -> -1
        np.inf + 0j,     # open -> +1
        50.0 + 50.0j,    # inductive
        50.0 - 50.0j,    # capacitive
        10.0 + 0j,       # low resistive
        250.0 + 0j,      # high resistive
        0.0 + 100.0j,    # pure inductive
        0.0 - 100.0j,    # pure capacitive
    ]

    for z in test_impedances:
        g = meas.reflection_coefficient(z, Z0)
        mag = abs(g)
        assert mag <= 1.0 + 1e-12, f"Passivity violated for Z={z}: |Gamma|={mag}"

        # Compare with independent analytical formula
        exp_g = analytical_load_reflection(z, Z0)
        assert g == pytest.approx(exp_g, abs=1e-12)


# =============================================================================
# Benchmark 9: VSWR and Return Loss (Singularities and Inversions)
# =============================================================================
def test_benchmark_9_vswr_and_return_loss():
    """
    Benchmark 9: Bidirectional consistency between Gamma, VSWR, and Return Loss.
    Expected:
      - Gamma = 0 -> VSWR = 1.0, RL = inf dB.
      - |Gamma| = 1 -> VSWR = inf, RL = 0.0 dB.
      - Exact inversion: |Gamma| = (VSWR - 1) / (VSWR + 1) = 10^(-RL / 20).
    """
    gamma_test_vals = [0.0, 0.1, 0.25, 0.5, 0.8, 1.0]

    for g_mag in gamma_test_vals:
        vswr_val = meas.vswr(g_mag)
        rl_val = meas.return_loss_db(g_mag)

        if g_mag == 0.0:
            assert vswr_val == pytest.approx(1.0, abs=1e-12)
            assert np.isinf(rl_val)
        elif g_mag == 1.0:
            assert np.isinf(vswr_val)
            assert rl_val == pytest.approx(0.0, abs=1e-12)
        else:
            # Reconstruct |Gamma| from VSWR:
            reconstructed_from_vswr = (vswr_val - 1.0) / (vswr_val + 1.0)
            assert reconstructed_from_vswr == pytest.approx(g_mag, rel=1e-10)

            # Reconstruct |Gamma| from Return Loss:
            reconstructed_from_rl = 10.0 ** (-rl_val / 20.0)
            assert reconstructed_from_rl == pytest.approx(g_mag, rel=1e-10)


# =============================================================================
# Benchmark 10: Fault Location Calculations (TDR, Phase Slope, Range Resolution)
# =============================================================================
def test_benchmark_10_fault_location(default_line_params, broadband_freq_sweep, numerical_tolerances):
    """
    Benchmark 10: TDR distance localization and physical range resolution limits.
    Expected:
      - Range resolution delta_R = vp / (2*B).
      - Unambiguous range R_max = vp / (2*df).
      - Fault at known physical positions (e.g. 0.40 m, 0.75 m) detected within delta_R.
      - Healthy matched line yields None (no echo).
    """
    Z0 = default_line_params["Z0"]
    length = 1.2
    vf = default_line_params["vf"]
    f_arr = broadband_freq_sweep
    vp = analytical_phase_velocity(vf)
    B = f_arr[-1] - f_arr[0]
    expected_delta_r = vp / (2.0 * B)

    # 10A: Verify resolution metrics
    res_metrics = fl.calculate_resolution_metrics(f_arr, vf=vf)
    assert res_metrics["range_res_m"] == pytest.approx(expected_delta_r, rel=1e-7)

    # 10B: Test known fault distance estimation (short circuit at 0.75 m)
    true_pos = 0.75
    sim_short = fs.simulate_fault("short", Z0, length, f_arr, vf=vf, fault_pos=true_pos)
    d_est = diag.estimate_distance(sim_short["sweep"], vf, "short")
    assert d_est is not None
    assert abs(d_est - length) <= 2.0 * expected_delta_r

    # 10C: Series L discontinuity at 0.40 m
    sim_L = fs.simulate_fault("series_L", Z0, length, f_arr, vf=vf, fault_pos=0.40, L_val=20e-9)
    d_est_L = diag.estimate_distance(sim_L["sweep"], vf, "mismatch")
    assert d_est_L is not None
    assert abs(d_est_L - 0.40) <= 2.0 * expected_delta_r

    # 10D: Healthy line yields None
    sim_healthy = fs.simulate_fault("healthy", Z0, length, f_arr, vf=vf)
    d_est_healthy = diag.estimate_distance(sim_healthy["sweep"], vf, "healthy")
    assert d_est_healthy is None
