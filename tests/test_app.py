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
    sb = at.selectbox[0] if len(at.selectbox) > 0 else at.sidebar.selectbox[0]
    btn = at.button[0] if len(at.button) > 0 else at.sidebar.button[0]
    sb.set_value(fault_condition).run()
    btn.click().run()
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


def test_metric_cards_rendering_and_styling():
    """
    Verify that the 6 metric cards render via responsive CSS Grid with
    proper typography, word-break controls, and no awkward splitting.
    """
    import app

    card1 = app.render_metric_card("Condition", "Series inductance", "Z0 = 50.0 Ohms")
    card2 = app.render_metric_card("Reflection |Gamma|", "0.5947", "Mean magnitude")
    card3 = app.render_metric_card("VSWR", "4.57", "At 2250 MHz")
    card4 = app.render_metric_card("Return Loss", "3.9 dB", "At 2250 MHz")
    card5 = app.render_metric_card("Input Impedance", "21.5 + j46.6", "Ohms at mid-band")
    card6 = app.render_metric_card("Fault Distance", "0.50 m", "From input")

    grid_html = app.render_metrics_grid([card1, card2, card3, card4, card5, card6])

    assert 'class="metrics-grid"' in grid_html
    assert 'class="metric-card"' in grid_html
    assert "Series inductance" in grid_html
    assert "Input Impedance" in grid_html
    assert "21.5 + j46.6" in grid_html
    assert "word-break: break-all" not in grid_html


def test_right_sidebar_layout_styling():
    """
    Verify that app.py injects the CSS required to position the
    entire navigation sidebar cleanly on the RIGHT side of the desktop screen.
    """
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(root_dir, "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Flex row-reverse on app view container
    assert '[data-testid="stAppViewContainer"]' in content
    assert "flex-direction: row-reverse !important;" in content

    # Sidebar border on left side
    assert "border-left: 1px solid #e2e8f0 !important;" in content
    assert "border-right: none !important;" in content

    # Sidebar collapse behavior and controls flipped for right-side orientation
    assert 'section[data-testid="stSidebar"][data-collapsed="true"]' in content
    assert "transform: translateX(100%) !important;" in content
    assert '[data-testid="stSidebarCollapseButton"] button' in content
    assert "transform: scaleX(-1) !important;" in content
    assert '[data-testid="stExpandSidebarButton"]' in content


def test_no_technical_details_rendered():
    """
    Verify that the Technical Details expander, internal rules triggered,
    and diagnostic debug features are completely removed from app rendering.
    """
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(root_dir, "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Technical details and rules" not in content
    assert "Rules triggered" not in content
    assert "rules_fired" not in content
    assert "st.expander" not in content


def test_left_panel_collapsible_and_expandable():
    """
    Verify that the left parameters panel can be collapsed and expanded,
    retaining parameter values and toggling layout without exceptions.
    """
    from streamlit.testing.v1 import AppTest

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(root_dir, "app.py")
    at = AppTest.from_file(app_path, default_timeout=30)
    at.run()

    # Initially open
    assert at.session_state["left_panel_open"] is True
    assert len(at.exception) == 0

    # Collapse left panel
    collapse_btn = [b for b in at.button if b.key == "btn_collapse_left"][0]
    collapse_btn.click().run()
    assert at.session_state["left_panel_open"] is False
    assert len(at.exception) == 0

    # Expand left panel
    expand_btn = [b for b in at.button if b.key == "btn_expand_left"][0]
    expand_btn.click().run()
    assert at.session_state["left_panel_open"] is True
    assert len(at.exception) == 0


def test_no_empty_params_card_div():
    """
    Verify that the unclosed/empty params-card div is completely removed
    and replaced by native container controls.
    """
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(root_dir, "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "params-card" not in content
    assert 'class="params-card"' not in content
    assert "btn_collapse_left" in content
    assert "btn_expand_left" in content



