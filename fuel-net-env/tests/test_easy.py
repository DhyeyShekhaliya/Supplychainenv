import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fuel_env.environment import FuelEnvironment
from fuel_env.models import FuelAction
from fuel_env.graders import grade_episode
import json

def test_easy():
    env = FuelEnvironment()
    obs = env.reset("easy_refinery_maintenance")
    print(f"Initial day: {obs.current_day}, Done: {obs.done}")
    
    # Run a perfect play-like sequence doing nothing except waiting for auto-draw
    # Wait, perfect play might require shipping fuel. We will just "hold"
    
    for day in range(15):
        action = FuelAction(action_type="hold", parameters={})
        obs, reward, done, info = env.step(action)
        print(f"Day {day+1}: Reward: {reward:.2f}, Global coverage: {obs.global_supply_coverage:.2f}")

    score = grade_episode(
        task_id=env.task["task_id"],
        daily_fulfillment_history=env.daily_fulfillment,
        total_spent=env.total_spent,
        total_budget=env.task["total_budget"],
        shortage_days=env.shortage_days,
        consumer_count=len([r for r in env.regions.values() if r.region_type.value == "consumer"]),
        total_days=env.task["episode_length"]
    )
    print(f"Final Grader Score doing 'nothing': {score}")

if __name__ == '__main__':
    test_easy()
