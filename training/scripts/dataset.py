import json
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms

class ChestXrayDataset(Dataset):
    def __init__(self, file_list_path: Path, batch_dir: Path, stats_path: Path, augment: bool = False, image_size: int = 224):
        self.file_list = self._load_file_list(file_list_path)
        self.batch_dir = batch_dir
        self.stats = json.loads(stats_path.read_text())
        self.augment = augment
        self.image_size = image_size
        
        self._build_index()
        
        normalize = transforms.Normalize(mean=self.stats["mean"], std=self.stats["std"])
        
        self.base_transform = transforms.Compose([
            transforms.ToTensor(),
            normalize
        ])
        
        self.augment_transform = transforms.Compose([
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=10),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.ToTensor(),
            normalize
        ])
    
    def _load_file_list(self, path: Path) -> list[str]:
        return [line.strip() for line in path.read_text().splitlines() if line.strip()]
    
    def _build_index(self):
        self._index = {}
        batch_size = 500
        for i, filename in enumerate(self.file_list):
            batch_idx = i // batch_size
            pos = i % batch_size
            self._index[i] = (batch_idx, pos)
    
    def __len__(self) -> int:
        return len(self.file_list)
    
    def __getitem__(self, idx: int) -> tuple[torch.Tensor, str]:
        batch_idx, pos = self._index[idx]
        batch_path = self.batch_dir / f"batch_{batch_idx:03d}.npy"
        
        # Load only needed image safely via mmap
        batch = np.load(batch_path, mmap_mode="r")
        image_array = batch[pos].copy() 
        
        image = Image.fromarray(image_array, mode="RGB")
        transform = self.augment_transform if self.augment else self.base_transform
        tensor = transform(image)
        
        return tensor, self.file_list[idx]
    
    @staticmethod
    def create_dataloaders(processed_dir: Path, batch_size: int = 8, num_workers: int = 0) -> tuple[DataLoader, DataLoader]:
        stats_path = processed_dir / "dataset_stats.json"
        batch_dir = processed_dir / "batches"
        
        train_dataset = ChestXrayDataset(processed_dir / "train_files.txt", batch_dir, stats_path, augment=True)
        val_dataset = ChestXrayDataset(processed_dir / "val_files.txt", batch_dir, stats_path, augment=False)
        
        train_loader = DataLoader(
            train_dataset, batch_size=batch_size, shuffle=True,
            num_workers=num_workers, pin_memory=False, # Safe for Windows
            persistent_workers=False, drop_last=True
        )
        val_loader = DataLoader(
            val_dataset, batch_size=batch_size, shuffle=False,
            num_workers=num_workers, pin_memory=False
        )
        return train_loader, val_loader
