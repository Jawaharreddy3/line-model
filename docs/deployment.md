# RF LINE DOCTOR — Deployment & Operations Guide

This document describes the deployment architecture, configuration, and verification procedures for the **RF LINE DOCTOR** application on both cloud and local environments.

---

## 1. Cloud Deployment Architecture (Streamlit Community Cloud)

### 1.1 Overview
The production web interface is hosted on **Streamlit Community Cloud**, connected directly to the primary GitHub repository.

- **Production URL:** [https://line-model-dbtwte9td8ta2nffkzmhd9.streamlit.app/](https://line-model-dbtwte9td8ta2nffkzmhd9.streamlit.app/)
- **Connected Repository:** `https://github.com/Jawaharreddy3/line-model`
- **Target Branch:** `main`
- **Application Entry Point:** `app.py`
- **Python Runtime:** Python 3.10+ (64-bit Linux container)

### 1.2 Configuration & Theme (`.streamlit/config.toml`)
The application presentation is configured via `.streamlit/config.toml`:
```toml
[server]
headless = true
port = 8501
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#00d4aa"
backgroundColor = "#07090f"
secondaryBackgroundColor = "#0d131f"
textColor = "#dce4ee"
font = "sans serif"
```

### 1.3 Dependency Specification (`requirements.txt`)
All production dependencies are pinned/constrained in `requirements.txt`:
```text
numpy>=1.24.0,<2.3.0
scipy>=1.11.0,<1.15.0
matplotlib>=3.8.0,<3.11.0
streamlit>=1.28.0,<1.44.0
scikit-rf>=0.30.0,<1.6.0
pytest>=7.4.0,<9.3.0
```

---

## 2. Local Execution & Testing

### 2.1 Standard Local Execution
To run the full application locally:

```bash
# Clone the repository
git clone https://github.com/Jawaharreddy3/line-model.git
cd line-model

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Launch Streamlit dashboard
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 2.2 Running the Automated Regression Suite
```bash
# Fast test run
python -m pytest

# Detailed test run with verbose output
python -m pytest -v
```

### 2.3 Running the Validation Laboratory
```bash
python validation/run_validation.py
```
Outputs:
- Generates empirical CSV tables in `results/csv/`
- Generates publication-quality figures in `results/figures/`

---

## 3. Docker Containerization (Optional Self-Hosted Deployment)

For institutions or laboratories requiring self-hosted on-premise execution, the following Dockerfile configuration can be used:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

To build and run:
```bash
docker build -t rf-line-doctor .
docker run -p 8501:8501 rf-line-doctor
```

---

## 4. Operational Troubleshooting

### 4.1 Sleeping Cloud Application
Streamlit Community Cloud automatically puts inactive apps into sleep mode after several days of inactivity to conserve resources:
- When accessing the URL after inactivity, the service displays a "Wake up app" prompt.
- Clicking the button restarts the container within 15–30 seconds.
- No data or state is lost because the application is fully stateless and reads directly from Git.

### 4.2 Clearing Streamlit Session State & Cache
If the browser dashboard displays stale parameters:
- Press `C` in the browser or select the three dots in the top-right corner $\to$ **Clear cache**.
- Rerun with `R`.
