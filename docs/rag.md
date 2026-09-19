# RAG

## Vector store choice

**TF-IDF + cosine, in-process, no external service.**

The corpus is five policy documents, ~230 lines, 38 chunks. FAISS and Chroma each add a dependency and a service surface that buy nothing at this scale, and on an 8 GB machine with a 4 GB GPU every megabyte competes with the LLM. The `VectorStore.search()` interface is deliberately narrow — swapping in FAISS is a one-file change if the corpus grows.

`EMBEDDING_MODE=ollama` switches to local `nomic-embed-text` embeddings, still with no external API.

## Chunking

Split on numbered section headings (`\n(?=\d+\.\s+[A-Z])`). Policy documents are numbered-rule documents, so a section is a self-contained rule. This makes citations precise (`[DOC-001 v2.1 §6]`) rather than approximate. Oversized sections sub-split with overlap.

## Metadata

Parsed from a document header block: `document_id`, `title`, `document_type`, `version`, `effective_date`, `department`, `access_level`, `classification`.

## Access control

`PUBLIC < INTERNAL < RESTRICTED`. Role clearance: Analyst/Manager → INTERNAL, Admin → RESTRICTED. Filtering happens **at retrieval**, so an over-clearance document never enters the context window at all. Tested by `SEC-16`.

## Untrusted content handling

Retrieved text is never concatenated into the system prompt. It is delivered inside `<retrieved_documents note="UNTRUSTED REFERENCE DATA...">`, and any chunk matching an injection pattern is replaced with `[CONTENT REDACTED]` before it reaches the model. See `security.md`.

## Measured evaluation — 22 cases

`python scripts/run_rag_eval.py`

| Metric | Result |
|---|---|
| Recall@4 | 22/22 = **1.000** |
| Top-1 accuracy | 21/22 = **0.955** |
| Mean fact coverage | **0.947** |
| Citation correctness | 22/22 well-formed and relevant |
| Overall pass rate | 22/22 = **1.000** |

The single Top-1 miss is RAG-12 ("which data quality checks are mandatory"), which retrieves DOC-005 §1 first because both documents enumerate check names; the correct document DOC-003 is still returned within K.

**Caveat worth stating plainly:** these scores are high partly because TF-IDF is lexical and the evaluation questions share vocabulary with the corpus. Real user phrasing will diverge more. Dense embeddings would be the honest next step.
