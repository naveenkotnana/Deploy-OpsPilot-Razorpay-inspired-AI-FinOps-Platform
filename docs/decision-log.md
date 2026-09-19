# Decision Log

**SQLite default, Postgres optional.** The project must run on a reviewer's machine in under a minute. SQLAlchemy makes the switch a one-line env change, so defaulting to zero-setup costs nothing and removes the largest barrier to someone actually running it.

**Natural keys as primary keys.** Source identifiers are already anonymised surrogates. An integer surrogate would add a join hop to every query for no benefit.

**TF-IDF over FAISS/Chroma.** 38 chunks. A vector database at this scale is a dependency and a service surface that buys nothing, and on an 8 GB machine every megabyte competes with the model. The retriever interface is narrow enough that swapping is a one-file change. Measured Recall@4 = 1.000 on this corpus.

**Section-level chunking.** Policy documents are numbered-rule documents. Splitting on the numbered heading makes each chunk a self-contained rule, so citations are precise (`§6`) rather than approximate.

**Deterministic planner, not LLM tool selection.** Tool selection is a security boundary. An LLM-driven planner means a prompt-injected document can influence which tools run. The investigation sequence is fixed anyway, so nothing is lost.

**Severity by rule, never by model.** Severity drives escalation policy and must be reproducible across runs. ML-only detections are capped at LOW — an unsupervised score is a prompt to investigate, not grounds to escalate.

**Approval gate as graph structure, not a conditional.** The graph *ends* at `approval_gate`; `action_executor` is a separate graph. A conditional edge could be reached by a bug; a missing edge cannot. `action_executor` also re-reads the DB rather than trusting state.

**Named-query allowlist instead of SQL sanitisation.** Filtering model-generated SQL is a losing game. Not letting the model produce SQL at all is structural.

**Redaction, not just detection, for prompt injection.** Logging an injection attempt while still passing the text to the model defeats the purpose. Matching chunks are replaced before assembly.

**PBKDF2 from stdlib rather than bcrypt/passlib.** One less binary wheel to install on Windows, and 200k iterations of PBKDF2-HMAC-SHA256 is appropriate for a local synthetic environment.

**Ollama on host, not in Docker.** On Windows, containerised Ollama routes through WSL2 and loses direct GPU access. The GTX 1650 is the reason this constraint exists at all, so giving up the GPU to gain container tidiness is backwards.

**No LLM inference in CI.** Slow, nondeterministic, and it would gate merges on model mood. The deterministic behaviour — guardrails, approval, failure paths — is exactly what should be gated. Real-Ollama evaluation is a separate local command.

**Numeric grounding check.** Cheaper and more reliable than asking the model to self-verify. Every number in the output is matched against numbers actually computed; unmatched figures force confidence to LOW.

**Full-refresh for usage, upsert for masters.** `setup_all.py` must be re-runnable. Masters use `merge`; usage is cleared before insert; revenue deletes the month before recomputing.

**Exceptions flagged, never imputed.** An imputed number that looks right is more dangerous than a visible gap. April's six `MISSING_USAGE` rows are a real data gap, surfaced rather than filled.
