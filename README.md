# Agentic Interaction WS 2627

A Python agent that answers questions about a mock calendar using an OpenAI-compatible language model and a calendar tool.

## Requirements

- Python 3.11 or newer
- An API key for the configured model provider

## Project Structure

```text
agentic-interaction-ws2627/
├── agent/
│   ├── __init__.py
│   ├── __main__.py
│   ├── calendar_tool.py
│   ├── config.py
│   ├── logger.py
│   └── runner.py
├── logs/
├── .env
├── .gitignore
├── README.md
└── requirements.txt
```

## Setup

Clone the repository and enter the project directory.

Create and activate a virtual environment:

```bash
python -m venv .venv
```

On Windows:

```bash
.venv\Scripts\activate
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```dotenv
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_API_KEY=YOUR_API_KEY
MODEL=openai/gpt-oss-20b
DATA_BASE_URL=https://jhbelz.github.io/agentic-interaction-data/v1
```

Replace `YOUR_API_KEY` with your API key.

Environment variables take precedence over values loaded from `.env`.

Never commit API keys or the `.env` file.

## Usage

Ask a question about a calendar day:

```bash
python -m agent "Was steht am 29.10.2026 im Kalender?"
```

The agent can call a calendar tool, also in a loop if neccassary. It returns each result to the model and repeats until the model provides a final answer. A failed calendar call is reported to the model so it can continue or explain the problem.

The answer is printed to standard output.

Each run is limited to 8 calendar tool calls. Reaching that limit ends the run as an error: the command exits with status `1` and the run log records an `error` event. A successful answer exits with status `0` and is recorded as a `final` event.

## Logging

Each agent run creates a JSONL log file in the `logs/` directory.
The final event identifies whether the run completed successfully or ended with an error.

Log files are excluded from version control.

