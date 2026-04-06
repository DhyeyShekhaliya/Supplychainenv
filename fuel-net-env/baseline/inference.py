import os
import re
import time
import requests
import json
import argparse
import textwrap
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ─── Terminal Styling ────────────────────────────────────────────────────────
C_BLUE = "\033[94m"
C_CYAN = "\033[96m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_BOLD = "\033[1m"
C_RESET = "\033[0m"

def get_progress_bar(current, total, width=30):
    progress = int((current / total) * width)
    bar = "█" * progress + "░" * (width - progress)
    return f"{C_CYAN}[{bar}]{C_RESET}"

# ─── Initialization ──────────────────────────────────────────────────────────
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ.get("NVIDIA_API_KEY", "dummy-key-for-testing")
)

ROUTE_REFERENCE = """ROUTE REFERENCE:
  hormuz_india      : 5 days  | cap 5M/day  [FAST]
  hormuz_china      : 15 days | cap 6M/day
  hormuz_japan      : 12 days | cap 4M/day
  russia_europe_pipe: 3 days  | cap 4M/day  [FAST]
  russia_china_pipe : 5 days  | cap 2M/day
  russia_india_sea  : 20 days | cap 1.5M/day
  wa_europe_sea     : 10 days | cap 2M/day
  wa_india_sea      : 15 days | cap 1.5M/day
  us_europe_sea     : 12 days | cap 3M/day
  pg_cape_india     : 25 days | cap 2M/day  [SLOW]
  pg_cape_europe    : 35 days | cap 3M/day  [SLOW]"""

# ─── Logistics Engine ─────────────────────────────────────────────────────────
def rule_based_action(obs):
    """Identify ALL critical shortages and resolve them simultaneously via the fastest routes."""
    actions = []
    try:
        obs_dict = obs if isinstance(obs, dict) else obs.dict()
        regions = obs_dict.get("regions", [])
        consumers = [r for r in regions if r.get("region_type") == "consumer"]
        fulfillment = obs_dict.get("demand_fulfillment", {})
        routes = obs_dict.get("routes", [])

        # Check every consumer region
        for region in consumers:
            r_id = region["region_id"]
            if fulfillment.get(r_id, 1.0) < 0.99:
                # Find fastest route to this specific region
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
            return [{"action_type": "hold", "parameters": {}, "reasoning": "Global supply stable. ⏳"}]
            
        # Attach reasoning to the first action (dashboard will display it)
        actions[0]["reasoning"] = "Coordinating global multi-market shipments to stabilize supply chains."
        return actions
    except Exception as e:
        return [{"action_type": "hold", "parameters": {}, "reasoning": f"Strategy adjustment needed. ⏳"}]

def call_llm_with_retry(messages, model="meta/llama-3.1-8b-instruct", max_retries=3):
    for attempt in range(max_retries):
        try:
            completion = client.chat.completions.create(model=model, messages=messages, temperature=0.6, top_p=0.9, max_tokens=1024)
            return completion.choices[0].message.content
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                time.sleep(5 * (attempt + 1))
            else:
                raise e

# ─── Simulation Dashboards ────────────────────────────────────────────────────
def run_episode(task_id="easy_refinery_maintenance", base_url="http://localhost:8000"):
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"\n{C_BOLD}{C_CYAN}🚀 FUEL-NET GLOBAL CRISIS COMMAND CENTER{C_RESET}")
    print(f"{C_YELLOW}Task: {task_id.replace('_', ' ').title()}{C_RESET}\n")

    try:
        resp = requests.post(f"{base_url}/reset", params={"task_id": task_id})
        obs = resp.json()
    except:
        print(f"{C_RED}❌ Connection Error: Ensure server is running on {base_url}{C_RESET}")
        return

    done = False
    history = []
    total_days = obs.get("total_days", 30)

    while not done:
        # 1. Logistics Decision
        action_dict = rule_based_action(obs)

        # 2. Strategic Intelligence (LLM)
        try:
            reasoning_prompt = [
                {"role": "system", "content": "You are a crisis analyst. Give a 1-sentence briefing on the situation. No JSON."},
                {"role": "user", "content": f"Task: {obs.get('task_description')}\nShortages: {obs.get('markets_in_shortage')}\nDay: {obs.get('current_day')}/{total_days}"}
            ]
            full_output = call_llm_with_retry(reasoning_prompt)
            if full_output:
                # Clean up the reasoning (keep full length)
                reasoning = full_output.strip().replace('\n', ' ')
                action_dict[0]["reasoning"] = reasoning + " 🤖"
        except:
            pass

        # 3. Environment Step
        resp = requests.post(f"{base_url}/step", json=action_dict)
        if resp.status_code != 200:
            print(f"{C_RED}❌ Server Error ({resp.status_code}):{C_RESET}")
            print(resp.text)
            break
            
        try:
            step_data = resp.json()
        except Exception as e:
            print(f"{C_RED}❌ JSON Decode Error:{C_RESET} {str(e)}")
            print(f"Server Response Content: {resp.text}")
            break
            
        reward = step_data.get("reward", 0.0)
        obs = step_data["observation"]
        done = step_data["done"]

        # 📊 RENDER DASHBOARD
        day = obs['current_day']
        progress = get_progress_bar(day, total_days)
        print(f"{C_BOLD}{C_CYAN}┌{'─'*68}┐{C_RESET}")
        print(f"{C_BOLD}{C_CYAN}│ DAY {day:02d}/{total_days}  {progress}  Reward: {reward:+.2f} │{C_RESET}")
        print(f"{C_BOLD}{C_CYAN}├{'─'*68}┤{C_RESET}")
        
        # Reason wrapping
        reason = action_dict[0].get('reasoning', '')
        wrapped_reason = textwrap.wrap(f"{C_YELLOW}AI ANALYSIS:{C_RESET} {reason}", 66)
        for line in wrapped_reason:
            print(f"{C_BOLD}{C_CYAN}│{C_RESET} {line:<66} {C_BOLD}{C_CYAN}│{C_RESET}")
        
        # Shipment Arrivals (NEW SECTION)
        arrivals = obs.get("newly_delivered", [])
        if arrivals:
            print(f"{C_BOLD}{C_CYAN}├─ SHIPMENT ARRIVALS {'─'*48}┤{C_RESET}")
            for s in arrivals:
                from_reg = s.get('from_region') if isinstance(s, dict) else s.from_region
                to_reg = s.get('to_region') if isinstance(s, dict) else s.to_region
                vol = s.get('volume_barrels') if isinstance(s, dict) else s.volume_barrels
                days = s.get('days_in_transit') if isinstance(s, dict) else s.days_in_transit
                arrival_info = f"🚢 +{vol/1e6:.1f}M bbl to {to_reg.title()} (Took {days} days) from {from_reg.title()}"
                print(f"{C_BOLD}{C_CYAN}│{C_RESET} {C_GREEN}{arrival_info:<66}{C_RESET} {C_BOLD}{C_CYAN}│{C_RESET}")

        print(f"{C_BOLD}{C_CYAN}├{'─'*68}┤{C_RESET}")
        
        # Logistics Table
        for action in action_dict:
            params = action.get('parameters', {})
            act_type = action.get('action_type', 'HOLD').upper()
            if act_type == "SHIP_FUEL":
                ship_info = f"🚀 SHIP: {params.get('from','?')} → {params.get('to','?')} ({params.get('volume', 0)/1e6:.1f}M bbl)"
                print(f"{C_BOLD}{C_CYAN}│{C_RESET} {C_GREEN}{ship_info:<66}{C_RESET} {C_BOLD}{C_CYAN}│{C_RESET}")
            elif act_type != "HOLD":
                print(f"{C_BOLD}{C_CYAN}│{C_RESET} {C_YELLOW}⚡ ACTION: {act_type:<55}{C_RESET} {C_BOLD}{C_CYAN}│{C_RESET}")
            else:
                print(f"{C_BOLD}{C_CYAN}│{C_RESET} {C_YELLOW}⏳ COMMAND: {act_type:<55}{C_RESET} {C_BOLD}{C_CYAN}│{C_RESET}")
        
        print(f"{C_BOLD}{C_CYAN}├─ SUPPLY LEVELS {'─'*51}┤{C_RESET}")
        
        fulfillment = obs.get("demand_fulfillment", {})
        for region, pct in fulfillment.items():
            color = C_GREEN if pct >= 0.9 else C_YELLOW if pct >= 0.5 else C_RED
            status = "STABLE" if pct >= 0.9 else "CRITICAL" if pct < 0.2 else "SHORTAGE"
            bar_pct = int(pct * 20)
            fill_bar = f"{color}{'█'*bar_pct}{' '*(20-bar_pct)}{C_RESET}"
            print(f"{C_BOLD}{C_CYAN}│{C_RESET} {region.replace('_',' ').title():<15} {fill_bar} {color}{pct*100:5.1f}%{C_RESET} | {color}{status:<8}{C_RESET} {C_BOLD}{C_CYAN}│{C_RESET}")
        
        print(f"{C_BOLD}{C_CYAN}└{'─'*68}┘{C_RESET}")
        time.sleep(1) # Dramatic pause for demo

    # Final Summary
    grader_resp = requests.post(f"{base_url}/grader")
    score = grader_resp.json().get("score", 0.0)
    print(f"\n{C_BOLD}{C_GREEN}🏁 SIMULATION COMPLETE{C_RESET}")
    print(f"{C_BOLD}🏆 FINAL MISSION SCORE: {C_GREEN}{score*100:.2f}/100{C_RESET}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=str, default="easy", choices=["easy", "medium", "hard"])
    args = parser.parse_args()
    
    task_map = {"easy": "easy_refinery_maintenance", "medium": "medium_multi_crisis", "hard": "hard_hormuz_crisis"}
    run_episode(task_map[args.task])
