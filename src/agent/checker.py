# checker.py
"""LLM checker: a local Qwen model (via Ollama) reviews the NLI triage result.

It receives the message, predicted topic, predicted priority and escalation decision and returns:
  - whether the ticket is ambiguous (not enough information to act on)
  - if ambiguous: follow-up questions + a ready-to-send reply asking the customer for details
  - its own view on topic, priority and whether to escalate
"""
import json
import os
from typing import Literal

from ollama import Client
from pydantic import BaseModel, Field, ValidationError

from agent.triage import TOPIC_DESCRIPTIONS

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")

OLLAMA_THINK = os.getenv("OLLAMA_THINK", "false").lower() 

ALLOWED_TOPICS = [*TOPIC_DESCRIPTIONS.keys(), "Other"]

_client = Client()  # respects OLLAMA_HOST, default http://localhost:11434


class TicketCheck(BaseModel):
    ambiguous: bool = Field(description="True if the ticket lacks information needed to act on it.")
    ambiguity_reason: str = Field(description="Short reason why it is ambiguous. Empty string if not ambiguous.")
    follow_up_questions: list[str] = Field(
        description="1-3 specific questions to ask the customer. Empty list if not ambiguous.")
    customer_reply: str = Field(
        description="Short, polite reply to the customer in the ticket's language asking for the "
                    "missing information. Empty string if not ambiguous.")


_TOPIC_LINES = "\n".join(f"- {label}: {desc}" for label, desc in TOPIC_DESCRIPTIONS.items())

SYSTEM_PROMPT = f"""You are the quality checker of an automated customer-support triage system.
Tickets can be in German or English. An automatic classifier has already assigned a topic,
a priority and an escalation decision. Review them and decide whether the ticket is ambiguous.

Allowed topics:
{_TOPIC_LINES}
- Other: none of the above

A ticket is AMBIGUOUS when support could not act on it without asking the customer first, e.g.:
- it is unclear what the actual problem or request is
- the affected product, system, account, contract or date is missing and needed
- it fits several topics equally well
A ticket is NOT ambiguous just because it is long, formal or polite.

If ambiguous:
- ask 1-3 specific, concrete follow-up questions (no generic "please provide more details")
- write a short, polite customer reply in the SAME language as the ticket that asks exactly these questions
If not ambiguous: leave ambiguity_reason and customer_reply empty and follow_up_questions as an empty list.


Judge the ticket content yourself. Answer only with the JSON object."""


def check_ticket(message: str, predicted_topic: str, priority: str, escalated: bool,
                 retries: int = 1) -> TicketCheck:
    """Ask the LLM to review one triaged ticket. Retries once on invalid output."""
    payload = {
        "message": message,
        "classifier_result": {
            "predicted_topic": predicted_topic,
            "priority": priority,
            "escalated": escalated,
        },
    }
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False, indent=2)},
    ]

    last_error = None
    for _ in range(retries + 1):
        response = _client.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            format=TicketCheck.model_json_schema(),  
            options={"temperature": 0},
            think=OLLAMA_THINK,
        )
        try:
            check = TicketCheck.model_validate_json(response.message.content)
        except ValidationError as e:
            last_error = e
            continue

        return check

    raise RuntimeError(f"LLM returned invalid output after {retries + 1} attempts: {last_error}")


def check_to_row(check: TicketCheck) -> dict:
    """Flatten the check into CSV-friendly columns."""
    return {
        "ambiguous": check.ambiguous,
        "ambiguity_reason": check.ambiguity_reason,
        "follow_up_questions": " | ".join(check.follow_up_questions),
        "customer_reply": check.customer_reply
    }