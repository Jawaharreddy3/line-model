import numpy as np
import pytest

import line_model as lm
import measurements as meas
import matching as match

Z0 = 50.0
F0 = 100e6
VF = 1.0


def test_hand_calculation_transformer_50_to_200():
    # HAND_CALCULATIONS: Item 6 (50 -> 200 ohm: Zt = 100 ohm, lt = 0.75 m at 100 MHz, vf=1)
    res = match.design_quarter_wave(Z0, 200.0, F0, vf=VF)
    assert res["Zt"] == pytest.approx(100.0, rel=1e-9)
    # Exact c0 gives 0.74948 m, rounding to 0.75 m
    assert res["length_m"] == pytest.approx(lm.wavelength(F0, VF) / 4.0, rel=1e-9)
    assert res["length_m"] == pytest.approx(0.75, rel=1e-3)


def test_exact_match_at_design_frequency():
    freqs = np.linspace(80e6, 120e6, 41)
    res = match.compare_matching(Z0, 100.0, freqs, vf=VF, f_design=F0)

    # At f_design, matching must be exact
    f0_metrics = res["at_f_design"]
    assert f0_metrics["gamma"] == pytest.approx(0.0, abs=1e-12)
    assert f0_metrics["vswr"] == pytest.approx(1.0, abs=1e-12)
    assert np.isinf(f0_metrics["rl_db"])

    # Transformer params
    assert res["Zt"] == pytest.approx(np.sqrt(50 * 100))
    assert res["bandwidth_hz"] > 0


def test_compare_matching_contract_keys():
    freqs = np.linspace(80e6, 120e6, 41)
    res = match.compare_matching(Z0, 100.0, freqs, vf=VF, f_design=F0)

    assert "before" in res
    assert "after" in res
    for k in ["f", "zin", "gamma", "vswr", "rl_db"]:
        assert k in res["before"]
        assert k in res["after"]


def test_reject_complex_load():
    freqs = np.linspace(80e6, 120e6, 21)
    with pytest.raises(ValueError, match="real load resistance"):
        match.compare_matching(Z0, 50.0 + 25j, freqs, vf=VF)

    with pytest.raises(ValueError, match="purely real"):
        match.design_quarter_wave(Z0, 50.0 + 25j, F0, vf=VF)


def test_reject_negative_or_zero_load():
    with pytest.raises(ValueError):
        match.design_quarter_wave(Z0, -50.0, F0, vf=VF)

    with pytest.raises(ValueError):
        match.design_quarter_wave(Z0, 0.0, F0, vf=VF)


def test_usable_bandwidth_behavior():
    freqs = np.linspace(50e6, 150e6, 201)
    # 20 dB threshold: compare 60 ohm load vs 200 ohm load
    # Larger mismatch has narrower bandwidth
    res_small_mismatch = match.compare_matching(
        Z0, 60.0, freqs, vf=VF, f_design=F0, rl_threshold=20.0
    )
    res_large_mismatch = match.compare_matching(
        Z0, 200.0, freqs, vf=VF, f_design=F0, rl_threshold=20.0
    )

    assert res_small_mismatch["bandwidth_hz"] > res_large_mismatch["bandwidth_hz"]
