# Examples

This file maps the repository examples to the distilled skill surface.
Treat the examples as context, not as the authoritative API surface.

| Example | What it shows | Caveat |
| --- | --- | --- |
| `examples/simple_question/simple_question.py` | basic question answering from a text brain | the snippet is stale because it omits the current `run_id` requirement |
| `examples/simple_question/simple_question_streaming.py` | async streaming QA and a save/load round-trip | good reference for `Brain.ask_streaming(...)`, but still needs live credentials for the persistence path |
| `examples/save_load_brain.py` | brain serialization and reload | only valid with serializable OpenAI embeddings plus FAISS |
| `examples/pdf_document_from_yaml.py` | YAML-driven ingestion configuration | hardcoded paths make it reference-only |
| `core/example_workflows/talk_to_file_rag_config_workflow.yaml` | repo-owned YAML workflow sample | config reference only; pair it with the ingestion workaround and current API notes |
| `docs/docs/workflows/examples/basic_ingestion.md` | ingestion-side YAML/config walkthrough | the snippet is useful for config shape, but its `Brain.from_files` example follows the current ingestion caveat |
| `examples/pdf_parsing_tika.py` | Tika-based PDF parsing comparison | requires a live Tika service |
| `examples/chatbot/main.py` | Chainlit chatbot starter | UI-specific and external-API-key dependent |
| `examples/chatbot_voice/main.py` | voice chatbot starter | UI-specific and external-API-key dependent |
| `examples/quivr-whisper/app.py` | Flask voice application scaffold | excluded from the core reusable workflow |

## Practical takeaway

For the current snapshot, the bundled smoke scripts are safer than the raw
examples because they already encode the `run_id` requirement, the fake-LLM test
path, and the ingestion workaround.
