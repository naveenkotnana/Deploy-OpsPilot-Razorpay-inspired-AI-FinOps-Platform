"""Local Ollama client. The ONLY LLM path in this project.

Every failure mode degrades to a structured unavailable-state instead of an
exception, because an LLM outage must never take down the API.
"""
import json, time
from dataclasses import dataclass
from typing import Optional, List
import urllib.request, urllib.error

from app.core.config import settings


@dataclass
class LLMResult:
    ok: bool
    text: str = ""
    model: str = ""
    latency_ms: int = 0
    error: Optional[str] = None
    eval_count: Optional[int] = None       # real token count if Ollama reports it


def _post(path: str, payload: dict, timeout: int):
    req = urllib.request.Request(
        f"{settings.OLLAMA_BASE_URL}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def is_available(timeout: int = 3) -> bool:
    try:
        urllib.request.urlopen(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=timeout)
        return True
    except Exception:
        return False


def list_models(timeout: int = 5) -> List[str]:
    try:
        with urllib.request.urlopen(f"{settings.OLLAMA_BASE_URL}/api/tags",
                                    timeout=timeout) as r:
            data = json.loads(r.read().decode())
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


RECOMMENDED = "qwen2.5:3b-instruct"   # ~2 GB, fits GTX 1650 4 GB comfortably


def resolve_model() -> Optional[str]:
    """Never assume a model is installed. Prefer configured, else first small one."""
    models = list_models()
    if not models:
        return None
    if settings.OLLAMA_MODEL in models:
        return settings.OLLAMA_MODEL
    base = settings.OLLAMA_MODEL.split(":")[0]
    for m in models:
        if m.split(":")[0] == base:
            return m
    return models[0]


def generate(prompt: str, system: str = "", temperature: float = 0.1,
             timeout: int = None) -> LLMResult:
    timeout = timeout or settings.OLLAMA_TIMEOUT
    model = resolve_model()
    if model is None:
        return LLMResult(ok=False, error="OLLAMA_UNAVAILABLE_OR_NO_MODEL")
    t0 = time.time()
    try:
        data = _post("/api/generate", {
            "model": model, "prompt": prompt, "system": system, "stream": False,
            "options": {"temperature": temperature, "num_predict": 700,
                        "num_ctx": 4096}}, timeout)
        return LLMResult(ok=True, text=data.get("response", "").strip(), model=model,
                         latency_ms=int((time.time() - t0) * 1000),
                         eval_count=data.get("eval_count"))
    except urllib.error.URLError as e:
        return LLMResult(ok=False, error=f"OLLAMA_UNREACHABLE: {e}",
                         latency_ms=int((time.time() - t0) * 1000))
    except TimeoutError:
        return LLMResult(ok=False, error="OLLAMA_TIMEOUT",
                         latency_ms=int((time.time() - t0) * 1000))
    except Exception as e:
        return LLMResult(ok=False, error=f"OLLAMA_ERROR: {type(e).__name__}: {e}",
                         latency_ms=int((time.time() - t0) * 1000))


def generate_json(prompt: str, system: str = "", timeout: int = None) -> tuple:
    """Returns (LLMResult, parsed_dict_or_None). Malformed JSON is a handled
    failure path, not a crash."""
    res = generate(prompt, system, timeout=timeout)
    if not res.ok:
        return res, None
    txt = res.text.strip()
    txt = txt.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    start, end = txt.find("{"), txt.rfind("}")
    if start == -1 or end == -1:
        return res, None
    try:
        return res, json.loads(txt[start:end + 1])
    except json.JSONDecodeError:
        return res, None
