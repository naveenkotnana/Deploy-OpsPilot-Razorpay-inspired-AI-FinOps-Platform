# Troubleshooting

**`ollama list` shows nothing / health says unavailable**
Run `python scripts/check_ollama.py`. If unreachable, start Ollama and `ollama pull qwen2.5:3b-instruct`. The system still runs fully without it — evidence is collected and a degraded state is returned.

**Out of VRAM on the GTX 1650**
Drop to `qwen2.5:1.5b` (~1 GB), or lower `num_ctx` in `ollama_client.generate`. Close other GPU applications.

**`UNIQUE constraint failed: water_usage.usage_id`**
Fixed — usage is a full-refresh source and the table is cleared before insert. If you see it on an older checkout, delete `opspilot.db` and re-run `setup_all.py`.

**Dashboard: "API unreachable"**
Start the API first (`uvicorn app.api.main:app --reload`). In Docker, `API_BASE_URL` must be `http://api:8000`, not `localhost`.

**401 on every endpoint**
Sign in via `/auth/login`. Tokens expire after `JWT_EXPIRE_MINUTES` (default 120).

**403 as analyst**
Expected. Analysts may investigate but not approve. Use `manager`/`manager123`.

**`GROUP_CONCAT` error on Postgres**
SQLite syntax in `multiple_active_plans`. Replace with `STRING_AGG(plan_id, ',')`.

**Tests fail on a fresh clone**
Run `python scripts/setup_all.py` first — integration tests assert against loaded data.

**Slow first investigation**
First Ollama call loads the model into VRAM. Subsequent calls are much faster.
