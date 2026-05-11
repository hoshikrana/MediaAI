import torch
import torch.nn as nn
import torch.nn.functional as F
from pathlib import Path
from PIL import Image
from torchvision import transforms
import numpy as np

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
    def score_convae(image_path: Path, session: any, stats: dict) -> tuple[float, float, any]:
        # session is an onnxruntime.InferenceSession
        image = Image.open(image_path).convert("L").resize((128, 128))
        img_np = np.array(image, dtype=np.float32) / 255.0
        input_tensor = img_np[np.newaxis, np.newaxis, :, :] # 1x1x128x128
        
        # ONNX Inference
        outputs = session.run(None, {session.get_inputs()[0].name: input_tensor})
        reconstructed = outputs[0][0, 0, :, :]
        
        raw_score = np.mean((img_np - reconstructed)**2)
        
        z = (raw_score - stats["mean"]) / (stats["std"] + 1e-8)
        normalized = float(min(100, max(0, (z + 3) / 6 * 100)))
        
        confidence = abs(normalized - 50) / 50
        return round(normalized, 1), round(confidence, 3), reconstructed

    @staticmethod
    def score(image_path: Path, model: nn.Module, head: nn.Module, stats: dict, device: str) -> tuple[float, float]:
        # Legacy DINO path
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
