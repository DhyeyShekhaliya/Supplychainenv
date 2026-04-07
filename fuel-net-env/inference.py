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

def llm_agent_action(obs):
    """Uses LLM to dynamically choose logistics actions based on full world state."""
    # Build compact route table for LLM
    route_info = []
    for r in obs.get('routes', []):
        if r.get('active'):
            route_info.append(f"  {r['route_id']}: {r.get('from_region','?')} → {r.get('to_region','?')} ({r.get('current_transit_days','?')}d, ${r.get('cost_per_barrel','?')}/bbl, cap {r.get('capacity_per_day',0)//1_000_000}M/day)")
    routes_str = "\n".join(route_info) if route_info else "  None available"
    
    # Build demand fulfillment summary
    ful = obs.get('demand_fulfillment', {})
    ful_str = ", ".join([f"{k}: {v:.0%}" for k, v in ful.items()]) if ful else "unknown"
    
    # Reserve levels
    reserves = obs.get('reserve_levels', {})
    res_str = ", ".join([f"{k}: {v.get('days_of_cover',0):.0f}d cover" for k, v in reserves.items()]) if reserves else "unknown"

    system_prompt = """You are a fuel supply chain AI. You MUST respond with ONLY a JSON array. No text before or after.
Rules:
- Use ship_fuel to send oil from producers to consumers via active routes
- Use hold ONLY if all consumers have >95% fulfillment
- Always use exact route_id values from the Available Routes list
- volume must be an integer (barrels per day), max = route capacity"""

    user_prompt = f"""Day {obs.get('current_day', 0)}/{obs.get('total_days', 30)} | Budget: ${obs.get('remaining_budget', 0):,.0f} remaining
Task: {obs.get('task_description', 'Manage supply chain')}
Markets in shortage: {obs.get('markets_in_shortage', [])}
Demand fulfillment: {ful_str}
Reserves: {res_str}

Available Routes:
{routes_str}

Respond with a JSON array. Example:
[{{"action_type":"ship_fuel","parameters":{{"from":"hormuz","to":"india","route":"hormuz_india","volume":5000000}}}},{{"action_type":"ship_fuel","parameters":{{"from":"russia","to":"europe","route":"russia_europe_pipe","volume":4000000}}}}]"""

    try:
        raw = call_llm_with_retry([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ], max_retries=2)
        
        if raw:
            import re
            clean_str = raw.strip().replace('\n', '').replace('```json', '').replace('```', '')
            # Try full string first, then regex extract
            try:
                return json.loads(clean_str)
            except json.JSONDecodeError:
                match = re.search(r'\[.*\]', clean_str, re.DOTALL)
                if match:
                    return json.loads(match.group(0))
    except Exception:
        pass
    
    return [{"action_type": "hold", "parameters": {}}]

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
