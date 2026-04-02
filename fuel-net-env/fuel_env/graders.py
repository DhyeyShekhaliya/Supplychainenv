def grade_episode(task_id, daily_fulfillment_history, total_spent,
                  total_budget, shortage_days, consumer_count, total_days):
    """
    Score = supply_score * 0.40 + cost_score * 0.20 +
            shortage_score * 0.25 + reserve_score * 0.15

    All deterministic, all 0.0-1.0.
    """

    # Average supply fulfillment across all regions across all days
    if total_days > 0 and daily_fulfillment_history:
        total_fulfillment = sum(
            sum(day.values()) / max(len(day), 1) for day in daily_fulfillment_history
        )
        supply_score = total_fulfillment / total_days
    else:
        supply_score = 0.0

    # Cost efficiency
    cost_ratio = total_spent / max(total_budget, 1.0)
    cost_score = max(0.0, 1.0 - cost_ratio)

    # Shortage-free days (higher = better)
    shortage_free_ratio = 1.0 - (shortage_days / max((total_days * consumer_count), 1))
    shortage_score = max(0.0, shortage_free_ratio)

    # Reserve management (did reserves end reasonably?)
    # Simplified: score based on not fully draining reserves
    reserve_score = 0.7  # Default, adjusted by environment state

    score = (supply_score * 0.40 +
             cost_score * 0.20 +
             shortage_score * 0.25 +
             reserve_score * 0.15)

    return round(min(max(score, 0.0), 1.0), 4)
