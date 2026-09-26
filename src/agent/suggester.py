import json
import re
from enum import Enum
import logging

from pydantic import BaseModel, ValidationError, field_validator
from qwen_agent.agents import Assistant

logging.getLogger("qwen_agent_logger").setLevel(logging.WARNING)

class Category(str, Enum):
    CONTRACT = "Police / Vertrag"
    CLAIM = "Schadenmeldung / Schaden"
    BILLING = "Rechnung / Zahlung"
    TECHNICAL = "Technik / Online-Zugang"
    OTHER = "Andere"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


ROUTING = {
    Category.BILLING: "Forward to billing team",
    Category.TECHNICAL: "Forward to technical support",
    Category.CONTRACT: "Escalate to human supervisor",
    Category.CLAIM: "Create or update a claim",
    Category.OTHER: "Send standard FAQ or self-service link",
}

ESCALATION_KEYWORDS = ["anwalt", "lawyer", "lawsuit", "datenschutz", "data breach",
                       "hacked", "gehackt", "bafin", "ombudsmann"]


def _normalize(s: str) -> str:
    s = re.sub(r"^\s*\d+[.)]\s*", "", s)          # drop "3. " prefixes
    return re.sub(r"\s*/\s*", " / ", s).strip().lower()

_CATEGORY_LOOKUP = {_normalize(c.value): c for c in Category}


class TriageResult(BaseModel):
    predicted_topic: Category
    priority: Priority
    action: str | None = None
    escalated: bool = False

    @field_validator("predicted_topic", mode="before")
    @classmethod
    def match_category(cls, v):
        if isinstance(v, str) and _normalize(v) in _CATEGORY_LOOKUP:
            return _CATEGORY_LOOKUP[_normalize(v)]
        return v  

    @field_validator("priority", mode="before")
    @classmethod
    def lower_priority(cls, v):
        return v.strip().lower() if isinstance(v, str) else v


SYSTEM_PROMPT = """
Du bist ein erfahrener Support-Mitarbeiter für die Triage von Kundentickets. Du erhältst eine Nachricht, die aus einem Betreff und dem Nachrichtentext besteht. Deine Aufgabe ist es, die Nachricht genau einer der folgenden Kategorien zuzuordnen und ihre Priorität zu bestimmen.

Es gibt 5 Kategorien:
1. Police / Vertrag
2. Schadenmeldung / Schaden
3. Rechnung / Zahlung
4. Technik / Online-Zugang
5. Andere

Es gibt 3 Prioritäten:
- high: Kunde ist komplett blockiert, akuter Schaden, Frist läuft ab, rechtliche Drohung oder Datenschutzproblem
- medium: Problem beeinträchtigt den Kunden, ist aber nicht akut
- low: allgemeine Frage, Information oder Feedback

Antworte ausschließlich mit JSON in dieser Form:
{"predicted_topic": "<Kategorie exakt wie oben geschrieben>", "priority": "<low|medium|high>"}

Beispiel:
Betreff: Headset-Probleme
Nachricht: Mein Headset trennt ständig die Verbindung während Meetings, Treiber sind neu installiert.
Antwort: {"predicted_topic": "Technik / Online-Zugang", "priority": "medium"}
"""

llm_cfg = {
    "model": "qwen3.6",
    "model_type": "oai",
    "model_server": "http://localhost:11434/v1",
    "api_key": "EMPTY",
    "generate_cfg": {"temperature": 0.1},
}

bot = Assistant(llm=llm_cfg, system_message=SYSTEM_PROMPT)


def _extract_json(text: str) -> dict:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object in model output")
    return json.loads(text[start : end + 1])


def _ask(messages: list[dict]) -> str:
    responses = []
    for responses in bot.run(messages=messages):
        pass
    content = responses[-1]["content"]
    return content if isinstance(content, str) else str(content)


def triage(message: str, max_retries: int = 2) -> TriageResult:

    messages = [{"role": "user", "content": message}]

    for attempt in range(max_retries + 1):
        raw = _ask(messages)
        try:
            result = TriageResult(**_extract_json(raw))
            break
        except (ValueError, ValidationError) as e:
            if attempt == max_retries:
                raise RuntimeError(f"Invalid model output after retries:\n{raw}") from e
            messages += [
                {"role": "assistant", "content": raw},
                {"role": "user", "content": (
                    f"Ungültige Antwort: {e}. Antworte ausschließlich mit JSON: "
                    '{"predicted_topic": "<Kategorie exakt wie oben>", "priority": "<low|medium|high>"}'
                )},
            ]

    # Deterministic post-processing
    result.action = ROUTING[result.predicted_topic]
    text = f"{message}".lower()
    if any(k in text for k in ESCALATION_KEYWORDS):
        result.priority = Priority.HIGH
        result.escalated = True
    return result