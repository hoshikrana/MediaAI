# Vision anomaly model — scope, layout, and integration

This document is the canonical reference for wiring **your trained outputs** into the MedSight API.  
(Referenced in product discussions as **contextScopeItemMention**.)  
Training notebook in repo: **`covid (1).ipynb`** (same content as any copy named `covid.ipynb`).

## Primary architecture (covid notebook)

The default production path matches **`covid.ipynb`** / **`covid (1).ipynb`**:

**Frozen VGG16 → β-VAE on 512-d features → ViT anomaly scorer on latent `z` → fused score** (`PulmonaryAnomalyDetector`).

Checkpoint: `pulmonary_anomaly_detector.pth` with `vae_state`, `vit_state`, `config`, calibration (`recon_mean`, `recon_std`, `kl_mean`, `kl_std`), and `threshold`.

## Supported runtime modes (`VISION_ANOMALY_BACKEND`)

| Mode | Artifacts | Notes |
|------|-----------|--------|
| **pulmonary** | `pulmonary_anomaly_detector.pth` (or `pulmonary_anomaly.pth`) | Notebook export; VGG weights from torchvision |
| **onnx** | `chest_convae.onnx` or `convae.onnx` + optional `anomaly_stats.json` | Legacy ConvAE path only |

With **`VISION_ANOMALY_BACKEND=auto`** (default):

1. If a pulmonary checkpoint exists under search paths → **pulmonary**
2. Else if ONNX exists → **onnx**
3. Else → demo / heuristic vision fallback

## Search order (where to put files)

1. **`TRAINED_MODEL_OUTPUT_DIR`** (default: `./results/outputs`)
2. **`MODEL_CACHE_DIR`**
3. **`./models`**

Optional overrides in `.env`:

- `PULMONARY_CHECKPOINT_PATH` — full path to `pulmonary_anomaly_detector.pth`
- `CONVAE_ONNX_PATH` — ONNX ConvAE
- `ANOMALY_STATS_PATH` — ONNX stats JSON (optional)

## Heatmaps (no GradCAM, no DINO)

- **Pulmonary**: last ViT block **CLS → latent-patch** attention, reshaped and upsampled to 224×224, overlaid on the X-ray.
- **ONNX ConvAE**: **reconstruction difference** map (same idea as before, implemented in `pulmonary_anomaly.onnx_reconstruction_panel`).

## Environment variables (summary)

```env
VISION_ANOMALY_BACKEND=auto
TRAINED_MODEL_OUTPUT_DIR=./results/outputs
# PULMONARY_CHECKPOINT_PATH=
# CONVAE_ONNX_PATH=
# ANOMALY_STATS_PATH=
```

## Operational notes

- First **VGG16** load uses **torchvision** pretrained weights (download once if not cached).
- **ONNX** path requires **`onnxruntime`**.
- Plot PNGs under `results/outputs` are not used for inference.

## Code map

| Piece | Role |
|-------|------|
| `backend/ml/vision/model_paths.py` | Resolves pulmonary checkpoint vs ONNX |
| `backend/ml/vision/pulmonary_anomaly.py` | Notebook architecture + inference + heatmaps |
| `backend/ml/registry.py` | Loads `convae_anomaly` slot (pulmonary wrapper or ONNX session) |
| `backend/orchestration/pipeline.py` | Vision branch |
| `backend/ml/vision/anomaly.py` | ONNX scoring only |
