from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Union, List
import uvicorn

import traceback
from fuel_env.environment import FuelEnvironment
from fuel_env.models import FuelAction
from fuel_env.graders import grade_episode
from fuel_env.tasks import TASKS

app = FastAPI(title="FuelNetEnv API")
env = FuelEnvironment()

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    print(f"🔥 SERVER CRASH: {exc}")
    traceback.print_exc()
    return HTTPException(status_code=500, detail=str(exc))

@app.post("/reset")
def reset_env(task_id: str = "easy_refinery_maintenance"):
    obs = env.reset(task_id)
    return obs.model_dump()

@app.post("/step")
def step_env(action: Union[FuelAction, List[FuelAction]]):
    if env.done:
        raise HTTPException(status_code=400, detail="Episode already done. Please reset.")
    obs, reward, done, info = env.step(action)
    return {"observation": obs.model_dump(), "reward": reward, "done": done, "info": info}

@app.get("/state")
def get_state():
    obs = env._build_observation()
    return obs.model_dump()

@app.get("/tasks")
def get_tasks():
    return TASKS

@app.post("/grader")
def run_grader():
    score = grade_episode(
        task_id=env.task["task_id"],
        daily_fulfillment_history=env.daily_fulfillment,
        total_spent=env.total_spent,
        total_budget=env.task["total_budget"],
        shortage_days=env.shortage_days,
        consumer_count=len([r for r in env.regions.values() if r.region_type.value == "consumer"]),
        total_days=env.task["episode_length"]
    )
    return {"score": score}

@app.post("/baseline")
def run_baseline(task_id: str = "easy_refinery_maintenance"):
    import subprocess
    import sys
    try:
        # We run it as a subprocess so it doesn't block the server loop if connected via HTTP
        # Or better, just return advice since /baseline is typically run independently
        return {
            "message": "Baseline is an external client script. Run `python baseline/inference.py` to trigger the agent." 
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
