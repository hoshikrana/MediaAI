import os
import logging

logger = logging.getLogger(__name__)

RENDER_FREE_TIER_MEMORY_MB = 480  # leave 32MB for OS

def is_render_environment() -> bool:
    return os.environ.get("RENDER", "").lower() == "true"

def get_startup_mode() -> str:
    if is_render_environment():
        return "lite"
    return "full"

def apply_lite_mode_restrictions(MODEL_PROFILES):
    """Updates MODEL_PROFILES in-place to respect Render.com limits."""
    if get_startup_mode() == "lite":
        logger.info("🚀 Running in LITE mode (Render.com free tier) — disabling memory-heavy models.")
        LITE_MODE_MODELS = ["minilm"] # Only load RAG embeddings
        
        for name, profile in MODEL_PROFILES.items():
            if name not in LITE_MODE_MODELS:
                profile.is_required = False
                profile.device_preference = "cpu" # Force CPU just in case
                # The registry will still try to load them on demand, but we can set their priority extremely low 
                # or manually fail their load in _load_model_sync to protect RAM.
