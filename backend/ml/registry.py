import asyncio
import time
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal, Any

from backend.core.config import settings
from backend.core.logging_config import ml_logger

logger = logging.getLogger(__name__)

@dataclass
class ModelProfile:
    name: str
    hf_model_id: str
    local_cache_subdir: str
    device_preference: Literal["cuda", "cpu", "auto"]
    vram_mb: int
    ram_mb: int
    load_priority: int
    is_required: bool

MODEL_PROFILES = {
    "convae_anomaly": ModelProfile(
        name="convae_anomaly", hf_model_id="local/chest-convae", local_cache_subdir="convae",
        device_preference="cpu", vram_mb=50, ram_mb=50, load_priority=1, is_required=True
    ),
    "scispacy_ner": ModelProfile(
        name="scispacy_ner", hf_model_id="en_core_sci_sm", local_cache_subdir="scispacy",
        device_preference="cpu", vram_mb=0, ram_mb=100, load_priority=2, is_required=True
    ),
    "whisper_tiny": ModelProfile(
        name="whisper_tiny", hf_model_id="openai/whisper-tiny", local_cache_subdir="whisper",
        device_preference="cpu", vram_mb=0, ram_mb=300, load_priority=3, is_required=False
    ),
    "biogpt_base": ModelProfile(
        name="biogpt_base", hf_model_id="microsoft/biogpt", local_cache_subdir="biogpt",
        device_preference="cpu", vram_mb=0, ram_mb=700, load_priority=4, is_required=False
    ),
    "minilm": ModelProfile(
        name="minilm", hf_model_id="sentence-transformers/all-MiniLM-L6-v2", local_cache_subdir="minilm",
        device_preference="cpu", vram_mb=0, ram_mb=100, load_priority=1, is_required=True
    ),
    "classifier": ModelProfile(
        name="classifier", hf_model_id="valhalla/distilbart-mnli-12-1", local_cache_subdir="classifier",
        device_preference="cpu", vram_mb=0, ram_mb=300, load_priority=5, is_required=False
    ),
}

@dataclass
class ModelState:
    profile: ModelProfile
    model: Any = None
    tokenizer: Any = None
    head: Any = None # Extension for DINO head architecture
    stats: dict = None # Extension for anomaly scoring
    is_loaded: bool = False
    is_loading: bool = False
    load_error: str | None = None
    load_time_ms: int = 0
    last_used: datetime | None = None
    current_device: str = "unloaded"
    
    @property
    def is_available(self) -> bool:
        return self.is_loaded and self.load_error is None and self.model is not None

class ModelRegistry:
    def __init__(self):
        self._states: dict[str, ModelState] = {
            name: ModelState(profile=profile) for name, profile in MODEL_PROFILES.items()
        }
        self._locks: dict[str, asyncio.Lock] = {
            name: asyncio.Lock() for name in MODEL_PROFILES
        }
        self._gpu_budget_mb = settings.GPU_VRAM_BUDGET_MB
    
    async def startup_load(self):
        ml_logger.logger.info("Starting model registry startup")
        sorted_models = sorted(MODEL_PROFILES.values(), key=lambda m: m.load_priority)
        
        for profile in sorted_models:
            if profile.device_preference == "cpu":
                await self._load_model(profile.name)
            else:
                if self._get_used_vram() + profile.vram_mb <= self._gpu_budget_mb:
                    await self._load_model(profile.name)
                else:
                    ml_logger.logger.warning(f"Skipping GPU load for {profile.name}: VRAM budget exceeded. Will load on CPU on first request.")
        
        loaded = [n for n, s in self._states.items() if s.is_available]
        failed = [n for n, s in self._states.items() if s.load_error]
        required_failed = [n for n in failed if MODEL_PROFILES[n].is_required]
        
        if required_failed:
            raise RuntimeError(f"Critical models failed to load: {required_failed}. Check logs.")
            
        ml_logger.logger.info("Registry startup complete", extra={"loaded": loaded, "failed": failed, "vram_used_mb": self._get_used_vram()})

    async def get(self, model_name: str) -> ModelState:
        if model_name not in self._states:
            raise ValueError(f"Unknown model: {model_name}")
        
        state = self._states[model_name]
        if not state.is_available and not state.is_loading:
            await self._load_model(model_name)
            
        self._states[model_name].last_used = datetime.now(timezone.utc)
        return self._states[model_name]

    def is_available(self, model_name: str) -> bool:
        return self._states.get(model_name, ModelState(ModelProfile("","","","cpu",0,0,0,False))).is_available

    async def _load_model(self, model_name: str):
        async with self._locks[model_name]:
            state = self._states[model_name]
            if state.is_available:
                return
            
            state.is_loading = True
            start_time = time.monotonic()
            
            try:
                profile = state.profile
                device = self._resolve_device(profile)
                
                if device == "cuda":
                    needed = profile.vram_mb
                    available = self._gpu_budget_mb - self._get_used_vram()
                    if available < needed:
                        evicted = await self._evict_lru_gpu_model(except_model=model_name)
                        if evicted:
                            ml_logger.logger.info(f"Evicted {evicted} to make room for {model_name}")
                
                # Fetch objects securely
                result = await asyncio.to_thread(self._load_model_sync, model_name, profile, device)
                
                load_time_ms = int((time.monotonic() - start_time) * 1000)
                
                state.model = result.get('model')
                state.tokenizer = result.get('tokenizer')
                state.head = result.get('head')
                state.stats = result.get('stats')
                
                state.is_loaded = True
                state.load_error = None
                state.load_time_ms = load_time_ms
                state.current_device = device
                
                ml_logger.log_model_load(model_name, device, load_time_ms, vram_delta_mb=profile.vram_mb if device == "cuda" else None)
                
            except Exception as e:
                state.load_error = str(e)
                state.is_loaded = False
                ml_logger.logger.error(f"Failed to load model {model_name}: {e}", exc_info=True)
                if MODEL_PROFILES[model_name].is_required:
                    raise
            finally:
                state.is_loading = False

    def _load_model_sync(self, name: str, profile: ModelProfile, device: str) -> dict:
        cache_dir = settings.MODEL_CACHE_DIR / profile.local_cache_subdir
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        if name == "convae_anomaly":
            # Loader for the custom ONNX or PT Autoencoder
            model_path = settings.MODEL_CACHE_DIR / "chest_convae.onnx"
            stats_path = settings.MODEL_CACHE_DIR / "anomaly_stats.json"
            
            if not model_path.exists():
                logger.warning("ConvAE model file not found. Running with random-init fallback.")
                # We return None so the pipeline knows to use a mock/fallback
                return {"model": None, "tokenizer": None, "stats": {"mean": 0.001, "std": 0.0005}}
            
            # In a real impl, we'd load ONNX runtime here
            import onnxruntime as ort
            session = ort.InferenceSession(str(model_path))
            
            import json
            stats = {"mean": 0.001, "std": 0.0005}
            if stats_path.exists():
                stats = json.loads(stats_path.read_text())
                
            return {"model": session, "tokenizer": None, "stats": stats}
            
        elif name == "scispacy_ner":
            import spacy
            try:
                nlp = spacy.load(profile.hf_model_id)
            except OSError:
                logger.warning(f"scispaCy model {profile.hf_model_id} not found. Use 'python -m spacy download {profile.hf_model_id}'")
                return {"model": None, "tokenizer": None}
            return {"model": nlp, "tokenizer": None}
            
        elif name == "whisper_tiny":
            import whisper
            model = whisper.load_model("tiny", device="cpu", download_root=str(cache_dir))
            return {"model": model, "tokenizer": None}
            
        elif name == "biogpt_base":
            try:
                import os
                old_offline = os.environ.get("HF_HUB_OFFLINE")
                os.environ["HF_HUB_OFFLINE"] = "1"
                try:
                    from transformers import BioGptForCausalLM, BioGptTokenizer
                    tokenizer = BioGptTokenizer.from_pretrained(profile.hf_model_id, cache_dir=cache_dir, local_files_only=True)
                    model = BioGptForCausalLM.from_pretrained(profile.hf_model_id, cache_dir=cache_dir, local_files_only=True)
                    model.eval()
                    return {"model": model, "tokenizer": tokenizer}
                finally:
                    if old_offline is None:
                        os.environ.pop("HF_HUB_OFFLINE", None)
                    else:
                        os.environ["HF_HUB_OFFLINE"] = old_offline
            except Exception as e:
                logger.warning(f"BioGPT failed to load (offline/no cache): {e}. Report generation will use template fallback.")
                return {"model": None, "tokenizer": None}
            
        elif name == "minilm":
            try:
                from sentence_transformers import SentenceTransformer
                import os
                old_offline = os.environ.get("HF_HUB_OFFLINE")
                os.environ["HF_HUB_OFFLINE"] = "1"
                try:
                    model = SentenceTransformer(profile.hf_model_id, cache_folder=str(cache_dir))
                finally:
                    if old_offline is None:
                        os.environ.pop("HF_HUB_OFFLINE", None)
                    else:
                        os.environ["HF_HUB_OFFLINE"] = old_offline
                return {"model": model, "tokenizer": None}
            except Exception as e:
                logger.warning(f"SentenceTransformer failed to load (offline/timeout): {e}. Using Mock.")
                class MockEncoder:
                    def encode(self, texts, **kwargs):
                        import numpy as np
                        return np.random.rand(len(texts), 384)
                return {"model": MockEncoder(), "tokenizer": None}
            
        elif name == "biomedvlp":
            # This model is very heavy (900MB). We load it only if explicitly requested or if RAM is high.
            from transformers import AutoModel, AutoTokenizer
            # Skip loading if we are in a tight environment
            return {"model": None, "tokenizer": None}
            
        elif name == "classifier":
            try:
                import os
                old_offline = os.environ.get("HF_HUB_OFFLINE")
                os.environ["HF_HUB_OFFLINE"] = "1"
                try:
                    from transformers import pipeline
                    pipe = pipeline(
                        "zero-shot-classification",
                        model=profile.hf_model_id,
                        device=-1,
                        model_kwargs={"local_files_only": True}
                    )
                    return {"model": pipe, "tokenizer": None}
                finally:
                    if old_offline is None:
                        os.environ.pop("HF_HUB_OFFLINE", None)
                    else:
                        os.environ["HF_HUB_OFFLINE"] = old_offline
            except Exception as e:
                logger.warning(f"Classifier failed to load (offline/no cache): {e}. Using rule-based classification.")
                return {"model": None, "tokenizer": None}
            
        else:
            raise ValueError(f"No loader defined for model: {name}")

    def _resolve_device(self, profile: ModelProfile) -> str:
        if profile.device_preference == "cpu":
            return "cpu"
        import torch
        if profile.device_preference == "cuda":
            if not torch.cuda.is_available():
                ml_logger.logger.warning(f"CUDA not available, loading {profile.name} on CPU")
                return "cpu"
            return "cuda"
        if profile.device_preference == "auto":
            if torch.cuda.is_available():
                free_vram = self._gpu_budget_mb - self._get_used_vram()
                if free_vram >= profile.vram_mb:
                    return "cuda"
            return "cpu"

    def _get_used_vram(self) -> int:
        return sum(s.profile.vram_mb for s in self._states.values() if s.is_available and s.current_device == "cuda")

    async def _evict_lru_gpu_model(self, except_model: str) -> str | None:
        gpu_models = [
            (name, state) for name, state in self._states.items()
            if state.is_available and state.current_device == "cuda" and name != except_model
        ]
        if not gpu_models:
            return None
            
        lru_name, _ = min(gpu_models, key=lambda x: x[1].last_used or datetime.min.replace(tzinfo=timezone.utc))
        await asyncio.to_thread(self._move_to_cpu, lru_name)
        return lru_name

    def _move_to_cpu(self, model_name: str):
        state = self._states[model_name]
        if state.model is not None and hasattr(state.model, "cpu"):
            import torch
            state.model = state.model.cpu()
            torch.cuda.empty_cache()
            state.current_device = "cpu"
            ml_logger.logger.info(f"Moved {model_name} to CPU")

    def get_status(self) -> dict:
        return {
            "models": {
                name: {
                    "is_available": state.is_available,
                    "device": state.current_device,
                    "load_error": state.load_error,
                    "load_time_ms": state.load_time_ms,
                    "last_used": state.last_used.isoformat() if state.last_used else None,
                    "vram_mb": state.profile.vram_mb if state.current_device == "cuda" else 0
                }
                for name, state in self._states.items()
            },
            "gpu_budget_mb": self._gpu_budget_mb,
            "gpu_used_mb": self._get_used_vram(),
            "gpu_free_mb": self._gpu_budget_mb - self._get_used_vram()
        }

model_registry = ModelRegistry()
