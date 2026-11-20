import json
from pathlib import Path
from time import perf_counter
from typing import Any

from openai import OpenAI

from .tools.calendar_tool import CALENDAR_TOOL_NAME, CALENDAR_TOOL, get_calendar_day
from .tools.weather_tool import WEATHER_TOOL_NAME, WEATHER_TOOL, get_weather_for_city_and_day
from .tools.connections_tool import CONNECTIONS_TOOL_NAME, CONNECTIONS_TOOL, get_connections

from .config import API_KEY, BASE_URL, MODEL, validate_configuration
from .logger import create_run_log, write_log


MAX_TOOL_CALLS = 8
TOOLS = [CALENDAR_TOOL, WEATHER_TOOL, CONNECTIONS_TOOL]


# -----------------------------------------------------
# Antwort vom Model fordern (mit oder ohne Tool)
# -----------------------------------------------------

def request_model_response(
    client: OpenAI,
    messages: list[dict[str, Any]],
) -> tuple[Any, list[Any]]:
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    assistant_message = response.choices[0].message
    return assistant_message, assistant_message.tool_calls or []


# -----------------------------------------------------
# Einzelnen Tool-Aufruf ausführen
# -----------------------------------------------------

def execute_tool_call(tool_call: Any, log_file: Path, run_id: str) -> str:
    # Wird für die Log-Einträge bereitgehalten: 
    tool_name = tool_call.function.name
    step_started = perf_counter()

    # Modell-Argumente aus JSON dekodieren und ihre erwartete Form prüfen.
    try:
        arguments = json.loads(tool_call.function.arguments)
        if not isinstance(arguments, dict):
            raise ValueError("Tool-Argumente müssen ein JSON-Objekt sein.")
    
    # Bei ungültigen Argumenten: Fehler protokollieren und Fehler-Ergebnis zurückgeben
    except (TypeError, ValueError) as exc:
        write_log(
            log_file,
            run_id=run_id,
            event="tool_call",
            ok=False,
            model=MODEL,
            duration_ms=round((perf_counter() - step_started) * 1000, 2),
            tool=tool_name,
            error_type=type(exc).__name__,
            error=str(exc),
        )
        tool_result = json.dumps(
            {"error": {"type": type(exc).__name__, "message": str(exc)}},
            ensure_ascii=False,
        )
        write_log(
            log_file,
            run_id=run_id,
            event="tool_result",
            ok=False,
            model=MODEL,
            duration_ms=0,
            tool=tool_name,
            error_type=type(exc).__name__,
            error=str(exc),
        )
        return tool_result

    # Bei gültigen Argumenten: Tool call protokollieren und ausführen.  
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

    step_started = perf_counter()
    try:

        # Entsprechend des Tool-Namens das passende Tool ausführen
        if tool_name == CALENDAR_TOOL_NAME:
            tool_result = get_calendar_day(**arguments)
        elif tool_name == WEATHER_TOOL_NAME:
            tool_result = get_weather_for_city_and_day(**arguments)
        elif tool_name == CONNECTIONS_TOOL_NAME:
            tool_result = get_connections(**arguments)
        else:
            raise RuntimeError("Unbekanntes Tool angefordert.")

    # Exception beim Tool-Aufruf abfangen
    except Exception as exc:
        tool_result = json.dumps(
            {
                "error": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                }
            },
            ensure_ascii=False,
        )
        write_log(
            log_file,
            run_id=run_id,
            event="tool_result",
            ok=False,
            model=MODEL,
            duration_ms=round((perf_counter() - step_started) * 1000, 2),
            tool=tool_name,
            args=arguments,
            error_type=type(exc).__name__,
            error=str(exc),
        )

    # Erfolgreichen Tool-Aufruf protokollieren
    else:
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

    return tool_result


# -----------------------------------------------------
# Koordination: Model -> Tool -> Model
# -----------------------------------------------------

def run_agent(question: str) -> str:
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
    tool_calls_executed = 0

    try:
        validate_configuration()
        client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

        messages = [
            {
                "role": "system",
                "content": (
                    "Du bist ein hilfreicher Chat- und Kalenderassistent und "
                    "antwortest auf Deutsch. Beantworte normale Gesprächsfragen "
                    "direkt und verwende dafür kein Tool. "
                    "Rufe get_calendar_day nur für Fragen nach Kalenderterminen "
                    "oder dem Kalenderinhalt eines bestimmten Tages auf. "
                    "Rufe get_weather_for_city_and_day für Fragen nach Wetterdaten "
                    "für eine bestimmte Stadt und einen bestimmten Tag auf. "
                    "Rufe die passenden Tools für jeden angefragten Datensatz auf; "
                    "mehrere Tool-Aufrufe in einer Antwort sind erlaubt. "
                    "Übergib das Datum im Format YYYY-MM-DD. "
                    "Für Kalenderdaten beantworte die Frage nur anhand des Felds "
                    "calendar, wenn available=true ist. "
                    "Für Wetterdaten beantworte die Frage nur anhand der "
                    "zurückgegebenen Wetter-Informationen. "
                    "Rufe get_connections für Fragen nach Zugverbindungen auf, "
                    "wenn Abfahrtsort, Zielort und Datum bekannt sind. "
                    "Wenn die Information zum Abfahrtsbahnhof fehlt, gehe davon aus, dass "
                    "jemand von Ulm aus starten möchte. Betrachte Ulm also als den Heimatbahnhof,"
                    "wenn es nötig ist."
                    "Wenn die Reiseart nicht spezifiziert ist, gehe davon aus, dass "
                    "jemand mit dem Zug fahren möchte und nutze das Connections-Tool. "
                    "Wenn ein Tool available=false zurückgibt, behaupte nicht, dass "
                    "die Daten vorhanden sind oder der Tag frei ist. Sage höflich, "
                    "dass die angefragten Daten nicht abgerufen werden konnten. "
                    "Wenn ein Tool-Ergebnis ein error-Feld enthält, behaupte "
                    "keine Daten aus dem Tool-Ergebnis; erkläre den Fehler oder versuche es "
                    "erneut, sofern noch Schritte verfügbar sind. "
                    "Beantworte Fragen zu Kalender, Wetter oder Verbindungen erst "
                    "anhand der zurückgegebenen Tool-Daten und erfinde keine Angaben."
                ),
            },
            {"role": "user", "content": question},
        ]

        # Loop: Solange das Modell Tool-Aufrufe zurückgibt, diese ausführen und die Ergebnisse wieder an das Modell übergeben.
        while True:
            step = "model_response"
            step_started = perf_counter()
            assistant_message, tool_calls = request_model_response(client, messages)

            if not tool_calls:
                answer = assistant_message.content
                if not answer:
                    raise RuntimeError("Das Modell hat keine Antwort geliefert.")

                write_log(
                    log_file,
                    run_id=run_id,
                    event="final",
                    ok=True,
                    model=MODEL,
                    duration_ms=round((perf_counter() - step_started) * 1000, 2),
                )
                return answer

            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                        for tool_call in tool_calls
                    ],
                }
            )

            # Alle Tool-Aufrufe einen nach dem anderen ausführen und hochzählen
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_calls_executed += 1
                tool_result = execute_tool_call(tool_call, log_file, run_id)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result,
                    }
                )

                if tool_calls_executed >= MAX_TOOL_CALLS:
                    step = "step_limit"
                    step_started = perf_counter()
                    raise RuntimeError(
                        f"Das Limit von {MAX_TOOL_CALLS} Tool-Aufrufen wurde erreicht. "
                        "Bitte stelle eine Frage, die weniger Tool-Aufrufe erfordert."
                    )

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
