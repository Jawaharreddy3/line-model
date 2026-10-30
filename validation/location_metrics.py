"""
validation/location_metrics.py -- Metrics for fault location accuracy.

Calculates:
  - Mean Absolute Error (MAE)
  - Root Mean Squared Error (RMSE)
  - Error vs Noise and Error vs Bandwidth dependencies
"""

import numpy as np

__all__ = [
    "compute_location_metrics",
]


def compute_location_metrics(true_positions, estimated_positions):
    """
    Compute error statistics between true fault positions and IFFT estimates.

    Parameters
    ----------
    true_positions      : array-like of true fault distances [m]
    estimated_positions : array-like of estimated fault distances [m]

    Returns
    -------
    dict with:
        mae_m     : Mean Absolute Error [m]
        rmse_m    : Root Mean Squared Error [m]
        max_err_m : Maximum absolute error [m]
        errors_cm : array of absolute errors in centimetres
        valid_count: number of valid comparison pairs
    """
    y_true = np.asarray(true_positions, dtype=float)
    y_est = np.asarray(estimated_positions, dtype=float)

    # Filter out NaNs or Nones
    valid_mask = np.isfinite(y_true) & np.isfinite(y_est)
    if not np.any(valid_mask):
        return {
            "mae_m": float("nan"),
            "rmse_m": float("nan"),
            "max_err_m": float("nan"),
            "errors_cm": np.array([]),
            "valid_count": 0,
        }

    t_valid = y_true[valid_mask]
    e_valid = y_est[valid_mask]

    diff = np.abs(e_valid - t_valid)
    mae = float(np.mean(diff))
    rmse = float(np.sqrt(np.mean(diff**2)))
    max_err = float(np.max(diff))

    return {
        "mae_m": mae,
        "rmse_m": rmse,
        "max_err_m": max_err,
        "errors_cm": diff * 100.0,
        "valid_count": int(np.sum(valid_mask)),
    }
