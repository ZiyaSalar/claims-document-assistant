import torch
import pandas as pd

from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics import confusion_matrix, classification_report

MODEL_DIR = "models/claims-document-classifier"
DATA_PATH = "data/hf_dataset/classifier_dataset_v2.csv"

CLASS_NAMES = [
    "admission_advice",
    "discharge_summary",
    "hospital_bill",
    "signed_claim_form"
]

# Load test data
df = pd.read_csv(DATA_PATH)
test_df = df[df["split"] == "test"].copy()

# Load trained model and tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)

model.eval()

predictions = []

# Predict in batches
for i in range(0, len(test_df), 8):
    texts = test_df["text"].iloc[i:i+8].tolist()

    inputs = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=256,
        return_tensors="pt"
    )

    with torch.no_grad():
        outputs = model(**inputs)

    predicted_ids = torch.argmax(outputs.logits, dim=1)
    predictions.extend(predicted_ids.tolist())

# Convert numeric predictions into class names
id2label = model.config.id2label

y_true = test_df["label"].tolist()
y_pred = [id2label[p] for p in predictions]

# Classification report
print("\nCLASSIFICATION REPORT")
print(classification_report(
    y_true,
    y_pred,
    labels=CLASS_NAMES,
    target_names=CLASS_NAMES,
    zero_division=0
))

# Confusion matrix
cm = confusion_matrix(y_true, y_pred, labels=CLASS_NAMES)

print("\nCONFUSION MATRIX")
print(pd.DataFrame(
    cm,
    index=CLASS_NAMES,
    columns=CLASS_NAMES
))

# Show incorrect predictions
test_df["predicted_label"] = y_pred

errors = test_df[test_df["label"] != test_df["predicted_label"]]

print("\nMISCLASSIFIED DOCUMENTS")
for _, row in errors.iterrows():
    print("\nActual:    ", row["label"])
    print("Predicted: ", row["predicted_label"])
    print("Text:      ", row["text"][:250])