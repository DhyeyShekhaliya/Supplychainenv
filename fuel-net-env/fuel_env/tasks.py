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
}

TASKS = {
    "easy_refinery_maintenance": TASK_EASY,
    "medium_multi_crisis": TASK_MEDIUM,
    "hard_hormuz_crisis": TASK_HARD,
}
