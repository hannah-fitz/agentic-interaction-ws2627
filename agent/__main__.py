import sys
import os
import uuid
import json
import requests

from time import perf_counter
from dotenv import load_dotenv
from openai import OpenAI
from datetime import date as Date
from pathlib import Path
from typing import Any

from .logger import create_run_log, write_log


# --------------------------------------------------
# Konfiguration
# --------------------------------------------------

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BASE_URL = os.getenv("OPENAI_BASE_URL")
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL")
DATA_BASE_URL = os.getenv("DATA_BASE_URL")


# Definition des Kalender-Tools, um dem Modell mitzuteilen, wie es auf Kalenderfragen reagieren soll.  

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



# --------------------------------------------------
# Kalender-Tool-Funktion
# --------------------------------------------------

def get_calendar_day(date: str) -> str:
    parsed_date = Date.fromisoformat(date)

    if parsed_date.isoformat() != date:
        raise ValueError("Das Datum muss YYYY-MM-DD entsprechen.") 

    url = f"{DATA_BASE_URL.rstrip('/')}/calendar/{parsed_date}.json"

    response = requests.get(url, timeout=15)

    # Wenn für dieses Datum keine Kalenderdaten vorhanden sind, geben wir eine strukturierte Antwort zurück, die das LLM für eine Antwort verwenden kann.
    if response.status_code == 404:
        return json.dumps(
            {
                "available": False,
                "date": parsed_date.isoformat(),
            },
            ensure_ascii=False,
        )

    response.raise_for_status()

    calendar_data = response.json()
    return json.dumps(
        {
            "available": True,
            "date": parsed_date.isoformat(),
            "calendar": calendar_data,
        },
        ensure_ascii=False,
    )



# --------------------------------------------------
# Konfig auf Vollständigkeit für run_agent() prüfen
# --------------------------------------------------

def validate_configuration() -> None:
    configuration = {
        "OPENAI_BASE_URL": BASE_URL,
        "OPENAI_API_KEY": API_KEY,
        "MODEL": MODEL,
        "DATA_BASE_URL": DATA_BASE_URL,
    }

    missing = [name for name, value in configuration.items() if not value]

    if missing:
        raise RuntimeError("Fehlende Konfiguration: " + ", ".join(missing))


# --------------------------------------------------
# 1. Modellaufruf aus run_agent(): Modell -> Tool
# --------------------------------------------------

def request_calendar_tool(client: OpenAI, messages: list[dict[str, Any]],) -> tuple[Any, Any]:
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice="required",
    )

    assistant_message = response.choices[0].message

    if not assistant_message.tool_calls:
        raise RuntimeError("Das Modell hat keinen Tool-Aufruf geliefert.")

    if len(assistant_message.tool_calls) != 1:
        raise RuntimeError("Erwartet wurde genau ein Tool-Aufruf.")

    tool_call = assistant_message.tool_calls[0]

    if tool_call.function.name != TOOL_NAME:
        raise RuntimeError("Unbekanntes Tool angefordert.")

    return assistant_message, tool_call



# --------------------------------------------------
# 2. Modellaufruf aus run_agent(): Modell -> Antwort
# --------------------------------------------------

def request_final_answer(client: OpenAI, messages: list[dict[str, Any]],) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )

    answer = response.choices[0].message.content

    if not answer:
        raise RuntimeError("Das Modell hat keine Antwort geliefert.")

    return answer



# --------------------------------------------------
# Agent: Modell -> Tool -> Modell
# --------------------------------------------------

def run_agent(question: str) -> str:

    # Logging 
    run_id, log_file = create_run_log() 
    write_log(
        log_file,
        run_id=run_id,
        event="user_task",
        ok=True,
        model=MODEL,
        duration_ms=0,
        question=question,
    )
    step = "configuration"
    step_started = perf_counter()
    tool_name = None
    arguments = None


    try:
        validate_configuration()

        # OpenAI-Client initialisieren
        client = OpenAI(
            base_url=BASE_URL,
            api_key=API_KEY,
        )

        messages = [
            {
                "role": "system",
                "content": ("Du bist ein Kalenderassistent und antwortest auf Deutsch. "
                            "Rufe für Kalenderfragen immer das Tool get_calendar_day auf. "
                            "Übergib das Datum im Format YYYY-MM-DD. "
                            "Wenn available=true ist, beantworte die Frage nur anhand "
                            "des Felds calendar. "
                            "Wenn das Tool available=false zurückgibt, sage höflich, dass "
                            "für dieses Datum keine Kalenderdaten abgerufen werden konnten. "
                            "Behaupte nicht, dass der Tag terminfrei ist. "
                            "Beantworte die Frage erst nach Erhalt der Kalenderdaten "
                            "und erfinde keine Termine."),
            },
            {
                "role": "user",
                "content": question,

            }
        ]

        # Logging
        step = "tool_call"
        step_started = perf_counter()

        assistant_message, tool_call = request_calendar_tool(client, messages)

        # Logging
        arguments = json.loads(tool_call.function.arguments)
        tool_name = tool_call.function.name
        write_log(
            log_file,
            run_id=run_id,
            event="tool_call",
            ok=True,
            model=MODEL,
            duration_ms=round((perf_counter() - step_started) * 1000, 2),
            tool=tool_name,
            args=arguments,
        )

        step = "tool_result"
        step_started = perf_counter()
        tool_result = get_calendar_day(**arguments)

        write_log(
            log_file,
            run_id=run_id,
            event="tool_result",
            ok=True,
            model=MODEL,
            duration_ms=round((perf_counter() - step_started) * 1000, 2),
            tool=tool_name,
            args=arguments,
        )

        # Das Modell muss im Gesprächsverlauf sehen, welchen Tool-Aufruf es angefordert hat. Die message hält fest: „Ich möchte get_calendar_day mit diesen Argumenten aufrufen.“ 
        messages.append(
            {
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [
                    {
                        "id": tool_call.id, # identifiziert den Tool-Aufruf eindeutig, damit das Modell später die Antwort des Tools zuordnen kann.
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                ],
            }
        )

        # Das Modell muss im Gesprächsverlauf sehen, welches Ergebnis das Tool zurückgegeben hat.
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id, # Die tool_call_id verknüpft die Antwort des Tools mit genau dieser Anforderung. 
                "content": tool_result,
            }
        )

        # Logging
        step = "final"
        step_started = perf_counter()

        # Der zweite Modellaufruf bekommt den Verlauf samt Kalenderdaten und formuliert daraus die Antwort.
        answer = request_final_answer(client, messages)

        write_log(
            log_file,
            run_id=run_id,
            event="final",
            ok=True,
            model=MODEL,
            duration_ms=round((perf_counter() - step_started) * 1000, 2),
            tool=tool_name,
            args=arguments,
        )

        return answer

    except Exception as exc:
        write_log(
            log_file,
            run_id=run_id,
            event="error",
            ok=False,
            model=MODEL,
            duration_ms=round((perf_counter() - step_started) * 1000, 2),
            tool=tool_name,
            args=arguments,
            step=step,
            error_type=type(exc).__name__,
            error=str(exc),
        )
        raise



# --------------------------------------------------
# Programmeinstieg
# --------------------------------------------------
#
# Gibt einen Statuscode zurück: 
# 0 = Erfolg
# 1 = Fehler bei der Ausführung (exception)
# 2 = Kalenderfrage fehlt

def main() -> int:

    # Prüfe, ob das Skript ohne Argumente aufgerufen wurde
    if len(sys.argv) < 2:         # sys.argv enthält die beim Start übergebenen Wörter
        print('Fehler: Kalenderfrage fehlt. Rufe das Programm ' \
        'z. B. folgendermaßen auf: python main.py "Was steht heute im Kalender?"', 
        file=sys.stderr)
        return 2

    # Verarbeite die Kalenderfrage
    question = " ".join(sys.argv[1:])        # Die Wörter werden verbunden, damit auch eine Frage mit Leerzeichen als ein Text ankommt
    
    try:
        answer = run_agent(question)
        print(answer)
        return 0
    
    except Exception as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return 1




if __name__ == "__main__":
    # SystemExit beendet das Programm mit dem angegebenen Statuscode aus main
    raise SystemExit(main())