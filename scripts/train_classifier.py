
import os
import numpy as np
import pandas as pd
import torch

from datasets import Dataset, DatasetDict
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
    set_seed,
)

from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
)

# ==================================================
# 1. CONFIGURATION
# ==================================================

MODEL_NAME = "distilbert/distilbert-base-uncased"

DATASET_PATH = "data/synthetic_data/classifier_dataset_v3.csv"

OUTPUT_DIR = "models/claims-document-classifier-v3"

MAX_LENGTH = 1024
EPOCHS = int(os.getenv("TRAIN_EPOCHS", "3"))
BATCH_SIZE = 8
LEARNING_RATE = 2e-5

set_seed(42)

# ==================================================
# 2. LABEL MAPPING
# ==================================================

label2id = {
    "admission_advice": 0,
    "discharge_summary": 1,
    "hospital_bill": 2,
    "signed_claim_form": 3,
}

id2label = {
    value: key for key, value in label2id.items()
}

# ==================================================
# 3. LOAD DATASET
# ==================================================

print("\nLoading dataset...")

df = pd.read_csv(DATASET_PATH)

if df[["text", "label", "split"]].isnull().any().any():
    raise ValueError("Dataset contains missing values.")

if not set(df["label"]).issubset(label2id):
    raise ValueError("Dataset contains unknown document labels.")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

datasets = {}

for split in ["train", "validation", "test", "challenge"]:

    split_df = df[df["split"] == split][
        ["text", "label"]
    ].copy()

    split_df["labels"] = split_df["label"].map(label2id)

    datasets[split] = Dataset.from_pandas(
        split_df[["text", "labels"]],
        preserve_index=False,
    )

dataset_dict = DatasetDict(datasets)

print(dataset_dict)

# ==================================================
# 4. TOKENIZATION
# ==================================================

def tokenize_function(examples):
    return tokenizer(
        examples["text"],
        truncation=True,
        max_length=MAX_LENGTH,
    )


print("\nTokenizing dataset...")

tokenized_datasets = dataset_dict.map(
    tokenize_function,
    batched=True,
    remove_columns=["text"],
)

# DistilBERT does not use token_type_ids.
for split in tokenized_datasets:
    if "token_type_ids" in tokenized_datasets[split].column_names:
        tokenized_datasets[split] = (
            tokenized_datasets[split].remove_columns(
                ["token_type_ids"]
            )
        )

# ==================================================
# 5. LOAD CLASSIFICATION MODEL
# ==================================================

print("\nLoading DistilBERT model...")

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=4,
    label2id=label2id,
    id2label=id2label,
)

# ==================================================
# 6. EVALUATION METRICS
# ==================================================

def compute_metrics(eval_pred):

    logits, labels = eval_pred

    predictions = np.argmax(logits, axis=-1)

    precision, recall, f1, _ = (
        precision_recall_fscore_support(
            labels,
            predictions,
            average="macro",
            zero_division=0,
        )
    )

    accuracy = accuracy_score(labels, predictions)

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


# ==================================================
# 7. DYNAMIC PADDING
# ==================================================

data_collator = DataCollatorWithPadding(
    tokenizer=tokenizer
)

# ==================================================
# 8. TRAINING CONFIGURATION
# ==================================================

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,

    num_train_epochs=EPOCHS,

    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,

    learning_rate=LEARNING_RATE,
    weight_decay=0.01,

    eval_strategy="epoch",
    save_strategy="epoch",

    load_best_model_at_end=True,
    metric_for_best_model="f1",
    greater_is_better=True,

    logging_strategy="steps",
    logging_steps=10,

    save_total_limit=2,

    report_to="none",

    seed=42,
    use_cpu=True,
)

# ==================================================
# 9. CREATE TRAINER
# ==================================================

trainer = Trainer(
    model=model,
    args=training_args,

    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["validation"],

    processing_class=tokenizer,
    data_collator=data_collator,

    compute_metrics=compute_metrics,
)

# ==================================================
# 10. FINE-TUNING
# ==================================================

print("\nStarting DistilBERT fine-tuning...")

trainer.train()


# ==================================================
# 11. FINAL TEST AND CHALLENGE EVALUATION
# ==================================================

from sklearn.metrics import classification_report, confusion_matrix

CLASS_NAMES = [
    "admission_advice",
    "discharge_summary",
    "hospital_bill",
    "signed_claim_form",
]

def evaluate_split(split_name):

    print(f"\n{'=' * 55}")
    print(f"EVALUATING: {split_name.upper()}")
    print(f"{'=' * 55}")

    # Get evaluation metrics
    results = trainer.evaluate(
        eval_dataset=tokenized_datasets[split_name],
        metric_key_prefix=split_name,
    )

    for metric, value in results.items():
        print(f"{metric}: {value}")

    # Get individual predictions
    prediction_output = trainer.predict(
        tokenized_datasets[split_name]
    )

    predictions = np.argmax(
        prediction_output.predictions,
        axis=-1
    )

    actual_labels = prediction_output.label_ids

    target_names = [
        id2label[i] for i in range(len(id2label))
    ]

    print("\nCLASSIFICATION REPORT")

    print(classification_report(
        actual_labels,
        predictions,
        labels=list(range(len(CLASS_NAMES))),
        target_names=target_names,
        zero_division=0,
    ))

    print("CONFUSION MATRIX")

    print(confusion_matrix(
        actual_labels,
        predictions,
        labels=list(range(len(CLASS_NAMES))),
    ))


# Standard test: familiar template families
evaluate_split("test")

# Challenge: completely unseen template family
evaluate_split("challenge")

# ==================================================
# 12. SAVE MODEL AND TOKENIZER
# ==================================================

print("\nSaving final model...")

trainer.save_model(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print("\nTraining completed successfully!")
print("Model saved at:", OUTPUT_DIR)
