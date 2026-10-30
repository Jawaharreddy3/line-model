"""
core/diagnostic_explanations.py -- Physical explanation and advisory engine.

Provides comprehensive diagnostic reporting:
  - Transmission-line electromagnetic physical justifications
  - Signal evidence and rule trigger tracking
  - Potential measurement ambiguities
  - Engineering corrective action recommendations
"""

__all__ = [
    "generate_full_diagnostic_report",
]


def generate_full_diagnostic_report(diag_result, Z0, vf=1.0):
    """
    Generate an academic-grade diagnostic report for faculty review.

    Parameters
    ----------
    diag_result : DiagnosisResult instance (from diagnosis.classify)
    Z0          : characteristic impedance [ohm]
    vf          : velocity factor

    Returns
    -------
    dict with:
        category           : public contract classification string
        subtype            : specific physical subtype
        confidence         : confidence level
        evidence           : list of observed signal metrics
        rules_triggered    : list of rules fired
        physics_explanation: transmission-line theory derivation
        ambiguities        : potential failure modes or ambiguities
        corrective_actions : suggested field/lab remedial procedures
    """
    label = str(diag_result)
    subtype = getattr(diag_result, "subtype", label)
    confidence = getattr(diag_result, "confidence", "medium")
    feat = getattr(diag_result, "features", {})
    rules = getattr(diag_result, "rules_fired", [])

    mm = feat.get("mag_mean", 0.0)
    ms = feat.get("mag_std", 0.0)
    tr = feat.get("trend", 0.0)
    lf_re = feat.get("lf_real", 0.0)
    de_im = feat.get("deembedded_imag", 0.0)

    evidence = [
        f"Mean reflection magnitude |Gamma|: {mm:.4f}",
        f"Reflection magnitude standard deviation: {ms:.4f}",
        f"High-frequency vs low-frequency magnitude trend: {tr:+.4f}",
        f"Low-frequency real reflection Re(Gamma[0]): {lf_re:+.4f}",
    ]

    ambiguities = []
    corrective_actions = []
    physics_explanation = ""

    if label == "healthy":
        physics_explanation = (
            f"The line is terminated in an impedance closely matched to Z0 = {Z0} Ω. "
            "According to the reflection coefficient equation Gamma = (ZL - Z0)/(ZL + Z0), "
            "when ZL = Z0, the reflected wave amplitude is identically zero (|Gamma| = 0). "
            "All incident power is transferred to the load; VSWR = 1.0 and Return Loss -> infinity."
        )
        ambiguities.append("A matched line with high distributed attenuation could look matched even if terminated incorrectly.")
        corrective_actions.append("No action required. Line is operating at peak transmission efficiency.")

    elif label == "open":
        physics_explanation = (
            f"An open-circuit termination (ZL -> infinity) forces the terminal boundary current to zero. "
            "From boundary conditions, the voltage wave reflects in-phase (Gamma_L = +1.0 + 0j). "
            "Total reflection occurs across all frequencies (|Gamma| = 1.0, VSWR -> infinity, Return Loss = 0 dB). "
            "The observed positive real reflection verifies that the terminal voltage wave undergoes zero phase inversion."
        )
        ambiguities.append("A high-impedance load (RL > 10*Z0) produces near-total in-phase reflection that resembles an open circuit.")
        corrective_actions.extend([
            "Inspect line termination for severed conductors, disconnected SMA/BNC plugs, or broken solder joints.",
            "Verify center pin seating in coaxial receptacle.",
        ])

    elif label == "short":
        physics_explanation = (
            f"A short-circuit termination (ZL = 0 Ω) forces the terminal boundary voltage to zero. "
            "From boundary conditions, the voltage wave reflects with a 180° phase inversion (Gamma_L = -1.0 + 0j). "
            "Total reflection occurs across all frequencies (|Gamma| = 1.0, VSWR -> infinity, Return Loss = 0 dB). "
            "The observed negative real reflection confirms that the terminal boundary voltage is clamped to ground."
        )
        ambiguities.append("A very large shunt capacitance (> 50 pF) at microwave frequencies acts as a virtual RF short circuit.")
        corrective_actions.extend([
            "Check for metallic whiskers, crimp short-circuits, or dielectric punch-through across inner and outer conductors.",
            "Test DC isolation with a digital multimeter before RF re-energization.",
        ])

    elif label == "mismatch":
        if subtype == "series_L":
            physics_explanation = (
                f"A series inductive discontinuity (Zs = j*omega*L) introduces frequency-dependent series impedance. "
                "At low frequencies, omega*L is negligible and the line appears transparent (|Gamma| -> 0). "
                "As frequency increases, inductive reactance XL = omega*L rises linearly, increasing the reflection magnitude. "
                "The de-embedded reflection plane exhibits positive imaginary phase (inductive upper half of Smith chart)."
            )
            ambiguities.append("Cracked connector solder joints or pinched center pins frequently manifest as parasitic series inductances.")
            corrective_actions.extend([
                "Inspect cable at estimated fault distance for physical crushing, excessive bend radius, or connector neck necking.",
                "Tighten or replace the intermediate coaxial connector with a calibrated torque wrench.",
            ])
        elif subtype == "shunt_C":
            physics_explanation = (
                f"A shunt capacitive discontinuity (Yp = j*omega*C) introduces frequency-dependent shunt admittance. "
                "At low frequencies, capacitive susceptance BC = omega*C is negligible (|Gamma| -> 0). "
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
                f"A resistive load mismatch (ZL = RL != Z0) produces a frequency-independent load reflection magnitude "
                f"|Gamma_L| = |(RL - Z0)/(RL + Z0)|. For a lossless line, the input reflection magnitude |Gamma_in(f)| "
                "remains strictly constant across frequency, while its phase rotates uniformly with electrical length theta = 2*beta*l."
            )
            ambiguities.append("A mismatched termination cannot be located using phase alone without frequency sweep bandwidth.")
            corrective_actions.extend([
                "Synthesize a quarter-wave transformer (Zt = sqrt(Z0*RL)) at the operating frequency.",
                "Alternatively, install a single-stub or broadband multi-section matching network.",
            ])

    else:
        physics_explanation = (
            "The measured reflection signature does not match any of the five canonical transmission-line failure patterns. "
            "High noise, distributed attenuation, or overlapping multiple discontinuities may be present."
        )
        ambiguities.append("Complex multi-fault interactions cannot be resolved by single-port reflectometry alone.")
        corrective_actions.extend([
            "Increase frequency sweep span B to improve temporal range resolution.",
            "Averaging multiple sweeps to reduce measurement noise variance.",
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
