"""
Pulmonary anomaly architecture from covid.ipynb:
VGG16 (frozen) -> VAE on 512-d features -> ViT scorer on latent z -> fused anomaly score.

Checkpoint format: pulmonary_anomaly_detector.pth with vae_state, vit_state, config, threshold, recon_*, kl_*.
"""

from __future__ import annotations

import base64
import io
import logging
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image, ImageDraw
from torchvision import models, transforms

logger = logging.getLogger(__name__)


class VGG16Backbone(nn.Module):
    """Pre-trained VGG16 with frozen weights -> 512-dim feature vector."""

    def __init__(self, freeze: bool = True):
        super().__init__()
        vgg = models.vgg16(weights=models.VGG16_Weights.IMAGENET1K_V1)
        self.features = vgg.features
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        if freeze:
            for param in self.parameters():
                param.requires_grad = False
        self.out_dim = 512

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = self.avgpool(x)
        return torch.flatten(x, 1)


class VAEEncoder(nn.Module):
    def __init__(self, in_dim: int, hidden_dims: list[int], latent_dim: int):
        super().__init__()
        layers: list[nn.Module] = []
        prev = in_dim
        for h in hidden_dims:
            layers += [nn.Linear(prev, h), nn.LayerNorm(h), nn.GELU(), nn.Dropout(0.1)]
            prev = h
        self.net = nn.Sequential(*layers)
        self.fc_mu = nn.Linear(prev, latent_dim)
        self.fc_var = nn.Linear(prev, latent_dim)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        h = self.net(x)
        return self.fc_mu(h), self.fc_var(h)


class VAEDecoder(nn.Module):
    def __init__(self, latent_dim: int, hidden_dims: list[int], out_dim: int):
        super().__init__()
        layers: list[nn.Module] = []
        prev = latent_dim
        for h in reversed(hidden_dims):
            layers += [nn.Linear(prev, h), nn.LayerNorm(h), nn.GELU(), nn.Dropout(0.1)]
            prev = h
        layers += [nn.Linear(prev, out_dim)]
        self.net = nn.Sequential(*layers)

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        return self.net(z)


class VAE(nn.Module):
    def __init__(self, in_dim: int, hidden_dims: list[int], latent_dim: int):
        super().__init__()
        self.encoder = VAEEncoder(in_dim, hidden_dims, latent_dim)
        self.decoder = VAEDecoder(latent_dim, hidden_dims, in_dim)
        self.latent_dim = latent_dim

    def reparameterize(self, mu: torch.Tensor, log_var: torch.Tensor) -> torch.Tensor:
        if self.training:
            std = torch.exp(0.5 * log_var)
            return mu + torch.randn_like(std) * std
        return mu

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        mu, log_var = self.encoder(x)
        z = self.reparameterize(mu, log_var)
        x_hat = self.decoder(z)
        return x_hat, mu, log_var, z


class MultiHeadSelfAttention(nn.Module):
    def __init__(self, dim: int, num_heads: int, dropout: float = 0.0):
        super().__init__()
        assert dim % num_heads == 0
        self.num_heads = num_heads
        self.head_dim = dim // num_heads
        self.scale = self.head_dim**-0.5
        self.qkv = nn.Linear(dim, dim * 3, bias=False)
        self.proj = nn.Linear(dim, dim)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        b, n, d = x.shape
        qkv = self.qkv(x).reshape(b, n, 3, self.num_heads, self.head_dim)
        qkv = qkv.permute(2, 0, 3, 1, 4)
        q, k, v = qkv.unbind(0)
        attn = (q @ k.transpose(-2, -1)) * self.scale
        attn = attn.softmax(dim=-1)
        attn = self.dropout(attn)
        out = (attn @ v).transpose(1, 2).reshape(b, n, d)
        return self.proj(out), attn


class TransformerBlock(nn.Module):
    def __init__(self, dim: int, num_heads: int, mlp_dim: int, dropout: float = 0.0):
        super().__init__()
        self.norm1 = nn.LayerNorm(dim)
        self.attn = MultiHeadSelfAttention(dim, num_heads, dropout)
        self.norm2 = nn.LayerNorm(dim)
        self.ffn = nn.Sequential(
            nn.Linear(dim, mlp_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(mlp_dim, dim),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        attn_out, weights = self.attn(self.norm1(x))
        x = x + attn_out
        x = x + self.ffn(self.norm2(x))
        return x, weights


class ViTAnomalyScorer(nn.Module):
    """ViT that scores anomaly level of latent vector z -> scalar in [0, 1]."""

    def __init__(
        self,
        latent_dim: int,
        patch_dim: int,
        depth: int,
        num_heads: int,
        mlp_dim: int,
        dropout: float = 0.1,
    ):
        super().__init__()
        assert latent_dim % patch_dim == 0
        self.num_patches = latent_dim // patch_dim
        self.d_model = patch_dim * 4

        self.patch_embed = nn.Linear(patch_dim, self.d_model)
        self.cls_token = nn.Parameter(torch.zeros(1, 1, self.d_model))
        self.pos_embed = nn.Parameter(torch.randn(1, self.num_patches + 1, self.d_model) * 0.02)
        self.dropout = nn.Dropout(dropout)
        self.blocks = nn.ModuleList(
            [TransformerBlock(self.d_model, num_heads, mlp_dim, dropout) for _ in range(depth)]
        )
        self.norm = nn.LayerNorm(self.d_model)
        self.head = nn.Sequential(
            nn.Linear(self.d_model, mlp_dim // 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(mlp_dim // 4, 1),
            nn.Sigmoid(),
        )
        nn.init.trunc_normal_(self.cls_token, std=0.02)
        nn.init.trunc_normal_(self.pos_embed, std=0.02)

    def forward(self, z: torch.Tensor, return_attention: bool = False):
        b = z.shape[0]
        x = self.patch_embed(z.reshape(b, self.num_patches, -1))
        cls = self.cls_token.expand(b, -1, -1)
        x = self.dropout(torch.cat([cls, x], dim=1) + self.pos_embed)
        all_attns: list[torch.Tensor] = []
        for block in self.blocks:
            x, attn = block(x)
            all_attns.append(attn)
        x = self.norm(x)
        score = self.head(x[:, 0]).squeeze(-1)
        if return_attention:
            return score, all_attns
        return score


class PulmonaryAnomalyDetector(nn.Module):
    """X-ray -> VGG16 -> VAE -> ViT -> anomaly components (matches notebook)."""

    def __init__(self, backbone: VGG16Backbone, vae: VAE, vit: ViTAnomalyScorer):
        super().__init__()
        self.backbone = backbone
        self.vae = vae
        self.vit = vit
        self.register_buffer("recon_mean", torch.tensor(0.0))
        self.register_buffer("recon_std", torch.tensor(1.0))
        self.register_buffer("kl_mean", torch.tensor(0.0))
        self.register_buffer("kl_std", torch.tensor(1.0))
        self._calibrated = False

    def forward(self, x: torch.Tensor, return_attention: bool = False):
        with torch.no_grad():
            feats = self.backbone(x)
        x_hat, mu, log_var, z = self.vae(feats)

        if return_attention:
            vit_score, attns = self.vit(z.detach(), return_attention=True)
        else:
            vit_score = self.vit(z.detach())
            attns = None

        recon_err = F.mse_loss(x_hat, feats, reduction="none").mean(dim=1)
        kl_div = -0.5 * (1 + log_var - mu.pow(2) - log_var.exp()).mean(dim=1)

        results = {
            "feats": feats,
            "x_hat": x_hat,
            "mu": mu,
            "log_var": log_var,
            "z": z,
            "recon_err": recon_err,
            "kl_div": kl_div,
            "vit_score": vit_score,
        }
        if return_attention:
            results["attentions"] = attns
        return results

    def compute_anomaly_score(self, out: dict, weights: tuple[float, float, float] = (0.4, 0.2, 0.4)) -> torch.Tensor:
        if not self._calibrated:
            raise RuntimeError("PulmonaryAnomalyDetector is not calibrated (missing checkpoint stats).")
        w1, w2, w3 = weights
        recon = torch.sigmoid((out["recon_err"] - self.recon_mean) / self.recon_std)
        kl = torch.sigmoid((out["kl_div"] - self.kl_mean) / self.kl_std)
        return w1 * recon + w2 * kl + w3 * out["vit_score"]


def _load_checkpoint_dict(path: Path, device: torch.device) -> dict:
    try:
        return torch.load(path, map_location=device, weights_only=False)
    except TypeError:
        return torch.load(path, map_location=device)


def build_detector_from_checkpoint(ckpt: dict, device: torch.device) -> tuple[PulmonaryAnomalyDetector, float]:
    cfg = ckpt["config"]
    bb = VGG16Backbone(freeze=True).to(device)
    v = VAE(cfg["vgg_feat_dim"], cfg["vae_hidden"], cfg["latent_dim"]).to(device)
    vt = ViTAnomalyScorer(
        cfg["latent_dim"],
        cfg["vit_patch_dim"],
        cfg["vit_depth"],
        cfg["vit_heads"],
        cfg["vit_mlp_dim"],
        cfg["vit_dropout"],
    ).to(device)
    v.load_state_dict(ckpt["vae_state"])
    vt.load_state_dict(ckpt["vit_state"])
    m = PulmonaryAnomalyDetector(bb, v, vt).to(device)
    with torch.no_grad():
        m.recon_mean.copy_(torch.as_tensor(ckpt["recon_mean"], device=device).reshape_as(m.recon_mean))
        m.recon_std.copy_(torch.as_tensor(ckpt["recon_std"], device=device).reshape_as(m.recon_std).clamp_min(1e-8))
        m.kl_mean.copy_(torch.as_tensor(ckpt["kl_mean"], device=device).reshape_as(m.kl_mean))
        m.kl_std.copy_(torch.as_tensor(ckpt["kl_std"], device=device).reshape_as(m.kl_std).clamp_min(1e-8))
    m._calibrated = True
    m.eval()
    thresh = float(ckpt.get("threshold", 0.5))
    return m, thresh


def load_pulmonary_detector(checkpoint_path: Path, device: str | None = None) -> "PulmonaryModelWrapper":
    dev = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
    ckpt = _load_checkpoint_dict(checkpoint_path, dev)
    detector, thresh = build_detector_from_checkpoint(ckpt, dev)
    logger.info("Loaded pulmonary detector from %s (threshold=%.4f)", checkpoint_path, thresh)
    return PulmonaryModelWrapper(detector, thresh, dev)


class PulmonaryModelWrapper:
    """Inference + visualization (ViT CLS attention over latent patches, no GradCAM / no DINO)."""

    _transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    def __init__(self, detector: PulmonaryAnomalyDetector, threshold: float, device: torch.device):
        self.detector = detector
        self.threshold = threshold
        self.device = device

    def predict(self, image_path: Path) -> tuple[float, float, str, list[dict]]:
        img = Image.open(image_path).convert("RGB")
        x = self._transform(img).unsqueeze(0).to(self.device)
        original_np = np.array(img.resize((224, 224)), dtype=np.uint8)

        self.detector.eval()
        with torch.no_grad():
            out = self.detector(x, return_attention=True)

        score_01 = self.detector.compute_anomaly_score(out).squeeze()
        score_100 = float((score_01 * 100.0).clamp(0.0, 100.0).item())
        anomaly_score = round(score_100, 1)
        s01 = float(score_01.item())
        confidence = round(min(0.95, max(0.25, abs(s01 - self.threshold) * 2.0)), 3)

        heatmap = self._cls_attention_map(out["attentions"][-1])
        heatmap_b64, top_regions = self._panel_and_regions(original_np, heatmap, anomaly_score, "ViT attention")

        return anomaly_score, confidence, heatmap_b64, top_regions

    def _cls_attention_map(self, attn: torch.Tensor) -> np.ndarray:
        """(B, H, L, L) -> 384x384 grayscale heatmap in [0,1]."""
        att = attn[0].mean(dim=0).float().cpu().numpy()  # (L, L)
        n = att.shape[0] - 1
        w = att[0, 1 : 1 + n]
        side_h = int(np.sqrt(n))
        side_w = (n + side_h - 1) // side_h if side_h else 1
        if side_h * side_w < n:
            side_w = n
            side_h = 1
        pad = side_h * side_w - n
        if pad > 0:
            w = np.pad(w, (0, pad), constant_values=w.min())
        grid = w.reshape(side_h, side_w)
        grid = (grid - grid.min()) / (grid.max() - grid.min() + 1e-8)
        heat = cv2.resize(grid.astype(np.float32), (384, 384), interpolation=cv2.INTER_CUBIC)
        # Smooth the coarse attention grid to remove blocky artifacts
        heat = cv2.GaussianBlur(heat, (31, 31), sigmaX=12, sigmaY=12)
        return (heat - heat.min()) / (heat.max() - heat.min() + 1e-8)

    def _panel_and_regions(
        self, original_rgb: np.ndarray, heatmap: np.ndarray, anomaly_score: float, heatmap_label: str
    ) -> tuple[str, list[dict]]:
        panel_size = 384
        original_resized = cv2.resize(original_rgb, (panel_size, panel_size), interpolation=cv2.INTER_LANCZOS4)
        heatmap_resized = cv2.resize(heatmap, (panel_size, panel_size), interpolation=cv2.INTER_CUBIC) if heatmap.shape[0] != panel_size else heatmap

        # ── Clinical Grad-CAM colormap (black → dark red → orange → yellow) ──
        heat_color = _clinical_colormap(heatmap_resized)

        # ── Overlay with adaptive alpha masking (only hot regions glow) ──
        overlay = _clinical_overlay(original_resized, heatmap_resized, heat_color)

        top_regions = _find_top_regions(heatmap_resized, n=3)
        panel = _create_panel(original_resized, heat_color, overlay, anomaly_score, heatmap_label, heatmap_resized)

        buffer = io.BytesIO()
        Image.fromarray(panel).save(buffer, format="PNG", optimize=True, quality=95)
        b64 = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()
        return b64, top_regions


def _clinical_colormap(heatmap: np.ndarray) -> np.ndarray:
    """Build a dark-to-red-to-yellow clinical heatmap (Grad-CAM style).
    Low attention = dark/transparent, high attention = bright yellow/white.
    LUT must be BGR because cv2.applyColorMap operates in BGR space."""
    lut = np.zeros((256, 1, 3), dtype=np.uint8)
    for i in range(256):
        t = i / 255.0
        if t < 0.25:
            # Black → deep dark red
            r, g, b = int(t / 0.25 * 120), 0, int(t / 0.25 * 15)
        elif t < 0.55:
            # Deep red → bright red
            frac = (t - 0.25) / 0.30
            r, g, b = 120 + int(frac * 135), int(frac * 20), 15 - int(frac * 15)
        elif t < 0.80:
            # Red → orange/amber
            frac = (t - 0.55) / 0.25
            r, g, b = 255, 20 + int(frac * 160), 0
        else:
            # Orange → bright yellow/white
            frac = (t - 0.80) / 0.20
            r, g, b = 255, 180 + int(frac * 75), int(frac * 80)
        lut[i, 0] = [b, g, r]  # BGR order for OpenCV

    heat_u8 = np.uint8(255 * np.clip(heatmap, 0, 1))
    colored = cv2.applyColorMap(heat_u8, lut)
    return cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)


def _clinical_overlay(original: np.ndarray, heatmap: np.ndarray, heat_color: np.ndarray) -> np.ndarray:
    """Create overlay with adaptive per-pixel alpha: only hot regions glow over X-ray.
    Uses CLAHE-enhanced X-ray as base for better anatomical contrast."""
    # Enhance X-ray contrast with CLAHE
    gray = cv2.cvtColor(original, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_gray = clahe.apply(gray)
    base_rgb = cv2.cvtColor(enhanced_gray, cv2.COLOR_GRAY2RGB)

    # Adaptive alpha: ramp from 0 below 30th percentile to 0.65 at max
    p30 = np.percentile(heatmap, 30)
    alpha_map = np.clip((heatmap - p30) / (1.0 - p30 + 1e-8), 0, 1)
    alpha_map = (alpha_map ** 1.3) * 0.65  # Power curve for sharper falloff
    alpha_3ch = np.stack([alpha_map] * 3, axis=-1).astype(np.float32)

    overlay = np.uint8(alpha_3ch * heat_color.astype(np.float32) + (1.0 - alpha_3ch) * base_rgb.astype(np.float32))

    # Draw contour outlines around top anomaly regions
    p85 = np.percentile(heatmap, 85)
    binary = (heatmap >= p85).astype(np.uint8)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [c for c in contours if cv2.contourArea(c) > 50]
    cv2.drawContours(overlay, contours, -1, (255, 255, 100), 2, cv2.LINE_AA)

    return overlay


def _find_top_regions(heatmap: np.ndarray, n: int = 3) -> list[dict]:
    threshold = np.percentile(heatmap, 80)
    binary = (heatmap >= threshold).astype(np.uint8)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:n]
    regions: list[dict] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        confidence = float(heatmap[y : y + h, x : x + w].mean())
        regions.append({"x": int(x), "y": int(y), "width": int(w), "height": int(h), "confidence": round(confidence, 3)})
    return regions


def _create_panel(
    original: np.ndarray, heatmap: np.ndarray, overlay: np.ndarray,
    anomaly_score: float, heatmap_label: str = "Map", raw_heatmap: np.ndarray | None = None
) -> np.ndarray:
    h, w = original.shape[:2]
    gap = 4
    label_h = 36
    total_w = w * 3 + gap * 2
    panel = np.zeros((h + label_h, total_w, 3), dtype=np.uint8)
    heatmap_r = cv2.resize(heatmap, (w, h), interpolation=cv2.INTER_LANCZOS4) if heatmap.shape[:2] != (h, w) else heatmap
    overlay_r = cv2.resize(overlay, (w, h), interpolation=cv2.INTER_LANCZOS4) if overlay.shape[:2] != (h, w) else overlay
    panel[0:h, 0:w] = original
    panel[0:h, w + gap : w * 2 + gap] = heatmap_r
    panel[0:h, w * 2 + gap * 2 : w * 3 + gap * 2] = overlay_r
    panel_pil = Image.fromarray(panel)
    draw = ImageDraw.Draw(panel_pil)
    risk_color = (255, 80, 80) if anomaly_score > 70 else (255, 200, 0) if anomaly_score > 40 else (80, 200, 80)
    draw.text((5, h + 8), "Original", fill=(200, 200, 200))
    draw.text((w + gap + 5, h + 8), heatmap_label, fill=(200, 200, 200))
    draw.text((w * 2 + gap * 2 + 5, h + 8), f"Overlay ({anomaly_score:.1f})", fill=risk_color)
    return np.array(panel_pil)


def onnx_reconstruction_panel(
    image_path: Path, reconstructed_np: np.ndarray, anomaly_score: float
) -> tuple[str, list[dict]]:
    """Legacy ConvAE ONNX visualization (no GradCAM class)."""
    original_image = Image.open(image_path).convert("RGB")
    original_np = np.array(original_image.resize((224, 224)), dtype=np.uint8)
    orig_l = np.array(original_image.resize((224, 224)).convert("L"), dtype=np.float32) / 255.0
    rec = np.asarray(reconstructed_np, dtype=np.float32)
    if rec.shape != orig_l.shape:
        rec = cv2.resize(rec, (orig_l.shape[1], orig_l.shape[0]), interpolation=cv2.INTER_LINEAR)
    diff = np.abs(orig_l - rec)
    heatmap = cv2.GaussianBlur(diff, (15, 15), 0)
    heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min() + 1e-8)
    heat_u8 = np.uint8(255 * heatmap)
    heat_color = cv2.applyColorMap(heat_u8, cv2.COLORMAP_HOT)
    heat_color = cv2.cvtColor(heat_color, cv2.COLOR_BGR2RGB)
    overlay = np.uint8(0.5 * heat_color + 0.5 * original_np)
    top_regions = _find_top_regions(heatmap, n=3)
    panel = _create_panel(original_np, heat_color, overlay, anomaly_score, "Reconstruction")
    buffer = io.BytesIO()
    Image.fromarray(panel).save(buffer, format="PNG", optimize=True)
    b64 = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()
    return b64, top_regions
