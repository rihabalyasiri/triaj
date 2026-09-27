# triage.py
# Zero-shot NLI ticket triage with an open-source Hugging Face model:
#   classify_ticket()   -> topic of the ticket
#   predict_priority()  -> priority based on urgency (NLI), topic and keywords

from transformers import pipeline

MODEL_NAME = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
classifier = pipeline("zero-shot-classification", model=MODEL_NAME)


# ---------------------------------------------------------------------------
# Topic classification
# ---------------------------------------------------------------------------

TOPIC_DESCRIPTIONS = {
    "Contract": "a contract, policy, cancellation or change of contract details",
    "Claim": "an insurance claim, a damage or an accident",
    "Billing": "an invoice, a payment, a premium or a refund",
    "Technical": "a technical problem with the website, app, login or account",
}
TOPIC_HYPOTHESIS = "This ticket is about {}."

# "Other" is not a candidate label (NLI handles vague hypotheses like
# "something else" badly). Instead, a ticket is "Other" when no topic is
# confident enough.
OTHER_THRESHOLD = 0.40

_LABEL_BY_DESCRIPTION = {desc: label for label, desc in TOPIC_DESCRIPTIONS.items()}


def classify_ticket(message: str) -> dict:
    """Return {"message", "predicted_topic", "confidence"} for one ticket."""
    if not message or not str(message).strip():
        return {"message": message, "predicted_topic": "Other", "confidence": 0.0}

    output = classifier(
        message,
        list(TOPIC_DESCRIPTIONS.values()),
        hypothesis_template=TOPIC_HYPOTHESIS,
        multi_label=False, 
    )

    top_description = output["labels"][0]
    top_score = float(output["scores"][0])
    predicted_topic = (
        _LABEL_BY_DESCRIPTION[top_description] if top_score >= OTHER_THRESHOLD else "Other"
    )

    return {
        "message": message,
        "predicted_topic": predicted_topic,
        "confidence": round(top_score, 4),
    }


# ---------------------------------------------------------------------------
# Priority
# ---------------------------------------------------------------------------

TOPIC_BASE_PRIORITY = {
    "Claim": 0.7,
    "Billing": 0.5,
    "Technical": 0.5,
    "Contract": 0.4,
    "Other": 0.2,
}

URGENT_KEYWORDS = (
    "urgent", "asap", "immediately", "emergency", "deadline",
    "dringend", "sofort", "eilig", "notfall", "frist", "unfall",
)

URGENCY_WEIGHT = 0.6
TOPIC_WEIGHT = 0.4
KEYWORD_BOOST = 0.2

PRIORITY_THRESHOLDS = (("high", 0.65), ("medium", 0.40))


def predict_priority(message: str, predicted_topic: str) -> dict:
    """Return {"priority", "priority_score", "urgency"} for one ticket.

    score = 0.6 * NLI urgency + 0.4 * topic base priority (+0.2 on urgent keywords)
    """
    if not message or not str(message).strip():
        return {"priority": "low", "priority_score": 0.0, "urgency": 0.0}

    output = classifier(
        message,
        ["urgent", "not urgent"],
        hypothesis_template="This request is {}.",
        multi_label=False,
    )
    urgency = float(dict(zip(output["labels"], output["scores"]))["urgent"])

    base = TOPIC_BASE_PRIORITY.get(predicted_topic, TOPIC_BASE_PRIORITY["Other"])
    keyword_hit = any(k in message.lower() for k in URGENT_KEYWORDS)

    score = URGENCY_WEIGHT * urgency + TOPIC_WEIGHT * base
    if keyword_hit:
        score += KEYWORD_BOOST
    score = min(score, 1.0)

    priority = "low"
    for level, threshold in PRIORITY_THRESHOLDS:
        if score >= threshold:
            priority = level
            break

    return {
        "priority": priority,
        "priority_score": round(score, 4),
        "urgency": round(urgency, 4),
    }
