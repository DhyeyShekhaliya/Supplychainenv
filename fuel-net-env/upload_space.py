import os
from huggingface_hub import HfApi

print("Initializing HF API...")
api = HfApi()

REPO_ID = "Dhyeyyy18/Fuel-Net-Env-Final"

print(f"Creating Space {REPO_ID} if it doesn't exist...")
api.create_repo(repo_id=REPO_ID, repo_type="space", space_sdk="docker", exist_ok=True)

print("Uploading files...")
api.upload_folder(
    folder_path=".",
    repo_id=REPO_ID,
    repo_type="space",
    ignore_patterns=["hf-deploy", "venv", ".venv", ".git", ".env", "*.pyc", "__pycache__", "upload_space.py"]
)

print("UPLOAD COMPLETE! 🚀")
