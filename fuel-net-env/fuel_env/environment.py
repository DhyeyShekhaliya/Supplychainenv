import uuid
from typing import Union, List
from fuel_env.models import FuelObservation, FuelAction, ShipmentStatus
from fuel_env.world import build_world, RegionType
from fuel_env.disruptions import load_disruptions
from fuel_env.tasks import TASKS
from fuel_env.rewards import compute_reward

class FuelEnvironment:
    def __init__(self):
        self.reset()
        
    def reset(self, task_id="easy_refinery_maintenance"):
        if task_id not in TASKS:
            task_id = "easy_refinery_maintenance"
        self.task = TASKS[task_id]
        self.regions, self.routes = build_world()
        self.disruptions = load_disruptions(task_id)
        self.current_day = 0
        self.shipments = []
        self.daily_fulfillment = []
        self.total_spent = 0.0
        self.shortage_days = 0
        self.done = False
        self.global_price = 75.0
        self.new_alerts = []
        self.failed_deliveries = 0
        self.completed_deliveries = 0
        self.newly_delivered = []  # Track arrivals this step
        return self._build_observation()
        
    def step(self, action: Union[FuelAction, List[FuelAction]]):
        self.new_alerts = []
        cost = 0.0
        
        # Execute action(s)
        if isinstance(action, list):
            for a in action:
                cost += self._execute_action(a)
        else:
            cost = self._execute_action(action)
            
        self.total_spent += cost

        self.current_day += 1

        new_disruptions = self._process_disruptions()
        self._update_price()
        
        self.newly_delivered = self._advance_shipments()

        fulfillment, reserve_changes = self._calculate_fulfillment_and_reserves(self.newly_delivered)
        self.daily_fulfillment.append(fulfillment)

        shortage_regions = [r for r, pct in fulfillment.items() if pct < 0.5]
        self.shortage_days += len(shortage_regions)

        if self.current_day >= self.task["episode_length"]:
            self.done = True

        reward = compute_reward(
            demand_fulfillment=fulfillment,
            shipment_costs=cost,
            reserve_changes=reserve_changes,
            shortage_regions=shortage_regions,
            action=action,
            budget_remaining=self.task["total_budget"] - self.total_spent,
            total_budget=self.task["total_budget"],
            new_disruptions=len(new_disruptions) > 0,
            done=self.done,
            day=self.current_day,
            total_days=self.task["episode_length"]
        )

        # 📊 Internal logging silenced for high-fidelity agent dashboard
        # print(f"\n--- 🌏 Day {self.current_day} Update ---")
        # for r, pct in fulfillment.items():
        #     status = "✅" if pct >= 0.9 else "⚠️" if pct >= 0.5 else "🚨"
        #     print(f"  {status} {r.replace('_', ' ').capitalize()}: {pct*100:.1f}% supply")
        
        # for r, change in reserve_changes.items():
        #     if change < -500000:
        #         print(f"  🔋 Reserves: Drawing {abs(change)/1000000:.1f}M bbl in {r}")
        
        # if cost > 0:
        #     print(f"  💸 Cost: ${cost/1000000:.1f}M spent on {action.action_type}")
        
        # if new_disruptions:
        #     for d_msg in self.new_alerts:
        #         if "Disruption ended" not in d_msg:
        #             print(f"  🔥 CRISIS ALERT: {d_msg}")

        # print(f"  ⭐ Step Reward: {reward:+.2f}")

        return self._build_observation(), reward, self.done, {}

    def _execute_action(self, action: FuelAction):
        cost = 0.0
        if action.action_type == "ship_fuel":
            params = action.parameters
            r_id = params.get("route")
            vol = params.get("volume", 0)
            route = next((r for r in self.routes if r.route_id == r_id), None)
            if route and route.active:
                shipment = ShipmentStatus(
                    shipment_id=str(uuid.uuid4())[:8],
                    from_region=params.get("from", ""),
                    to_region=params.get("to", ""),
                    volume_barrels=vol,
                    route_id=r_id,
                    days_in_transit=0,
                    days_remaining=route.current_transit_days,
                    cost_so_far=0.0
                )
                self.shipments.append(shipment)
                cost = vol * route.cost_per_barrel
        elif action.action_type == "reroute_shipment":
            params = action.parameters
            s_id = params.get("shipment_id")
            new_route_id = params.get("new_route")
            shipment = next((s for s in self.shipments if s.shipment_id == s_id), None)
            new_route = next((r for r in self.routes if r.route_id == new_route_id), None)
            if shipment and new_route and new_route.active:
                shipment.route_id = new_route_id
                shipment.days_remaining += 2 
                cost = shipment.volume_barrels * new_route.cost_per_barrel * 0.5
        elif action.action_type == "release_reserves":
            params = action.parameters
            region_id = params.get("region")
            vol = params.get("volume", 0)
            region = self.regions.get(region_id)
            if region and region.current_storage >= vol:
                region.current_storage -= vol
        elif action.action_type == "reduce_demand":
            params = action.parameters
            region_id = params.get("region")
            reduction = params.get("reduction_percent", 0)
            region = self.regions.get(region_id)
            if region:
                region.demand = int(region.demand * (1.0 - (reduction/100.0)))
                cost = reduction * 10_000_000 
                
        return cost

    def _process_disruptions(self):
        new_active = []
        for d in self.disruptions:
            if d.trigger_day == self.current_day and not d.resolved:
                self.new_alerts.append(d.description)
                new_active.append(d)
                
                if d.disruption_type == "chokepoint_closure":
                    for entity in d.affected_entities:
                        for r in self.routes:
                            if r.passes_through == entity or r.to_region == entity or r.from_region == entity:
                                r.active = False
                                r.current_transit_days = 999
                elif d.disruption_type == "houthi_attack":
                    for r in self.routes:
                        if r.passes_through == "suez" or r.to_region == "suez":
                            r.active = False
                elif d.disruption_type == "demand_spike":
                    for entity in d.affected_entities:
                        if entity in self.regions:
                            self.regions[entity].demand = int(self.regions[entity].demand * 1.3)
                elif d.disruption_type == "pipeline_attack":
                    for entity in d.affected_entities:
                        for r in self.routes:
                            if r.route_id == entity:
                                r.capacity_per_day = int(r.capacity_per_day * 0.5)
                elif d.disruption_type == "refinery_shutdown" or d.disruption_type == "production_cut":
                    for entity in d.affected_entities:
                        if entity in self.regions:
                            self.regions[entity].current_output = int(self.regions[entity].current_output * (1.0 - d.severity))
                elif d.disruption_type == "sanctions":
                    for entity in d.affected_entities:
                        for r in self.routes:
                            if r.route_id == entity:
                                r.active = False
            
            if self.current_day == d.trigger_day + d.duration_days and not d.resolved:
                d.resolved = True
                self.new_alerts.append(f"Disruption ended: {d.description}")
                # We do not fully model restoring exact previous state perfectly to keep logic simple,
                # but we re-activate routes:
                for r in self.routes:
                    if r.current_transit_days == 999 or not r.active:
                        r.active = True
                        r.current_transit_days = r.normal_transit_days
        return new_active
        
    def _update_price(self):
        price = 75.0
        for d in self.disruptions:
            if d.trigger_day <= self.current_day < (d.trigger_day + d.duration_days):
                price += d.price_impact
        self.global_price = price

    def _advance_shipments(self):
        delivered = []
        active = []
        for s in self.shipments:
            s.days_in_transit += 1
            route = next((r for r in self.routes if r.route_id == s.route_id), None)
            if route and not route.active:
                s.days_remaining += 1 # Stuck
            else:
                s.days_remaining -= 1
                
            if s.days_remaining <= 0:
                delivered.append(s)
                self.completed_deliveries += 1
            else:
                active.append(s)
        self.shipments = active
        return delivered

    def _calculate_fulfillment_and_reserves(self, delivered_shipments):
        fulfillment = {}
        reserve_changes = {r: 0 for r in self.regions}
        
        delivery_volumes = {r: 0 for r in self.regions}
        for s in delivered_shipments:
            delivery_volumes[s.to_region] += s.volume_barrels
            
        for r_id, region in self.regions.items():
            if region.region_type == RegionType.CONSUMER:
                target_demand = region.demand
                if target_demand == 0:
                    fulfillment[r_id] = 1.0
                    continue
                    
                supply = region.current_output + delivery_volumes[r_id]
                
                shortfall = target_demand - supply
                if shortfall > 0:
                    draw_amount = min(shortfall, region.current_storage)
                    region.current_storage -= draw_amount
                    supply += draw_amount
                    reserve_changes[r_id] -= draw_amount
                
                pct = supply / target_demand
                fulfillment[r_id] = min(1.0, pct)
                
        return fulfillment, reserve_changes

    def _build_observation(self):
        active_disruptions = [d.model_dump() for d in self.disruptions if d.trigger_day <= self.current_day < (d.trigger_day + d.duration_days)]
        
        reserve_levels = {r_id: {"current": r.current_storage, "capacity": r.storage_capacity, "days_of_cover": r.current_storage / max(r.demand, 1)} for r_id, r in self.regions.items()}
        
        obs = FuelObservation(
            task_id=self.task["task_id"],
            task_description=self.task["description"],
            difficulty=self.task["difficulty"],
            current_day=self.current_day,
            total_days=self.task["episode_length"],
            regions=[r.model_dump() for r in self.regions.values()],
            routes=[r.model_dump() for r in self.routes],
            global_oil_price=self.global_price,
            active_disruptions=active_disruptions,
            new_alerts=self.new_alerts,
            active_shipments=self.shipments,
            newly_delivered=self.newly_delivered,
            completed_deliveries=self.completed_deliveries,
            failed_deliveries=self.failed_deliveries,
            demand_fulfillment=self.daily_fulfillment[-1] if self.daily_fulfillment else {r.region_id: 1.0 for r in self.regions.values() if r.region_type == RegionType.CONSUMER},
            reserve_levels=reserve_levels,
            total_budget=self.task["total_budget"],
            spent=self.total_spent,
            remaining_budget=self.task["total_budget"] - self.total_spent,
            global_supply_coverage=sum(self.daily_fulfillment[-1].values())/max(len(self.daily_fulfillment[-1]), 1) if self.daily_fulfillment else 1.0,
            average_cost_per_barrel=self.total_spent / max(self.completed_deliveries * 1000000, 1),
            markets_in_shortage=[r for r, pct in (self.daily_fulfillment[-1].items() if self.daily_fulfillment else {}) if pct < 0.5],
            done=self.done,
            message="Day completed" if self.current_day > 0 else "Environment reset"
        )
        return obs
