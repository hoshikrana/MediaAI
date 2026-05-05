import logging
import numpy as np
from pathlib import Path
from transformers import (
    AutoModelForTokenClassification, AutoTokenizer,
    TrainingArguments, Trainer, DataCollatorForTokenClassification
)
from datasets import load_from_disk
from seqeval.metrics import f1_score, precision_score, recall_score, classification_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

id2label = {
    0: "O", 1: "B-DISEASE", 2: "I-DISEASE",
    3: "B-SYMPTOM", 4: "I-SYMPTOM",
    5: "B-MEDICATION", 6: "I-MEDICATION",
    7: "B-ANATOMY", 8: "I-ANATOMY"
}
label2id = {v: k for k, v in id2label.items()}

def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=2)
    
    true_labels = [[id2label[l] for l in label if l != -100] for label in labels]
    true_predictions = [
        [id2label[p] for p, l in zip(pred, label) if l != -100]
        for pred, label in zip(predictions, labels)
    ]
    
    return {
        "precision": precision_score(true_labels, true_predictions),
        "recall": recall_score(true_labels, true_predictions),
        "f1": f1_score(true_labels, true_predictions),
    }

def main():
    dataset = load_from_disk("data/processed/ner_dataset")
    model_id = "dmis-lab/biobert-base-cased-v1.2"
    
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForTokenClassification.from_pretrained(
        model_id, num_labels=9, id2label=id2label, label2id=label2id
    )
    
    training_args = TrainingArguments(
        output_dir="models/biobert_ner",
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        gradient_accumulation_steps=4,
        fp16=True,
        gradient_checkpointing=True,
        dataloader_num_workers=0,  # Windows fix
        dataloader_pin_memory=False, # Windows fix
        num_train_epochs=10,
        warmup_ratio=0.1,
        learning_rate=2e-5,
        weight_decay=0.01,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        save_total_limit=3,
        logging_steps=50,
        report_to="none",
    )
    
    data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics
    )
    
    # Auto-resume logic
    checkpoint_dir = Path("models/biobert_ner")
    latest_checkpoint = None
    if checkpoint_dir.exists():
        checkpoints = list(checkpoint_dir.glob("checkpoint-*"))
        if checkpoints:
            latest_checkpoint = str(max(checkpoints, key=lambda p: int(p.name.split("-")[1])))
            logger.info(f"📂 Resuming from {latest_checkpoint}")

    trainer.train(resume_from_checkpoint=latest_checkpoint)
    
    logger.info("Evaluating on test set...")
    test_results = trainer.predict(dataset["test"])
    print(classification_report(*Trainer._get_labels_and_preds(test_results.predictions, test_results.label_ids)))
    
    final_dir = "models/biobert_ner_finetuned"
    trainer.save_model(final_dir)
    tokenizer.save_pretrained(final_dir)
    logger.info(f"✅ Model saved to {final_dir}")

if __name__ == "__main__":
    main()
