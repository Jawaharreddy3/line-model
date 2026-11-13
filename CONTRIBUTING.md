# Contributing to RF LINE DOCTOR

Thank you for your interest in contributing to **RF LINE DOCTOR**! This project is an educational virtual transmission-line simulation, diagnostics, and impedance matching system developed for university-level microwave engineering courses.

---

## 1. Ground Rules & Interface Preservation

Before submitting changes, please note the following non-negotiable principles:

1. **Preserve Frozen Interface Contracts:** All public function signatures, parameter names, argument ordering, and return dictionaries documented in [`INTERFACES.md`](INTERFACES.md) are strictly frozen. Do not modify public contracts.
2. **Preserve the 5 Public Classification Labels:** The diagnostic classifier must strictly return one of:
   - `"healthy"`
   - `"open"`
   - `"short"`
   - `"mismatch"`
   - `"unknown"`
3. **Preserve the 6 Physical Scenarios:** The underlying simulation engine must preserve the 6 canonical scenarios:
   - `healthy`
   - `mismatch`
   - `open`
   - `short`
   - `series_L`
   - `shunt_C`
4. **Physical Grounding:** All mathematical formulations must be grounded in classical electromagnetic theory (Telegrapher's equations, Pozar, Collin). Do not change model assumptions silently.
5. **No Synthetic/Fabricated Data:** Do not fabricate test results or claim physical hardware measurements without documented evidence.

---

## 2. Development Setup

1. **Fork and Clone:**
   ```bash
   git clone https://github.com/Jawaharreddy3/line-model.git
   cd line-model
   ```

2. **Create a Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1
   ```

3. **Install Dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Verify Existing Tests:**
   ```bash
   python -m pytest
   ```
   All 169 automated tests must pass before making any changes.

---

## 3. Contribution Workflow

1. **Create a Feature Branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Implement Changes & Tests:**
   - Any bug fix or feature enhancement must include corresponding unit and regression tests in `tests/`.
   - Ensure code is formatted cleanly and adheres to standard PEP 8 conventions.

3. **Run Full Verification:**
   ```bash
   # Run full test suite
   python -m pytest -v

   # Run validation laboratory
   python validation/run_validation.py

   # Run reproducible examples
   python reproducible_examples.py
   ```

4. **Commit & Push:**
   Use clear, descriptive commit messages:
   ```bash
   git commit -m "feat(diagnostics): improve phase unwrapping stability for high-loss lines"
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request:**
   - Target branch: `main`.
   - Provide a clear summary of changes, motivation, and verification evidence.
   - Ensure all GitHub Actions CI checks pass.
