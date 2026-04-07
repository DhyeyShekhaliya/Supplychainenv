# 🚀 FuelNet Command Center — Quickstart Guide

This guide will help you set up and run the upgraded high-fidelity crisis simulation either in headless automated mode or using the beautiful Web Dashboard!

## 1. Environment Setup

It is strongly recommended to use a virtual environment or `uv` to avoid dependency conflicts.

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

Ensure you have your environment variables set! Either export them directly, or create a `.env` file in the `fuel-net-env/` directory:

```text
HF_TOKEN=your_huggingface_or_nvidia_api_key_here
```
*(Note: If you are running locally without Hugging Face, you can also fall back to `NVIDIA_API_KEY` for the LLM.)*

## 3. Running the Simulation Map (Frontend)

To boot up the gorgeous interactive Glassmorphism Dashboard and the actual underlying simulation engine map:

```bash
# Boot the FastAPI Engine!
python -m uvicorn server.app:app --host 0.0.0.0 --port 7860
```
Open **`http://localhost:7860`** in your web browser! You can select missions and run the automated agent natively from the website window.

---

## 4. Running the CLI Agents Locally (Backend)

If you strictly want to run the python scripts via Terminal (e.g. for testing the Hackathon grading pipeline) while your server is running in the background:

### The Beautiful ASCII Terminal Visualizer
This is exactly what you want to use for your demonstration videos!
```bash
python interactive_demo.py --task hard
```

### The Sterile OpenEnv Standard Grader Script
This is the completely silent, Regex-compliant pipeline that the Meta Evaluators use to calculate your score in headless mode.
```bash
python inference.py
```

---

## ✨ Key Features in this Repository
- **Complete Vector Mapping:** The Frontend Web Dashboard features a mathematically mapped geographic D3 Vector Map bounding the nodes flawlessly.
- **Hackathon Safe:** Dual-file pipeline separating gorgeous visualizations (`interactive_demo.py`) from strict `[START]/[STEP]/[END]` standards (`inference.py`).
- **Resilient AI Pipeline:** Boot cycles gracefully catch missing API Keys and fallback to deterministic route mathematics without crashing with ugly `500 Server` errors.
