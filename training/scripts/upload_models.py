import os
from pathlib import Path
from huggingface_hub import HfApi, upload_file, create_repo

HF_USERNAME = "your-username"  # REPLACE WITH YOUR ACTUAL HF USERNAME
api = HfApi(token=os.environ.get("HF_TOKEN"))

def upload_anomaly_detector():
    if not api.token:
        print("⚠️ HF_TOKEN not set. Skipping upload.")
        return
        
    repo_id = f"{HF_USERNAME}/medsight-anomaly-detector"
    
    try:
        create_repo(repo_id, exist_ok=True, private=False)
        print(f"Created/verified repo: {repo_id}")
    except Exception as e:
        print(f"Repo creation issue: {e}")
    
    files_to_upload = [
        ("models/anomaly_head.pt", "anomaly_head.pt"),
        ("models/anomaly_stats.json", "anomaly_stats.json"),
    ]
    
    for local_path, repo_path in files_to_upload:
        if Path(local_path).exists():
            upload_file(
                path_or_fileobj=local_path,
                path_in_repo=repo_path,
                repo_id=repo_id,
                commit_message=f"Upload {repo_path}"
            )
            print(f"✅ Uploaded {local_path} → {repo_id}/{repo_path}")
        else:
            print(f"⚠️ File not found: {local_path} (skipping)")
    
    model_card = '''---
language: en
license: mit
tags:
  - medical
  - chest-xray
  - anomaly-detection
  - unsupervised
  - pytorch
datasets:
  - nih-chest-xray-14
---

# MedSight AI — Anomaly Detector

A DINOv2-based unsupervised anomaly detector for chest X-rays.
Trained on 30,000 "No Finding" images from NIH ChestX-ray14.

## Architecture
- **Backbone**: DINOv2-small (frozen) — Facebook AI
- **Head**: Trainable projection MLP (384→128→384)
- **Training**: Reconstruction loss on normal images only
- **Anomaly Score**: Normalized reconstruction error (0-100)

## Performance
- Validation Loss: ~0.0021 (MSE)
- Estimated AUC-ROC: 0.68-0.75 (varies with test set)

## Disclaimer
This model is for educational and research purposes only. Not validated for clinical use.
'''
    
    api.upload_file(
        path_or_fileobj=model_card.encode(),
        path_in_repo="README.md",
        repo_id=repo_id,
        commit_message="Add model card"
    )
    print("✅ Model card uploaded.")

def upload_biobert_ner():
    if not api.token: return
    repo_id = f"{HF_USERNAME}/medsight-biobert-ner"
    
    try:
        create_repo(repo_id, exist_ok=True, private=False)
    except Exception:
        pass
    
    fine_tuned_path = Path("models/biobert_ner_finetuned")
    if fine_tuned_path.exists():
        api.upload_folder(
            folder_path=str(fine_tuned_path),
            repo_id=repo_id,
            commit_message="Upload fine-tuned BioBERT NER model"
        )
        print(f"✅ Uploaded BioBERT NER → {repo_id}")
    else:
        print("⚠️ Fine-tuned BioBERT not found. Train it first with finetune_ner.py")

if __name__ == "__main__":
    print("🚀 Uploading models to HuggingFace Hub...")
    upload_anomaly_detector()
    upload_biobert_ner()
    print("✅ Upload complete!")
