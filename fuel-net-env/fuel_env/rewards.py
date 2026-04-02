from fuel_env.models import FuelAction

def compute_reward(demand_fulfillment, shipment_costs, reserve_changes,
                   shortage_regions, action: FuelAction, budget_remaining, total_budget,
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
