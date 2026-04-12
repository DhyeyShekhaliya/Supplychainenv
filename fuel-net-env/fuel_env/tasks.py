TASK_VERY_EASY = {
    "task_id": "very_easy_startup",
    "description": "Baseline startup scenario with no disruptions. Simply route fuel to meet normal demand.",
    "episode_length": 10,
    "total_budget": 3_000_000_000,
    "consumers": ["india", "china", "japan_korea", "europe"],
    "disruption_count": 0,
    "difficulty": "very_easy",
    "ground_truth_explanation": "Establish a structural equilibrium targeting precise demand satisfaction across all four consumer regions. Since there are no disruptions, the optimal policy leverages the most cost-effective and high-capacity maritime and pipeline routes to strictly fulfill baseline structural deficits without drawing down strategic reserves.",
}

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
    "ground_truth_explanation": "Promptly recognize the 30% supply drop in the Persian Gulf and re-balance global outflows. Prioritize continuous fulfillment to Asian markets by offsetting the Gulf deficit with scaled-up shipments from US Shale or West Africa before local reserves are depleted.",
}

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
    "ground_truth_explanation": "A dynamic triage strategy is required. Proactively ship to Europe via US/West Africa before the Russian pipeline sanctions hit. Divert Persian Gulf shipments targeting Europe toward India to cover the massive 60% heatwave demand spike. Accept higher transit costs to bypass the blocked Suez Canal.",
}

TASK_HARD = {
    "task_id": "hard_hormuz_crisis",
    "description": "STRAIT OF HORMUZ CRISIS -- based on real February 2026 events. "
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
    "ground_truth_explanation": "Radical budget preservation and strategic reserves pacing. With Hormuz closed and 20M+ bbl/day lost, global fulfillment is impossible. The optimal strategy utilizes US Shale and West African supply exclusively through non-chokepoint routes (like the Cape of Good Hope). Ration existing supplies, prioritizing cost-efficiency over 100% fulfillment.",
}

TASK_EXTREME = {
    "task_id": "extreme_global_crisis",
    "description": "A devastating global scenario. Suez is blocked, Strait of Malacca faces piracy, "
                   "and US shale production drops. Route fuel creatively around the globe.",
    "episode_length": 40,
    "total_budget": 40_000_000_000,
    "consumers": ["india", "china", "japan_korea", "europe"],
    "disruption_count": 7,
    "difficulty": "extreme",
    "ground_truth_explanation": "Complete structural supply chain breakdown. Must immediately authorize maximum reserve withdrawals for all critical zones while initiating cross-hemisphere long-haul routing (e.g. West Africa to Japan/Korea) completely ignoring baseline transit costs. The primary goal is preventing zero-supply events via aggressive emergency spot routing.",
}

TASKS = {
    "very_easy_startup": TASK_VERY_EASY,
    "easy_refinery_maintenance": TASK_EASY,
    "medium_multi_crisis": TASK_MEDIUM,
    "hard_hormuz_crisis": TASK_HARD,
    "extreme_global_crisis": TASK_EXTREME,
}
