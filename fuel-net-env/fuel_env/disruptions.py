from enum import Enum
from pydantic import BaseModel
from typing import List

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
    affected_entities: List[str]       # Region IDs or route IDs
    severity: float                    # 0.0-1.0
    description: str
    price_impact: float                # $/barrel price increase globally
    resolved: bool = False

EASY_DISRUPTIONS = [
    Disruption(
        disruption_id="e1",
        disruption_type=DisruptionType.REFINERY_SHUTDOWN,
        trigger_day=3,
        duration_days=5,
        affected_entities=["persian_gulf"],
        severity=0.3,
        description="Scheduled maintenance at Saudi Ras Tanura refinery. Persian Gulf output reduced by 30% for 5 days.",
        price_impact=5.0,
    ),
]

MEDIUM_DISRUPTIONS = [
    Disruption(
        disruption_id="m1",
        disruption_type=DisruptionType.HOUTHI_ATTACK,
        trigger_day=3,
        duration_days=8,
        affected_entities=["suez"],
        severity=0.8,
        description="Houthi forces resume attacks on Red Sea shipping. Suez Canal transit suspended. Europe-bound tankers must reroute via Cape of Good Hope (+3 weeks transit time).",
        price_impact=12.0,
    ),
    Disruption(
        disruption_id="m2",
        disruption_type=DisruptionType.DEMAND_SPIKE,
        trigger_day=6,
        duration_days=5,
        affected_entities=["india"],
        severity=0.6,
        description="Indian summer heatwave. Electricity demand surges, driving diesel generator use up 60%. India demand increases from 5.5M to 8M bbl/day.",
        price_impact=3.0,
    ),
    Disruption(
        disruption_id="m3",
        disruption_type=DisruptionType.SANCTIONS,
        trigger_day=10,
        duration_days=10,
        affected_entities=["russia_europe_pipe"],
        severity=1.0,
        description="EU announces new sanctions on Russian oil. Russia-Europe pipeline flow cut to zero.",
        price_impact=8.0,
    ),
]

HARD_DISRUPTIONS = [
    Disruption(
        disruption_id="h1",
        disruption_type=DisruptionType.CHOKEPOINT_CLOSURE,
        trigger_day=3,
        duration_days=15,
        affected_entities=["hormuz"],
        severity=1.0,
        description="STRAIT OF HORMUZ CLOSED. Military conflict between Iran and US/Israel. All tanker traffic through Hormuz suspended. 20M bbl/day cut off. Bypass pipeline at 7M max. This is a global energy emergency.",
        price_impact=35.0,
    ),
    Disruption(
        disruption_id="h2",
        disruption_type=DisruptionType.HOUTHI_ATTACK,
        trigger_day=5,
        duration_days=12,
        affected_entities=["suez"],
        severity=0.9,
        description="Houthis resume Red Sea attacks in solidarity with Iran. Suez/Bab al-Mandeb routes suspended. Cape of Good Hope is now the ONLY sea route from Gulf to Europe.",
        price_impact=15.0,
    ),
    Disruption(
        disruption_id="h3",
        disruption_type=DisruptionType.PIPELINE_ATTACK,
        trigger_day=8,
        duration_days=6,
        affected_entities=["pg_bypass_pipe"],
        severity=0.5,
        description="Iranian missile strikes damage Saudi East-West pipeline. Bypass pipeline capacity halved from 7M to 3.5M bbl/day.",
        price_impact=10.0,
    ),
    Disruption(
        disruption_id="h4",
        disruption_type=DisruptionType.DEMAND_SPIKE,
        trigger_day=7,
        duration_days=10,
        affected_entities=["india", "china", "japan_korea"],
        severity=0.7,
        description="Asian nations panic-buying to fill strategic reserves. Demand in India +40%, China +25%, Japan/Korea +30%.",
        price_impact=8.0,
    ),
    Disruption(
        disruption_id="h5",
        disruption_type=DisruptionType.PRODUCTION_CUT,
        trigger_day=12,
        duration_days=8,
        affected_entities=["persian_gulf"],
        severity=0.4,
        description="Gulf state refineries damaged in conflict. Persian Gulf output drops 40% even if strait reopens.",
        price_impact=12.0,
    ),
]

def load_disruptions(task_id: str):
    import copy
    if "easy" in task_id:
        return [d.copy(deep=True) for d in EASY_DISRUPTIONS]
    elif "medium" in task_id:
        return [d.copy(deep=True) for d in MEDIUM_DISRUPTIONS]
    elif "hard" in task_id:
        return [d.copy(deep=True) for d in HARD_DISRUPTIONS]
    else:
        return []
