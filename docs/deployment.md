# Deployment

## Local (recommended for the GTX 1650)

```bash
pip install -r requirements.txt
cp .env.example .env          # set JWT_SECRET
python scripts/setup_all.py
uvicorn app.api.main:app --reload
streamlit run dashboard/app.py
```

Defaults to SQLite. No Postgres or Docker required.

## Windows setup

1. **Python 3.11+** from python.org (tick "Add to PATH").
2. **Ollama** from https://ollama.com/download — installs as a background service.
3. `ollama pull qwen2.5:3b-instruct`
4. `python scripts/check_ollama.py` to confirm detection.
5. `pip install -r requirements.txt`
6. `copy .env.example .env`, edit `JWT_SECRET`.
7. `python scripts/setup_all.py`

## Docker

```bash
docker compose up --build
```

Brings up `postgres`, `api`, `dashboard`, `worker`. API on :8000, dashboard on :8501.

**Ollama stays on the host.** On Windows, containerised Ollama routes through WSL2 and loses direct GPU access, forcing CPU inference on a machine that has a usable GPU. Containers reach it via `host.docker.internal:11434`.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | SQLite file | Postgres connection when set |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local Ollama |
| `OLLAMA_MODEL` | `qwen2.5:3b-instruct` | Preferred model |
| `OLLAMA_TIMEOUT` | 90 | Seconds |
| `EMBEDDING_MODE` | `tfidf` | or `ollama` for dense |
| `JWT_SECRET` | dev default | **Change this** |
| `SQL_ROW_LIMIT` | 200 | Agent query cap |
| `API_BASE_URL` | `http://localhost:8000` | Dashboard → API |

## Database initialisation

`init_db()` runs `create_all` at API startup and in `setup_all.py`. Alembic is in requirements for future migration history but no migrations are authored yet — stated plainly rather than implied.

## CI

`.github/workflows/ci.yml`: lint (ruff), type check (mypy), bootstrap, unit tests, integration tests, RAG eval, agent/security eval, Docker build for both images. **No LLM inference runs in CI** — the gated assertions are deterministic. Real-Ollama evaluation is a separate local command.
