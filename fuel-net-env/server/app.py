import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    print(f"🔥 SERVER CRASH: {exc}")
    traceback.print_exc()
    return HTTPException(status_code=500, detail=str(exc))

@app.get("/", response_class=FileResponse)
def index():
    html_path = os.path.join(static_dir, "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"message": "Frontend building..."}

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

@app.get("/config")
def get_config():
    return {"task": env.task}

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

@app.post("/run_step_advanced")
def run_step_advanced():
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from inference import llm_agent_action, call_llm_with_retry

    if env.done:
        return {"done": True, "error": "Episode finished"}

    obs_d = env._build_observation().model_dump()
    action_dict = llm_agent_action(obs_d)

    # Normalize LLM output: wrap any format into FuelAction schema
    ROUTE_LOOKUP = {r.get('route_id'): r for r in obs_d.get('routes', [])}
    
    def normalize_action(a):
        # Unwrap nested "ship_fuel" / "hold" keys
        if "ship_fuel" in a:
            inner = a["ship_fuel"]
            if isinstance(inner, list):
                return [normalize_action(x) for x in inner]
            a = inner
        if "hold" in a:
            return {"action_type": "hold", "parameters": {}}
        
        # Already correct format
        if "action_type" in a and "parameters" in a:
            p = a["parameters"]
            # Fill missing from/to from route lookup
            rid = p.get("route") or p.get("route_id", "")
            if rid and rid in ROUTE_LOOKUP:
                r = ROUTE_LOOKUP[rid]
                if not p.get("from"): p["from"] = r.get("from_region", "")
                if not p.get("to"): p["to"] = r.get("to_region", "")
                if "route_id" in p: p["route"] = p.pop("route_id")
            if p.get("volume"): p["volume"] = int(float(p["volume"]))
            return a
        
        # Flat format: {"route_id": "x", "volume": 5000000, ...}
        if "route_id" in a or "route" in a or "from" in a:
            rid = a.get("route_id") or a.get("route", "")
            params = {"route": rid, "volume": int(float(a.get("volume", 5000000)))}
            if rid and rid in ROUTE_LOOKUP:
                r = ROUTE_LOOKUP[rid]
                params["from"] = a.get("from") or a.get("source") or a.get("producer") or r.get("from_region", "")
                params["to"] = a.get("to") or a.get("destination") or a.get("consumer") or r.get("to_region", "")
            else:
                params["from"] = a.get("from", "")
                params["to"] = a.get("to", "")
            if not params["from"] or not params["to"]:
                return {"action_type": "hold", "parameters": {}}
            return {"action_type": "ship_fuel", "parameters": params}
        return {"action_type": "hold", "parameters": {}}
    
    normalized = []
    if isinstance(action_dict, list):
        for a in action_dict:
            result = normalize_action(a)
            if isinstance(result, list):
                normalized.extend(result)
            else:
                normalized.append(result)
    elif isinstance(action_dict, dict):
        result = normalize_action(action_dict)
        normalized = result if isinstance(result, list) else [result]
    action_dict = normalized if normalized else [{"action_type": "hold", "parameters": {}}]

    try:
        total_days = env.task["episode_length"]
        reasoning_prompt = [
            {"role": "system", "content": "You are a crisis analyst. Give a 1-sentence briefing on the situation. No JSON."},
            {"role": "user", "content": f"Task: {obs_d.get('task_description')}\nShortages: {obs_d.get('markets_in_shortage')}\nDay: {obs_d.get('current_day')}/{total_days}"}
        ]
        full_output = call_llm_with_retry(reasoning_prompt)
        last_reasoning = ""
        if full_output:
            last_reasoning = full_output.strip().replace('\n', ' ') + " 🤖"
            if isinstance(action_dict, list) and len(action_dict) > 0:
                action_dict[0]["reasoning"] = last_reasoning
            elif isinstance(action_dict, dict):
                action_dict["reasoning"] = last_reasoning
    except Exception as e:
        last_reasoning = f"Analysis limited: {str(e)}"
        
    if isinstance(action_dict, list):
        parsed_actions = [FuelAction(**a) for a in action_dict]
    else:
        parsed_actions = FuelAction(**action_dict)

    try:
        obs, reward, done, info = env.step(parsed_actions)
    except Exception as step_err:
        import sys
        print(f"[ENV DEBUG] env.step failed: {step_err}", file=sys.stderr)
        return {"observation": obs_d, "reward": 0, "done": False, "action": action_dict, "reasoning": f"Step error: {step_err}"}
    
    return {
        "observation": obs.model_dump(),
        "reward": reward,
        "done": done,
        "action": action_dict,
        "reasoning": last_reasoning
    }

@app.post("/grader_ui")
def run_grader_ui():
    from fuel_env.graders import grade_episode
    score = grade_episode(
        task_id=env.task["task_id"],
        daily_fulfillment_history=env.daily_fulfillment,
        total_spent=env.total_spent,
        total_budget=env.task["total_budget"],
        shortage_days=env.shortage_days,
        consumer_count=len([r for r in env.regions.values() if getattr(r.region_type, "value", r.region_type) == "consumer"]),
        total_days=env.task["episode_length"]
    )
    return {"score": min(max(score, 0.001), 0.999)}

def main():
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860, reload=False)

if __name__ == "__main__":
    main()
