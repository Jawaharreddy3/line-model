"""
tests/test_data_alignment_and_plotting.py -- Data Alignment and Visualization Integrity.

Verifies:
  - Frequency sweep arrays (f, zin, gamma, vswr, rl_db) share exact dimensions and point alignment.
  - Rectangular frequency response curves plot against the exact corresponding frequency coordinates.
  - Smith chart complex trajectories plot Re(Gamma) and Im(Gamma) without index distortion.
  - Matching studio Before and After sweeps remain strictly aligned in frequency.
"""

import pytest
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import line_model as lm
import measurements as meas
import matching as match


def test_sweep_arrays_shape_and_pointwise_alignment():
    """
    Ensure every element across sweep arrays corresponds to the same frequency index.
    """
    Z0 = 50.0
    ZL = 75.0 - 25j
    length = 1.4
    vf = 0.66
    freqs = np.linspace(400e6, 3200e6, 141)

    sw = meas.sweep(Z0, ZL, length, freqs, vf=vf)

    N = len(freqs)
    assert sw["f"].shape == (N,)
    assert sw["zin"].shape == (N,)
    assert sw["gamma"].shape == (N,)
    assert sw["vswr"].shape == (N,)
    assert sw["rl_db"].shape == (N,)

    # Pointwise alignment check across every single index
    for i in range(N):
        fi = sw["f"][i]
        expected_zin_i = lm.input_impedance_at_freq(Z0, ZL, fi, length, vf=vf)
        expected_g_i = meas.reflection_coefficient(expected_zin_i, Z0)
        expected_swr_i = meas.vswr(expected_g_i)
        expected_rl_i = meas.return_loss_db(expected_g_i)

        assert sw["zin"][i] == pytest.approx(expected_zin_i, rel=1e-12)
        assert sw["gamma"][i] == pytest.approx(expected_g_i, rel=1e-12)
        assert sw["vswr"][i] == pytest.approx(expected_swr_i, rel=1e-12)
        assert sw["rl_db"][i] == pytest.approx(expected_rl_i, rel=1e-12)


def test_smith_chart_trajectory_alignment():
    """
    Verify that smith_plot correctly extracts Re(Gamma) as X and Im(Gamma) as Y,
    preserving exact point counts and coordinate ordering.
    """
    freqs = np.linspace(500e6, 2000e6, 51)
    sw = meas.sweep(50.0, 100.0, 1.0, freqs, vf=0.70)
    gamma = sw["gamma"]

    fig, ax = plt.subplots()
    meas.smith_plot(gamma, ax=ax, label="Trajectory", color="red")

    # Find the plotted trajectory line (label="Trajectory")
    trajectory_line = None
    for line in ax.lines:
        if line.get_label() == "Trajectory":
            trajectory_line = line
            break

    assert trajectory_line is not None, "Trajectory line not found on Smith chart"

    x_data = trajectory_line.get_xdata()
    y_data = trajectory_line.get_ydata()

    # Verify length and point-for-point coordinate alignment
    assert len(x_data) == len(gamma)
    assert len(y_data) == len(gamma)
    assert np.allclose(x_data, np.real(gamma), atol=1e-12)
    assert np.allclose(y_data, np.imag(gamma), atol=1e-12)

    plt.close(fig)


def test_matching_before_after_frequency_alignment():
    """
    Verify that compare_matching preserves identical frequency arrays
    between before and after sweeps and aligns f_design with peak return loss.
    """
    Z0 = 50.0
    RL = 150.0
    freqs = np.linspace(800e6, 1600e6, 81)
    f_design = 1200e6

    res = match.compare_matching(Z0, RL, freqs, vf=0.66, f_design=f_design)

    # Frequency grids must be identical
    assert np.array_equal(res["before"]["f"], freqs)
    assert np.array_equal(res["after"]["f"], freqs)

    # Find the frequency closest to f_design
    idx_design = np.argmin(np.abs(freqs - f_design))
    f_closest = freqs[idx_design]
    assert abs(f_closest - f_design) < (freqs[1] - freqs[0])

    # Return loss after matching should peak at or near f_design
    rl_after = res["after"]["rl_db"]
    assert np.argmax(rl_after) == idx_design
