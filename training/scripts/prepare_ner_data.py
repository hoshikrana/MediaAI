import json
import logging
from pathlib import Path
from datasets import load_dataset
from transformers import AutoTokenizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYMPTOMS_LIST = [
    "fever", "cough", "pain", "fatigue", "nausea", "vomiting",
    "headache", "dizziness", "shortness of breath", "chest pain",
    "dyspnea", "tachycardia", "edema", "rash"
]

def add_symptom_labels(example):
    tokens = example["tokens"]
    tags = example["ner_tags"]
    
    for i, token in enumerate(tokens):
        if tags[i] == 0:  # If currently 'O'
            if token.lower() in SYMPTOMS_LIST:
                # 3 is B-SYMPTOM, 4 is I-SYMPTOM in our mapping
                tags[i] = 3 
    return {"tokens": tokens, "ner_tags": tags}

def tokenize_and_align_labels(examples, tokenizer):
    tokenized = tokenizer(
        examples["tokens"],
        truncation=True,
        max_length=512,
        is_split_into_words=True,  # CRITICAL: Tells tokenizer input is already word-split
        padding=False
    )
    
    all_labels = []
    for i, labels in enumerate(examples["ner_tags"]):
        word_ids = tokenized.word_ids(batch_index=i)
        aligned = []
        prev_word_id = None
        
        for word_id in word_ids:
            if word_id is None:
                aligned.append(-100)  # Special tokens (CLS, SEP) ignored in loss
            elif word_id != prev_word_id:
                aligned.append(labels[word_id])  # First subword gets the actual label
            else:
                label = labels[word_id]
                # If B- label (odd numbers in NCBI), convert to I- label (even) for subwords
                if label % 2 == 1:
                    label += 1
                aligned.append(label)
            prev_word_id = word_id
            
        all_labels.append(aligned)
        
    tokenized["labels"] = all_labels
    return tokenized

def main():
    out_dir = Path("data/processed/ner_dataset")
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("Loading NCBI Disease dataset...")
    dataset = load_dataset("ncbi_disease")
    
    logger.info("Augmenting symptom labels...")
    dataset = dataset.map(add_symptom_labels)
    
    logger.info("Tokenizing and aligning BIO tags...")
    tokenizer = AutoTokenizer.from_pretrained("dmis-lab/biobert-base-cased-v1.2")
    
    tokenized_dataset = dataset.map(
        lambda x: tokenize_and_align_labels(x, tokenizer),
        batched=True,
        remove_columns=dataset["train"].column_names
    )
    
    tokenized_dataset.save_to_disk(str(out_dir))
    logger.info(f"✅ NER dataset prepared and saved to {out_dir}")

if __name__ == "__main__":
    main()
