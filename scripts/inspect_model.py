
from transformers import AutoModelForSequenceClassification

# -----------------------------------
# 1. Model configuration
# -----------------------------------

MODEL_NAME = "distilbert/distilbert-base-uncased"

label2id = {
    "admission_advice": 0,
    "discharge_summary": 1,
    "hospital_bill": 2,
    "signed_claim_form": 3,
}

id2label = {
    value: key for key, value in label2id.items()
}

# -----------------------------------
# 2. Load pretrained model
# -----------------------------------

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=4,
    label2id=label2id,
    id2label=id2label,
)

# -----------------------------------
# 3. Inspect model
# -----------------------------------

print("\nModel loaded successfully!")

print("\nModel architecture:")
print(model)

print("\nNumber of output classes:")
print(model.config.num_labels)

print("\nLabel mapping:")
print(model.config.id2label)

print("\nTotal parameters:")
print(sum(p.numel() for p in model.parameters()))

print("\nTrainable parameters:")
print(
    sum(
        p.numel()
        for p in model.parameters()
        if p.requires_grad
    )
)
