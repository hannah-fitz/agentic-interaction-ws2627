import json
from datetime import date as Date

import requests

from .config import DATA_BASE_URL


# -----------------------------------------------------
# Tool-Definition
# -----------------------------------------------------

TOOL_NAME = "get_calendar_day"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": TOOL_NAME,
            "description": "Lädt die Kalendertermine für einen bestimmten Tag. Verwende dieses Tool, um Fragen zum Kalender zu beantworten.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Das Datum im Format YYYY-MM-DD.",
                    }
                },
                "required": ["date"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    }
]


# -----------------------------------------------------
# Abrufen der Kalendertermine für einen bestimmten Tag
# -----------------------------------------------------

def get_calendar_day(date: str) -> str:

    # Formatierung
    parsed_date = Date.fromisoformat(date)

    if parsed_date.isoformat() != date:
        raise ValueError("Das Datum muss YYYY-MM-DD entsprechen.")


    # Abrufen der Kalendertermine von der API
    url = f"{DATA_BASE_URL.rstrip('/')}/calendar/{parsed_date}.json"
    response = requests.get(url, timeout=15)


    # Fehlerbehandlung
    if response.status_code == 404:
        return json.dumps(
            {
                "available": False,
                "date": parsed_date.isoformat(),
            },
            ensure_ascii=False,
        )

    response.raise_for_status()


    # Rückgabe der Kalendertermine im JSON-Format
    return json.dumps(
        {
            "available": True,
            "date": parsed_date.isoformat(),
            "calendar": response.json(),
        },
        ensure_ascii=False,
    )
