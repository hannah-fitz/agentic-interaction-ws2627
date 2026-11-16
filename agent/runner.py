import json
from pathlib import Path
from time import perf_counter
from typing import Any

from openai import OpenAI

from .calendar_tool import TOOL_NAME, TOOLS, get_calendar_day
from .config import API_KEY, BASE_URL, MODEL, validate_configuration
from .logger import create_run_log, write_log


MAX_TOOL_CALLS = 8


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

        # Fehler bei Aufruf eines unbekannten Tools abfangen
        if tool_name != TOOL_NAME:
            raise RuntimeError("Unbekanntes Tool angefordert.")

        # Tool-Aufruf ausführen
        tool_result = get_calendar_day(**arguments)

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
                    "Rufe das Tool für jeden angefragten Tag auf; mehrere "
                    "Tool-Aufrufe in einer Antwort sind erlaubt. "
                    "Übergib das Datum im Format YYYY-MM-DD. "
                    "Wenn available=true ist, beantworte die Frage nur anhand "
                    "des Felds calendar. "
                    "Wenn das Tool available=false zurückgibt, sage höflich, dass "
                    "für dieses Datum keine Kalenderdaten abgerufen werden konnten. "
                    "Behaupte nicht, dass der Tag terminfrei ist. "
                    "Wenn ein Tool-Ergebnis ein error-Feld enthält, behaupte "
                    "keine Kalenderdaten; erkläre den Fehler oder versuche es "
                    "erneut, sofern noch Schritte verfügbar sind. "
                    "Beantworte die Frage erst nach Erhalt der Kalenderdaten "
                    "und erfinde keine Termine."
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
