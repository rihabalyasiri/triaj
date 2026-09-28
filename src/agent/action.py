# action.py


def decide_action(predicted_topic: str, predicted_priority: str, urgency: float) -> dict:
    """Decide the next action based on predicted topic and priority."""
    priority = (predicted_priority or "").strip().lower()   # predict_priority returns "high"/"medium"/"low"
    URGENCY_THRESHOLD = 0.9

    if priority == "high" and urgency > URGENCY_THRESHOLD:
        return {"action": "escalate to human supervisor", "escalated": True}
    elif predicted_topic in ["Billing"]:
        return {"action": "send to the billing team", "escalated": False}
    elif predicted_topic in ["Technical"]:
        return {"action": "send to the technical team", "escalated": False}
    elif predicted_topic in ["Claim"]:
        return {"action": "create or update a claim", "escalated": False}
    else:
        return {"action": "send a standard FAQ or self-service link", "escalated": False}