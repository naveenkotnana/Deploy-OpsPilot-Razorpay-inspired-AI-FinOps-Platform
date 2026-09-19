# Ollama

**All LLM inference is local. No paid LLM API is used anywhere in this project.** There are no API keys and no external LLM endpoints in the codebase.

## Configuration

```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b-instruct
OLLAMA_TIMEOUT=90
EMBEDDING_MODEL=nomic-embed-text
```

## Model recommendation for GTX 1650 4 GB / 8 GB RAM

The application **does not assume a model is installed**. `resolve_model()` queries `/api/tags`, prefers the configured model, falls back to a same-family tag, then to any installed model, then returns `None` and the system degrades cleanly.

Run `python scripts/check_ollama.py`:

| Model | Size | Note |
|---|---|---|
| `qwen2.5:3b-instruct` | ~2.0 GB | **Recommended.** Good JSON adherence at 3B. |
| `llama3.2:3b` | ~2.0 GB | Solid alternative. |
| `phi3:mini` | ~2.3 GB | Strong reasoning for its size. |
| `qwen2.5:1.5b` | ~1.0 GB | Fallback if 4 GB VRAM is tight. |

`num_ctx=4096`, `temperature=0.1`, `num_predict=700` — tuned to fit 4 GB VRAM alongside the OS.

## Failure handling

Every failure returns a structured `LLMResult`, never an exception:

| Condition | Result |
|---|---|
| Ollama not running | `OLLAMA_UNAVAILABLE_OR_NO_MODEL` |
| Unreachable | `OLLAMA_UNREACHABLE` |
| Timeout | `OLLAMA_TIMEOUT` |
| Malformed JSON | `generate_json` returns `(result, None)` |

The workflow then produces a deterministic fallback recommendation, and the API returns:

```
AI investigation unavailable.
Evidence collected:            YES
Automated recommendation:      NO
Manual investigation required: YES
```

**The API never crashes because of an LLM outage.** Verified by `FA-02` and `FA-03`.

## Token metrics

When Ollama reports `eval_count`, it is recorded as `eval_tokens` — a **measured** value. No cost metric is reported, because local inference has no API cost and inventing one would be dishonest.

## Status in this build

Ollama was **not available in the environment where this project was built**, so the fallback path was exercised and the generation path was not. The degradation behaviour is tested; narrative quality is not yet measured. Run `scripts/run_agent_eval.py` locally with Ollama running to measure it.
