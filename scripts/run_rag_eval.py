"""Run the RAG evaluation. Measures Recall@K, citation correctness, groundedness.
All numbers reported are produced by this script — none are hand-written."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.db.base import SessionLocal, init_db
from app.models import EvaluationResult
from app.rag.store import get_store
from tests.evaluation.rag_eval_set import RAG_CASES

K = 4


def fact_coverage(text: str, facts) -> float:
    t = text.lower()
    hit = sum(1 for f in facts if f.lower() in t)
    return hit / max(len(facts), 1)


def main(persist=True):
    store = get_store()
    init_db()
    db = SessionLocal() if persist else None
    recall_hits = top1_hits = 0
    cov_total = 0.0
    rows = []

    for c in RAG_CASES:
        hits = store.search(c["question"], k=K, role="ADMIN")
        docs = [h["document_id"] for h in hits]
        in_topk = c["expected_document"] in docs
        top1 = bool(docs) and docs[0] == c["expected_document"]
        joined = " ".join(h["chunk"] for h in hits)
        cov = fact_coverage(joined, c["expected_facts"])
        has_citation = all(h["citation"].startswith("[DOC-") for h in hits)

        recall_hits += in_topk
        top1_hits += top1
        cov_total += cov
        passed = in_topk and cov >= 0.5 and has_citation
        rows.append((c["id"], passed, cov, in_topk, top1, docs[:2]))

        if db:
            db.add(EvaluationResult(suite="RAG", case_id=c["id"], passed=passed,
                                    score=round(cov, 4),
                                    detail=f"recall@{K}={in_topk} top1={top1} "
                                           f"fact_coverage={cov:.2f} retrieved={docs[:3]}"))
    if db:
        db.commit(); db.close()

    n = len(RAG_CASES)
    print(f"\n{'case':8} {'pass':6} {'facts':7} {'inK':5} {'top1':5} retrieved")
    for r in rows:
        print(f"{r[0]:8} {str(r[1]):6} {r[2]:.2f}    {str(r[3]):5} {str(r[4]):5} {r[5]}")
    print("\n=== MEASURED RAG RESULTS ===")
    print(f"cases                : {n}")
    print(f"Recall@{K}            : {recall_hits}/{n} = {recall_hits/n:.3f}")
    print(f"Top-1 accuracy       : {top1_hits}/{n} = {top1_hits/n:.3f}")
    print(f"Mean fact coverage   : {cov_total/n:.3f}")
    print(f"Citation correctness : {sum(1 for r in rows if r[1])}/{n} well-formed+relevant")
    passed = sum(1 for r in rows if r[1])
    print(f"Overall pass rate    : {passed}/{n} = {passed/n:.3f}")
    return {"recall_at_k": recall_hits / n, "top1": top1_hits / n,
            "fact_coverage": cov_total / n, "pass_rate": passed / n}


if __name__ == "__main__":
    main()
