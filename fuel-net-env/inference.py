import os
import requests
import json
from openai import OpenAI

# ─── MANDATORY HACKATHON CONFIGURATION ───────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://integrate.api.nvidia.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "meta/llama-3.1-8b-instruct")
HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN is missing")

# Initialize OpenAI client 
client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN
)

ENV_BASE_URL = "http://localhost:7860"

def call_llm_with_retry(messages, model=None, max_retries=3):
    import time, sys
    model = model or MODEL_NAME
    for attempt in range(max_retries):
        try:
            if not client:
                print("[LLM DEBUG] client is None - OpenAI init failed", file=sys.stderr)
                return ""
            completion = client.chat.completions.create(model=model, messages=messages, temperature=0.7, top_p=0.9, max_tokens=512)
            result = completion.choices[0].message.content
            print(f"[LLM DEBUG] Got response: {result[:100]}...", file=sys.stderr)
            return result
        except Exception as e:
            print(f"[LLM DEBUG] Attempt {attempt+1} failed: {e}", file=sys.stderr)
            if "429" in str(e) and attempt < max_retries - 1:
                time.sleep(3)
            else:
                return ""
    return ""

def _smart_actions(obs):
    """Proactive shipping: send fuel every day to cover the structural deficit before reserves dry up."""
    actions = []
    consumers = [r for r in obs.get("regions", []) if r.get("region_type") == "consumer"]
    routes = [r for r in obs.get("routes", []) if r.get("active", True)]
    
    for region in consumers:
        r_id = region["region_id"]
        demand = region.get("demand", 0)
        output = region.get("current_output", 0)
        shortfall = max(0, demand - output)
        
        if shortfall > 0:
            viable = sorted(
                [r for r in routes if r.get("to_region") == r_id],
                key=lambda r: r.get("current_transit_days", 999)
            )
            for best in viable:
                vol = min(shortfall, best.get("capacity_per_day", 5000000))
                if vol > 0:
                    actions.append({
                        "action_type": "ship_fuel",
                        "reasoning": f"Smart fallback: fulfilling {r_id} deficit",
                        "parameters": {
                            "from": best.get("from_region", ""),
                            "to": r_id,
                            "route": best.get("route_id", ""),
                            "volume": int(vol)
                        }
                    })
                    shortfall -= vol
                if shortfall <= 0:
                    break
                    
    return actions if actions else [{"action_type": "hold", "parameters": {}}]

def llm_agent_action(obs):
    """Hybrid: tries LLM first, uses smart deterministic if LLM fails."""
    import sys
    # Build compact route table for LLM
    route_info = []
    for r in obs.get('routes', []):
        if r.get('active'):
            route_info.append(f"  {r['route_id']}: {r.get('from_region','?')} → {r.get('to_region','?')} ({r.get('current_transit_days','?')}d, ${r.get('cost_per_barrel','?')}/bbl, cap {r.get('capacity_per_day',0)//1_000_000}M/day)")
    routes_str = "\n".join(route_info) if route_info else "  None available"
    
    # Calculate structural deficits for LLM context
    deficits = []
    for r in obs.get("regions", []):
        if r.get("region_type") == "consumer":
            d = r.get("demand", 0)
            o = r.get("current_output", 0)
            if d > o:
                deficits.append(f"{r['region_id']}: needs {d-o} bbl/day")
    deficit_str = ", ".join(deficits) if deficits else "None"

    system_prompt = """You are a fuel supply chain AI. Respond with ONLY a JSON array, no other text.
Rules:
- Ship fuel PROACTIVELY every single day to cover the 'Daily Deficits' for consumer regions.
- Do NOT wait for reserves to drop. Transit takes days, you must act now.
- Always use exact route_id from Available Routes.
- volume = integer (barrels/day), max is route capacity
- MUST include a "reasoning" key inside each action explaining your strategic logic!

Example:
[{"action_type": "ship_fuel", "reasoning": "Europe is at -2.5M deficit. Deploying from US via sea.", "parameters": {"from": "us_shale", "to": "europe", "route": "us_europe_sea", "volume": 2500000}}]"""

    user_prompt = f"""Day {obs.get('current_day', 0)}/{obs.get('total_days', 30)} | Budget: ${obs.get('remaining_budget', 0):,.0f}
Task: {obs.get('task_description', '')}
Daily Deficits (Demand - Output): {deficit_str}
Shortages: {obs.get('markets_in_shortage', [])}

Routes:
{routes_str}

JSON array:"""

    try:
        raw = call_llm_with_retry([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ], max_retries=2)
        
        if raw:
            import re
            clean_str = raw.strip().replace('\n', '').replace('```json', '').replace('```', '')
            try:
                result = json.loads(clean_str)
                if isinstance(result, list) and len(result) > 0:
                    print(f"[LLM DEBUG] Parsed {len(result)} actions from LLM", file=sys.stderr)
                    return result
            except json.JSONDecodeError:
                match = re.search(r'\[.*\]', clean_str, re.DOTALL)
                if match:
                    result = json.loads(match.group(0))
                    if isinstance(result, list) and len(result) > 0:
                        print(f"[LLM DEBUG] Regex-extracted {len(result)} actions", file=sys.stderr)
                        return result
    except Exception as e:
        print(f"[LLM DEBUG] llm_agent_action failed: {e}", file=sys.stderr)
    
    # LLM failed → use smart deterministic actions so ships actually move
    print("[LLM DEBUG] Falling back to smart deterministic actions", file=sys.stderr)
    return _smart_actions(obs)

def run_episode(task_id="easy_refinery_maintenance"):
    rewards_list = []
    step_count = 0
    success = False
    score = 0.001  # Never exactly 0.0 — hackathon rejects it

    # 1. Print [START] — always first
    print(f"[START] task={task_id} env=fuel_net_env model={MODEL_NAME}", flush=True)
    
    try:
        resp = requests.post(f"{ENV_BASE_URL}/reset", params={"task_id": task_id})
        obs = resp.json()

        done = False

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
                error = step_data.get("error", None)
                
                rewards_list.append(reward)
                
                error_val = str(error).replace(' ', '_') if error else "null"
                print(f"[STEP] step={step_count} action={action_str} reward={reward:.2f} done={str(done).lower()} error={error_val}", flush=True)
                
            except Exception as e:
                err_str = str(e).replace(' ', '_')
                print(f"[STEP] step={step_count} action={action_str} reward=0.00 done=true error={err_str}", flush=True)
                break

        # Calculate score via grader
        try:
            resp = requests.post(f"{ENV_BASE_URL}/grader_ui")
            grader_data = resp.json()
            score = float(grader_data.get("score", 0.0))
            # Clamp to strict (0, 1) exclusive
            score = min(max(score, 0.001), 0.999)
        except Exception:
            score = 0.001

        success = score > 0.1

    except Exception as e:
        import sys
        print(f"[DEBUG] Episode error: {e}", file=sys.stderr, flush=True)

    finally:
        # 3. [END] — ALWAYS emitted, even on exception
        rewards_str = ",".join(f"{r:.2f}" for r in rewards_list)
        print(f"[END] success={str(success).lower()} steps={step_count} rewards={rewards_str}", flush=True)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=str, default="all")
    args = parser.parse_args()
    
    if args.task == "all":
        tasks = [
            "very_easy_startup", 
            "easy_refinery_maintenance", 
            "medium_multi_crisis", 
            "hard_hormuz_crisis",
            "extreme_global_crisis"
        ]
        for t in tasks:
            run_episode(t)
    else:
        run_episode(args.task)
