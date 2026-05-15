# Trained model outputs (drop zone)

Place **inference artifacts** here so the API finds them with default settings (`TRAINED_MODEL_OUTPUT_DIR=./results/outputs`).

## Option A — Pulmonary detector (covid notebook)

Export from the notebook as **`pulmonary_anomaly_detector.pth`** (includes VAE + ViT states, `config`, calibration stats, and `threshold`).

Suggested filename: `pulmonary_anomaly_detector.pth`  
(alternate: `pulmonary_anomaly.pth`)

## Option B — ConvAE ONNX (legacy)

- `chest_convae.onnx` (or `convae.onnx`)
- `anomaly_stats.json` (optional but recommended)

## Optional

- Plots (`training_curves.png`, etc.) are for reporting only.

See `docs/contextScopeItemMention.md`.
