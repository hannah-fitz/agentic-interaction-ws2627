import sys

from .runner import run_agent


# -----------------------------------------------------
# Einstiegspunkt für die Kommandozeilenanwendung
# -----------------------------------------------------

def main() -> int:
    if len(sys.argv) < 2:
        print(
            'Fehler: Kalenderfrage fehlt. Beispiel: '
            'python -m agent "Was steht heute im Kalender?"',
            file=sys.stderr,
        )
        return 2

    question = " ".join(sys.argv[1:])

    try:
        answer = run_agent(question)
        print(answer)
        return 0
    except Exception as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
