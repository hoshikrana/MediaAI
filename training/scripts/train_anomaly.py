import logging
import json
import time
from pathlib import Path
import torch
from dataset import ChestXrayDataset
from anomaly_model import DINOAnomalyDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Hyperparameters tailored for 4GB VRAM
EPOCHS = 50
BATCH_SIZE = 8
LEARNING_RATE = 1e-3
WEIGHT_DECAY = 1e-4
GRAD_ACCUMULATION = 4
CHECKPOINT_EVERY = 5
EARLY_STOP_PATIENCE = 10
FP16 = True

def evaluate(model, loader, device):
    model.eval()
    total_loss = 0.0
    with torch.no_grad():
        for images, _ in loader:
            images = images.to(device, non_blocking=True)
            outputs = model(images)
            total_loss += outputs["loss"].item()
    return total_loss / len(loader)

def compute_normalization_stats(model, loader, device, out_dir):
    model.eval()
    all_scores = []
    with torch.no_grad(), torch.autocast(device_type="cuda", dtype=torch.float16, enabled=FP16):
        for images, _ in loader:
            images = images.to(device, non_blocking=True)
            scores = model.get_anomaly_score_raw(images).cpu().numpy()
            all_scores.extend(scores.tolist())
    
    import numpy as np
    arr = np.array(all_scores)
    stats = {
        "mean": float(arr.mean()),
        "std": float(arr.std()),
        "min": float(arr.min()),
        "max": float(arr.max()),
        "p95": float(np.percentile(arr, 95)),
        "p99": float(np.percentile(arr, 99))
    }
    with open(out_dir / "anomaly_stats.json", "w") as f:
        json.dump(stats, f)
    logger.info(f"Saved normalization stats: {stats}")

def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")
    
    processed_dir = Path("data/processed")
    ckpt_dir = Path("checkpoints")
    model_dir = Path("models")
    ckpt_dir.mkdir(exist_ok=True)
    model_dir.mkdir(exist_ok=True)
    
    train_loader, val_loader = ChestXrayDataset.create_dataloaders(processed_dir, batch_size=BATCH_SIZE)
    model = DINOAnomalyDetector(device=device)
    
    optimizer = torch.optim.AdamW(model.head.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=3)
    scaler = torch.cuda.amp.GradScaler(enabled=FP16)
    
    start_epoch = 0
    best_val_loss = float("inf")
    patience_counter = 0
    
    latest_ckpt = ckpt_dir / "latest.pt"
    if latest_ckpt.exists():
        print("📂 Resuming from latest checkpoint...")
        ckpt = torch.load(latest_ckpt, map_location=device)
        start_epoch = ckpt["epoch"] + 1
        model.head.load_state_dict(ckpt["model_state_dict"])
        optimizer.load_state_dict(ckpt["optimizer_state_dict"])
        scaler.load_state_dict(ckpt["scaler_state_dict"])
        best_val_loss = ckpt["best_val_loss"]
        print(f"✅ Resumed from epoch {ckpt['epoch']}, best_val_loss={best_val_loss:.6f}")
        
    for epoch in range(start_epoch, EPOCHS):
        model.head.train()
        train_loss = 0.0
        start_time = time.time()
        optimizer.zero_grad()
        
        for batch_idx, (images, _) in enumerate(train_loader):
            images = images.to(device, non_blocking=True)
            
            try:
                with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=FP16):
                    outputs = model(images)
                    loss = outputs["loss"] / GRAD_ACCUMULATION
                    
                scaler.scale(loss).backward()
                
                if (batch_idx + 1) % GRAD_ACCUMULATION == 0:
                    scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(model.head.parameters(), max_norm=1.0)
                    scaler.step(optimizer)
                    scaler.update()
                    optimizer.zero_grad()
                    
                train_loss += loss.item() * GRAD_ACCUMULATION
            except RuntimeError as e:
                if "out of memory" in str(e).lower():
                    torch.cuda.empty_cache()
                    logger.error(f"CUDA OOM at epoch {epoch}, batch {batch_idx}. Skipping batch.")
                    optimizer.zero_grad()
                    continue
                raise
                
        train_loss /= len(train_loader)
        val_loss = evaluate(model, val_loader, device)
        scheduler.step(val_loss)
        
        epoch_time = time.time() - start_time
        vram = torch.cuda.memory_reserved() // 1024 // 1024 if device == "cuda" else 0
        logger.info(f"Epoch {epoch+1}/{EPOCHS} | Train: {train_loss:.6f} | Val: {val_loss:.6f} | LR: {scheduler.get_last_lr()[0]:.2e} | VRAM: {vram}MB | Time: {epoch_time:.1f}s")
        
        is_best = val_loss < best_val_loss
        if is_best:
            best_val_loss = val_loss
            patience_counter = 0
            torch.save(model.head.state_dict(), model_dir / "anomaly_head.pt")
            compute_normalization_stats(model, train_loader, device, model_dir)
        else:
            patience_counter += 1
            
        # Checkpointing
        ckpt_data = {
            "epoch": epoch,
            "model_state_dict": model.head.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scaler_state_dict": scaler.state_dict(),
            "best_val_loss": best_val_loss,
        }
        torch.save(ckpt_data, latest_ckpt)
        
        if (epoch + 1) % CHECKPOINT_EVERY == 0:
            torch.save(ckpt_data, ckpt_dir / f"epoch_{epoch+1:03d}.pt")
            
        if patience_counter >= EARLY_STOP_PATIENCE:
            logger.info("Early stopping triggered.")
            break

if __name__ == "__main__":
    main()
