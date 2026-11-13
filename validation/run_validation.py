"""
validation/run_validation.py -- Automated validation laboratory runner.

Generates:
  - Randomized held-out test datasets with realistic noise (documented seed = 42).
  - Empirical confusion matrix and classification metrics (Precision, Recall, F1).
  - Fault location accuracy metrics (MAE, RMSE, error distribution).
  - Noise sensitivity and bandwidth degradation studies.
  - Actual CSV outputs in results/csv/ and publication plots in results/figures/.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Ensure root is in path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import line_model as lm
import measurements as meas
import fault_simulation as fs
import diagnosis as diag
from validation.classification_metrics import (
    compute_confusion_matrix,
    compute_classification_report,
)
from validation.location_metrics import compute_location_metrics

RESULTS_CSV_DIR = os.path.join(ROOT_DIR, "results", "csv")
RESULTS_FIG_DIR = os.path.join(ROOT_DIR, "results", "figures")
os.makedirs(RESULTS_CSV_DIR, exist_ok=True)
os.makedirs(RESULTS_FIG_DIR, exist_ok=True)


def generate_heldout_dataset(n_per_class=40, seed=42, noise_std=0.02):
    """
    Generate randomized test cases covering all 6 fault scenarios.
    """
    rng = np.random.default_rng(seed)
    dataset = []

    for scenario in fs.FAULT_SCENARIOS:
        for _ in range(n_per_class):
            Z0 = float(rng.choice([50.0, 75.0]))
            length = float(rng.uniform(0.5, 2.5))
            vf = float(rng.choice([0.66, 0.70, 1.0]))
            f_start = float(rng.uniform(200e6, 600e6))
            f_stop = float(rng.uniform(3000e6, 5000e6))
            n_pts = 300
            freqs = np.linspace(f_start, f_stop, n_pts)

            fp = float(rng.uniform(0.15 * length, 0.85 * length))
            L_val = float(rng.uniform(2e-9, 40e-9))
            C_val = float(rng.uniform(2e-12, 40e-12))
            # Test standard mismatches as well as extreme finite mismatches (e.g. 500 ohm, 1000 ohm, 5 ohm, 2.5 ohm)
            ZL_mismatch = float(rng.choice([1.5 * Z0, 2.5 * Z0, 0.4 * Z0, 0.7 * Z0, 10.0 * Z0, 20.0 * Z0, 0.1 * Z0, 0.05 * Z0]))

            sim = fs.simulate_fault(
                scenario,
                Z0,
                length,
                freqs,
                vf=vf,
                fault_pos=fp,
                L_val=L_val,
                C_val=C_val,
                ZL_mismatch=ZL_mismatch,
                noise_std=noise_std,
                rng=rng,
            )

            # Ground truth target contract label
            if scenario == "healthy":
                target_label = "healthy"
                true_pos = None
            elif scenario in ["open"]:
                target_label = "open"
                true_pos = length
            elif scenario in ["short"]:
                target_label = "short"
                true_pos = length
            elif scenario in ["mismatch", "series_L", "shunt_C"]:
                target_label = "mismatch"
                true_pos = fp if scenario in ["series_L", "shunt_C"] else length
            else:
                target_label = "unknown"
                true_pos = None

            dataset.append({
                "scenario": scenario,
                "target_contract": target_label,
                "Z0": Z0,
                "length": length,
                "vf": vf,
                "true_pos": true_pos,
                "sweep": sim["sweep"],
            })

    return dataset


def generate_abstention_challenge_suite(seed=42):
    """
    Generate dedicated challenge dataset of unclassifiable, out-of-distribution,
    and ambiguous cases to evaluate classifier abstention ('unknown').

    Challenge Categories (10 cases each = 70 total):
      U1: Empty / Missing Data
      U2: Corrupted Data (NaN / Inf)
      U3: Severe Noise (sigma = 0.35, SNR < 0 dB)
      U4: Insufficient Bandwidth (B < 5 MHz)
      U5: Non-Canonical Ripple / Chaotic profiles
      U6: Ambiguous Boundary Cases (indeterminate phase / high boundary variance)
      U7: Insufficient Frequency Points (N < 4)
    """
    rng = np.random.default_rng(seed)
    suite = []

    # U1: Empty / Missing Data
    for i in range(10):
        suite.append({
            "category": "U1_empty_data",
            "description": "Empty frequency or reflection arrays",
            "sweep": {"f": np.array([]), "gamma": np.array([])},
            "Z0": 50.0,
            "target": "unknown",
        })

    # U2: Corrupted Data (NaN / Inf)
    for i in range(10):
        freqs = np.linspace(500e6, 3e9, 100)
        gamma = np.full(100, 0.2 + 0.1j)
        nan_indices = rng.choice(100, size=int(rng.integers(1, 10)), replace=False)
        gamma[nan_indices] = np.nan if i % 2 == 0 else np.inf
        suite.append({
            "category": "U2_corrupted_data",
            "description": "Sweep data containing NaN or Inf values",
            "sweep": {"f": freqs, "gamma": gamma},
            "Z0": 50.0,
            "target": "unknown",
        })

    # U3: Severe Noise (sigma = 0.35, SNR < 0 dB)
    for i in range(10):
        freqs = np.linspace(400e6, 3.5e9, 200)
        noise = rng.normal(0, 0.35, 200) + 1j * rng.normal(0, 0.35, 200)
        suite.append({
            "category": "U3_severe_noise",
            "description": "Severe noise sigma=0.35 obscuring physical signature",
            "sweep": {"f": freqs, "gamma": noise},
            "Z0": 50.0,
            "target": "unknown",
        })

    # U4: Insufficient Bandwidth (B < 5 MHz)
    for i in range(10):
        bw = float(rng.uniform(0.5e6, 4.0e6))
        f0 = float(rng.uniform(100e6, 2e9))
        freqs = np.linspace(f0, f0 + bw, 50)
        gamma = np.full(50, 0.5 + 0.2j)
        suite.append({
            "category": "U4_insufficient_bw",
            "description": f"Narrowband sweep B={bw/1e6:.2f} MHz < 5 MHz",
            "sweep": {"f": freqs, "gamma": gamma},
            "Z0": 50.0,
            "target": "unknown",
        })

    # U5: Non-Canonical Ripple / Chaotic profiles
    for i in range(10):
        freqs = np.linspace(500e6, 3e9, 200)
        mag = rng.uniform(0.1, 0.9, 200)
        phase = rng.uniform(-np.pi, np.pi, 200)
        gamma = mag * np.exp(1j * phase)
        suite.append({
            "category": "U5_non_canonical_ripple",
            "description": "Chaotic unphysical reflection profile",
            "sweep": {"f": freqs, "gamma": gamma},
            "Z0": 50.0,
            "target": "unknown",
        })

    # U6: Ambiguous Boundary Cases
    for i in range(10):
        freqs = np.linspace(500e6, 3e9, 200)
        if i % 2 == 0:
            gamma = np.full(200, 0.0 + 0.99j)  # 90 deg orthogonal phase
        else:
            noise = rng.normal(0, 0.04, 200)
            gamma = np.clip(0.955 + noise, 0, 1.0) * np.exp(1j * float(rng.uniform(0.8, 1.4)))
        suite.append({
            "category": "U6_boundary_ambiguity",
            "description": "Near-total reflection with ambiguous phase or threshold variance",
            "sweep": {"f": freqs, "gamma": gamma},
            "Z0": 50.0,
            "target": "unknown",
        })

    # U7: Insufficient Frequency Points (N < 4)
    for i in range(10):
        n_pts = int(rng.choice([1, 2, 3]))
        freqs = np.linspace(500e6, 2e9, n_pts)
        gamma = np.full(n_pts, 0.5 + 0.0j)
        suite.append({
            "category": "U7_insufficient_points",
            "description": f"Insufficient points N={n_pts} < 4",
            "sweep": {"f": freqs, "gamma": gamma},
            "Z0": 50.0,
            "target": "unknown",
        })

    return suite


def run_full_validation():
    print("=" * 80)
    print("RF LINE DOCTOR -- Independent Experimental Validation Laboratory")
    print("=" * 80)

    # 1. Generate test dataset (N = 240, 40 per scenario, noise = 0.02)
    print("Generating randomized held-out test dataset (N = 240, seed = 42, noise sigma = 0.02)...")
    dataset = generate_heldout_dataset(n_per_class=40, seed=42, noise_std=0.02)

    y_true_contract = []
    y_pred_contract = []
    y_true_scenario = []
    y_pred_subtype = []
    true_positions = []
    est_positions = []

    for item in dataset:
        sw = item["sweep"]
        Z0 = item["Z0"]
        vf = item["vf"]

        # Run classifier (SINGLE-PORT S11 ONLY)
        pred = diag.classify(sw, Z0)
        y_true_contract.append(item["target_contract"])
        y_pred_contract.append(str(pred))
        y_true_scenario.append(item["scenario"])
        y_pred_subtype.append(pred.subtype)

        # Run fault location
        if item["true_pos"] is not None:
            dist = diag.estimate_distance(sw, vf, pred)
            true_positions.append(item["true_pos"])
            est_positions.append(dist if dist is not None else np.nan)

    # 2. Compute Contract Classification Metrics (5 Frozen Classes)
    contract_labels = ["healthy", "open", "short", "mismatch", "unknown"]
    report = compute_classification_report(y_true_contract, y_pred_contract, contract_labels)
    cm = report["confusion_matrix"]

    print("\n--- Empirical Confusion Matrix (Frozen 5-Class Public Contract) ---")
    df_cm = pd.DataFrame(cm, index=[f"True: {l}" for l in contract_labels], columns=[f"Pred: {l}" for l in contract_labels])
    print(df_cm.to_string())

    cm_path = os.path.join(RESULTS_CSV_DIR, "confusion_matrix.csv")
    df_cm.to_csv(cm_path)
    print(f"Saved: {cm_path}")

    # Export Contract Classification Report
    metrics_rows = []
    for l in contract_labels:
        row = {"Class": l}
        row.update(report["per_class"][l])
        metrics_rows.append(row)
    df_metrics = pd.DataFrame(metrics_rows)
    metrics_path = os.path.join(RESULTS_CSV_DIR, "classification_metrics.csv")
    df_metrics.to_csv(metrics_path, index=False)
    print(f"\n--- Classification Metrics Summary (Overall Accuracy = {report['accuracy']*100:.2f}%) ---")
    print(df_metrics.to_string(index=False))
    print(f"Saved: {metrics_path}")

    # 2b. Compute Subtype Classification Metrics (6 Physical Scenarios)
    subtype_map = {
        "matched": "healthy",
        "resistive_mismatch": "mismatch",
        "open_circuit": "open",
        "short_circuit": "short",
        "series_L": "series_L",
        "shunt_C": "shunt_C",
        "uncertain": "unknown",
    }
    y_pred_scenario_mapped = [subtype_map.get(s, "unknown") for s in y_pred_subtype]
    scenario_labels = ["healthy", "mismatch", "open", "short", "series_L", "shunt_C"]
    subtype_report = compute_classification_report(y_true_scenario, y_pred_scenario_mapped, scenario_labels)
    cm_sub = subtype_report["confusion_matrix"]

    print("\n--- Empirical Subtype Confusion Matrix (6 Physical Scenarios) ---")
    df_cm_sub = pd.DataFrame(cm_sub, index=[f"True: {l}" for l in scenario_labels], columns=[f"Pred: {l}" for l in scenario_labels])
    print(df_cm_sub.to_string())

    cm_sub_path = os.path.join(RESULTS_CSV_DIR, "subtype_confusion_matrix.csv")
    df_cm_sub.to_csv(cm_sub_path)
    print(f"Saved: {cm_sub_path}")

    sub_metrics_rows = []
    for l in scenario_labels:
        row = {"Scenario": l}
        row.update(subtype_report["per_class"][l])
        sub_metrics_rows.append(row)
    df_sub_metrics = pd.DataFrame(sub_metrics_rows)
    sub_metrics_path = os.path.join(RESULTS_CSV_DIR, "subtype_classification_metrics.csv")
    df_sub_metrics.to_csv(sub_metrics_path, index=False)
    print(f"\n--- Subtype Classification Metrics Summary (Accuracy = {subtype_report['accuracy']*100:.2f}%) ---")
    print(df_sub_metrics.to_string(index=False))
    print(f"Saved: {sub_metrics_path}")

    # 2c. Evaluate Abstention Challenge Suite (Unclassifiable / Ambiguous Data)
    print("\n--- Evaluating Abstention Challenge Suite (70 Ambiguous / Corrupt Cases) ---")
    challenge_suite = generate_abstention_challenge_suite(seed=42)
    challenge_records = []
    category_counts = {}
    category_abstained = {}

    for ch in challenge_suite:
        pred_res = diag.classify(ch["sweep"], ch["Z0"])
        pred_str = str(pred_res)
        cat = ch["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1
        is_abstained = (pred_str == "unknown")
        if is_abstained:
            category_abstained[cat] = category_abstained.get(cat, 0) + 1

        challenge_records.append({
            "category": cat,
            "description": ch["description"],
            "target": ch["target"],
            "predicted": pred_str,
            "subtype": pred_res.subtype,
            "abstained_as_unknown": is_abstained,
            "rules_fired": ";".join(pred_res.rules_fired),
        })

    df_challenge = pd.DataFrame(challenge_records)
    challenge_csv_path = os.path.join(RESULTS_CSV_DIR, "abstention_challenge_results.csv")
    df_challenge.to_csv(challenge_csv_path, index=False)
    print(f"Saved: {challenge_csv_path}")

    # Compute per-category breakdown
    breakdown_rows = []
    for cat in sorted(category_counts.keys()):
        total_c = category_counts[cat]
        abst_c = category_abstained.get(cat, 0)
        breakdown_rows.append({
            "Challenge_Category": cat,
            "Total_Cases": total_c,
            "Abstained_Unknown": abst_c,
            "Abstention_Rate_Pct": (abst_c / total_c) * 100.0,
        })
    df_breakdown = pd.DataFrame(breakdown_rows)
    print("\n--- Abstention Performance Breakdown by Category ---")
    print(df_breakdown.to_string(index=False))

    total_challenge = len(challenge_suite)
    total_abstained = sum(category_abstained.values())
    abstention_recall = (total_abstained / total_challenge) * 100.0
    print(f"\nOverall Abstention Recall on Challenge Suite: {total_abstained}/{total_challenge} ({abstention_recall:.1f}%)")

    # False abstentions on valid physical lines
    false_abstentions = sum(1 for p in y_pred_contract if p == "unknown")
    false_abstention_rate = (false_abstentions / len(dataset)) * 100.0
    coverage_physical = 100.0 - false_abstention_rate
    print(f"False Abstentions on Physical Cases: {false_abstentions}/{len(dataset)} ({false_abstention_rate:.2f}%)")
    print(f"Coverage on Physical Dataset: {coverage_physical:.2f}%")

    # 3. Compute Fault Location Metrics
    loc_metrics = compute_location_metrics(true_positions, est_positions)
    print("\n--- Fault Location Performance (IFFT Reflectometry) ---")
    print(f"Valid Comparisons : {loc_metrics['valid_count']} / {len(true_positions)}")
    print(f"Mean Absolute Error: {loc_metrics['mae_m']*100:.2f} cm")
    print(f"Root Mean Sq Error : {loc_metrics['rmse_m']*100:.2f} cm")
    print(f"Max Absolute Error : {loc_metrics['max_err_m']*100:.2f} cm")

    df_loc = pd.DataFrame({
        "true_pos_m": true_positions,
        "est_pos_m": est_positions,
        "abs_error_cm": loc_metrics["errors_cm"],
    })
    loc_csv_path = os.path.join(RESULTS_CSV_DIR, "location_errors.csv")
    df_loc.to_csv(loc_csv_path, index=False)
    print(f"Saved: {loc_csv_path}")

    # 4. Noise Sensitivity Study (Accuracy vs Noise Sigma)
    print("\nRunning Noise Sensitivity Study...")
    noise_sigmas = [0.0, 0.02, 0.05, 0.08, 0.12, 0.18]
    acc_vs_noise = []

    for n_sigma in noise_sigmas:
        ds_noise = generate_heldout_dataset(n_per_class=20, seed=100 + int(n_sigma * 100), noise_std=n_sigma)
        c_true = [it["target_contract"] for it in ds_noise]
        c_pred = [str(diag.classify(it["sweep"], it["Z0"])) for it in ds_noise]
        rep = compute_classification_report(c_true, c_pred, contract_labels)
        acc_vs_noise.append(rep["accuracy"] * 100.0)

    df_noise = pd.DataFrame({"noise_sigma": noise_sigmas, "accuracy_pct": acc_vs_noise})
    noise_csv_path = os.path.join(RESULTS_CSV_DIR, "noise_sensitivity.csv")
    df_noise.to_csv(noise_csv_path, index=False)
    print(df_noise.to_string(index=False))
    print(f"Saved: {noise_csv_path}")

    # ── Figure 1: Confusion Matrix Heatmap ────────────────────────────────────
    fig_cm, ax_cm = plt.subplots(figsize=(7, 6))
    im = ax_cm.imshow(cm, cmap="Blues", interpolation="nearest")
    ax_cm.set_xticks(range(len(contract_labels)))
    ax_cm.set_yticks(range(len(contract_labels)))
    ax_cm.set_xticklabels(contract_labels, rotation=45, ha="right")
    ax_cm.set_yticklabels(contract_labels)
    ax_cm.set_xlabel("Predicted Contract Class")
    ax_cm.set_ylabel("Ground-Truth Class")
    ax_cm.set_title(f"Confusion Matrix (N = {report['total_samples']}, Acc = {report['accuracy']*100:.1f}%)")
    plt.colorbar(im, ax=ax_cm, label="Sample Count")

    # Annotate counts inside cells
    for i in range(len(contract_labels)):
        for j in range(len(contract_labels)):
            val = cm[i, j]
            color = "white" if val > cm.max() / 2 else "black"
            ax_cm.text(j, i, str(val), ha="center", va="center", color=color, fontweight="bold")

    plt.tight_layout()
    f_cm_path = os.path.join(RESULTS_FIG_DIR, "confusion_matrix.png")
    fig_cm.savefig(f_cm_path, dpi=150)
    plt.close(fig_cm)
    print(f"Saved figure: {f_cm_path}")

    # ── Figure 1b: Subtype Confusion Matrix Heatmap (6 Scenarios) ────────────
    fig_sub, ax_sub = plt.subplots(figsize=(7.5, 6))
    im_sub = ax_sub.imshow(cm_sub, cmap="Blues", interpolation="nearest")
    ax_sub.set_xticks(range(len(scenario_labels)))
    ax_sub.set_yticks(range(len(scenario_labels)))
    ax_sub.set_xticklabels(scenario_labels, rotation=45, ha="right")
    ax_sub.set_yticklabels(scenario_labels)
    ax_sub.set_xlabel("Predicted Physical Scenario")
    ax_sub.set_ylabel("Ground-Truth Scenario")
    ax_sub.set_title(f"Subtype Confusion Matrix (N = {subtype_report['total_samples']}, Acc = {subtype_report['accuracy']*100:.1f}%)")
    plt.colorbar(im_sub, ax=ax_sub, label="Sample Count")

    for i in range(len(scenario_labels)):
        for j in range(len(scenario_labels)):
            val = cm_sub[i, j]
            color = "white" if val > cm_sub.max() / 2 else "black"
            ax_sub.text(j, i, str(val), ha="center", va="center", color=color, fontweight="bold")

    plt.tight_layout()
    f_sub_path = os.path.join(RESULTS_FIG_DIR, "subtype_confusion_matrix.png")
    fig_sub.savefig(f_sub_path, dpi=150)
    plt.close(fig_sub)
    print(f"Saved figure: {f_sub_path}")

    # ── Figure 2: Accuracy vs Noise Degradation ───────────────────────────────
    fig_n, ax_n = plt.subplots(figsize=(7, 4.5))
    ax_n.plot(noise_sigmas, acc_vs_noise, "bo-", lw=2, markersize=7)
    ax_n.set_xlabel("Complex Measurement Noise Std Dev (σ)")
    ax_n.set_ylabel("Classification Accuracy (%)")
    ax_n.set_title("Diagnostic Robustness vs Measurement Noise")
    ax_n.set_ylim(50, 105)
    ax_n.grid(True, alpha=0.3)
    plt.tight_layout()
    f_noise_path = os.path.join(RESULTS_FIG_DIR, "accuracy_vs_noise.png")
    fig_n.savefig(f_noise_path, dpi=150)
    plt.close(fig_n)
    print(f"Saved figure: {f_noise_path}")

    # ── Figure 3: Location Error Histogram ────────────────────────────────────
    fig_h, ax_h = plt.subplots(figsize=(7, 4.5))
    valid_errs = loc_metrics["errors_cm"]
    if len(valid_errs) > 0:
        ax_h.hist(valid_errs, bins=15, color="#17becf", edgecolor="black", alpha=0.8)
        ax_h.axvline(loc_metrics["mae_m"] * 100, color="red", linestyle="--", lw=2, label=f"MAE: {loc_metrics['mae_m']*100:.2f} cm")
        ax_h.set_xlabel("Absolute Fault Distance Error (cm)")
        ax_h.set_ylabel("Frequency Count")
        ax_h.set_title("Distribution of IFFT TDR Distance Estimation Errors")
        ax_h.grid(True, alpha=0.3)
        ax_h.legend()
    plt.tight_layout()
    f_hist_path = os.path.join(RESULTS_FIG_DIR, "location_error_hist.png")
    fig_h.savefig(f_hist_path, dpi=150)
    plt.close(fig_h)
    print(f"Saved figure: {f_hist_path}")

    # ── Figure 4: Abstention Challenge Breakdown Bar Chart ────────────────────
    fig_abs, ax_abs = plt.subplots(figsize=(8, 4.5))
    cats_plot = df_breakdown["Challenge_Category"].tolist()
    rates_plot = df_breakdown["Abstention_Rate_Pct"].tolist()
    bars = ax_abs.bar(range(len(cats_plot)), rates_plot, color="#2ca02c", edgecolor="black", alpha=0.85)
    ax_abs.axhline(90.0, color="red", linestyle="--", lw=2, label="Target Threshold (90%)")
    ax_abs.set_ylabel("Abstention Rate (% Classified as 'unknown')")
    ax_abs.set_title(f"Classifier Abstention Recall Across Challenge Categories (Overall: {abstention_recall:.1f}%)")
    ax_abs.set_ylim(0, 115)
    ax_abs.set_xticks(range(len(cats_plot)))
    ax_abs.set_xticklabels(cats_plot, rotation=35, ha="right")
    ax_abs.grid(True, axis="y", alpha=0.3)
    ax_abs.legend(loc="lower right")

    for bar, rate in zip(bars, rates_plot):
        ax_abs.text(bar.get_x() + bar.get_width() / 2, rate + 2, f"{rate:.0f}%", ha="center", va="bottom", fontweight="bold")

    plt.tight_layout()
    f_abs_path = os.path.join(RESULTS_FIG_DIR, "abstention_challenge_breakdown.png")
    fig_abs.savefig(f_abs_path, dpi=150)
    plt.close(fig_abs)
    print(f"Saved figure: {f_abs_path}")

    print("=" * 80)
    print("Independent Validation Laboratory Execution Finished Successfully!")
    print("=" * 80)


if __name__ == "__main__":
    run_full_validation()
