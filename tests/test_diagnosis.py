import numpy as np
import pytest

import line_model as lm
import measurements as meas
import fault_simulation as fs
import diagnosis as diag

Z0 = 50.0
VF = 0.66
FREQS = np.linspace(500e6, 4e9, 400)


def test_classify_healthy_matched():
    sim = fs.simulate_fault("healthy", Z0, 1.0, FREQS, vf=VF)
    res = diag.classify(sim["sweep"], Z0)
    assert res == "healthy"
    assert res in diag.CLASSIFICATION_LABELS
    assert res.subtype == "matched"
    assert res.confidence == "high"


def test_classify_resistive_mismatch():
    sim = fs.simulate_fault("mismatch", Z0, 1.0, FREQS, vf=VF, ZL_mismatch=120.0)
    res = diag.classify(sim["sweep"], Z0)
    assert res == "mismatch"
    assert res in diag.CLASSIFICATION_LABELS
    assert res.subtype == "resistive_mismatch"


def test_classify_open_circuit():
    sim = fs.simulate_fault("open", Z0, 1.0, FREQS, vf=VF)
    res = diag.classify(sim["sweep"], Z0)
    assert res == "open"
    assert res in diag.CLASSIFICATION_LABELS
    assert res.subtype == "open_circuit"


def test_classify_short_circuit():
    sim = fs.simulate_fault("short", Z0, 1.0, FREQS, vf=VF)
    res = diag.classify(sim["sweep"], Z0)
    assert res == "short"
    assert res in diag.CLASSIFICATION_LABELS
    assert res.subtype == "short_circuit"


def test_classify_series_inductive_discontinuity():
    sim = fs.simulate_fault(
        "series_L", Z0, 1.0, FREQS, vf=VF, L_val=15e-9, fault_pos=0.4
    )
    res = diag.classify(sim["sweep"], Z0)
    assert res == "mismatch"
    assert res in diag.CLASSIFICATION_LABELS
    assert res.subtype == "series_L"


def test_classify_shunt_capacitive_discontinuity():
    sim = fs.simulate_fault(
        "shunt_C", Z0, 1.0, FREQS, vf=VF, C_val=15e-12, fault_pos=0.6
    )
    res = diag.classify(sim["sweep"], Z0)
    assert res == "mismatch"
    assert res in diag.CLASSIFICATION_LABELS
    assert res.subtype == "shunt_C"


def test_estimate_distance_healthy_returns_none():
    sim = fs.simulate_fault("healthy", Z0, 1.0, FREQS, vf=VF)
    d = diag.estimate_distance(sim["sweep"], VF, "healthy")
    assert d is None


def test_estimate_distance_against_known_fault_positions():
    # Sweep from 1 GHz to 5 GHz (B = 4 GHz)
    # Range resolution delta_R = vp / (2 * B) = (0.66 * 3e8) / (2 * 4e9) = 0.02475 m (~2.5 cm)
    freqs = np.linspace(1e9, 5e9, 500)
    res_info = diag.distance_resolution({"f": freqs}, vf=VF)
    delta_r = res_info["range_res"]
    assert delta_r < 0.03  # better than 3 cm resolution

    test_lengths = [0.3, 0.7, 1.2]
    for true_pos in test_lengths:
        sim = fs.simulate_fault("open", Z0, true_pos, freqs, vf=VF)
        d_est = diag.estimate_distance(sim["sweep"], VF, "open")
        assert d_est is not None
        abs_error = abs(d_est - true_pos)
        # Error must be within range resolution
        assert abs_error <= 1.5 * delta_r, (
            f"True {true_pos} m vs Est {d_est} m: error {abs_error:.4f} m > 1.5*delta_r ({delta_r:.4f} m)"
        )


def test_estimate_distance_series_L_intermediate():
    freqs = np.linspace(1e9, 5e9, 500)
    res_info = diag.distance_resolution({"f": freqs}, vf=VF)
    delta_r = res_info["range_res"]

    true_fault_pos = 0.45
    sim = fs.simulate_fault(
        "series_L", Z0, 1.0, freqs, vf=VF, L_val=20e-9, fault_pos=true_fault_pos
    )
    d_est = diag.estimate_distance(sim["sweep"], VF, "mismatch")
    assert d_est is not None
    assert abs(d_est - true_fault_pos) <= 2.0 * delta_r


def test_non_uniform_frequency_resampling():
    # Construct non-uniform frequency grid
    f_uniform = np.linspace(1e9, 5e9, 400)
    jitter = np.sin(np.linspace(0, 10, 400)) * 5e6
    f_non_uniform = f_uniform + jitter
    f_non_uniform = np.sort(f_non_uniform)

    sim = fs.simulate_fault("short", Z0, 0.8, f_non_uniform, vf=VF)
    d_est = diag.estimate_distance(sim["sweep"], VF, "short")
    assert d_est is not None
    # Still resolves close to 0.8 m
    assert abs(d_est - 0.8) < 0.08


@pytest.mark.parametrize("vf_val", [0.66, 0.70, 1.0])
@pytest.mark.parametrize("length_val", [0.4, 0.9, 1.8])
@pytest.mark.parametrize("scenario_val,expected_label", [("open", "open"), ("short", "short")])
def test_open_vs_short_separation_across_vf_and_lengths(vf_val, length_val, scenario_val, expected_label):
    freqs = np.linspace(400e6, 3.5e9, 250)
    rng = np.random.default_rng(42)
    sim = fs.simulate_fault(
        scenario_val,
        Z0=50.0,
        length=length_val,
        f_array=freqs,
        vf=vf_val,
        noise_std=0.02,
        rng=rng,
    )
    res = diag.classify(sim["sweep"], 50.0)
    assert res == expected_label, (
        f"Failed for {scenario_val} at vf={vf_val}, length={length_val}m: got {res} (cos_phi0={res.features.get('cos_phi0')})"
    )
    assert res.subtype == f"{expected_label}_circuit"


def test_diagnosis_validation_and_boundaries():
    # 1. Invalid Z0 in classify
    with pytest.raises(ValueError, match="positive real part"):
        diag.classify({"f": np.array([100e6, 200e6]), "gamma": np.array([0.1, 0.2])}, -50.0)

    with pytest.raises(ValueError, match="positive real part"):
        diag.classify({"f": np.array([100e6, 200e6]), "gamma": np.array([0.1, 0.2])}, 0.0)

    # 2. Missing contract keys
    with pytest.raises(KeyError, match="must contain 'f' and 'gamma'"):
        diag.classify({"f": np.array([100e6])}, 50.0)

    # 3. Empty sweep data safely returns "unknown" without crashing
    res_empty = diag.classify({"f": np.array([]), "gamma": np.array([])}, 50.0)
    assert res_empty == "unknown"
    assert res_empty.subtype == "uncertain"

    # 4. Non-finite (NaN / Inf) sweep data returns "unknown"
    res_nan = diag.classify({"f": np.array([100e6, 200e6]), "gamma": np.array([np.nan, 0.2])}, 50.0)
    assert res_nan == "unknown"
    assert "non-finite" in res_nan.explanation

    # 5. Invalid velocity factor in estimate_distance and distance_resolution
    with pytest.raises(ValueError, match="velocity factor"):
        diag.estimate_distance({"f": np.array([100e6, 200e6, 300e6, 400e6]), "gamma": np.zeros(4)}, vf=0.0, fault_class="mismatch")

    with pytest.raises(ValueError, match="velocity factor"):
        diag.distance_resolution({"f": np.array([100e6, 200e6])}, vf=1.5)

    # 6. Boundary conditions for distance_resolution
    res_few = diag.distance_resolution({"f": np.array([100e6])}, vf=1.0)
    assert np.isnan(res_few["range_res"])
    assert res_few["bandwidth_hz"] == 0.0


@pytest.mark.parametrize("zl_mismatch,expected_desc", [
    (500.0, "High resistance 500 ohm (|Gamma|=0.818)"),
    (1000.0, "High resistance 1000 ohm (|Gamma|=0.905)"),
    (2000.0, "High resistance 2000 ohm (|Gamma|=0.951)"),
    (5.0, "Low resistance 5 ohm (|Gamma|=0.818)"),
    (2.5, "Low resistance 2.5 ohm (|Gamma|=0.905)"),
    (1.25, "Low resistance 1.25 ohm (|Gamma|=0.951)"),
])
def test_extreme_finite_mismatches_classified_as_mismatch(zl_mismatch, expected_desc):
    """
    Verify that extreme finite resistive mismatches (|Gamma| between 0.81 and 0.96)
    are strictly classified as 'mismatch' (resistive_mismatch) and NEVER misclassified
    as 'open' or 'short'.
    """
    freqs = np.linspace(400e6, 3.5e9, 250)
    sim = fs.simulate_fault(
        "mismatch",
        Z0=50.0,
        length=1.2,
        f_array=freqs,
        vf=0.66,
        ZL_mismatch=zl_mismatch,
        noise_std=0.02,
        rng=np.random.default_rng(42),
    )
    res = diag.classify(sim["sweep"], 50.0)

    assert res == "mismatch", f"{expected_desc} was classified as {res} instead of mismatch"
    assert res.subtype == "resistive_mismatch"
    assert "R6_RESISTIVE_MISMATCH" in res.rules_fired
    assert res != "open", f"{expected_desc} was incorrectly classified as open"
    assert res != "short", f"{expected_desc} was incorrectly classified as short"


def test_abstention_insufficient_points():
    """Verify abstention to 'unknown' when frequency points N < 4."""
    freqs = np.array([500e6, 1e9, 1.5e9])
    gamma = np.array([0.5 + 0j, 0.5 + 0j, 0.5 + 0j])
    res = diag.classify({"f": freqs, "gamma": gamma}, 50.0)

    assert res == "unknown"
    assert res.subtype == "uncertain"
    assert "R_INSUFFICIENT_POINTS" in res.rules_fired


def test_abstention_insufficient_bandwidth():
    """Verify abstention to 'unknown' when frequency bandwidth B < 5 MHz."""
    freqs = np.linspace(100e6, 102e6, 50)  # B = 2 MHz < 5 MHz
    gamma = np.full(50, 0.5 + 0j)
    res = diag.classify({"f": freqs, "gamma": gamma}, 50.0)

    assert res == "unknown"
    assert res.subtype == "uncertain"
    assert "R_INSUFFICIENT_BANDWIDTH" in res.rules_fired


def test_abstention_excessive_noise():
    """Verify abstention to 'unknown' when measurement noise standard deviation > 0.20."""
    freqs = np.linspace(500e6, 3e9, 200)
    rng = np.random.default_rng(123)
    noise = rng.normal(0, 0.30, 200) + 1j * rng.normal(0, 0.30, 200)
    noisy_gamma = 0.2 + noise  # random cloud with std > 0.20
    res = diag.classify({"f": freqs, "gamma": noisy_gamma}, 50.0)

    assert res == "unknown"
    assert res.subtype == "uncertain"
    assert "R_EXCESSIVE_NOISE" in res.rules_fired


def test_abstention_ambiguous_total_reflection():
    """Verify abstention to 'unknown' when |Gamma| >= 0.975 but phase does not match open or short."""
    freqs = np.linspace(500e6, 3e9, 200)
    # 90 degree phase across band: |Gamma| = 1.0, but phase is orthogonal to open (0 deg) and short (180 deg)
    gamma = np.full(200, 0.0 + 1.0j)
    res = diag.classify({"f": freqs, "gamma": gamma}, 50.0)

    assert res == "unknown"
    assert res.subtype == "uncertain"
    assert "R4_AMBIGUOUS_TOTAL_REFL" in res.rules_fired

