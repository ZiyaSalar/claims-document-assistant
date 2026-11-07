
import pandas as pd

from datasets import Dataset, DatasetDict
from transformers import AutoTokenizer

# Configuration
DATASET_PATH = "data/synthetic_data/classifier_dataset_v3.csv"
MODEL_NAME = "distilbert/distilbert-base-uncased"
MAX_LENGTH = 256

label2id = {
    "admission_advice": 0,
    "discharge_summary": 1,
    "hospital_bill": 2,
    "signed_claim_form": 3,
}

# Load CSV
df = pd.read_csv(DATASET_PATH)

print("Original dataset:", df.shape)

if df[["text", "label", "split"]].isnull().any().any():
    raise ValueError("Dataset contains missing values.")

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

# Prepare all four splits
datasets = {}

for split in ["train", "validation", "test", "challenge"]:
    split_df = df[df["split"] == split][["text", "label"]].copy()

    split_df["labels"] = split_df["label"].map(label2id)

    if split_df["labels"].isna().any():
        raise ValueError(f"Unknown label found in {split}")

    datasets[split] = Dataset.from_pandas(
        split_df[["text", "labels"]],
        preserve_index=False
    )

dataset_dict = DatasetDict(datasets)

# Tokenization
def tokenize_function(examples):
    return tokenizer(
        examples["text"],
        truncation=True,
        max_length=MAX_LENGTH
    )

tokenized_datasets = dataset_dict.map(
    tokenize_function,
    batched=True,
    remove_columns=["text"]
)

print("\nPrepared dataset:")
for split, dataset in tokenized_datasets.items():
    print(f"{split}: {len(dataset)} examples")

print("\nFeatures:")
print(tokenized_datasets["train"].features)

print("\nLabel mapping:")
print(label2id)

print("\nDataset preparation successful!")
