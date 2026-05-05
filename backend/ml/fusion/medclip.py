import torch
import torch.nn.functional as F
from pathlib import Path
from PIL import Image
from torchvision import transforms
import logging

logger = logging.getLogger(__name__)

class MultimodalFusion:
    """Computes image-text alignment using BiomedVLP."""
    IMAGE_SIZE = 224
    
    @staticmethod
    def get_image_transform():
        return transforms.Compose([
            transforms.Resize((MultimodalFusion.IMAGE_SIZE, MultimodalFusion.IMAGE_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    
    @staticmethod
    def get_image_embedding(image_path: Path, model, device: str) -> torch.Tensor:
        image = Image.open(image_path).convert("RGB")
        transform = MultimodalFusion.get_image_transform()
        image_tensor = transform(image).unsqueeze(0).to(device)
        
        with torch.no_grad():
            embedding = model.get_image_embeddings(image_tensor)
        return F.normalize(embedding, p=2, dim=-1)
    
    @staticmethod
    def get_text_embedding(text: str, model, tokenizer, device: str) -> torch.Tensor:
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=256, padding="max_length").to(device)
        with torch.no_grad():
            embedding = model.get_text_embeddings(**inputs)
        return F.normalize(embedding, p=2, dim=-1)
    
    @staticmethod
    def compute_similarity(image_path: Path, text: str, model, tokenizer, device: str) -> tuple[float, str]:
        try:
            img_emb = MultimodalFusion.get_image_embedding(image_path, model, device)
            txt_emb = MultimodalFusion.get_text_embedding(text, model, tokenizer, device)
            
            similarity = float(torch.cosine_similarity(img_emb, txt_emb).item())
            similarity = (similarity + 1) / 2 # Shift to [0,1]
            
            if similarity >= 0.7:
                alignment = "HIGH"
            elif similarity >= 0.4:
                alignment = "MEDIUM"
            else:
                alignment = "LOW"
            return round(similarity, 3), alignment
        except Exception as e:
            logger.warning(f"Fusion similarity computation failed: {e}")
            return 0.5, "UNKNOWN"
            
    @staticmethod
    def get_fused_embedding(image_path: Path, text: str, model, tokenizer, device: str) -> torch.Tensor:
        img_emb = MultimodalFusion.get_image_embedding(image_path, model, device)
        txt_emb = MultimodalFusion.get_text_embedding(text, model, tokenizer, device)
        return torch.cat([img_emb, txt_emb], dim=-1)

class FallbackFusion:
    @staticmethod
    def compute_similarity(image_path: Path, text: str) -> tuple[float, str]:
        """Simple keyword-based fallback when BiomedVLP unavailable due to RAM constraints."""
        CHEST_KEYWORDS = ["chest", "lung", "cardiac", "pleural", "pneumo", "infiltrate", "opacity", "nodule", "effusion"]
        text_lower = text.lower()
        matches = sum(1 for kw in CHEST_KEYWORDS if kw in text_lower)
        score = min(0.9, 0.3 + matches * 0.1)
        alignment = "HIGH" if score > 0.6 else "MEDIUM" if score > 0.4 else "LOW"
        return score, alignment
