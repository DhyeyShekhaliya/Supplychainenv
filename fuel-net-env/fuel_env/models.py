from pydantic import BaseModel
from typing import List, Dict, Optional

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
    regions: List[Dict]                # Each region's current status
    routes: List[Dict]                 # Each route's current status
    global_oil_price: float            # $/barrel (Brent equivalent)

    # Disruptions
    active_disruptions: List[Dict]
    new_alerts: List[str]              # New events this day

    # Shipments
    active_shipments: List[ShipmentStatus]
    newly_delivered: List[ShipmentStatus]  # Ships that arrived this morning
    completed_deliveries: int
    failed_deliveries: int             # Markets that ran dry

    # Demand fulfillment by region
    demand_fulfillment: Dict[str, float]   # region_id -> % demand met today

    # Strategic reserves
    reserve_levels: Dict[str, Dict]    # region_id -> {current, capacity, days_of_cover}

    # Budget
    total_budget: float
    spent: float
    remaining_budget: float

    # Performance
    global_supply_coverage: float      # 0.0-1.0 across all consumers
    average_cost_per_barrel: float
    markets_in_shortage: List[str]     # Regions with <50% demand met

    done: bool
    message: str

class FuelAction(BaseModel):
    action_type: str
    parameters: dict
    reasoning: Optional[str] = ""

class FuelReward(BaseModel):
    total: float
    supply_fulfillment_reward: float   # Per-region demand met
    cost_efficiency_reward: float      # Lower cost = bonus
    shortage_penalty: float            # Markets running dry
    reserve_management_reward: float   # Smart reserve usage
    proactive_bonus: float             # Acting before crisis hits
    wasteful_spending_penalty: float   # Overpaying when cheaper options exist
