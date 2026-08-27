# Cross-Cutting Troubleshooting

Use this page when a Kotaemon task spans setup, optional dependencies, provider configuration, app launch, document parsing, and core RAG behavior.

## Start With Scope

| Symptom | First route |
| --- | --- |
| `python app.py` fails, login/setup is confusing, PDF viewer missing, app data paths wrong | `sub-skills/app-deployment/SKILL.md` |
| Parser cannot read PDF/DOCX/HTML/XLSX, OCR/table extraction fails, metadata is malformed | `sub-skills/document-ingestion/SKILL.md` |
| Retrieval returns empty/low-quality results, citations look wrong, vector/docstore ids mismatch | `sub-skills/rag-core/SKILL.md` |
| API key, endpoint, Ollama, local server, reranker, GraphRAG, or provider package issue | `sub-skills/model-providers/SKILL.md` |
| Custom component/index/page/template is not discovered or settings do not appear | `sub-skills/extensions/SKILL.md` |

## Install and Import Failures

| Observable signal | Likely cause | Recovery |
| --- | --- | --- |
| Dependency resolver backtracks for a long time | broad provider/app dependency set, unpinned packages, slow network | prefer documented lockfile/`uv` setup, install only selected optional groups, or use Docker for full app parity |
| `ModuleNotFoundError` for parser/provider/vector package | optional integration not installed | identify the owning workflow and install only that optional dependency after confirming credentials/services are available |
| `pip check` conflicts after adding GraphRAG or local-model packages | optional package changed shared vectorstore or ML dependencies | isolate the workflow in a fresh environment, record package constraints, and avoid mixing all optional stacks |
| top-level `kotaemon` imports but deeper modules fail | missing optional dependency imported by a specific loader/provider/index | route to the nearest sub-skill and document a fallback reader/provider rather than treating the whole package as broken |

## Configuration Failures

| Signal | Likely cause | Recovery |
| --- | --- | --- |
| `.env` changes do not affect an existing app | Resources UI/database entries outlive first-run env seeding | update the Resources tab or reset app data intentionally; do not assume `.env` is the only source after first launch |
| Provider key looks configured but calls fail | placeholder key, missing endpoint/deployment pair, wrong base URL suffix, or Docker `localhost` mismatch | run `sub-skills/model-providers/scripts/check_provider_env.py` and follow provider-specific guidance |
| PDF preview is unavailable | PDF.js assets not downloaded/extracted to the expected app asset directory | use `app-deployment` PDF.js guidance; avoid running download scripts in restricted networks without approval |
| GraphRAG toggles are enabled but indexing fails | missing key, optional package, custom settings file, or incompatible local provider URL | use `model-providers/references/graphrag.md`; validate settings offline before running indexing |

## Data and Runtime Safety

- Do not run migration scripts, update scripts, server launchers, provider API calls, model downloads, or indexing over user data until the task explicitly needs those side effects.
- Prefer the bundled checkers first; they are designed to be read-only and self-contained.
- Treat original repository tests/examples as verification evidence for a checkout, not as runtime dependencies for this skill.
- If a failure depends on credentials, network, GPU, model weights, or external services, stop after producing a precise preflight report unless the user authorizes those operations.

## Useful Diagnostics

```bash
python skills/kotaemon/scripts/check_install.py --repo-root <repo-root>
python skills/kotaemon/sub-skills/app-deployment/scripts/check_app_config.py --repo-root <repo-root> --env-file <repo-root>/.env
python skills/kotaemon/sub-skills/model-providers/scripts/check_provider_env.py --env-file <repo-root>/.env --select auto
python skills/kotaemon/sub-skills/document-ingestion/scripts/validate_document_metadata.py documents.json
python skills/kotaemon/sub-skills/extensions/scripts/scaffold_component_check.py --path <component-or-template>
```

Run these from any working directory. They should not require the generated skill to live inside the original repository.
