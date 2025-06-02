from transformers import pipeline

# No need for token here; model is public
model_id = "distilbert-base-uncased-finetuned-sst-2-english"  # A classification head!

# Set up pipeline
pipe = pipeline("text-classification", model=model_id)

def classify_email(email_text, labels):
    # You need a zero-shot pipeline for arbitrary labels
    nli_pipe = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

    # Predict
    result = nli_pipe(email_text, candidate_labels=labels)
    return result['labels'][0]

# Example usage
labels = ["invoice_request", "payment_dispute", "auto_reply", "other"]
email = " send the invoices"
predicted = classify_email(email, labels)
print("Predicted category:", predicted)
