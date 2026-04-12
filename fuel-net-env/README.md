---
title: Fuel Net Env
emoji: 🛢️
colorFrom: red
colorTo: yellow
sdk: docker
pinned: false
---

# FuelNetEnv — World Fuel Distribution Network Manager

## About This Project
**Team:** Dhokla Deep Learners  
**Hackathon:** Meta PyTorch OpenEnv Hackathon x SST  
FuelNetEnv is an OpenEnv-compliant reinforcement learning and LLM agent environment simulating macro global fuel distribution amidst **real-world geopolitical crises**.

HF Space: https://huggingface.co/spaces/Dhyeyyy18/Fuel-Net-Env-Final

### The Real-World Context (February-March 2026)
This environment is grounded in the reality of the ongoing **2026 Strait of Hormuz Crisis**. Currently, over 20 million barrels of day (~20% of global flow) are at risk, leading to skyrocketing Brent crude prices and rerouted supply chains. You act as the **Global Fuel Distribution Crisis Manager** for a multi-national consortium.

We've designed this OpenEnv spec precisely around actual world chokepoints based on current UNCTAD and EIA data metrics.

## The Environment (OpenEnv Standard)

The world state consists of a series of Producers (`persian_gulf`, `us_shale`, `russia`, `west_africa`), Chokepoints (`hormuz`, `suez`, `malacca`), and Consumers (`india`, `china`, `europe`, `japan_korea`).

Your goal is to issue daily macro-economic actions:
- `ship_fuel`
- `reroute_shipment`
- `release_reserves`
- `reduce_demand`
- `hold`

You are rewarded for successfully meeting global supply demands per-region, cost-efficiency, and strategic reserve capacity management. 

### Supported Endpoints:
The environment runs on standard REST API endpoints over FastAPI matching the OpenEnv requirements:
- `/reset`
- `/step`
- `/state`
- `/tasks`
- `/grader`
- `/baseline`

## Tasks (Difficulty Levels)
1. **Very Easy** (`very_easy_startup`): Benchmark non-disrupted market equilibrium fulfillment.
2. **Easy** (`easy_refinery_maintenance`): 15-day timeline focused on a localized 30% pipeline supply cut from the Persian Gulf.
3. **Medium** (`medium_multi_crisis`): 25-day cascade timeline. Houthis attack the Red Sea, forcing Cape of Good Hope reroutes while summer heatwaves hit Indian diesel supplies.
4. **Hard** (`hard_hormuz_crisis`): 30-day timeline. Simulates the actual **February 2026 Strait of Hormuz closure**. 20M bbl/day are suspended with localized attacks on bypass pipelines. Unsolvable perfectly; triage is required.
5. **Extreme** (`extreme_global_crisis`): Complete breakdown. 7 simultaneous disruptions require 100% emergency long-haul routing ignoring transit limits.

## Quickstart (Locally)
We've included a Dockerfile for HuggingFace Spaces/local deployment.
```bash
docker build -t fuel-net-env .
docker run -p 8000:8000 fuel-net-env
```

### Running the Baseline Agent
The environment comes with a fully-integrated **Hybrid Crisis Command Center**, combining a deterministic rule-based logistics engine with LLM-powered strategic intelligence. 

The logistics engine automatically calculates the fastest delivery routes for regions experiencing fuel shortages. Simultaneously, the real-time terminal dashboard uses NVIDIA's **meta/llama-3.1-8b-instruct** API to generate dynamic, 1-sentence situation briefings corresponding to the simulation day.

Make sure you configure the mandatory **OpenEnv** variables in your `.env` file at the root directory:
```env
API_BASE_URL="https://integrate.api.nvidia.com/v1"
MODEL_NAME="meta/llama-3.1-8b-instruct"
HF_TOKEN="nvapi-YOUR-NVIDIA-KEY"
```

Then, launch the command center simulation by passing in a task parameter (`easy`, `medium`, or `hard`):
```bash
python inference.py --task hard
```

### Official Baseline Benchmarks 
Using the hybrid rule-based and LLM intelligence framework embedded in the baseline agent:
- **Very Easy Task:** ` 0.8520 / 1`
- **Easy Task:** ` 0.7586 / 1`
- **Medium Task:** ` 0.7480 / 1`
- **Hard Task:** ` 0.7340 / 1`
- **Extreme Task:** ` 0.6510 / 1`

## Advanced Formatting & OpenEnv Alignment
FuelNetEnv utilizes advanced validation and grading schemas drawn directly from top-tier OpenEnv architectures:
1. **Three-Dimensional Evaluation**: The final grade blends mathematical deterministic scoring (70%) with a qualitative LLM Judge reasoning evaluation (30%). Agents must provide strategic reasoning for their action allocations to score maximally.
2. **Iterative Validation Rollback**: Invalid physical routing actions immediately yield HTTP error feedback without advancing the simulation clock, allowing LLM agents up to 3 context-grounded retries to self-correct parsing or geographical mistakes.
3. **Progressive Difficulty Scaling**: Final scores are natively bounded `(0, 1)`, and bounded further depending on task difficulty. Easy tasks limit the maximal reward, actively incentivizing agents to pursue the `extreme_global_crisis` task for maximal overall points.

## Grading System
Scores are distributed dynamically taking into account:
- **Supply Fulfillment Constraints**: Overall percentage met.
- **Budgetary Constraints**: Average transit premiums vs default logic.
- **Reasoning Structure**: Strategic capability mapped against curated ground-truths (LLM as a judge).
