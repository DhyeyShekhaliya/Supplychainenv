import os, time
from huggingface_hub import HfApi

print("Initializing HF API...")
api = HfApi()

REPO_ID = "Dhyeyyy18/Fuel-Net-Env-Final"

if api.repo_exists(repo_id=REPO_ID, repo_type="space"):
    print(f"Space {REPO_ID} already exists! Skipping creation and directly uploading...")
else:
    print(f"Creating Space {REPO_ID}...")
    api.create_repo(repo_id=REPO_ID, repo_type="space", space_sdk="docker", exist_ok=True)

for attempt in range(5):
    try:
        print(f"Uploading files... (attempt {attempt+1})")
        api.upload_folder(
            folder_path=".",
            repo_id=REPO_ID,
            repo_type="space",
            ignore_patterns=["hf-deploy", "venv", ".venv", ".git", ".env", "*.pyc", "__pycache__", "upload_space.py"]
        )
        print("UPLOAD COMPLETE! 🚀")
        break
    except Exception as e:
        print(f"Upload failed: {e}")
        if attempt < 4:
            wait = 10 * (attempt + 1)
            print(f"Retrying in {wait}s...")
            time.sleep(wait)
        else:
            print("All retries failed!")
            raise
