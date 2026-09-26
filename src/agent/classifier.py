# triage.py
from openai import OpenAI
import uuid
import json

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama") 

ticket_id = uuid.uuid4()

CATEGORIES = [
    "Police / Vertrag",
    "Schadenmeldung / Schaden",
    "Rechnung / Zahlung",
    "Technik / Online-Zugang",
    "Andere",
]

SYSTEM_PROMPT = """
Du bist ein erfahrener Support-Mitarbeiter für die Triage von Kundentickets. Du erhältst eine Nachricht, die aus einem Betreff und dem Nachrichtentext besteht. Deine Aufgabe ist es, die Nachricht einer der folgenden Kategorien zuzuordnen. Jede Nachricht gehört zu genau einer Kategorie, nicht zu mehreren.

Es gibt 5 Kategorien:
1. Police / Vertrag
2. Schadenmeldung / Schaden
3. Rechnung / Zahlung
4. Technik / Online-Zugang
5. Andere

Antworte ausschließlich mit JSON in dieser Form:
{"predicted_topic": "<Kategorie exakt wie oben geschrieben>"}

Beispiel:
Nachricht: Mein Headset trennt ständig die Verbindung während Meetings, Treiber sind neu installiert.
Antwort: {"predicted_topic": "Technik / Online-Zugang"}
"""
def triage(message: str)-> dict:
    resp = client.chat.completions.create(
        model="qwen3.5:4b",
        messages=[
         {"role": "system", "content": SYSTEM_PROMPT},
         {"role": "user", "content": message}],
        response_format={"type": "json_object"},  
        temperature=0, 
    )
    raw = resp.choices[0].message.content
    try:
        topic = json.loads(raw).get("predicted_topic", "Andere")
    except json.JSONDecodeError:
        topic = "Andere"
    if topic not in CATEGORIES:  # guard against hallucinated labels
        topic = "Andere"

    return {
        "ticket_id": str(uuid.uuid4()),
        "ticket_message": message,
        "predicted_topic": topic,
    }

