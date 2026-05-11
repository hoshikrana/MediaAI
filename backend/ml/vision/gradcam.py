import io
import base64
from pathlib import Path
import numpy as np
import cv2
import torch
from torchvision import transforms
from PIL import Image, ImageDraw

class ReconstructionDiffMap:
    """Visualizes anomalies by highlighting pixel-wise reconstruction error."""
    @staticmethod
    def generate(original_image: Image.Image, reconstructed_np: np.ndarray) -> np.ndarray:
        # original_image: PIL Image (128x128 or 224x224)
        # reconstructed_np: np.ndarray normalized (0-1)
        
        orig_np = np.array(original_image.convert("L"), dtype=np.float32) / 255.0
        
        # Calculate absolute difference
        diff = np.abs(orig_np - reconstructed_np)
        
        # Apply Gaussian blur to smooth the heatmap
        heatmap = cv2.GaussianBlur(diff, (15, 15), 0)
        
        # Normalize to 0-1
        heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min() + 1e-8)
        return heatmap

class GradCAM:
    def generate(image_path: Path, model_session, anomaly_score: float, reconstructed_np: np.ndarray | None = None) -> tuple[str, list[dict]]:
        original_image = Image.open(image_path).convert("RGB")
        img_size = original_image.size # (W, H)
        original_np = np.array(original_image.resize((224, 224)))
        
        if reconstructed_np is not None:
            # ConvAE path: uses reconstruction difference
            heatmap = ReconstructionDiffMap.generate(original_image.resize((224, 224)), reconstructed_np)
        else:
            # ViT path: uses DINO rollout (if model_session is a torch model)
            # This is deprecated in Zero-Budget mode but kept for compatibility
            device = next(model_session.parameters()).device if hasattr(model_session, "parameters") else "cpu"
            image_tensor = GradCAM._preprocess(original_image, device)
            rollout = DINOAttentionRollout(model_session, discard_ratio=0.9)
            attention_map = rollout.compute_rollout(image_tensor)
            heatmap = cv2.resize(attention_map, (224, 224))
            heatmap = np.float32(heatmap)
        
        heatmap_colored = cv2.applyColorMap(np.uint8(255 * heatmap), cv2.COLORMAP_HOT)
        heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)
        
        alpha = 0.5
        overlay = np.uint8(alpha * heatmap_colored + (1 - alpha) * original_np)
        
        top_regions = GradCAM._find_top_regions(heatmap, n=3)
        panel = GradCAM._create_panel(original_np, heatmap_colored, overlay, anomaly_score)
        
        buffer = io.BytesIO()
        panel_image = Image.fromarray(panel)
        panel_image.save(buffer, format="PNG", optimize=True)
        b64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{b64}", top_regions
    
    @staticmethod
    def _preprocess(image: Image.Image, device: str) -> torch.Tensor:
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        return transform(image).unsqueeze(0).to(device)
    
    @staticmethod
    def _find_top_regions(heatmap: np.ndarray, n: int = 3) -> list[dict]:
        threshold = np.percentile(heatmap, 80)
        binary = (heatmap >= threshold).astype(np.uint8)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:n]
        
        regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            confidence = float(heatmap[y:y+h, x:x+w].mean())
            regions.append({
                "x": int(x), "y": int(y), "width": int(w), "height": int(h),
                "confidence": round(confidence, 3)
            })
        return regions
    
    @staticmethod
    def _create_panel(original: np.ndarray, heatmap: np.ndarray, overlay: np.ndarray, anomaly_score: float) -> np.ndarray:
        h, w = 224, 224
        panel = np.zeros((h + 30, w * 3 + 20, 3), dtype=np.uint8)
        
        panel[0:h, 0:w] = original
        panel[0:h, w+10:w*2+10] = heatmap
        panel[0:h, w*2+20:w*3+20] = overlay
        
        panel_pil = Image.fromarray(panel)
        draw = ImageDraw.Draw(panel_pil)
        risk_color = (255, 80, 80) if anomaly_score > 70 else (255, 200, 0) if anomaly_score > 40 else (80, 200, 80)
        draw.text((5, h+5), "Original", fill=(200, 200, 200))
        draw.text((w+15, h+5), "Attention Map", fill=(200, 200, 200))
        draw.text((w*2+25, h+5), f"Overlay ({anomaly_score:.1f})", fill=risk_color)
        
        return np.array(panel_pil)

if __name__ == "__main__":
    # Test script setup
    print("Testing GradCAM generation...")
    # You would pass a dummy model and image here to test.
