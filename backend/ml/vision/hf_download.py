"""Download trained model checkpoints from HuggingFace Hub when not available locally."""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────
HF_REPO_ID = os.getenv("HF_MODEL_REPO", "hoshikrana/VAE_and_VIT_Anomaly_detection")
MODEL_FILES = [
    "pulmonary_anomaly_detector.pth",
    "best_vae.pth",
    "best_vit.pth",
]


def ensure_models(target_dir: str | Path = "./results/outputs") -> bool:
    """Check if model files exist locally; if not, download from HuggingFace.
    
    Returns True if all models are available after this call.
    """
    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)

    missing = [f for f in MODEL_FILES if not (target / f).is_file()]

    if not missing:
        logger.info("All model checkpoints found locally in %s", target)
        return True

    logger.info("Missing models: %s — attempting HuggingFace download from %s", missing, HF_REPO_ID)

    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        logger.warning("huggingface_hub not installed. Run: pip install huggingface_hub")
        return False

    hf_token = os.getenv("HF_TOKEN")
    success = True

    for filename in missing:
        try:
            downloaded = hf_hub_download(
                repo_id=HF_REPO_ID,
                filename=filename,
                local_dir=str(target),
                token=hf_token,
            )
            logger.info("Downloaded %s → %s", filename, downloaded)
        except Exception as exc:
            logger.error("Failed to download %s: %s", filename, exc)
            success = False

    return success
