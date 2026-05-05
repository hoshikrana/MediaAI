import io
import base64
from pathlib import Path
import numpy as np
import cv2
import torch
from torchvision import transforms
from PIL import Image, ImageDraw

class DINOAttentionRollout:
    """Extracts spatial attention maps from DINOv2 using Rollout."""
    def __init__(self, model, discard_ratio: float = 0.9):
        self.model = model
        self.discard_ratio = discard_ratio
        self._attention_maps = []
        self._hooks = []
    
    def _register_hooks(self):
        def hook_fn(module, input, output):
            self._attention_maps.append(output.detach())
        
        for block in self.model.blocks:
            hook = block.attn.register_forward_hook(hook_fn)
            self._hooks.append(hook)
    
    def _remove_hooks(self):
        for hook in self._hooks:
            hook.remove()
        self._hooks.clear()
        self._attention_maps.clear()
    
    @torch.no_grad()
    def compute_rollout(self, image_tensor: torch.Tensor) -> np.ndarray:
        self._attention_maps = []
        self._register_hooks()
        
        try:
            _ = self.model(image_tensor)
        finally:
            self._remove_hooks()
            
        result = torch.eye(197, device=image_tensor.device)
        
        for attn in self._attention_maps:
            attn_mean = attn.mean(dim=1) 
            
            flat = attn_mean.view(attn_mean.size(0), -1)
            threshold = torch.quantile(flat, self.discard_ratio, dim=-1, keepdim=True)
            threshold = threshold.view(-1, 1, 1)
            attn_mean = torch.where(attn_mean >= threshold, attn_mean, torch.zeros_like(attn_mean))
            
            attn_mean = attn_mean + torch.eye(197, device=image_tensor.device)
            attn_mean = attn_mean / attn_mean.sum(dim=-1, keepdim=True)
            result = torch.matmul(attn_mean[0], result)
            
        mask = result[0, 1:]
        mask = mask.reshape(14, 14)
        mask = mask.cpu().numpy()
        mask = (mask - mask.min()) / (mask.max() - mask.min() + 1e-8)
        return mask

class GradCAM:
    @staticmethod
    def generate(image_path: Path, model, anomaly_score: float) -> tuple[str, list[dict]]:
        device = next(model.parameters()).device
        
        original_image = Image.open(image_path).convert("RGB")
        original_np = np.array(original_image.resize((224, 224)))
        
        image_tensor = GradCAM._preprocess(original_image, device)
        
        rollout = DINOAttentionRollout(model.dino if hasattr(model, 'dino') else model, discard_ratio=0.9)
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
