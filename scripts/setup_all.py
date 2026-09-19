"""One-command bootstrap: ingest -> revenue -> anomalies -> users -> evals.
Run this first. Idempotent; safe to re-run."""
import sys, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.db.base import SessionLocal, init_db
from app.core.security import seed_demo_users
from app.services.ingestion import ingest_all
from app.services.revenue import compute_month
from app.ml.anomaly import detect
from app.rag.store import get_store
from app.rag import ollama_client

MONTHS = ["2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09"]


def main():
    t0 = time.time()
    print("=" * 64); print("OpsPilot setup — synthetic data, local inference"); print("=" * 64)

    print("\n[1/6] Schema")
    init_db(); print("  tables created")

    print("\n[2/6] Ingestion + validation")
    ingest_all()

    db = SessionLocal()
    print("\n[3/6] Revenue calculation")
    for m in MONTHS:
        r = compute_month(db, m)
        print(f"  {m}: {r['apartments']} apartments, "
              f"total={r['total_revenue']:,.2f}, exceptions={r['exceptions']}")

    print("\n[4/6] Anomaly detection + alerts")
    print(" ", detect(db))

    print("\n[5/6] Demo users")
    print(f"  seeded {seed_demo_users(db)} new user(s) "
          f"(analyst/manager/admin — see docs/security.md)")

    print("\n[6/6] RAG index")
    print(" ", get_store().stats())

    models = ollama_client.list_models()
    print("\nOllama:", f"{len(models)} model(s): {models}" if models else
          "NOT DETECTED — run:  ollama pull qwen2.5:3b-instruct")
    db.close()
    print(f"\nDone in {time.time()-t0:.1f}s")
    print("\nNext:")
    print("  uvicorn app.api.main:app --reload          # API  -> localhost:8000/docs")
    print("  streamlit run dashboard/app.py             # UI   -> localhost:8501")
    print("  python scripts/run_rag_eval.py             # measured RAG metrics")
    print("  python scripts/run_agent_eval.py           # measured agent/security metrics")


if __name__ == "__main__":
    main()
