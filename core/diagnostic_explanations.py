"""
core/diagnostic_explanations.py -- Academic-grade physics explanations for diagnostic decisions.

Generates clear electromagnetic justifications, lists observed signal features,
warns about known measurement ambiguities, and suggests actionable engineering next steps.
Adheres to EC-3104 syllabus guidelines (phasor domain, boundary reflection, Smith chart).
"""

from typing import Dict, Any, List


__all__ = [
    "generate_full_diagnostic_report",
]


def generate_full_diagnostic_report(diag_result, Z0: float, vf: float = 1.0) -> Dict[str, Any]:
    """
    Generate an academic-grade diagnostic report explaining why a transmission line
    was classified into a particular state.

    Parameters
    ----------
    diag_result : DiagnosisResult
        Result object returned by diagnosis.classify().
    Z0 : float
        Characteristic impedance in ohms.
    vf : float
        Velocity factor (relative to speed of light c0).

    Returns
    -------
    dict
        Dictionary containing:
          - 'category': public contract classification string
          - 'subtype': specific physical subtype
          - 'confidence': confidence level
          - 'rules_triggered': list of rules fired
          - 'physics_explanation': str, rigorous EM theory explanation with proper LaTeX math.
          - 'evidence': list of str, bullet points of observed signals.
          - 'ambiguities': list of str, limitations and alternate physical causes.
          - 'corrective_actions': list of str, actionable lab/bench procedures.
    """
    label = str(diag_result)
    subtype = getattr(diag_result, "subtype", "uncertain")
    confidence = getattr(diag_result, "confidence", "medium")
    feat = getattr(diag_result, "features", {})
    rules = getattr(diag_result, "rules_fired", [])

    mm = feat.get("mag_mean", 0.0)
    ms = feat.get("mag_std", 0.0)
    tr = feat.get("trend", 0.0)
    lf_re = feat.get("lf_real", 0.0)
    de_im = feat.get("deembedded_imag", 0.0)

    evidence = [
        f"Mean reflection magnitude $|\\Gamma|$: {mm:.4f}",
        f"Reflection magnitude standard deviation $\\sigma_{{|\\Gamma|}}$: {ms:.4f}",
        f"High-frequency vs low-frequency magnitude trend: {tr:+.4f}",
        f"Low-frequency real reflection $\\operatorname{{Re}}(\\Gamma_0)$: {lf_re:+.4f}",
    ]

    ambiguities = []
    corrective_actions = []
    physics_explanation = ""

    if label == "healthy":
        physics_explanation = (
            f"The line is terminated in an impedance closely matched to $Z_0 = {Z0:.1f}\\ \\Omega$. "
            "According to the reflection coefficient equation $\\Gamma = (Z_L - Z_0)/(Z_L + Z_0)$, "
            "when $Z_L = Z_0$, the reflected wave amplitude is identically zero ($|\\Gamma| = 0$). "
            "All incident power is transferred to the load; $\\text{VSWR} = 1.0$ and $\\text{Return Loss} \\to \\infty$."
        )
        ambiguities.append("A matched line with high distributed attenuation could look matched even if terminated incorrectly.")
        corrective_actions.append("No action required. Line is operating at peak transmission efficiency.")

    elif label == "open":
        physics_explanation = (
            "An open-circuit termination ($Z_L \\to \\infty$) forces the terminal boundary current to zero. "
            "From boundary conditions, the voltage wave reflects in-phase ($\\Gamma_L = +1.0$). "
            "Total reflection occurs across all frequencies ($|\\Gamma| = 1.0$, $\\text{VSWR} \\to \\infty$, $\\text{Return Loss} = 0\\text{ dB}$). "
            "The observed positive real reflection verifies that the terminal voltage wave undergoes zero phase inversion."
        )
        ambiguities.append("A high-impedance load ($R_L > 10\\,Z_0$) produces near-total in-phase reflection that resembles an open circuit.")
        corrective_actions.extend([
            "Inspect line termination for severed conductors, disconnected SMA/BNC plugs, or broken solder joints.",
            "Verify center pin seating in coaxial receptacle.",
        ])

    elif label == "short":
        physics_explanation = (
            f"A short-circuit termination ($Z_L = 0\\ \\Omega$) forces the terminal boundary voltage to zero. "
            "From boundary conditions, the voltage wave reflects with a $180^\\circ$ phase inversion ($\\Gamma_L = -1.0$). "
            "Total reflection occurs across all frequencies ($|\\Gamma| = 1.0$, $\\text{VSWR} \\to \\infty$, $\\text{Return Loss} = 0\\text{ dB}$). "
            "The observed negative real reflection confirms that the terminal boundary voltage is clamped to ground."
        )
        ambiguities.append("A very large shunt capacitance ($C > 50\\text{ pF}$) at microwave frequencies acts as a virtual RF short circuit.")
        corrective_actions.extend([
            "Check for metallic whiskers, crimp short-circuits, or dielectric punch-through across inner and outer conductors.",
            "Test DC isolation with a digital multimeter before RF re-energization.",
        ])

    elif label == "mismatch":
        if subtype == "series_L":
            physics_explanation = (
                "A series inductive discontinuity ($Z_s = j\\omega L$) introduces frequency-dependent series impedance. "
                "At low frequencies, $\\omega L$ is negligible and the line appears transparent ($|\\Gamma| \\to 0$). "
                "As frequency increases, inductive reactance $X_L = \\omega L$ rises linearly, increasing the reflection magnitude. "
                "The de-embedded reflection plane exhibits positive imaginary phase (inductive upper half of Smith chart)."
            )
            ambiguities.append("Cracked connector solder joints or pinched center pins frequently manifest as parasitic series inductances.")
            corrective_actions.extend([
                "Inspect cable at estimated fault distance for physical crushing, excessive bend radius, or connector neck necking.",
                "Tighten or replace the intermediate coaxial connector with a calibrated torque wrench.",
            ])
        elif subtype == "shunt_C":
            physics_explanation = (
                "A shunt capacitive discontinuity ($Y_p = j\\omega C$) introduces frequency-dependent shunt admittance. "
                "At low frequencies, capacitive susceptance $B_C = \\omega C$ is negligible ($|\\Gamma| \\to 0$). "
                "As frequency increases, the shunt branch draws increasing displacement current, causing reflection to rise. "
                "The de-embedded reflection plane exhibits negative imaginary phase (capacitive lower half of Smith chart)."
            )
            ambiguities.append("Moisture ingress or dielectric contamination increases local permittivity, manifesting as shunt capacitance.")
            corrective_actions.extend([
                "Inspect the line for water ingress, dielectric crushing, or metal swarf across transmission paths.",
                "Dry out the coaxial section or replace the degraded cable segment.",
            ])
        else:
            physics_explanation = (
                f"A resistive load mismatch ($Z_L = R_L \\ne Z_0$) produces a frequency-independent load reflection magnitude "
                f"$|\\Gamma_L| = |(R_L - Z_0)/(R_L + Z_0)|$. For a lossless line, the input reflection magnitude $|\\Gamma_{{\\text{{in}}}}(f)|$ "
                "remains strictly constant across frequency, while its phase rotates uniformly with electrical length $\\theta = 2\\beta l$."
            )
            ambiguities.append("A mismatched termination cannot be located using phase alone without frequency sweep bandwidth.")
            corrective_actions.extend([
                "Synthesize a quarter-wave transformer ($Z_t = \\sqrt{Z_0 R_L}$) at the operating frequency.",
                "Alternatively, install a single-stub or broadband multi-section matching network.",
            ])

    else:
        physics_explanation = (
            "The measured reflection signature does not match any of the five canonical transmission-line failure patterns. "
            "High noise, distributed attenuation, or overlapping multiple discontinuities may be present."
        )
        ambiguities.append("Complex multi-fault interactions cannot be resolved by single-port reflectometry alone.")
        corrective_actions.extend([
            "Check connection integrity and verify line continuity with a calibrated VNA.",
            "Increase frequency sweep points or average multiple sweeps to suppress measurement noise.",
        ])

    return {
        "category": label,
        "subtype": subtype,
        "confidence": confidence,
        "evidence": evidence,
        "rules_triggered": rules,
        "physics_explanation": physics_explanation,
        "ambiguities": ambiguities,
        "corrective_actions": corrective_actions,
    }
