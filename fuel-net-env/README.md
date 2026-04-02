# FuelNetEnv — World Fuel Distribution Network Manager

## About This Project
**Team:** Dhokla Deep Learners  
**Hackathon:** Meta PyTorch OpenEnv Hackathon x SST  
FuelNetEnv is an OpenEnv-compliant reinforcement learning and LLM agent environment simulating macro global fuel distribution amidst **real-world geopolitical crises**.

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
1. **Easy** (`easy_refinery_maintenance`): 15-day timeline focused on a localized 30% pipeline supply cut from the Persian Gulf.
2. **Medium** (`medium_multi_crisis`): 25-day cascade timeline. Houthis attack the Red Sea, forcing Cape of Good Hope reroutes while summer heatwaves hit Indian diesel supplies.
3. **Hard** (`hard_hormuz_crisis`): 30-day timeline. Simulates the actual **February 2026 Strait of Hormuz closure**. 20M bbl/day are suspended with localized attacks on bypass pipelines. Unsolvable perfectly; triage is required.

## Quickstart (Locally)
We've included a Dockerfile for HuggingFace Spaces/local deployment.
```bash
docker build -t fuel-net-env .
docker run -p 8000:8000 fuel-net-env
```

To run the NVIDIA Llama 3 baseline check:
```bash
export NVIDIA_API_KEY="nvapi-..."
python baseline/inference.py
```

## Grading System
Scores are distributed from `0.0` to `1.0`, taking into account average percentage supply-fulfillment constraints, budgetary constraints (average transit premiums), and duration of markets under severe shortage.
