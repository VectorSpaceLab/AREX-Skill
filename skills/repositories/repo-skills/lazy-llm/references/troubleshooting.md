# Cross-cutting Troubleshooting

## Missing optional dependencies

**Symptom**

```text
ImportError: Missing package(s): [...]
You can install them by:
    lazyllm install rag
```

**Likely cause**: LazyLLM uses optional dependency group checks. Base install succeeded, but the selected workflow imports a group such as RAG, advanced agents, multimodal, tracing, or local serving.

**Recovery**

1. Route to the owning sub-skill and identify the smallest needed extra.
2. Install the named extra in the active Python environment, for example `lazyllm install rag`.
3. Run `python scripts/check_lazyllm_env.py --require-rag` from this skill directory.
4. Do not install `full` unless the task explicitly needs many optional stacks.

## CLI usage exits non-zero

**Symptom**: `lazyllm --help` or a typo command prints usage and exits with status 1.

**Likely cause**: The CLI dispatcher is simple and expects concrete top-level commands.

**Recovery**

- Use one of the command families documented in [API surface map](api-surface-map.md).
- Use safe commands such as `lazyllm skills list` for CLI smoke checks.
- Do not treat the non-zero `--help` dispatcher behavior as a package install failure.

## Provider/API-key errors

**Symptom**: online module calls fail with authentication, quota, inspection, timeout, or provider-specific errors.

**Likely cause**: `OnlineModule` or `OnlineChatModule` requires provider source/model/API-key configuration. Some tests cover pure message sanitation, but real calls need credentials.

**Recovery**

1. Route to [model-deployment](../sub-skills/model-deployment/SKILL.md).
2. Verify model type and provider selection without calling the provider when possible.
3. Ask the user for credential and budget approval before making real calls.
4. Preserve provider responses/error fragments for troubleshooting; do not print secrets.

## GPU/local model backend missing

**Symptom**: local deployment/fine-tune examples fail due to missing CUDA, vLLM, LMDeploy, LLaMA-Factory, model weights, or ports.

**Likely cause**: local model serving/training is an optional backend, not part of CPU verification.

**Recovery**

- Route to [model-deployment](../sub-skills/model-deployment/SKILL.md) and classify required backends.
- Check hardware, package extra, model path/cache, memory budget, and selected launcher before running.
- Use CPU/provider-free tests for documentation or planning tasks when the user has not asked to execute a model.

## External services unavailable

**Symptom**: Milvus, OpenSearch, Redis, parser service, SQL database, Kubernetes, Slurm, SCO, Feishu, GitHub, npm/npx, or MCP server commands fail.

**Likely cause**: the task requires an external service or side-effecting tool process.

**Recovery**

- Keep the workflow optional unless the user provided connection details and approved side effects.
- Use local fixtures where possible: BM25 for RAG, SQLite/temp files for document service metadata, writer JSON artifacts for review workflows, and function-call schema checks for agents.
- Do not post PR comments, mutate remote docs, run external server processes, or write to production databases without explicit approval.

## Flow output mismatch

**Symptom**: a LazyLLM flow returns a tuple/list/dict shape different from expected, or `bind` arguments appear swapped.

**Likely cause**: `pipeline`, `parallel`, `diverter`, `_skip_items`, `_kept_items`, and `bind` have specific input propagation semantics.

**Recovery**

- Route to [flow-orchestration](../sub-skills/flow-orchestration/SKILL.md).
- Reproduce the shape with `sub-skills/flow-orchestration/scripts/flow_smoke.py`.
- Avoid embedding model or RAG calls until the flow's Python-callable skeleton produces the expected shape.

## Writer/review side effects

**Symptom**: writer or review code needs Feishu/GitHub credentials, attempts to post comments, or reads/writes remote documents.

**Likely cause**: writer artifacts can be local and deterministic, but adapters and review commands may be side-effecting.

**Recovery**

- Route to [writer-review](../sub-skills/writer-review/SKILL.md).
- Use local `WriterDocument`/`WritingContext` artifacts first.
- Only enable Feishu/GitHub posting when requested and credentialed.

## Skill staleness

**Symptom**: current LazyLLM checkout has different commit, version, API signatures, CLI commands, or optional extras than this skill.

**Recovery**

- Read [Repository provenance](repo-provenance.md).
- Refresh the repo skill instead of patching isolated instructions from memory.
