import torch
import torch.nn as nn
import torch.nn.functional as F
from pathlib import Path
from PIL import Image
from torchvision import transforms

class AnomalyDetector:
    """Stateless wrapper. Model passed in as parameter — loaded by registry."""
    
    @staticmethod
    def preprocess_image(image_path: Path) -> torch.Tensor:
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        image = Image.open(image_path).convert("RGB")
        return transform(image).unsqueeze(0) 
    
    @staticmethod
    def score(image_path: Path, model: nn.Module, head: nn.Module, stats: dict, device: str) -> tuple[float, float]:
        image_tensor = AnomalyDetector.preprocess_image(image_path).to(device)
        
        with torch.no_grad():
            dtype = torch.float16 if device == "cuda" else torch.float32
            with torch.autocast(device_type=device, dtype=dtype, enabled=(device=="cuda")):
                with torch.no_grad():
                    features = model(image_tensor) 
                reconstructed = head(features)
                raw_score = F.mse_loss(reconstructed, features).item()
        
        z = (raw_score - stats["mean"]) / (stats["std"] + 1e-8)
        normalized = float(min(100, max(0, (z + 3) / 6 * 100)))
        
        confidence = abs(normalized - 50) / 50
        return round(normalized, 1), round(confidence, 3)
