import torch
import torch.nn as nn
import torch.nn.functional as F
from pathlib import Path

class DINOProjectionHead(nn.Module):
    def __init__(self, input_dim: int = 384, hidden_dim: int = 128):
        super().__init__()
        self.projector = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.GELU(),
            nn.LayerNorm(hidden_dim),
            nn.Linear(hidden_dim, input_dim)
        )
        self._init_weights()
    
    def _init_weights(self):
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                nn.init.zeros_(module.bias)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.projector(x)

class DINOAnomalyDetector(nn.Module):
    def __init__(self, device: str = "cuda"):
        super().__init__()
        self.device_name = device
        
        self.dino = torch.hub.load(
            "facebookresearch/dinov2", "dinov2_vits14",
            pretrained=True, force_reload=False
        )
        for param in self.dino.parameters():
            param.requires_grad = False
        self.dino.eval()
        
        self.head = DINOProjectionHead(input_dim=384, hidden_dim=128)
        self.to(device)
    
    def get_features(self, images: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            outputs = self.dino(images)
        return outputs 
    
    def forward(self, images: torch.Tensor) -> dict:
        features = self.get_features(images)
        reconstructed = self.head(features)
        loss = F.mse_loss(reconstructed, features)
        return {"features": features, "reconstructed": reconstructed, "loss": loss}
    
    @torch.no_grad()
    def get_anomaly_score_raw(self, images: torch.Tensor) -> torch.Tensor:
        features = self.get_features(images)
        reconstructed = self.head(features)
        scores = F.mse_loss(features, reconstructed, reduction="none")
        return scores.mean(dim=1)

def score_image(image_path: Path, model, stats: dict, device: str) -> float:
    from torchvision import transforms
    from PIL import Image
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    image = Image.open(image_path).convert("RGB")
    image_tensor = transform(image).unsqueeze(0).to(device)
    
    with torch.no_grad(), torch.autocast(device_type="cuda", dtype=torch.float16):
        raw_score = model.get_anomaly_score_raw(image_tensor).item()
    
    z_score = (raw_score - stats["mean"]) / (stats["std"] + 1e-8)
    normalized = min(100, max(0, (z_score + 3) / 6 * 100)) 
    return round(normalized, 1)
