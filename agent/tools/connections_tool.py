import json
from urllib.parse import quote

import requests

from ..config import DATA_BASE_URL
from ..util import formatDate, normalize_city


# -----------------------------------------------------
# Tool-Definition
# -----------------------------------------------------

CONNECTIONS_TOOL_NAME = "get_connections"

CONNECTIONS_TOOL = {
        "type": "function",
        "function": {
            "name": CONNECTIONS_TOOL_NAME,
            "description": (
                "Lädt Zugverbindungen zwischen einem Abfahrtsort und einem "
                "Zielort für einen bestimmten Tag."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "departure": {
                        "type": "string",
                        "description": "Abfahrtsort, z. B. München oder Ulm.",
                    },
                    "arrival": {
                        "type": "string",
                        "description": "Zielort, z. B. München oder Ulm.",
                    },
                    "date": {
                        "type": "string",
                        "description": "Das Datum im Format YYYY-MM-DD.",
                    },
                },
                "required": ["departure", "arrival", "date"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    }


# -----------------------------------------------------
# Abrufen von Zugverbindungen
# -----------------------------------------------------

def get_connections(departure: str, arrival: str, date: str) -> str:
    parsed_date = formatDate(date)
    
    departure_slug = normalize_city(departure)

    arrival_slug = normalize_city(arrival)

    url = (
        f"{DATA_BASE_URL.rstrip('/')}/transit/"
        f"{quote(departure_slug, safe='')}/{quote(arrival_slug, safe='')}/"
        f"{parsed_date}.json"
    )
    response = requests.get(url, timeout=15)

    if response.status_code == 404:
        return json.dumps(
            {
                "available": False,
                "departure": departure_slug,
                "arrival": arrival_slug,
                "date": parsed_date.isoformat(),
                "connections": [],
            },
            ensure_ascii=False,
        )

    response.raise_for_status()

    return json.dumps(
        {
            "available": True,
            "departure": departure_slug,
            "arrival": arrival_slug,
            "date": parsed_date.isoformat(),
            "connections": response.json(),
        },
        ensure_ascii=False,
    )
