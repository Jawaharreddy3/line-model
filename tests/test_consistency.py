"""
tests/test_consistency.py -- Mutual Consistency Between Related Calculations.

Validates that mathematically coupled equations throughout RF LINE DOCTOR
satisfy theoretical identities and inverse relationships across all parameters.
"""

import pytest
import numpy as np
import line_model as lm
import measurements as meas
import matching as match
import core.fault_location as fl


def test_zin_to_gamma_bidirectional_consistency():
    """
    Verify Zin <-> Gamma bijection:
      Gamma = (Zin - Z0) / (Zin + Z0)
      Zin = Z0 * (1 + Gamma) / (1 - Gamma)
    """
    Z0 = 50.0
    f = np.linspace(200e6, 500e6, 50)
    sw = meas.sweep(Z0, 120.0 + 30j, 1.2, f, vf=0.66)

    zin = sw["zin"]
    gamma = sw["gamma"]

    # Reconstruct Gamma from Zin
    g_reconstructed = (zin - Z0) / (zin + Z0)
    assert np.allclose(gamma, g_reconstructed, atol=1e-12)

    # Reconstruct Zin from Gamma
    zin_reconstructed = Z0 * (1.0 + gamma) / (1.0 - gamma)
    assert np.allclose(zin, zin_reconstructed, atol=1e-12)


def test_vswr_and_return_loss_cross_coupling():
    """
    Verify coupling between VSWR and Return Loss:
      VSWR = (1 + 10^(-RL/20)) / (1 - 10^(-RL/20))
      RL = -20 * log10((VSWR - 1) / (VSWR + 1))
    """
    test_rl_db = np.array([5.0, 10.0, 15.0, 20.0, 30.0, 40.0])

    for rl in test_rl_db:
        # 1. Compute expected Gamma magnitude from RL
        mag = 10.0 ** (-rl / 20.0)

        # 2. Compute VSWR
        vswr_val = meas.vswr(mag)
        expected_vswr = (1.0 + mag) / (1.0 - mag)
        assert vswr_val == pytest.approx(expected_vswr, rel=1e-11)

        # 3. Invert VSWR back to RL
        inverted_rl = -20.0 * np.log10((vswr_val - 1.0) / (vswr_val + 1.0))
        assert inverted_rl == pytest.approx(rl, rel=1e-11)


def test_lossy_reduction_to_lossless_as_attenuation_approaches_zero():
    """
    Verify that as R -> 0 and G -> 0, lossy equations converge continuously
    to the lossless formulas.
    """
    L = 250e-9
    C = 100e-12
    f = 1e9
    length = 1.5

    # Lossless baseline
    z0_lossless = np.sqrt(L / C)  # 50 Ohm
    vf_lossless = (1.0 / np.sqrt(L * C)) / lm.C0
    zin_lossless = lm.input_impedance_at_freq(z0_lossless, 80.0, f, length, vf=vf_lossless)

    # Sequence of diminishing loss: R, G -> 0
    attenuations = [1e-2, 1e-4, 1e-6, 1e-8]
    prev_error = float("inf")

    for factor in attenuations:
        R_val = 2.0 * factor
        G_val = 0.001 * factor
        z0_lossy = lm.characteristic_impedance_rlgc(R_val, L, G_val, C, f)
        gamma_lossy = lm.propagation_constant(R_val, L, G_val, C, f)
        zin_lossy = lm.input_impedance_lossy(z0_lossy, 80.0, gamma_lossy, length)

        error = abs(zin_lossy - zin_lossless)
        assert error < prev_error, "Convergence failure: error did not decrease with lower loss"
        prev_error = error

    # At 1e-8 factor, lossy Zin matches lossless Zin to within 1e-6 Ohm
    assert prev_error < 1e-6


def test_quarter_wave_transformer_inversion_identity():
    """
    Verify analytical quarter-wave matching identity:
      Zt = sqrt(Z0 * RL)
      Zin(f0) = Zt^2 / RL = Z0
      Gamma(f0) = 0.0
      VSWR(f0) = 1.0
      RL(f0) = inf
    """
    Z0 = 50.0
    RL_vals = [25.0, 75.0, 100.0, 200.0]
    f0 = 1.5e9
    f_arr = np.linspace(1e9, 2e9, 101)

    for RL in RL_vals:
        res = match.compare_matching(Z0, RL, f_arr, vf=0.70, f_design=f0)

        # Check Zt formula
        assert res["Zt"] == pytest.approx(np.sqrt(Z0 * RL), rel=1e-12)

        # Check exact match at f0
        f0_metrics = res["at_f_design"]
        assert f0_metrics["gamma"] == pytest.approx(0.0, abs=1e-12)
        assert f0_metrics["vswr"] == pytest.approx(1.0, abs=1e-12)
        assert np.isinf(f0_metrics["rl_db"])
        assert f0_metrics["zin"] == pytest.approx(Z0, rel=1e-10)


def test_dual_method_distance_consistency_for_resistive_fault():
    """
    For a non-reactive fault (e.g. open, short, or resistive mismatch),
    Method 1 (IFFT TDR) and Method 2 (Phase Slope) must be highly consistent
    and agree within 1x Rayleigh resolution.
    """
    f = np.linspace(400e6, 3500e6, 300)
    vf = 0.66
    Z0 = 50.0
    length = 1.2
    sw = meas.sweep(Z0, lm.OPEN, length, f, vf=vf)

    res_metrics = fl.calculate_resolution_metrics(f, vf=vf)
    dual = fl.locate_fault_dual_method(sw["gamma"], f, vf=vf, fault_class="open")

    assert dual["is_reliable"] is True
    assert dual["dist_ifft_m"] is not None
    assert dual["dist_phase_m"] is not None

    discrepancy = abs(dual["dist_ifft_m"] - dual["dist_phase_m"])
    assert discrepancy < res_metrics["range_res_m"], (
        f"Dual methods should agree within Rayleigh limit ({res_metrics['range_res_m']:.3f} m), "
        f"got discrepancy {discrepancy:.3f} m"
    )
