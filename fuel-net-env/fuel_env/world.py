from enum import Enum
from pydantic import BaseModel
from typing import Optional, List, Dict
import copy

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
    passes_through: Optional[str] = None # Chokepoint this route uses (if any)

# Base templates for resetting environments
REGIONS_TEMPLATE = {
    # === PRODUCERS ===
    "persian_gulf": FuelRegion(
        region_id="persian_gulf",
        name="Persian Gulf (Saudi, UAE, Iraq, Kuwait, Qatar)",
        region_type=RegionType.PRODUCER,
        production_capacity=20_000_000,
        current_output=18_000_000,
        demand=2_000_000,
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
        demand=20_000_000,
        storage_capacity=700_000_000,
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
        production_capacity=800_000,
        current_output=750_000,
        demand=5_500_000,
        storage_capacity=40_000_000,
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
        production_capacity=3_000_000,
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

ROUTES_TEMPLATE = [
    # Persian Gulf exports
    FuelRoute(route_id="pg_hormuz", from_region="persian_gulf", to_region="hormuz", route_type="sea", normal_transit_days=1, current_transit_days=1, cost_per_barrel=2.0, capacity_per_day=20_000_000, active=True, passes_through=None),
    FuelRoute(route_id="hormuz_india", from_region="hormuz", to_region="india", route_type="sea", normal_transit_days=5, current_transit_days=5, cost_per_barrel=3.0, capacity_per_day=5_000_000, active=True, passes_through="hormuz"),
    FuelRoute(route_id="hormuz_china", from_region="hormuz", to_region="china", route_type="sea", normal_transit_days=15, current_transit_days=15, cost_per_barrel=5.0, capacity_per_day=6_000_000, active=True, passes_through="hormuz"),
    FuelRoute(route_id="hormuz_japan", from_region="hormuz", to_region="japan_korea", route_type="sea", normal_transit_days=12, current_transit_days=12, cost_per_barrel=4.5, capacity_per_day=4_000_000, active=True, passes_through="hormuz"),
    FuelRoute(route_id="hormuz_suez", from_region="hormuz", to_region="suez", route_type="sea", normal_transit_days=4, current_transit_days=4, cost_per_barrel=2.5, capacity_per_day=4_000_000, active=True, passes_through="hormuz"),
    FuelRoute(route_id="suez_europe", from_region="suez", to_region="europe", route_type="sea", normal_transit_days=7, current_transit_days=7, cost_per_barrel=3.5, capacity_per_day=5_000_000, active=True, passes_through="suez"),

    # Bypass pipelines (Saudi East-West, UAE ADCOP)
    FuelRoute(route_id="pg_bypass_pipe", from_region="persian_gulf", to_region="suez", route_type="pipeline", normal_transit_days=2, current_transit_days=2, cost_per_barrel=4.0, capacity_per_day=7_000_000, active=True, passes_through=None),

    # Cape of Good Hope (long route bypassing Hormuz+Suez)
    FuelRoute(route_id="pg_cape_europe", from_region="persian_gulf", to_region="europe", route_type="sea", normal_transit_days=35, current_transit_days=35, cost_per_barrel=8.0, capacity_per_day=3_000_000, active=True, passes_through=None),
    FuelRoute(route_id="pg_cape_india", from_region="persian_gulf", to_region="india", route_type="sea", normal_transit_days=25, current_transit_days=25, cost_per_barrel=7.0, capacity_per_day=2_000_000, active=True, passes_through=None),

    # Russia exports
    FuelRoute(route_id="russia_europe_pipe", from_region="russia", to_region="europe", route_type="pipeline", normal_transit_days=3, current_transit_days=3, cost_per_barrel=3.0, capacity_per_day=4_000_000, active=True, passes_through=None),
    FuelRoute(route_id="russia_china_pipe", from_region="russia", to_region="china", route_type="pipeline", normal_transit_days=5, current_transit_days=5, cost_per_barrel=3.5, capacity_per_day=2_000_000, active=True, passes_through=None),
    FuelRoute(route_id="russia_india_sea", from_region="russia", to_region="india", route_type="sea", normal_transit_days=20, current_transit_days=20, cost_per_barrel=5.5, capacity_per_day=1_500_000, active=True, passes_through=None),

    # US exports
    FuelRoute(route_id="us_europe_sea", from_region="us_shale", to_region="europe", route_type="sea", normal_transit_days=12, current_transit_days=12, cost_per_barrel=5.0, capacity_per_day=3_000_000, active=True, passes_through=None),
    FuelRoute(route_id="us_india_sea", from_region="us_shale", to_region="india", route_type="sea", normal_transit_days=25, current_transit_days=25, cost_per_barrel=7.0, capacity_per_day=1_000_000, active=True, passes_through=None),
    FuelRoute(route_id="us_japan_sea", from_region="us_shale", to_region="japan_korea", route_type="sea", normal_transit_days=18, current_transit_days=18, cost_per_barrel=6.0, capacity_per_day=2_000_000, active=True, passes_through=None),

    # West Africa exports
    FuelRoute(route_id="wa_europe_sea", from_region="west_africa", to_region="europe", route_type="sea", normal_transit_days=10, current_transit_days=10, cost_per_barrel=4.0, capacity_per_day=2_000_000, active=True, passes_through=None),
    FuelRoute(route_id="wa_india_sea", from_region="west_africa", to_region="india", route_type="sea", normal_transit_days=15, current_transit_days=15, cost_per_barrel=5.0, capacity_per_day=1_500_000, active=True, passes_through=None),
    FuelRoute(route_id="wa_china_sea", from_region="west_africa", to_region="china", route_type="sea", normal_transit_days=22, current_transit_days=22, cost_per_barrel=6.0, capacity_per_day=1_000_000, active=True, passes_through=None),

    # Malacca Strait routes
    FuelRoute(route_id="malacca_china", from_region="malacca", to_region="china", route_type="sea", normal_transit_days=3, current_transit_days=3, cost_per_barrel=1.5, capacity_per_day=8_000_000, active=True, passes_through="malacca"),
    FuelRoute(route_id="malacca_japan", from_region="malacca", to_region="japan_korea", route_type="sea", normal_transit_days=5, current_transit_days=5, cost_per_barrel=2.0, capacity_per_day=4_000_000, active=True, passes_through="malacca"),
]

def build_world():
    """Returns a deepcopy of regions and routes for a fresh environment."""
    regions_copy = {k: v.copy(deep=True) for k, v in REGIONS_TEMPLATE.items()}
    routes_copy = [r.copy(deep=True) for r in ROUTES_TEMPLATE]
    return regions_copy, routes_copy
