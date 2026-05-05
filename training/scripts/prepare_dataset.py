import argparse
import json
import logging
import random
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from tqdm import tqdm
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default="D:/medsight_data", help="Raw images directory")
    parser.add_argument("--max_images", type=int, default=30000)
    parser.add_argument("--output_dir", type=str, default="data/processed/")
    parser.add_argument("--image_size", type=int, default=224)
    return parser.parse_args()

def main():
    args = parse_args()
    data_dir = Path(args.data_dir)
    out_dir = Path(args.output_dir)
    batch_dir = out_dir / "batches"
    
    out_dir.mkdir(parents=True, exist_ok=True)
    batch_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Parse CSV
    logger.info("Parsing CSV metadata...")
    csv_path = data_dir / "Data_Entry_2017.csv"
    if not csv_path.exists():
        logger.error(f"CSV not found at {csv_path}")
        return

    df = pd.read_csv(csv_path)
    normal_df = df[df["Finding Labels"] == "No Finding"]
    all_normal_images = normal_df["Image Index"].tolist()
    
    logger.info(f"Total 'No Finding' images found: {len(all_normal_images)}")
    
    sampled_images = random.sample(all_normal_images, min(args.max_images, len(all_normal_images)))
    logger.info(f"Sampled {len(sampled_images)} images for processing.")
    
    with open(out_dir / "normal_images.txt", "w") as f:
        for img in sampled_images:
            f.write(f"{img}\n")

    # Step 2: Validate and Convert
    logger.info("Processing images in memory-safe batches...")
    batch_size = 500
    corrupted = []
    processed_count = 0
    
    # Pre-calculate to allow resuming
    total_batches = (len(sampled_images) + batch_size - 1) // batch_size
    
    for batch_idx in range(total_batches):
        batch_file = batch_dir / f"batch_{batch_idx:03d}.npy"
        if batch_file.exists():
            logger.info(f"Resuming: {batch_file.name} already exists. Skipping.")
            processed_count += batch_size
            continue
            
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(sampled_images))
        current_batch_images = sampled_images[start_idx:end_idx]
        
        batch_array = []
        for img_name in tqdm(current_batch_images, desc=f"Batch {batch_idx+1}/{total_batches}"):
            img_path = data_dir / "images" / img_name
            try:
                with Image.open(img_path) as img:
                    img = img.convert("RGB")
                    img = img.resize((args.image_size, args.image_size), Image.LANCZOS)
                    batch_array.append(np.array(img, dtype=np.uint8))
            except Exception as e:
                corrupted.append(img_name)
                # Append a black placeholder to maintain indexing
                batch_array.append(np.zeros((args.image_size, args.image_size, 3), dtype=np.uint8))
                
        np.save(batch_file, np.array(batch_array, dtype=np.uint8))
        processed_count += len(batch_array)

    if corrupted:
        with open(out_dir / "corrupted.txt", "w") as f:
            for c in corrupted:
                f.write(f"{c}\n")

    # Step 3: Train/Val split
    logger.info("Splitting train/val sets...")
    random.seed(42)
    valid_images = [img for img in sampled_images if img not in corrupted]
    random.shuffle(valid_images)
    
    split_idx = int(len(valid_images) * 0.9)
    train_files = valid_images[:split_idx]
    val_files = valid_images[split_idx:]
    
    (out_dir / "train_files.txt").write_text("\n".join(train_files))
    (out_dir / "val_files.txt").write_text("\n".join(val_files))

    # Step 4: Compute Statistics
    logger.info("Computing dataset statistics...")
    sample_size = min(1000, len(train_files))
    sample_arrays = []
    
    # Load sample from batch 0
    if (batch_dir / "batch_000.npy").exists():
        sample_batch = np.load(batch_dir / "batch_000.npy")
        pixels = sample_batch[:sample_size].astype(np.float32) / 255.0
        mean = pixels.mean(axis=(0, 1, 2)).tolist()
        std = pixels.std(axis=(0, 1, 2)).tolist()
    else:
        mean, std = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225] # Fallback

    stats = {
        "mean": mean,
        "std": std,
        "total_images": len(sampled_images),
        "train_count": len(train_files),
        "val_count": len(val_files),
        "image_size": args.image_size,
        "corrupted_count": len(corrupted)
    }
    (out_dir / "dataset_stats.json").write_text(json.dumps(stats, indent=2))

    # Step 5: Verification Grid
    logger.info("Generating sample grid...")
    fig, axes = plt.subplots(3, 3, figsize=(8, 8))
    sample_batch = np.load(batch_dir / "batch_000.npy")
    for i, ax in enumerate(axes.flat):
        if i < len(sample_batch):
            ax.imshow(sample_batch[i])
        ax.axis("off")
    plt.tight_layout()
    plt.savefig(out_dir / "sample_grid.png")
    
    print(json.dumps(stats, indent=2))
    print("✅ Dataset preparation complete")

if __name__ == "__main__":
    main()
