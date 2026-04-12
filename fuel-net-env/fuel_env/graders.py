import os
import re
from openai import OpenAI
from fuel_env.tasks import TASKS

def evaluate_reasoning(reasoning_history, ground_truth):
    if not reasoning_history:
        return 0.0
    
    api_key = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
    api_base_url = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
    model = os.getenv("MODEL_NAME", "meta/llama-3.1-8b-instruct")
    
    if not api_key:
        return 0.0
        
    client = OpenAI(api_key=api_key, base_url=api_base_url)
    history_str = "\n".join(reasoning_history)
    
    prompt = f"""You are an expert logistics evaluator. Evaluate the quality of the generated AI reasoning steps against the expert ground truth strategy.

Rate the reasoning on a scale from 0.0 to 1.0, where:
- 1.0 = Excellent: Strategy perfectly aligns with the ground truth
- 0.7-0.9 = Good: Most key insights present
- 0.4-0.6 = Fair: Partial insights
- 0.1-0.3 = Poor: Strategy is completely wrong or misguided
- 0.0 = Completely irrelevant

GENERATED REASONING:
{history_str}

EXPERT GROUND TRUTH:
{ground_truth}

Respond with ONLY a single float number between 0.0 and 1.0."""
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=10,
            timeout=15
        )
        content = response.choices[0].message.content.strip()
        match = re.search(r"(0?\.\d+|1\.0+|0|1)", content)
        if match:
            return min(1.0, max(0.0, float(match.group(1))))
        return 0.0
    except Exception as e:
        print(f"[GRADER DEBUG] LLM Judge failed: {e}")
        return 0.0

def grade_episode(task_id, daily_fulfillment_history, total_spent,
                  total_budget, shortage_days, consumer_count, total_days, reasoning_history=None):
    """
    Score = Deterministic Score (70%) + LLM Reasoning Score (30%)
    
    Deterministic:
    supply_score * 0.40 + cost_score * 0.20 + shortage_score * 0.25 + reserve_score * 0.15
    """

    # Average supply fulfillment across all regions across all days
    if total_days > 0 and daily_fulfillment_history:
        total_fulfillment = sum(
            sum(day.values()) / max(len(day), 1) for day in daily_fulfillment_history
        )
        supply_score = total_fulfillment / total_days
    else:
        supply_score = 0.0

    # Cost efficiency
    cost_ratio = total_spent / max(total_budget, 1.0)
    cost_score = max(0.0, 1.0 - cost_ratio)

    # Shortage-free days (higher = better)
    shortage_free_ratio = 1.0 - (shortage_days / max((total_days * consumer_count), 1))
    shortage_score = max(0.0, shortage_free_ratio)

    # Reserve management (did reserves end reasonably?)
    reserve_score = 0.7

    deterministic_score = (supply_score * 0.40 +
             cost_score * 0.20 +
             shortage_score * 0.25 +
             reserve_score * 0.15)
             
    # LLM-as-a-judge Reasoning Score
    reasoning_score = 0.0
    if reasoning_history:
        ground_truth = TASKS.get(task_id, {}).get("ground_truth_explanation", "")
        if ground_truth:
            reasoning_score = evaluate_reasoning(reasoning_history, ground_truth)
            
    # Blend: 70% Math, 30% Strategy
    final_score = (deterministic_score * 0.70) + (reasoning_score * 0.30)
    
    # Idea 3: Progressive Difficulty Scales (Incentivizes taking on hard tasks)
    difficulty = TASKS.get(task_id, {}).get("difficulty", "medium")
    multiplier_map = {
        "very_easy": 0.2,
        "easy": 0.4,
        "medium": 0.6,
        "hard": 0.8,
        "extreme": 1.0
    }
    multiplier = multiplier_map.get(difficulty, 1.0)
    scaled_score = final_score * multiplier

    # Clamp strictly to (0, 1) exclusive
    safe_score = float(min(max(scaled_score, 0.000001), 0.999999))
    return round(safe_score, 5)
