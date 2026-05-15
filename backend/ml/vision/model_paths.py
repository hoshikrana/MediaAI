"""Resolve trained vision artifacts (Pulmonary VGG+VAE+ViT checkpoint vs optional ONNX ConvAE)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Literal

from backend.core.config import settings

logger = logging.getLogger(__name__)

VisionBackend = Literal["auto", "onnx", "pulmonary"]


def _search_dirs() -> list[Path]:
    dirs: list[Path] = []
    out = Path(settings.TRAINED_MODEL_OUTPUT_DIR)
    if out.exists():
        dirs.append(out.resolve())
    cache = Path(settings.MODEL_CACHE_DIR)
    dirs.append(cache.resolve())
    mdir = Path("./models").resolve()
    if mdir not in dirs:
        dirs.append(mdir)
    seen: set[str] = set()
    unique: list[Path] = []
    for d in dirs:
        key = str(d)
        if key not in seen:
            seen.add(key)
            unique.append(d)
    return unique


def resolve_pulmonary_checkpoint_path() -> Path | None:
    if settings.PULMONARY_CHECKPOINT_PATH:
        p = Path(settings.PULMONARY_CHECKPOINT_PATH)
        return p if p.is_file() else None
    for d in _search_dirs():
        for name in ("pulmonary_anomaly_detector.pth", "pulmonary_anomaly.pth"):
            cand = d / name
            if cand.is_file():
                return cand
    return None


def resolve_onnx_path() -> Path | None:
    if settings.CONVAE_ONNX_PATH:
        p = Path(settings.CONVAE_ONNX_PATH)
        return p if p.is_file() else None
    names = ("chest_convae.onnx", "convae.onnx")
    for d in _search_dirs():
        for n in names:
            cand = d / n
            if cand.is_file():
                return cand
    return None


def resolve_anomaly_stats_path() -> Path | None:
    if settings.ANOMALY_STATS_PATH:
        p = Path(settings.ANOMALY_STATS_PATH)
        return p if p.is_file() else None
    for d in _search_dirs():
        cand = d / "anomaly_stats.json"
        if cand.is_file():
            return cand
    return None


def load_stats(path: Path | None) -> dict:
    default = {"mean": 0.001, "std": 0.0005}
    if path is None or not path.is_file():
        return default
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if "mean" in data and "std" in data:
            return {"mean": float(data["mean"]), "std": float(data["std"])}
    except Exception as exc:
        logger.warning("Failed to read anomaly stats from %s: %s", path, exc)
    return default


def resolve_vision_backend() -> tuple[VisionBackend, str]:
    """Returns (effective_backend, reason) for logging."""
    pref = settings.VISION_ANOMALY_BACKEND
    pulm_p = resolve_pulmonary_checkpoint_path()
    onnx_p = resolve_onnx_path()

    if pref == "pulmonary":
        if not pulm_p:
            raise FileNotFoundError("VISION_ANOMALY_BACKEND=pulmonary but no pulmonary_anomaly_detector.pth found.")
        return "pulmonary", str(pulm_p)

    if pref == "onnx":
        if not onnx_p:
            raise FileNotFoundError("VISION_ANOMALY_BACKEND=onnx but no ConvAE ONNX file found.")
        return "onnx", str(onnx_p)

    if pulm_p:
        return "pulmonary", str(pulm_p)
    if onnx_p:
        return "onnx", str(onnx_p)
    return "none", "no_artifacts"
