"""
validation/classification_metrics.py -- Statistical classification metrics.

Calculates:
  - Confusion matrix across true and predicted scenarios.
  - Per-class Precision, Recall, and F1-score.
  - Overall accuracy and sample support.
"""

import numpy as np

__all__ = [
    "compute_confusion_matrix",
    "compute_classification_report",
]


def compute_confusion_matrix(y_true, y_pred, labels):
    """
    Compute multi-class confusion matrix.

    Parameters
    ----------
    y_true : list or array of ground-truth labels
    y_pred : list or array of predicted labels
    labels : list of unique class labels

    Returns
    -------
    matrix : 2D numpy array of shape (len(labels), len(labels))
             Row = true class, Column = predicted class
    """
    label_to_idx = {label: i for i, label in enumerate(labels)}
    N = len(labels)
    cm = np.zeros((N, N), dtype=int)

    for true_val, pred_val in zip(y_true, y_pred):
        if true_val in label_to_idx and pred_val in label_to_idx:
            r = label_to_idx[true_val]
            c = label_to_idx[pred_val]
            cm[r, c] += 1

    return cm


def compute_classification_report(y_true, y_pred, labels):
    """
    Compute Precision, Recall, F1-score, Support, and Overall Accuracy.

    Parameters
    ----------
    y_true : list of true labels
    y_pred : list of predicted labels
    labels : list of class labels

    Returns
    -------
    dict with:
        per_class: dict of {label: {'precision': float, 'recall': float, 'f1': float, 'support': int}}
        accuracy : float
        total_samples: int
    """
    cm = compute_confusion_matrix(y_true, y_pred, labels)
    total_samples = len(y_true)
    per_class = {}

    total_correct = int(np.trace(cm))
    accuracy = float(total_correct / total_samples) if total_samples > 0 else 0.0

    for i, label in enumerate(labels):
        tp = int(cm[i, i])
        fp = int(np.sum(cm[:, i]) - tp)
        fn = int(np.sum(cm[i, :]) - tp)
        support = int(np.sum(cm[i, :]))

        precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = (
            float(2.0 * precision * recall / (precision + recall))
            if (precision + recall) > 0
            else 0.0
        )

        per_class[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        }

    return {
        "per_class": per_class,
        "accuracy": accuracy,
        "total_samples": total_samples,
        "confusion_matrix": cm,
        "labels": labels,
    }
