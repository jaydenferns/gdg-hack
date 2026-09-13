# Guardian AI

Guardian AI is a hackathon-ready, human-in-the-loop digital safety MVP. It looks for escalating **conversation patterns**—not isolated banned words—and recommends review without making accusations or automatic irreversible decisions.

## Run it locally

1. Open a terminal in `backend`.
2. Create and activate a virtual environment: `python -m venv .venv` then `.venv\\Scripts\\activate` (Windows).
3. Install dependencies: `pip install -r requirements.txt`.
4. Start the API: `python -m uvicorn main:app --reload`.
5. Serve the `frontend` directory with a local static server (for example VS Code Live Server), then open `index.html`.

The frontend automatically falls back to its built-in deterministic risk engine if the backend is unavailable, so **Run Demo** is reliable offline.

## API

- `POST /analyze` — analyze the new incoming message in conversational context
- `POST /cases` — persist a human-review case in SQLite
- `GET /cases`, `GET /cases/{case_code}` — retrieve cases
- `PATCH /cases/{case_code}` — update case status

## Architecture

`frontend → FastAPI → ai_provider → risk_engine → SQLite case system`

`backend/ai_provider.py` is intentionally a provider boundary: replace `LocalAIProvider` with a multilingual LLM, classifier, or embedding model later without changing the UI or API contract.

## Safety note

Guardian AI surfaces potential indicators and recommends human review. It does not determine criminality, identity, or intent.
