# FuelNetEnv — World Fuel Distribution Network Manager
## Complete Implementation Plan

**Team:** Dhokla Deep Learners  
**Hackathon:** Meta PyTorch OpenEnv Hackathon x SST  
**Submission Deadline:** 7 April 2026, 11:59 PM IST  
**Submission Format:** Hugging Face Spaces URL  

---

## PART 1: WHAT WE'RE BUILDING

An OpenEnv-compliant RL environment where an LLM agent acts as a **Global Fuel Distribution Crisis Manager**. The agent manages fuel routing from oil-producing regions to consuming nations through maritime chokepoints, pipelines, and strategic reserves — responding to disruptions like strait closures, pipeline attacks, refinery shutdowns, and demand spikes.

**Why this is EXTREMELY timely:** The Strait of Hormuz crisis began on February 28, 2026 — literally one month ago. 20 million barrels/day of oil flow was disrupted. Brent crude spiked above $90/barrel. Shipping companies suspended transits. This is the single most consequential energy supply chain disruption in modern history, and it's happening RIGHT NOW as you read this.

**The core decision problem:** You're the operations manager for a multinational fuel distributor. You oversee fuel flows from producing regions (Middle East, Russia, US, West Africa) through maritime chokepoints (Hormuz, Suez, Malacca) to consuming regions (India, China, Europe, Japan). When disruptions hit, you must reroute shipments, activate strategic reserves, switch suppliers, and manage costs — all while preventing fuel shortages in your markets.

**Why this is a real-world task (not a game/toy):**
- 20% of global oil (~20M barrels/day) transits the Strait of Hormuz
- The current 2026 crisis has sent oil prices up 30%+, disrupted fertilizer and plastics supply chains
- UNCTAD warned of "serious consequences for global trade and development"
- No existing RL benchmark simulates global fuel distribution under geopolitical disruption
- This is exactly what operations teams at Shell, BP, IOCL, Aramco, and commodity traders like Vitol/Trafigura do

---

## PART 2: HACKATHON COMPLIANCE CHECKLIST

| Requirement | How We Meet It |
|---|---|
| Real-world task simulation | Global fuel distribution — literally happening right now (Hormuz crisis 2026) |
| Full OpenEnv spec | Typed Pydantic models, step()/reset()/state(), openenv.yaml |
| 3+ tasks with graders | Easy (single chokepoint), Medium (cascading multi-region), Hard (Hormuz-scale global crisis) |
| Graders score 0.0–1.0 | Supply fulfillment rate + cost efficiency + reserve management = deterministic numeric score |
| Meaningful reward function | Partial credit per delivery, cost penalties, proactive rerouting bonuses |
| Baseline inference script | Uses OpenAI API, reads OPENAI_API_KEY from env |
| HF Space deployment | Dockerfile + FastAPI server |
| README | Full docs with world map context |
| All required endpoints | /reset, /step, /state, /baseline, /grader, /tasks |
| `openenv validate` passes | Compliant openenv.yaml + typed models |
| `docker build && docker run` works | Clean Dockerfile, minimal dependencies |

---

## PART 3: PROJECT STRUCTURE

```
fuel-net-env/
│
├── openenv.yaml                  # OpenEnv metadata
├── Dockerfile                    # Container config
├── requirements.txt              # Python dependencies
├── README.md                     # Full documentation
├── LICENSE
│
├── fuel_env/
│   ├── __init__.py
│   ├── models.py                 # Pydantic: Observation, Action, Reward
│   ├── environment.py            # Core: step(), reset(), state()
│   ├── world.py                  # World map: regions, routes, chokepoints
│   ├── disruptions.py            # Disruption events (scripted per task)
│   ├── tasks.py                  # 3 task definitions
│   ├── graders.py                # Deterministic graders (0.0–1.0)
│   └── rewards.py                # Reward shaping logic
│
├── server/
│   └── app.py                    # FastAPI server with all endpoints
│
├── baseline/
│   └── inference.py              # OpenAI API baseline agent
│
└── tests/
    ├── test_environment.py
    ├── test_world.py
    └── test_graders.py
```

---

## PART 4: WORLD MODEL (world.py)

### The Global Fuel Network

The world is modeled as a directed graph with 3 types of nodes and weighted edges.

```python
from enum import Enum
from pydantic import BaseModel

class RegionType(str, Enum):
    PRODUCER = "producer"          # Oil-producing region
    CHOKEPOINT = "chokepoint"      # Maritime bottleneck
    CONSUMER = "consumer"          # Fuel-consuming market
    HUB = "hub"                    # Trading/storage hub

class FuelRegion(BaseModel):
    region_id: str
    name: str
    region_type: RegionType
    production_capacity: int       # Barrels/day (0 for consumers)
    current_output: int            # Current actual production
    demand: int                    # Barrels/day needed (0 for producers)
    storage_capacity: int          # Strategic reserve capacity (barrels)
    current_storage: int           # Current reserve level
    operational: bool              # Is this region functional?
    price_per_barrel: float        # Current local price

class FuelRoute(BaseModel):
    route_id: str
    from_region: str
    to_region: str
    route_type: str                # "sea", "pipeline", "rail"
    normal_transit_days: int       # Normal shipping time
    current_transit_days: int      # May be inflated during disruption
    cost_per_barrel: float         # Transport cost
    capacity_per_day: int          # Max barrels/day on this route
    active: bool                   # Is this route currently open?
    passes_through: str | None     # Chokepoint this route uses (if any)
```

### Regions (Simplified but Real)

```python
REGIONS = {
    # === PRODUCERS ===
    "persian_gulf": FuelRegion(
        region_id="persian_gulf",
        name="Persian Gulf (Saudi, UAE, Iraq, Kuwait, Qatar)",
        region_type=RegionType.PRODUCER,
        production_capacity=20_000_000,    # 20M bbl/day
        current_output=18_000_000,
        demand=2_000_000,                  # Local consumption
        storage_capacity=50_000_000,
        current_storage=30_000_000,
        operational=True,
        price_per_barrel=45.0,
    ),
    "russia": FuelRegion(
        region_id="russia",
        name="Russia (Urals, Siberia)",
        region_type=RegionType.PRODUCER,
        production_capacity=10_000_000,
        current_output=9_500_000,
        demand=3_500_000,
        storage_capacity=30_000_000,
        current_storage=20_000_000,
        operational=True,
        price_per_barrel=55.0,
    ),
    "us_shale": FuelRegion(
        region_id="us_shale",
        name="United States (Shale, Gulf of Mexico)",
        region_type=RegionType.PRODUCER,
        production_capacity=13_000_000,
        current_output=12_500_000,
        demand=20_000_000,                 # Net importer
        storage_capacity=700_000_000,      # SPR
        current_storage=400_000_000,
        operational=True,
        price_per_barrel=70.0,
    ),
    "west_africa": FuelRegion(
        region_id="west_africa",
        name="West Africa (Nigeria, Angola)",
        region_type=RegionType.PRODUCER,
        production_capacity=4_000_000,
        current_output=3_500_000,
        demand=1_000_000,
        storage_capacity=10_000_000,
        current_storage=5_000_000,
        operational=True,
        price_per_barrel=60.0,
    ),

    # === CHOKEPOINTS ===
    "hormuz": FuelRegion(
        region_id="hormuz",
        name="Strait of Hormuz",
        region_type=RegionType.CHOKEPOINT,
        production_capacity=0,
        current_output=0,
        demand=0,
        storage_capacity=0,
        current_storage=0,
        operational=True,
        price_per_barrel=0,
    ),
    "suez": FuelRegion(
        region_id="suez",
        name="Suez Canal / Bab al-Mandeb",
        region_type=RegionType.CHOKEPOINT,
        production_capacity=0, current_output=0,
        demand=0, storage_capacity=0, current_storage=0,
        operational=True, price_per_barrel=0,
    ),
    "malacca": FuelRegion(
        region_id="malacca",
        name="Strait of Malacca",
        region_type=RegionType.CHOKEPOINT,
        production_capacity=0, current_output=0,
        demand=0, storage_capacity=0, current_storage=0,
        operational=True, price_per_barrel=0,
    ),

    # === CONSUMERS ===
    "india": FuelRegion(
        region_id="india",
        name="India",
        region_type=RegionType.CONSUMER,
        production_capacity=800_000,       # Domestic production
        current_output=750_000,
        demand=5_500_000,                  # 5.5M bbl/day
        storage_capacity=40_000_000,       # SPR + commercial
        current_storage=25_000_000,
        operational=True,
        price_per_barrel=80.0,
    ),
    "china": FuelRegion(
        region_id="china",
        name="China",
        region_type=RegionType.CONSUMER,
        production_capacity=4_000_000,
        current_output=3_800_000,
        demand=16_000_000,
        storage_capacity=900_000_000,
        current_storage=600_000_000,
        operational=True,
        price_per_barrel=78.0,
    ),
    "europe": FuelRegion(
        region_id="europe",
        name="Europe (EU + UK)",
        region_type=RegionType.CONSUMER,
        production_capacity=3_000_000,     # North Sea
        current_output=2_800_000,
        demand=14_000_000,
        storage_capacity=150_000_000,
        current_storage=100_000_000,
        operational=True,
        price_per_barrel=85.0,
    ),
    "japan_korea": FuelRegion(
        region_id="japan_korea",
        name="Japan & South Korea",
        region_type=RegionType.CONSUMER,
        production_capacity=0,
        current_output=0,
        demand=6_000_000,
        storage_capacity=80_000_000,
        current_storage=50_000_000,
        operational=True,
        price_per_barrel=82.0,
    ),
}
```

### Routes (Key Global Fuel Corridors)

```python
ROUTES = [
    # Persian Gulf exports
    FuelRoute("pg_hormuz", "persian_gulf", "hormuz", "sea", 1, 1, 2.0, 20_000_000, True, None),
    FuelRoute("hormuz_india", "hormuz", "india", "sea", 5, 5, 3.0, 5_000_000, True, "hormuz"),
    FuelRoute("hormuz_china", "hormuz", "china", "sea", 15, 15, 5.0, 6_000_000, True, "hormuz"),
    FuelRoute("hormuz_japan", "hormuz", "japan_korea", "sea", 12, 12, 4.5, 4_000_000, True, "hormuz"),
    FuelRoute("hormuz_suez", "hormuz", "suez", "sea", 4, 4, 2.5, 4_000_000, True, "hormuz"),
    FuelRoute("suez_europe", "suez", "europe", "sea", 7, 7, 3.5, 5_000_000, True, "suez"),

    # Bypass pipelines (Saudi East-West, UAE ADCOP)
    FuelRoute("pg_bypass_pipe", "persian_gulf", "suez", "pipeline", 2, 2, 4.0, 7_000_000, True, None),

    # Cape of Good Hope (long route bypassing Hormuz+Suez)
    FuelRoute("pg_cape_europe", "persian_gulf", "europe", "sea", 35, 35, 8.0, 3_000_000, True, None),
    FuelRoute("pg_cape_india", "persian_gulf", "india", "sea", 25, 25, 7.0, 2_000_000, True, None),

    # Russia exports
    FuelRoute("russia_europe_pipe", "russia", "europe", "pipeline", 3, 3, 3.0, 4_000_000, True, None),
    FuelRoute("russia_china_pipe", "russia", "china", "pipeline", 5, 5, 3.5, 2_000_000, True, None),
    FuelRoute("russia_india_sea", "russia", "india", "sea", 20, 20, 5.5, 1_500_000, True, None),

    # US exports
    FuelRoute("us_europe_sea", "us_shale", "europe", "sea", 12, 12, 5.0, 3_000_000, True, None),
    FuelRoute("us_india_sea", "us_shale", "india", "sea", 25, 25, 7.0, 1_000_000, True, None),
    FuelRoute("us_japan_sea", "us_shale", "japan_korea", "sea", 18, 18, 6.0, 2_000_000, True, None),

    # West Africa exports
    FuelRoute("wa_europe_sea", "west_africa", "europe", "sea", 10, 10, 4.0, 2_000_000, True, None),
    FuelRoute("wa_india_sea", "west_africa", "india", "sea", 15, 15, 5.0, 1_500_000, True, None),
    FuelRoute("wa_china_sea", "west_africa", "china", "sea", 22, 22, 6.0, 1_000_000, True, None),

    # Malacca Strait routes
    FuelRoute("malacca_china", "malacca", "china", "sea", 3, 3, 1.5, 8_000_000, True, "malacca"),
    FuelRoute("malacca_japan", "malacca", "japan_korea", "sea", 5, 5, 2.0, 4_000_000, True, "malacca"),
]
```

**Note:** Numbers are simplified from real data but proportionally accurate. The key relationships (Hormuz carries 20M bbl/day, bypass pipeline maxes at 7M, Cape route takes 5x longer) are grounded in real EIA and UNCTAD data.

---

## PART 5: DISRUPTION SYSTEM (disruptions.py)

```python
class DisruptionType(str, Enum):
    CHOKEPOINT_CLOSURE = "chokepoint_closure"        # Strait/canal blocked
    PIPELINE_ATTACK = "pipeline_attack"              # Pipeline damaged
    REFINERY_SHUTDOWN = "refinery_shutdown"           # Maintenance or attack
    PRODUCTION_CUT = "production_cut"                # OPEC+ quota change
    DEMAND_SPIKE = "demand_spike"                    # Sudden demand increase
    SANCTIONS = "sanctions"                          # Trade route blocked politically
    WEATHER_DISRUPTION = "weather_disruption"        # Hurricane, cyclone
    HOUTHI_ATTACK = "houthi_attack"                  # Red Sea shipping attacks

class Disruption(BaseModel):
    disruption_id: str
    disruption_type: DisruptionType
    trigger_day: int
    duration_days: int
    affected_entities: list[str]       # Region IDs or route IDs
    severity: float                    # 0.0–1.0
    description: str
    price_impact: float                # $/barrel price increase globally
    resolved: bool = False
```

### Task-Specific Disruption Scripts

**Easy task disruptions:**
```python
EASY_DISRUPTIONS = [
    Disruption(
        disruption_id="e1",
        disruption_type=DisruptionType.REFINERY_SHUTDOWN,
        trigger_day=3,
        duration_days=5,
        affected_entities=["persian_gulf"],
        severity=0.3,
        description="Scheduled maintenance at Saudi Ras Tanura refinery. "
                    "Persian Gulf output reduced by 30% for 5 days.",
        price_impact=5.0,
    ),
]
```

**Medium task disruptions:**
```python
MEDIUM_DISRUPTIONS = [
    Disruption(
        disruption_id="m1",
        disruption_type=DisruptionType.HOUTHI_ATTACK,
        trigger_day=3,
        duration_days=8,
        affected_entities=["suez"],
        severity=0.8,
        description="Houthi forces resume attacks on Red Sea shipping. "
                    "Suez Canal transit suspended. Europe-bound tankers must "
                    "reroute via Cape of Good Hope (+3 weeks transit time).",
        price_impact=12.0,
    ),
    Disruption(
        disruption_id="m2",
        disruption_type=DisruptionType.DEMAND_SPIKE,
        trigger_day=6,
        duration_days=5,
        affected_entities=["india"],
        severity=0.6,
        description="Indian summer heatwave. Electricity demand surges, "
                    "driving diesel generator use up 60%. India demand "
                    "increases from 5.5M to 8M bbl/day.",
        price_impact=3.0,
    ),
    Disruption(
        disruption_id="m3",
        disruption_type=DisruptionType.SANCTIONS,
        trigger_day=10,
        duration_days=10,
        affected_entities=["russia_europe_pipe"],
        severity=1.0,
        description="EU announces new sanctions on Russian oil. "
                    "Russia-Europe pipeline flow cut to zero.",
        price_impact=8.0,
    ),
]
```

**Hard task disruptions (Hormuz Crisis scenario):**
```python
HARD_DISRUPTIONS = [
    Disruption(
        disruption_id="h1",
        disruption_type=DisruptionType.CHOKEPOINT_CLOSURE,
        trigger_day=3,
        duration_days=15,
        affected_entities=["hormuz"],
        severity=1.0,
        description="STRAIT OF HORMUZ CLOSED. Military conflict between "
                    "Iran and US/Israel. All tanker traffic through Hormuz "
                    "suspended. 20M bbl/day cut off. Bypass pipeline at 7M max. "
                    "This is a global energy emergency.",
        price_impact=35.0,
    ),
    Disruption(
        disruption_id="h2",
        disruption_type=DisruptionType.HOUTHI_ATTACK,
        trigger_day=5,
        duration_days=12,
        affected_entities=["suez"],
        severity=0.9,
        description="Houthis resume Red Sea attacks in solidarity with Iran. "
                    "Suez/Bab al-Mandeb routes suspended. Cape of Good Hope "
                    "is now the ONLY sea route from Gulf to Europe.",
        price_impact=15.0,
    ),
    Disruption(
        disruption_id="h3",
        disruption_type=DisruptionType.PIPELINE_ATTACK,
        trigger_day=8,
        duration_days=6,
        affected_entities=["pg_bypass_pipe"],
        severity=0.5,
        description="Iranian missile strikes damage Saudi East-West pipeline. "
                    "Bypass pipeline capacity halved from 7M to 3.5M bbl/day.",
        price_impact=10.0,
    ),
    Disruption(
        disruption_id="h4",
        disruption_type=DisruptionType.DEMAND_SPIKE,
        trigger_day=7,
        duration_days=10,
        affected_entities=["india", "china", "japan_korea"],
        severity=0.7,
        description="Asian nations panic-buying to fill strategic reserves. "
                    "Demand in India +40%, China +25%, Japan/Korea +30%.",
        price_impact=8.0,
    ),
    Disruption(
        disruption_id="h5",
        disruption_type=DisruptionType.PRODUCTION_CUT,
        trigger_day=12,
        duration_days=8,
        affected_entities=["persian_gulf"],
        severity=0.4,
        description="Gulf state refineries damaged in conflict. Persian Gulf "
                    "output drops 40% even if strait reopens.",
        price_impact=12.0,
    ),
]
```

---

## PART 6: PYDANTIC MODELS (models.py)

### Observation

```python
class ShipmentStatus(BaseModel):
    shipment_id: str
    from_region: str
    to_region: str
    volume_barrels: int
    route_id: str
    days_in_transit: int
    days_remaining: int
    cost_so_far: float

class FuelObservation(BaseModel):
    # Task info
    task_id: str
    task_description: str
    difficulty: str

    # Time
    current_day: int
    total_days: int

    # World state
    regions: list[dict]                # Each region's current status
    routes: list[dict]                 # Each route's current status
    global_oil_price: float            # $/barrel (Brent equivalent)

    # Disruptions
    active_disruptions: list[dict]
    new_alerts: list[str]              # New events this day

    # Shipments
    active_shipments: list[ShipmentStatus]
    completed_deliveries: int
    failed_deliveries: int             # Markets that ran dry

    # Demand fulfillment by region
    demand_fulfillment: dict[str, float]   # region_id → % demand met today

    # Strategic reserves
    reserve_levels: dict[str, dict]    # region_id → {current, capacity, days_of_cover}

    # Budget
    total_budget: float
    spent: float
    remaining_budget: float

    # Performance
    global_supply_coverage: float      # 0.0–1.0 across all consumers
    average_cost_per_barrel: float
    markets_in_shortage: list[str]     # Regions with <50% demand met

    done: bool
    message: str
```

### Action

```python
class FuelAction(BaseModel):
    action_type: str
    parameters: dict

# ACTION TYPES:
#
# "ship_fuel" — Send a shipment from producer to consumer via specific route
#   params: {"from": "persian_gulf", "to": "india", "route": "hormuz_india",
#            "volume": 2_000_000}
#
# "reroute_shipment" — Redirect an in-transit shipment to alternate route
#   params: {"shipment_id": "ship_005", "new_route": "pg_cape_india"}
#
# "release_reserves" — Draw down strategic petroleum reserves
#   params: {"region": "india", "volume": 5_000_000}
#
# "activate_alternative_supplier" — Switch to more expensive alternate source
#   params: {"consumer": "europe", "new_supplier": "us_shale",
#            "route": "us_europe_sea", "volume": 1_500_000}
#
# "increase_production" — Ask a producer to ramp up (costs premium)
#   params: {"producer": "us_shale", "additional_volume": 500_000}
#
# "reduce_demand" — Implement rationing / demand reduction in a market
#   params: {"region": "india", "reduction_percent": 15}
#
# "hold" — Do nothing, observe
#   params: {}
```

### Reward

```python
class FuelReward(BaseModel):
    total: float
    supply_fulfillment_reward: float   # Per-region demand met
    cost_efficiency_reward: float      # Lower cost = bonus
    shortage_penalty: float            # Markets running dry
    reserve_management_reward: float   # Smart reserve usage
    proactive_bonus: float             # Acting before crisis hits
    wasteful_spending_penalty: float   # Overpaying when cheaper options exist
```

---

## PART 7: THREE TASKS

### Task 1: EASY — Single Refinery Shutdown (15 days)

One Saudi refinery goes down for maintenance. Agent must reroute ~30% of Persian Gulf supply through alternative routes for 5 days. Straightforward — activate backup routes, maybe draw reserves briefly.

```python
TASK_EASY = {
    "task_id": "easy_refinery_maintenance",
    "description": "Saudi Ras Tanura refinery scheduled maintenance. Persian Gulf "
                   "output drops 30% for 5 days. Reroute supply to prevent "
                   "shortages in India, China, and Japan.",
    "episode_length": 15,
    "total_budget": 5_000_000_000,     # $5 billion
    "consumers": ["india", "china", "japan_korea", "europe"],
    "disruption_count": 1,
    "difficulty": "easy",
}
```

### Task 2: MEDIUM — Red Sea Crisis + Heatwave + Sanctions (25 days)

Three cascading disruptions: Houthi Red Sea attacks (day 3), Indian heatwave demand spike (day 6), and EU Russia sanctions (day 10). Agent must juggle rerouting European supply away from both Suez AND Russian pipelines while handling Indian demand surge.

```python
TASK_MEDIUM = {
    "task_id": "medium_multi_crisis",
    "description": "Triple crisis: Houthi Red Sea attacks block Suez (day 3), "
                   "Indian heatwave spikes demand 60% (day 6), EU sanctions "
                   "cut Russian pipeline to zero (day 10). Manage supply to "
                   "4 consumer regions over 25 days.",
    "episode_length": 25,
    "total_budget": 15_000_000_000,
    "consumers": ["india", "china", "japan_korea", "europe"],
    "disruption_count": 3,
    "difficulty": "medium",
}
```

### Task 3: HARD — Strait of Hormuz Closure (30 days)

Based on the ACTUAL February 2026 crisis. Hormuz closes (day 3), Houthis block Red Sea (day 5), Saudi bypass pipeline attacked (day 8), Asian panic-buying (day 7), Gulf production damaged (day 12). Five overlapping disruptions. Budget is tight. Agent CANNOT meet all demand — must triage which markets to prioritize, when to release strategic reserves, and how to manage the most severe energy crisis in modern history.

```python
TASK_HARD = {
    "task_id": "hard_hormuz_crisis",
    "description": "STRAIT OF HORMUZ CRISIS — based on real February 2026 events. "
                   "Hormuz closed (day 3), Red Sea blocked (day 5), Saudi pipeline "
                   "attacked (day 8), Asian panic-buying (day 7), Gulf production "
                   "damaged (day 12). 20M bbl/day disrupted. Budget constrained. "
                   "You CANNOT meet all demand. Triage markets, manage reserves, "
                   "find alternative supply routes. Prevent global energy collapse.",
    "episode_length": 30,
    "total_budget": 30_000_000_000,
    "consumers": ["india", "china", "japan_korea", "europe"],
    "disruption_count": 5,
    "difficulty": "hard",
}
```

---

## PART 8: REWARD FUNCTION (rewards.py)

```python
def compute_reward(demand_fulfillment, shipment_costs, reserve_changes,
                   shortage_regions, action, budget_remaining, total_budget,
                   new_disruptions, done, day, total_days):

    reward = 0.0

    # 1. SUPPLY FULFILLMENT — main signal (per consumer region)
    for region_id, pct_met in demand_fulfillment.items():
        if pct_met >= 0.90:
            reward += 3.0              # Near-full supply
        elif pct_met >= 0.70:
            reward += 2.0              # Adequate
        elif pct_met >= 0.50:
            reward += 1.0              # Strained but functioning
        else:
            reward -= 2.0              # Shortage crisis

    # 2. SHORTAGE PENALTY — markets running dry
    reward -= len(shortage_regions) * 3.0

    # 3. COST EFFICIENCY — reward spending wisely
    if shipment_costs > 0:
        avg_cost = shipment_costs / max(sum(demand_fulfillment.values()), 0.01)
        if avg_cost < 60:
            reward += 1.0              # Below-average cost
        elif avg_cost > 100:
            reward -= 0.5              # Overspending

    # 4. RESERVE MANAGEMENT — don't drain reserves unless necessary
    for region_id, change in reserve_changes.items():
        if change < -10_000_000:       # Drawing >10M barrels
            reward -= 0.3              # Costly, but sometimes needed
        elif change > 0:
            reward += 0.1              # Building reserves is good

    # 5. PROACTIVE BONUS — rerouting before a disruption fully hits
    if action.action_type in ["reroute_shipment", "activate_alternative_supplier"]:
        if new_disruptions:
            reward += 1.5              # Acted same day as disruption

    # 6. EPISODE END
    if done:
        overall_supply = sum(demand_fulfillment.values()) / max(len(demand_fulfillment), 1)
        budget_efficiency = budget_remaining / total_budget

        if overall_supply >= 0.85:
            reward += 10.0
        elif overall_supply >= 0.70:
            reward += 5.0
        elif overall_supply >= 0.50:
            reward += 2.0

        reward += budget_efficiency * 3.0

    return reward
```

---

## PART 9: GRADERS (graders.py)

```python
def grade_episode(task_id, daily_fulfillment_history, total_spent,
                  total_budget, shortage_days, consumer_count, total_days):
    """
    Score = supply_score * 0.40 + cost_score * 0.20 +
            shortage_score * 0.25 + reserve_score * 0.15

    All deterministic, all 0.0–1.0.
    """

    # Average supply fulfillment across all regions across all days
    total_fulfillment = sum(
        sum(day.values()) / len(day) for day in daily_fulfillment_history
    )
    supply_score = total_fulfillment / total_days

    # Cost efficiency
    cost_ratio = total_spent / total_budget
    cost_score = max(0.0, 1.0 - cost_ratio)

    # Shortage-free days (higher = better)
    shortage_free_ratio = 1.0 - (shortage_days / (total_days * consumer_count))
    shortage_score = max(0.0, shortage_free_ratio)

    # Reserve management (did reserves end reasonably?)
    # Simplified: score based on not fully draining reserves
    reserve_score = 0.7  # Default, adjusted by environment state

    score = (supply_score * 0.40 +
             cost_score * 0.20 +
             shortage_score * 0.25 +
             reserve_score * 0.15)

    return round(min(max(score, 0.0), 1.0), 4)
```

---

## PART 10: ENVIRONMENT LOGIC (environment.py)

### reset()
```python
def reset(self, task_id="easy_refinery_maintenance"):
    self.task = TASKS[task_id]
    self.world = build_world()                    # Create global network
    self.disruptions = load_disruptions(task_id)  # Scripted events
    self.current_day = 0
    self.shipments = []
    self.daily_fulfillment = []
    self.total_spent = 0.0
    self.shortage_days = 0
    self.done = False
    self.global_price = 75.0                      # Base Brent price
    return self._build_observation()
```

### step(action) — One day per step
```python
def step(self, action: FuelAction):
    # 1. Validate + execute action
    cost = self._execute_action(action)
    self.total_spent += cost

    # 2. Advance day
    self.current_day += 1

    # 3. Trigger/resolve disruptions
    new_disruptions = self._process_disruptions()

    # 4. Update global oil price (based on active disruptions)
    self._update_price()

    # 5. Move shipments forward
    self._advance_shipments()

    # 6. Calculate demand fulfillment for each consumer
    fulfillment = self._calculate_fulfillment()
    self.daily_fulfillment.append(fulfillment)

    # 7. Track shortages
    shortages = [r for r, pct in fulfillment.items() if pct < 0.5]
    self.shortage_days += len(shortages)

    # 8. Consume from reserves if supply insufficient
    self._auto_draw_reserves(fulfillment)

    # 9. Check episode end
    if self.current_day >= self.task["episode_length"]:
        self.done = True

    # 10. Compute reward
    reward = compute_reward(fulfillment, cost, ...)

    return self._build_result(reward)
```

---

## PART 11: SERVER, BASELINE, DOCKERFILE, openenv.yaml

*(Same pattern as previous plans — FastAPI with /reset, /step, /state, /tasks, /grader, /baseline endpoints. Baseline uses OpenAI API with temperature=0. Dockerfile uses python:3.11-slim. openenv.yaml declares all models and tasks.)*

### openenv.yaml

```yaml
name: fuel-net-env
description: >
  Global fuel distribution network manager. Agent handles real-world
  disruptions — strait closures, pipeline attacks, sanctions, demand spikes —
  by rerouting shipments, managing strategic reserves, and activating
  alternative suppliers. Hard task based on actual 2026 Strait of Hormuz crisis.
author: Dhokla Deep Learners
version: "1.0.0"
tags:
  - openenv
  - energy
  - fuel-distribution
  - geopolitics
  - crisis-management

environment:
  observation_model: fuel_env.models.FuelObservation
  action_model: fuel_env.models.FuelAction
  reward_model: fuel_env.models.FuelReward

tasks:
  - id: easy_refinery_maintenance
    description: "Single refinery shutdown, simple rerouting"
    difficulty: easy
  - id: medium_multi_crisis
    description: "Red Sea + heatwave + sanctions cascade"
    difficulty: medium
  - id: hard_hormuz_crisis
    description: "Full Strait of Hormuz closure — based on real Feb 2026 events"
    difficulty: hard
```

---

## PART 12: DAY-BY-DAY EXECUTION PLAN

### Day 1 (March 28) — World Model + Foundation

**Mann — World & Simulation:**
- [ ] Implement `world.py` — all regions, routes, chokepoints
- [ ] Build network graph, verify connectivity
- [ ] Implement shipment tracking (creation, advancement, delivery)
- [ ] Test: shipment from Persian Gulf → India via Hormuz takes 6 days

**Dhyey — Models & Server:**
- [ ] Implement `models.py` — Observation, Action, Reward
- [ ] Scaffold FastAPI server with all endpoint stubs
- [ ] Create openenv.yaml, Dockerfile, requirements.txt
- [ ] Test: docker build succeeds, server starts

**Saomyaraj — Disruptions & Tasks:**
- [ ] Implement `disruptions.py` — all disruption types and effects
- [ ] Define all disruption scripts for 3 tasks
- [ ] Implement `tasks.py` — task configs
- [ ] Test: disruptions apply correctly (Hormuz closure blocks all Hormuz routes)

### Day 2 (March 29) — Core Environment

**Mann:**
- [ ] Implement `environment.py` — reset(), step(), state()
- [ ] Implement demand fulfillment calculation
- [ ] Implement reserve auto-draw logic
- [ ] Test: step through easy task with hardcoded actions

**Dhyey:**
- [ ] Connect environment to FastAPI endpoints
- [ ] Test all endpoints with curl
- [ ] Implement action validation
- [ ] Handle edge cases (invalid routes, over-budget shipments)

**Saomyaraj:**
- [ ] Implement `rewards.py` + `graders.py`
- [ ] Test grader produces expected scores
- [ ] Verify: perfect play on easy → score ~0.95, doing nothing → score ~0.15

### Day 3 (March 30) — Baseline + Integration

**Mann:**
- [ ] Complete all action types (reroute, release reserves, reduce demand, etc.)
- [ ] End-to-end test: play through all 3 tasks

**Dhyey:**
- [ ] Write baseline/inference.py — OpenAI API agent
- [ ] Implement /baseline and /grader endpoints
- [ ] Run baseline on easy task — verify score

**Saomyaraj:**
- [ ] Write README.md — full documentation
- [ ] Reference real 2026 Hormuz crisis, EIA data, UNCTAD report
- [ ] Document action/observation spaces, task descriptions

### Day 4 (March 31) — Deploy + Test

**All together:**
- [ ] Docker build && docker run locally
- [ ] Deploy to Hugging Face Spaces
- [ ] Verify all endpoints on live Space
- [ ] Run openenv validate
- [ ] Run baseline on deployed Space
- [ ] Attend bootcamp at 8 PM
- [ ] Add baseline scores to README

### Days 5-7 (April 1-3) — Polish + Submit

- [ ] Fix bugs, tune disruption parameters
- [ ] Improve baseline prompts with few-shot examples
- [ ] Edge case hardening
- [ ] Final submission before April 7 deadline

---

## PART 13: WHY THIS WILL WIN

**The killer advantage: This is based on events happening RIGHT NOW.**

When judges read your submission on April 10, the Strait of Hormuz crisis will still be dominating headlines. Your hard task literally simulates the biggest energy crisis of 2026. No other submission will have this level of real-world immediacy.

**Scoring projection:**

| Rubric | Score | Why |
|---|---|---|
| Real-world utility (30%) | 27-30 | This is LITERALLY happening right now. 20M bbl/day disrupted. $4T+ impact. |
| Task & grader quality (25%) | 21-24 | Three clear tiers. Hard task is unsolvable perfectly (like reality). Deterministic grading. |
| Environment design (20%) | 17-19 | Rich temporal dynamics. Cascading disruptions. Multi-objective optimization. |
| Code quality (15%) | 13-14 | Standard clean implementation. |
| Creativity & novelty (10%) | 9-10 | Nobody else will model the Hormuz crisis. Judges will immediately recognize the reference. |

**Estimated total: 87-95/100**

This is your highest-ceiling idea. The timeliness factor alone could push it to the top.
