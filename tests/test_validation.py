import numpy as np
import pytest

from validation.classification_metrics import (
    compute_confusion_matrix,
    compute_classification_report,
)
from validation.location_metrics import compute_location_metrics


def test_confusion_matrix_and_report_math():
    y_true = ["healthy", "healthy", "open", "short", "mismatch"]
    y_pred = ["healthy", "mismatch", "open", "short", "mismatch"]
    labels = ["healthy", "open", "short", "mismatch", "unknown"]

    rep = compute_classification_report(y_true, y_pred, labels)
    assert rep["accuracy"] == pytest.approx(4.0 / 5.0)  # 80%
    assert rep["per_class"]["open"]["precision"] == 1.0
    assert rep["per_class"]["open"]["recall"] == 1.0
    assert rep["per_class"]["healthy"]["recall"] == 0.5


def test_location_metrics_math():
    y_true = [1.0, 0.5, 0.8]
    y_est = [1.02, 0.49, 0.81]
    res = compute_location_metrics(y_true, y_est)
    assert res["valid_count"] == 3
    # Absolute errors: 0.02, 0.01, 0.01 -> mean = 0.04/3 ~ 0.01333 m
    assert res["mae_m"] == pytest.approx(0.04 / 3.0)
    assert res["rmse_m"] == pytest.approx(np.sqrt((0.02**2 + 0.01**2 + 0.01**2) / 3.0))


def test_location_metrics_handles_nans():
    y_true = [1.0, np.nan, 0.8]
    y_est = [1.02, 0.5, np.nan]
    res = compute_location_metrics(y_true, y_est)
    assert res["valid_count"] == 1
    assert res["mae_m"] == pytest.approx(0.02)
