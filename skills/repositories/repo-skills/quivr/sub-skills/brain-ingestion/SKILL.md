---
name: brain-ingestion
description: "Build a Quivr brain from text or documents, inspect chunking and
  storage, and use the current safe ingestion workaround."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Brain Ingestion

Use this sub-skill when you need to turn files or document chunks into a brain,
inspect how chunking works, or understand the save/load boundary.

## Start here

- For live API signatures and object names, read `../../references/api-reference.md`.
- For the canonical ingestion workflow, read `references/workflows.md`.
- For failure modes and the current workaround, read `references/troubleshooting.md`.
- For a safe executable smoke path, run `../../scripts/text_brain_smoke.py --phase ingestion`.

## What this sub-skill owns

- `load_qfile`
- `QuivrFile` and `QuivrFile.metadata`
- `SimpleTxtProcessor`
- `SplitterConfig`
- `ProcessedDocument.chunks`
- `TransparentStorage` and `LocalStorage`
- `Brain.afrom_langchain_documents`
- `Brain.save` / `Brain.load` caveats
- the current `Brain.from_files` workaround

## What this sub-skill does not own

- question answering, citations, streaming, or chat memory -> `../brain-qa/SKILL.md`
- optional parser stacks such as unstructured, Tika, or MegaParse -> root references only
- non-Quivr repository maintenance -> outside this skill

## Practical rule

If the user already has documents or a text file, prefer the processor output
chunks directly. In this snapshot, `Brain.from_files` on non-empty input is not a
reliable path, so route through `SimpleTxtProcessor.process_file(...).chunks`
plus `Brain.afrom_langchain_documents(...)` instead.
