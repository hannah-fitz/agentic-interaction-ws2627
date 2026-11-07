from pathlib import Path
import uuid
from datetime import datetime, timezone
from typing import Any
import json

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


def create_run_log() -> tuple[str, Path]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)   # Verzeichnis für Logs erstellen, falls es noch nicht existiert
    run_id = str(uuid.uuid4())   # Eindeutige ID für diesen Lauf generieren
    return run_id, LOG_DIR / f"run_{run_id}.jsonl"   # Log-Datei für diesen Lauf erstellen



# --------------------------------------------------
# Logging-Funktion
# --------------------------------------------------

def write_log(
    log_file: Path,
    *,
    run_id: str,
    event: str,
    ok: bool,
    model: str | None,
    duration_ms: float,
    tool: str | None = None,
    args: dict[str, Any] | None = None,
    **details: Any,
) -> None:
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "event": event,
        "tool": tool,
        "args": args,
        "ok": ok,
        "model": model,
        "duration_ms": duration_ms,
        **details,
    }

    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
