"""
tests/conftest.py -- Shared pytest fixtures, path setup, and analytical tolerances.
"""

import sys
import pathlib
import pytest
import numpy as np

# Ensure project root is in sys.path
ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure Matplotlib uses non-interactive backend for headless test execution
import matplotlib
matplotlib.use("Agg")


@pytest.fixture
def c0():
    """Exact speed of light in vacuum [m/s]."""
    return 299792458.0


@pytest.fixture
def default_line_params(c0):
    """Canonical test parameters for coaxial line."""
    return {
        "Z0": 50.0,
        "length": 1.0,
        "vf": 0.66,
        "vp": 0.66 * c0,
    }


@pytest.fixture
def standard_freq_sweep():
    """Standard 500 MHz to 2500 MHz sweep with 201 points."""
    return np.linspace(500e6, 2500e6, 201)


@pytest.fixture
def broadband_freq_sweep():
    """Broadband 100 MHz to 4000 MHz sweep with 400 points."""
    return np.linspace(100e6, 4000e6, 400)


@pytest.fixture
def numerical_tolerances():
    """
    Justified numerical tolerances for automated benchmarks:
    - algebraic: tight tolerance for direct formula evaluations (1e-12)
    - float_rel: relative float64 roundoff precision (1e-7)
    - ifft_distance_m: IFFT TDR peak grid bin resolution limit (0.02 m = 2 cm)
    """
    return {
        "algebraic": 1e-12,
        "float_rel": 1e-7,
        "ifft_distance_m": 0.02,
    }
