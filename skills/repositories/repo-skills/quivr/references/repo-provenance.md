# Repo Provenance

This skill was distilled from the Quivr repository snapshot used to inspect `quivr-core`.

- Skill id: `quivr`
- Source branch: `main`
- Source commit: `947a785415c6c35ab2ae8157222b4720b0710b4d`
- Working tree state during creation: dirty
- Package version: `quivr-core 0.0.33`
- Confirmed scope: `brain-ingestion`, `brain-qa`
- Runtime skill root: `skills/disco/quivr/`
- Review artifact root: `skills/tests/quivr/`

## Evidence Used

- `core/quivr_core/brain/brain.py`
- `core/quivr_core/brain/brain_defaults.py`
- `core/quivr_core/brain/info.py`
- `core/quivr_core/brain/serialization.py`
- `core/quivr_core/files/file.py`
- `core/quivr_core/llm/llm_endpoint.py`
- `core/quivr_core/processor/processor_base.py`
- `core/quivr_core/processor/implementations/simple_txt_processor.py`
- `core/quivr_core/processor/implementations/default.py`
- `core/quivr_core/processor/implementations/tika_processor.py`
- `core/quivr_core/processor/implementations/megaparse_processor.py`
- `core/quivr_core/processor/registry.py`
- `core/quivr_core/rag/entities/chat.py`
- `core/quivr_core/rag/entities/config.py`
- `core/quivr_core/rag/entities/models.py`
- `core/quivr_core/rag/quivr_rag.py`
- `core/quivr_core/rag/quivr_rag_langgraph.py`
- `core/quivr_core/rag/utils.py`
- `core/quivr_core/llm_tools/`
- `core/tests/`
- `core/tests/rag_config.yaml`
- `core/tests/rag_config_workflow.yaml`
- `core/example_workflows/talk_to_file_rag_config_workflow.yaml`
- `core/scripts/`
- `.github/workflows/backend-core-tests.yml`
- `docs/docs/`
- `docs/docs/workflows/examples/basic_ingestion.md`
- `examples/`

## Staleness Checks

- `Brain.from_files` / `Brain.afrom_files` bug was observed in the live checkout and must remain visible until the repository fixes it.
- The live API uses `max_context_tokens` / `max_output_tokens`; prefer the source code over stale example wording when the two disagree.
- The root smoke script and the `brain-ingestion` workaround path are the safest current entry points for future users.
