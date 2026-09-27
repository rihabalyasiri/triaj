# action.py


def decide_action(predicted_topic: str, priority: str) -> dict:
    """Decide the next action based on predicted topic and priority."""
    priority = (priority or "").strip().lower()   # predict_priority returns "high"/"medium"/"low"

    if priority == "high":
        return {"action": "escalate to human supervisor", "escalated": True}
    elif predicted_topic in ["Technical", "Billing"]:
        return {"action": "send to the right team", "escalated": False}
    elif predicted_topic in ["Claim"]:
        return {"action": "create or update a claim", "escalated": False}
    else:
        return {"action": "send a standard FAQ or self-service link", "escalated": False}