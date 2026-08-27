# Workflows

This file summarizes the most useful Quivr workflows in the order a future agent
is likely to need them.

## 1. Safe text-to-brain smoke

Use `scripts/text_brain_smoke.py --phase ingestion` when you want a deterministic
path from a plain text file to a brain.

Workflow shape:

1. Create or load a small text file.
2. Turn it into a `QuivrFile` with `load_qfile(...)`.
3. Process it with `SimpleTxtProcessor.process_file(...)`.
4. Use `processed.chunks`, not the `ProcessedDocument` object itself.
5. Build the brain with `Brain.afrom_langchain_documents(...)`.

This is the current safe workaround path while `Brain.from_files` remains broken
for non-empty inputs in this snapshot.

## 2. QA and streaming smoke

Use `scripts/text_brain_smoke.py --phase qa` when you want to verify the answer
path without reaching for a live provider.

Workflow shape:

1. Build a brain from fake embeddings and a fake chat model.
2. Run `Brain.asearch(...)` to confirm retrieval behaves as expected.
3. Run `Brain.aask(run_id=uuid4(), ...)` for a normal answer.
4. Optionally run `Brain.ask_streaming(...)` to see incremental chunks and the
   final metadata chunk.
5. Inspect the resulting `ParsedRAGResponse` or `ParsedRAGChunkResponse`.

## 3. Config-driven RAG

Use `RetrievalConfig.from_yaml(...)` when the user wants to tune retrieval,
reranking, or the workflow graph from a YAML file.

Relevant pieces:

- `llm_config` controls provider selection and token budgets.
- `reranker_config` activates Cohere or Jina reranking when keys are present.
- `workflow_config` controls the graph nodes and any declared tools.
- Add `available_tools: ["web search"]` when the user wants the web-search route.
- Keep `cited_answer` bound on the answer node when you want cited output.

Repo-owned workflow references worth opening for this shape:

- `core/example_workflows/talk_to_file_rag_config_workflow.yaml` captures a repo-local YAML workflow sample.
- `docs/docs/workflows/examples/basic_ingestion.md` shows the intended ingestion-side YAML/config shape.
- `docs/docs/workflows/examples/basic_rag.md` and `docs/docs/workflows/examples/rag_with_web_search.md` show the QA-side workflow shape and tool routing.

These are reference artifacts, not direct smoke commands; their `Brain.from_files`
examples reflect the current ingestion caveat and should be read together with
this skill's workaround path.

## 4. Save and load

Use `await brain.save(out_dir)` only after the brain uses FAISS plus OpenAI
embeddings.

Workflow shape:

1. Build the brain.
2. Save it to a dedicated output directory.
3. Load it back with `Brain.load(saved_path)`.
4. Re-run `brain.info()` or a small QA smoke to confirm the round-trip.

Do not claim this works for arbitrary vector stores or fake embedders.

## 5. When to stop and rethink

If the task is about PDF, DOCX, HTML, EPUB, or ODT parsing, first decide whether
it belongs in the verified core text workflow or in an optional parser backend.
If the user did not ask for an optional backend, stay with the core ingestion
sub-skill and the plain-text smoke path.
