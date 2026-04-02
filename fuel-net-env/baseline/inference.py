import os
import requests
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize the OpenAI client pointing to the NVIDIA API endpoint
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ.get("NVIDIA_API_KEY", "dummy-key-for-testing")
)

def run_episode(task_id="easy_refinery_maintenance", base_url="http://localhost:8000"):
    print(f"Starting baseline for task: {task_id}")
    
    try:
        resp = requests.post(f"{base_url}/reset", params={"task_id": task_id})
        obs = resp.json()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the environment server at", base_url)
        print("Please start it with: uvicorn server.app:app --host 0.0.0.0 --port 8000")
        return
    
    done = obs.get("done", False)
    
    system_prompt = """You are a Global Fuel Distribution Crisis Manager.
You receive a JSON observation of the current state of a global fuel network.
Your goal is to fulfill consumer demand while minimizing costs and maintaining strategic reserves.
Output exactly ONE valid JSON action object at the end of your response.
It MUST strictly follow this schema:
{
  "action_type": "type_here",
  "parameters": {
     ...
  }
}
Valid action_type values: "ship_fuel", "reroute_shipment", "release_reserves", "reduce_demand", "hold".
Example for ship_fuel:
{
  "action_type": "ship_fuel",
  "parameters": {"from": "russia", "to": "india", "route": "russia_india_sea", "volume": 1500000}
}


CRITICAL RULES FOR THINKING:
You are looping infinitely because you are trying to calculate every route and every region. STOP DOING THIS.
You must adopt an extremely "lazy" strategy:
1. Look at ONE consumer with a shortage (e.g., India).
2. Look at ONE producer.
3. Pick ONE connecting route.
4. STOP THINKING IMMEDIATELY. Do not evaluate alternatives. Output the JSON.

Example of an acceptable thought length:
"India has low supply. Russia has surplus. I will ship 2000000 barrels from Russia to India via russia_india_sea."
If you write more than 3 sentences, the simulation will crash!
Output your final answer inside a ```json ... ``` block."""

    while not done:
        # Prevent context length (8K tokens) overflow by only sending the current observation
        # Llama 3 won't remember past days this way, but it will solve the Markov state
        current_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(obs, indent=2)}
        ]
        
        try:
            completion = client.chat.completions.create(
                model="nvidia/nemotron-3-super-120b-a12b",
                messages=current_messages,
                temperature=1.0,
                top_p=0.95,
                max_tokens=8192,
                extra_body={"chat_template_kwargs":{"enable_thinking":True},"reasoning_budget":4096},
                stream=True
            )
            
            action_text = ""
            reasoning_text = ""
            print(f"\n[ Day {obs['current_day']} Agent Thinking ]")
            for chunk in completion:
                if not chunk.choices:
                    continue
                reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
                if reasoning:
                    print(reasoning, end="", flush=True)
                    reasoning_text += reasoning
                
                content = chunk.choices[0].delta.content
                if content is not None:
                    action_text += content
            print("\n[ End Thought ]")
            
            full_output = action_text + "\n" + reasoning_text
            import re
            match = re.search(r"```json(.*?)```", full_output, re.DOTALL)
            if match:
                extracted_json = match.group(1).strip()
            else:
                match = re.search(r"(\{.*\})", full_output, re.DOTALL)
                if match:
                    extracted_json = match.group(1).strip()
                else:
                    raise Exception("No JSON pattern matched in output.")
                    
            action_dict = json.loads(extracted_json)
        except Exception as e:
            print(f"LLM Error or Parse Error: {e}, falling back to 'hold'")
            action_dict = {"action_type": "hold", "parameters": {}}
        
        resp = requests.post(f"{base_url}/step", json=action_dict)
        if resp.status_code != 200:
            print("Environment returned an error:", resp.text)
            break
            
        step_data = resp.json()
        
        obs = step_data["observation"]
        reward = step_data["reward"]
        done = step_data["done"]
        
        print(f"Day {obs['current_day']}: Action={action_dict['action_type']} | Reward={reward:.2f}")
        # clear messages to save context except system prompt if you don't need full history
        # messages = [messages[0]] 

    if done:
        grader_resp = requests.post(f"{base_url}/grader")
        score = grader_resp.json().get("score", 0.0)
        print(f"Episode finished! Grader Score: {score}")
        return score

if __name__ == "__main__":
    run_episode("easy_refinery_maintenance")
