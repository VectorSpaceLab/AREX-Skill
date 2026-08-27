---
name: quivr
description: "Use Quivr to ingest documents into a brain, inspect storage and
  parser behavior, and ask or stream answers with RAG."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Quivr Repo Skill

Use this skill for the `quivr-core` package when a task involves building a brain from text or documents, asking questions of that brain, streaming answers, inspecting chat history, or diagnosing configuration, parser, or storage issues.

## Route by task

- Build or repair ingestion, chunking, storage, save/load, or file-processing workflows -> `sub-skills/brain-ingestion/SKILL.md`
- Ask questions, stream answers, search a brain, inspect chat history, or tune retrieval/web search -> `sub-skills/brain-qa/SKILL.md`
- Need API signatures or public class/method facts -> `references/api-reference.md`
- Need config, environment-variable, or compatibility details -> `references/configuration.md` and `references/compatibility.md`
- Need concrete failure modes and fixes -> `references/troubleshooting.md`
- Need distilled examples or workflow maps -> `references/examples.md` and `references/workflows.md`

## Safe start

Run the bundled checks from this skill directory:

```bash
python scripts/inspect_api.py --check-import
python scripts/text_brain_smoke.py --phase ingestion
python scripts/text_brain_smoke.py --phase qa
```

## Current version notes

- In `quivr-core 0.0.33`, `Brain.from_files` and `Brain.afrom_files` are not reliable on non-empty inputs because `process_files()` extends a `ProcessedDocument` instead of its `.chunks`.
- Prefer `SimpleTxtProcessor.process_file(...).chunks` plus `Brain.afrom_langchain_documents` until that ingestion path is fixed.
- `Brain.ask` is a synchronous wrapper that still requires a `run_id`; use `Brain.aask` or `Brain.ask_streaming` from async code.
- `Brain.save` only serializes FAISS plus OpenAI embeddings.

## When in doubt

Start with the narrowest sub-skill, then open the shared references if you need exact signatures, config fields, or troubleshooting detail. Keep optional parser stacks such as unstructured, Tika, and MegaParse as separate concerns unless the user explicitly asks for them.
