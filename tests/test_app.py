import os
import sys
import numpy as np
import pytest

import line_model as lm
import measurements as meas
import fault_simulation as fs
import diagnosis as diag
import matching as match


def test_app_core_integration_pipeline():
    """
    Test the entire computation pipeline that app.py executes.
    Verifies that all modules integrate seamlessly without UI dependency.
    """
    Z0 = 50.0
    length = 1.2
    vf = 0.66
    freqs = np.linspace(500e6, 3000e6, 200)

    # 1. Simulate fault
    sim = fs.simulate_fault("mismatch", Z0, length, freqs, vf=vf, ZL_mismatch=100.0)
    sweep_dict = sim["sweep"]

    # 2. Check measurement keys
    for k in ["f", "zin", "gamma", "vswr", "rl_db"]:
        assert k in sweep_dict

    # 3. Classify
    res = diag.classify(sweep_dict, Z0)
    assert res == "mismatch"
    assert res.subtype == "resistive_mismatch"
    assert res.confidence in ["high", "medium", "low"]

    # 4. Estimate distance
    d_est = diag.estimate_distance(sweep_dict, vf, res)
    assert d_est is not None
    assert abs(d_est - length) < 0.15

    # 5. Range resolution
    res_info = diag.distance_resolution(sweep_dict, vf=vf)
    assert res_info["range_res"] > 0
    assert res_info["unambig_range"] > 0

    # 6. Matching Studio
    matched = match.compare_matching(Z0, 100.0, freqs, vf=vf)
    assert matched["Zt"] == pytest.approx(np.sqrt(50 * 100))
    assert matched["at_f_design"]["vswr"] == pytest.approx(1.0, abs=1e-12)


def test_app_imports_cleanly():
    import app
    assert app is not None


@pytest.mark.parametrize("nav_view", [
    "Simulation",
    "Diagnosis",
    "Fault Location",
    "Impedance Matching",
    "Results",
])
def test_streamlit_app_views_navigation(nav_view):
    """
    Exercise each of the 5 Streamlit navigation views via AppTest.
    Verifies that all views render cleanly without exceptions.
    """
    from streamlit.testing.v1 import AppTest

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(root_dir, "app.py")
    at = AppTest.from_file(app_path, default_timeout=30)
    at.run()
    at.sidebar.radio[0].set_value(nav_view).run()
    assert len(at.exception) == 0, f"View '{nav_view}' raised exceptions: {[e.value for e in at.exception]}"


@pytest.mark.parametrize("fault_condition", [
    "Healthy line",
    "Resistive mismatch",
    "Open circuit",
    "Short circuit",
    "Series inductance",
    "Shunt capacitance",
])
def test_streamlit_app_fault_scenarios(fault_condition):
    """
    Exercise each of the 6 fault conditions in the Streamlit app.
    Verifies that all conditions simulate properly and update output.
    """
    from streamlit.testing.v1 import AppTest

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(root_dir, "app.py")
    at = AppTest.from_file(app_path, default_timeout=30)
    at.run()
    at.sidebar.selectbox[0].set_value(fault_condition).run()
    at.sidebar.button[0].click().run()
    assert len(at.exception) == 0, f"Condition '{fault_condition}' raised exceptions: {[e.value for e in at.exception]}"


def test_no_emojis_in_app_code():
    """Verify that app.py contains zero emojis or decorative unicode icons."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(root_dir, "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        content = f.read()

    for i, ch in enumerate(content):
        code = ord(ch)
        is_emoji = (
            (0x1F300 <= code <= 0x1FAD6) or
            (0x1F900 <= code <= 0x1F9FF) or
            (0x2600 <= code <= 0x26FF) or
            (0x2700 <= code <= 0x27BF) or
            (0x1F600 <= code <= 0x1F64F)
        )
        assert not is_emoji, f"Found forbidden emoji character '{ch}' (U+{code:04X}) at index {i}"
