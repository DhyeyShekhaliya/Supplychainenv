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
    """Deterministic logic that actually ships fuel to shortage markets."""
    actions = []
    consumers = [r for r in obs.get("regions", []) if r.get("region_type") == "consumer"]
    fulfillment = obs.get("demand_fulfillment", {})
    routes = obs.get("routes", [])
    
    for region in consumers:
        r_id = region["region_id"]
        if fulfillment.get(r_id, 1.0) < 0.95:
            viable = sorted(
                [r for r in routes if r.get("to_region") == r_id and r.get("active", True)],
                key=lambda r: r.get("current_transit_days", 999)
            )
            if viable:
                best = viable[0]
                vol = min(region.get("demand", 5000000), best.get("capacity_per_day", 5000000))
                actions.append({
                    "action_type": "ship_fuel",
                    "parameters": {
                        "from": best.get("from_region", ""),
                        "to": r_id,
                        "route": best.get("route_id", ""),
                        "volume": int(vol)
                    }
                })
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
    
    ful = obs.get('demand_fulfillment', {})
    ful_str = ", ".join([f"{k}: {v:.0%}" for k, v in ful.items()]) if ful else "unknown"
    
    reserves = obs.get('reserve_levels', {})
    res_str = ", ".join([f"{k}: {v.get('days_of_cover',0):.0f}d" for k, v in reserves.items() if v.get('capacity', 0) > 0]) if reserves else "unknown"

    system_prompt = """You are a fuel supply chain AI. Respond with ONLY a JSON array, no other text.
Rules:
- Use ship_fuel to send oil from producers to consumers via routes
- Use hold ONLY if ALL consumers have >95% fulfillment
- Always use exact route_id from Available Routes
- volume = integer (barrels/day), max is route capacity"""

    user_prompt = f"""Day {obs.get('current_day', 0)}/{obs.get('total_days', 30)} | Budget: ${obs.get('remaining_budget', 0):,.0f}
Task: {obs.get('task_description', '')}
Shortages: {obs.get('markets_in_shortage', [])}
Fulfillment: {ful_str}
Reserves: {res_str}

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
    score = 0.0

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
        print(f"[END] success={str(success).lower()} steps={step_count} score={score:.3f} rewards={rewards_str}", flush=True)

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
