# 🚀 FuelNet Command Center — Quickstart Guide

This guide will help you set up and run the upgraded high-fidelity crisis simulation.

## 1. Environment Setup

It is recommended to use a virtual environment to avoid dependency conflicts.

```bash
cd fuel-net-env
python -m venv .venv

# Activate the venv:
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Configuration

Ensure you have an `.env` file in the `fuel-net-env/` directory with your API key:

```text
NVIDIA_API_KEY=your_nvidia_api_key_here
```

## 3. Running the Simulation (2-Terminal Workflow)

### Terminal 1: Start the World Engine (Server)
This handles the global map, disruptions, and logistics physics.

```bash
# Set PYTHONPATH so the server can find local modules
# (Windows) $env:PYTHONPATH="."
# (Mac/Linux) export PYTHONPATH=.

python -m uvicorn server.app:app --host 0.0.0.0 --port 8000
```

### Terminal 2: Start the AI Command Center (Agent)
This is the "Brain" that coordinates global shipments and provides strategic briefings.

```bash
python baseline/inference.py --task hard
```

---

## ✨ Key Features in this PR:
- **Global Multi-Action**: The agent now handles shipments to multiple markets (Europe, India, China) in a single day.
- **Shipment Arrival Tracking**: Day-by-day reports on which ships reached port and how long they took.
- **High-Fidelity Dashboard**: A clean, professional terminal UI with status bars and full-text AI analysis.
