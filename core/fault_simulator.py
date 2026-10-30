"""
core/fault_simulator.py -- Fault simulation module (core package).

Exposes the 6-scenario cascaded transmission line simulator.
"""

from fault_simulation import (
    FAULT_SCENARIOS,
    abcd_uniform_line,
    abcd_series_impedance,
    abcd_shunt_admittance,
    zin_from_abcd,
    simulate_fault,
)

__all__ = [
    "FAULT_SCENARIOS",
    "abcd_uniform_line",
    "abcd_series_impedance",
    "abcd_shunt_admittance",
    "zin_from_abcd",
    "simulate_fault",
]
