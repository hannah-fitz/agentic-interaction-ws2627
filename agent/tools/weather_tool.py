import json
from datetime import date as Date
from urllib.parse import quote

import requests

from agent.util import formatDate, normalize_city

from ..config import DATA_BASE_URL




# -----------------------------------------------------
# Tool-Definition
# -----------------------------------------------------

WEATHER_TOOL_NAME = "get_weather_for_city_and_day"

WEATHER_TOOL = {
        "type": "function",
        "function": {
            "name": WEATHER_TOOL_NAME,
            "description": "Lädt das Wetter in einer bestimmten Stadt für einen bestimmten Tag. Verwende dieses Tool, um Fragen zum Wetter in einer Stadt wie München oder Ulm zu beantworten.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": (
                            "Stadtname, z. B. München, Munich oder Ulm; "
                            "Schreibvarianten werden abgeglichen."
                        ),
                    },
                    "date": {
                        "type": "string",
                        "description": "Das Datum im Format YYYY-MM-DD.",
                    }                    
                },
                "required": ["city", "date"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    }



# ---------------------------------------------------------------------------------
# Abrufen der Wetter-Information für einen bestimmten Tag für eine bestimmte Stadt
# ---------------------------------------------------------------------------------
def get_weather_for_city_and_day(city: str, date: str) -> str:

    parsed_date = formatDate(date)

    api_city = normalize_city(city)

    # Abrufen der Wetter-Information von der API
    url = (
        f"{DATA_BASE_URL.rstrip('/')}/weather/"
        f"{quote(api_city, safe='')}/{parsed_date}.json"
    )
    response = requests.get(url, timeout=15)

    # Fehlerbehandlung
    if response.status_code == 404:
        return json.dumps(
            {
                "available": False,
                "city": api_city,
                "date": parsed_date.isoformat(),
            },
            ensure_ascii=False,
        )

    elif response.status_code != 200:
        raise RuntimeError(
            f"Fehler beim Abrufen der Wetter-Information: {response.status_code} - {response.text}"
        )

    # Rückgabe der Wetter-Information
    return response.text
