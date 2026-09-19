"""Detect Ollama and recommend a model sized for 8 GB RAM / GTX 1650 4 GB."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from app.rag import ollama_client
from app.core.config import settings

RECOMMENDATIONS = [
    ("qwen2.5:3b-instruct", "~2.0 GB", "Recommended. Good JSON adherence at 3B."),
    ("llama3.2:3b",         "~2.0 GB", "Solid general alternative."),
    ("phi3:mini",           "~2.3 GB", "Strong reasoning for its size."),
    ("qwen2.5:1.5b",        "~1.0 GB", "Fallback if 4 GB VRAM is tight."),
]

print(f"OLLAMA_BASE_URL = {settings.OLLAMA_BASE_URL}")
print(f"OLLAMA_MODEL    = {settings.OLLAMA_MODEL}")
if not ollama_client.is_available():
    print("\nOllama is NOT reachable.")
    print("  1. Install from https://ollama.com/download")
    print("  2. Start it (it runs as a service on Windows)")
    print("  3. ollama pull qwen2.5:3b-instruct")
    sys.exit(1)

models = ollama_client.list_models()
print(f"\nOllama is up. {len(models)} model(s) installed: {models or 'none'}")
resolved = ollama_client.resolve_model()
if resolved:
    print(f"Resolved model for this run: {resolved}")
else:
    print("\nNo model installed. Recommended for your hardware:")
    for name, size, why in RECOMMENDATIONS:
        print(f"  ollama pull {name:24} {size:9} {why}")
