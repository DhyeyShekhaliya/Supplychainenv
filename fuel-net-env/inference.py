import os
import requests
import json
from openai import OpenAI

# ─── MANDATORY HACKATHON CONFIGURATION ───────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://integrate.api.nvidia.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "meta/llama-3.1-8b-instruct")
HF_TOKEN = os.getenv("HF_TOKEN", os.getenv("NVIDIA_API_KEY", "dummy"))

# Initialize OpenAI client referencing the strict standard
try:
    client = OpenAI(
        base_url=API_BASE_URL,
        api_key=HF_TOKEN
    )
except Exception:
    client = None


ENV_BASE_URL = "http://localhost:7860"

def call_llm_with_retry(messages, model="meta/llama-3.1-8b-instruct", max_retries=3):
    import time
    for attempt in range(max_retries):
        try:
            if not client: return ""
            completion = client.chat.completions.create(model=model, messages=messages, temperature=0.6, top_p=0.9, max_tokens=256)
            return completion.choices[0].message.content
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                time.sleep(3)
            else:
                return ""
    return ""

def rule_based_action(obs):
    """Baseline logistics rules acting as the fallback engine."""
    actions = []
    try:
        consumers = [r for r in obs.get("regions", []) if r.get("region_type") == "consumer"]
        fulfillment = obs.get("demand_fulfillment", {})
        routes = obs.get("routes", [])

        for region in consumers:
            r_id = region["region_id"]
            if fulfillment.get(r_id, 1.0) < 0.99:
                viable = sorted(
                    [r for r in routes if r.get("to_region") == r_id and r.get("active", True)],
                    key=lambda r: r.get("current_transit_days", 999)
                )
                if viable:
                    best_route = viable[0]
                    volume = min(region.get("demand", 5000000), best_route.get("capacity_per_day", 5000000))
                    actions.append({
                        "action_type": "ship_fuel",
                        "parameters": {
                            "from": best_route.get("from_region", ""), "to": r_id,
                            "route": best_route.get("route_id", ""), "volume": int(volume)
                        }
                    })
        
        if not actions:
            return [{"action_type": "hold", "parameters": {}}]
        return actions
    except Exception:
        return [{"action_type": "hold", "parameters": {}}]

def llm_agent_action(obs):
    """Uses LLM to select actions dynamically. Falls back to baseline on failure."""
    state_desc = f"""
    You are an AI logistics director.
    Day: {obs.get('current_day', 0)}/30
    Shortages: {obs.get('markets_in_shortage', [])}
    
    Output ONLY a valid JSON array of actions:
    [{{ "action_type": "ship_fuel", "parameters": {{"from": "us_shale", "to": "europe", "volume": 5000000}} }}]
    Or [{{ "action_type": "hold", "parameters": {{}} }}] if no action needed.
    """
    try:
        raw = call_llm_with_retry([
            {"role": "system", "content": "You are a JSON-only logistics AI robot."},
            {"role": "user", "content": state_desc}
        ], max_retries=1)
        
        if raw:
            clean = raw.strip().replace("```json", "").replace("```", "")
            return json.loads(clean)
    except Exception:
        pass
    
    # Fallback to deterministic math if LLM hallucinates to prevent grader crashes
    return rule_based_action(obs)

def run_episode(task_id="easy_refinery_maintenance"):
    # 1. Print Standard START string strictly for Meta RegEx parser
    print(f"[START] task={task_id} env=fuel_net_env model={MODEL_NAME}")
    
    try:
        resp = requests.post(f"{ENV_BASE_URL}/reset", params={"task_id": task_id})
        obs = resp.json()
    except Exception as e:
        print("[END] success=false steps=0 rewards=")
        return

    done = False
    rewards_list = []
    step_count = 0
    success = True

    while not done:
        step_count += 1
        
        action_dict = llm_agent_action(obs)
        action_str = json.dumps(action_dict).replace(' ', '')

        try:
            resp = requests.post(f"{ENV_BASE_URL}/step", json=action_dict)
            step_data = resp.json()
            
            reward = float(step_data.get("reward", 0.0))
            obs = step_data.get("observation", obs)
            done = step_data.get("done", True)
            
            rewards_list.append(reward)
            
            # 2. Print EXACT structured output mandated by OpenEnv Spec
            print(f"[STEP] step={step_count} action={action_str} reward={reward:.2f} done={str(done).lower()} error=null")
            
        except Exception as e:
            err_str = str(e).replace(' ', '_')
            print(f"[STEP] step={step_count} action={action_str} reward=0.00 done=true error={err_str}")
            success = False
            break

    rewards_str = ",".join([f"{r:.2f}" for r in rewards_list])
    # 3. Final validation hook
    print(f"[END] success={str(success).lower()} steps={step_count} rewards={rewards_str}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=str, default="all")
    args = parser.parse_args()
    
    if args.task == "all":
        tasks = ["easy_refinery_maintenance", "medium_multi_crisis", "hard_hormuz_crisis"]
        for t in tasks:
            run_episode(t)
    else:
        run_episode(args.task)
