import os
from pathlib import Path

from dotenv import load_dotenv


# -----------------------------------------------------
# Konfiguration laden
# -----------------------------------------------------

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BASE_URL = os.getenv("OPENAI_BASE_URL")
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL")
DATA_BASE_URL = os.getenv("DATA_BASE_URL")



# -----------------------------------------------------
# Geladene Konfiguration validieren
# -----------------------------------------------------

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
