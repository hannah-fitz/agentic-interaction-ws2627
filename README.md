# Agentic Interaction WS 2627

A Python agent that answers questions about a mock calendar using an OpenAI-compatible language model and a calendar tool.

## Requirements

- Python 3.11 or newer
- An API key for the configured model provider

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

The agent asks the model to call the calendar tool, retrieves the calendar data for the requested day, and sends the tool result back
to the model to generate an answer.

The answer is printed to standard output.

## Logging

Each agent run creates a JSONL log file in the `logs/` directory.

Log files are excluded from version control.

## Project Structure

```text
agentic-interaction-ws2627/
├── agent/
│   ├── __init__.py
│   └── __main__.py
├── logs/
├── .env
├── .gitignore
├── README.md
└── requirements.txt
```