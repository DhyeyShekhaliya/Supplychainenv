import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fuel_env.environment import FuelEnvironment
from fuel_env.models import FuelAction
from fuel_env.graders import grade_episode

def run_task(task_id):
    print(f"=== Testing E2E: {task_id} ===")
    env = FuelEnvironment()
    obs = env.reset(task_id)
    
    # Simple hold loop to ensure no crashes during the full duration of disruptions
    done = False
    while not done:
        action = FuelAction(action_type="hold", parameters={})
        obs, reward, done, info = env.step(action)
    
    score = grade_episode(
        task_id=env.task["task_id"],
        daily_fulfillment_history=env.daily_fulfillment,
        total_spent=env.total_spent,
        total_budget=env.task["total_budget"],
        shortage_days=env.shortage_days,
        consumer_count=len([r for r in env.regions.values() if r.region_type.value == "consumer"]),
        total_days=env.task["episode_length"]
    )
    print(f"{task_id} finished successfully. 'Hold' Grader Score: {score:.4f}\n")

if __name__ == '__main__':
    run_task("easy_refinery_maintenance")
    run_task("medium_multi_crisis")
    run_task("hard_hormuz_crisis")
    print("All tests passed without crashing!")
