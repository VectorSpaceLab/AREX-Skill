# Repository Layout

Use this map before deciding where a maintainer change belongs and which validations are likely relevant.

## Workspace Packages

Pydantic AI is a `uv` workspace with multiple published packages and one root aggregate package.

| Path | Package or role | Maintainer notes |
| --- | --- | --- |
| `pyproject.toml` | root `pydantic-ai` aggregate package | Publishes the full package and optional extras; `tool.uv.workspace.members` points at the member packages. |
| `pydantic_ai_slim/` | `pydantic-ai-slim` | Core agent framework, model/provider adapters, tools, toolsets, output/messages, capabilities, MCP, durable execution, UI adapters, CLI shims, embeddings, and native tools. |
| `pydantic_graph/` | `pydantic-graph` | Type-hint-based graph/state-machine library used by agents and exposed separately. |
| `pydantic_evals/` | `pydantic-evals` | Evaluation datasets, evaluators, reporting, online evals, and Logfire-oriented eval support. |
| `clai/` | `clai` | Chat CLI and web UI package that consumes Pydantic AI agents. |
| `examples/` | `pydantic-ai-examples` | Maintained examples used by docs and example tests; many examples require mocking or provider credentials when run outside the docs harness. |

The root package depends on `pydantic-ai-slim[...]` with many optional extras. Dependency or extra changes should update the relevant package metadata and regenerate lock data with the project’s normal install workflow, rather than hand-editing generated artifacts.

## Source Boundaries

| Source area | Owns | Route related generated-skill updates to |
| --- | --- | --- |
| `pydantic_ai_slim/pydantic_ai/agent/`, `_agent_graph.py`, `run.py`, `result.py`, `usage.py` | Agent construction, execution loop, run results, usage limits, specs, and core orchestration. | `../agent-core/` |
| `pydantic_ai_slim/pydantic_ai/tools.py`, `toolsets/`, `_function_schema.py`, `_tool_search.py` | Function tools, tool definitions, schema generation, retries, approvals, deferred tools, and reusable toolsets. | `../tools-and-toolsets/` |
| `pydantic_ai_slim/pydantic_ai/output.py`, `_output.py`, `messages.py`, `_parts_manager.py`, `_json_schema.py` | Structured/text/native/prompted output contracts, message parts, multimodal content, serialization, and normalized protocol shapes. | `../outputs-and-messages/` |
| `pydantic_ai_slim/pydantic_ai/models/`, `providers/`, `profiles/`, `native_tools/`, `embeddings/`, `common_tools/`, `settings.py` | Provider adapters, authentication clients, model-family facts, native provider tools, embeddings, and typed model settings. | `../models-and-providers/` |
| `pydantic_ai_slim/pydantic_ai/mcp.py`, `capabilities/`, `durable_exec/`, `ui/`, `ag_ui.py`, `a2a.py` | MCP, capabilities/hooks, durable runtimes, UI protocol adapters, A2A, and instrumentation integration surfaces. | `../mcp-and-integrations/` when present; otherwise root routing should direct users to the closest integration sub-skill. |
| `clai/`, `pydantic_ai_slim/pydantic_ai/_cli/`, `__main__.py` | Installed CLI entry points, custom agent loading, web UI launches, and help output. | `../cli-and-apps/` when present; otherwise root routing should direct CLI changes there once generated. |
| `pydantic_graph/`, `pydantic_evals/` | Graph and eval APIs, reports, datasets, graph builder, persistence, and diagrams. | `../evals-and-graph/` |

## Documentation and Examples

| Path | Purpose | Maintainer notes |
| --- | --- | --- |
| `docs/` | Public MkDocs site and API reference pages. | Follow `docs/AGENTS.md`: use `Pydantic AI`, reference-style API links, progressive disclosure, current APIs, and MkDocs admonitions. New docs files must be added to `mkdocs.yml` navigation. |
| `docs/api/` | Generated/API-reference-oriented docs. | Keep public API names and docstrings consistent; use reference links for API elements. |
| `docs/models/` | Provider-specific model docs. | Put provider-specific capabilities and config here instead of scattering lists in general docs. |
| `docs/examples/` | Narrative example pages. | The examples test harness runs docs, source docstrings, graph docs, and eval docs with provider/model mocks. Avoid `test="skip"` unless unavoidable. |
| `examples/pydantic_ai_examples/` | Importable example modules. | Treat examples as product docs: keep them runnable where feasible and update tests/docs together. |

## Tests and Cassettes

| Path | Purpose | Maintainer notes |
| --- | --- | --- |
| `tests/conftest.py` | Shared fixtures, `ALLOW_MODEL_REQUESTS = False`, VCR setup, API-key fixtures, env helper, HTTP client tracking, provider fixtures. | Read before adding provider, VCR, env, or model fixtures. |
| `tests/AGENTS.md` | Test philosophy and style. | VCR + public API tests are default; unit tests must earn their place. |
| `tests/cassettes/` | Root-level VCR HTTP cassettes for feature/integration tests. | Use names as evidence; do not copy cassettes into generated runtime skills. |
| `tests/models/cassettes/` | Provider/model VCR cassettes, including `.xai.yaml` protobuf-derived recordings for xAI. | Provider cassette work should route to `../models-and-providers/` too. |
| `tests/models/`, `tests/providers/`, `tests/profiles/` | Model adapters, providers, profiles, settings, wrappers, and provider-specific behavior. | Many tests use optional extras or recordings; choose targeted tests and expect skips when extras are absent. |
| `tests/evals/`, `tests/graph/` | Evals and graph behavior. | Prefer safe local subsets for routine validation. |
| `tests/test_examples.py` | Docs and docstring example test harness. | Mocks model/provider/network behavior, sets placeholder env vars, and applies example-level settings. |

## Maintainer Guidance Sources

Always account for the scoped maintainer instructions before editing:

- Root `AGENTS.md` sets the project philosophy, contribution requirements, validation strategy, PR conventions, and generated skill-update policy.
- `agent_docs/index.md` summarizes review-derived rules. Read topic guides when touching their areas: `api-design.md`, `documentation.md`, `code-simplification.md`, and `pydantic-ai-slim.md`.
- Nested `AGENTS.md` files apply to their directory trees, including `docs/AGENTS.md`, `tests/AGENTS.md`, and package-level instructions under `pydantic_ai_slim/pydantic_ai/`.
- `CONTRIBUTING.md` explains contribution alignment, maintainer priority, feature/API-change expectations, and model-integration policy.

## Scripts and Local Workflow Skills

| Path | Role | Runtime skill decision |
| --- | --- | --- |
| `scripts/check_cassettes.py` | Checks VCR cassette files have matching VCR-marked tests. | Reference-only maintainer utility; do not copy into generated skills. |
| `scripts/scrub_cassette.py` | One-time mutating cassette scrubber through the custom serializer. | Reference-only because it mutates cassette files. |
| `scripts/gather-pydantic-ai-review-context.sh` | PR review context collector for automated review flows. | Reference-only because it depends on GitHub CLI, PR numbers, and temporary runner context. |
| `scripts/gather-review-context.sh` | Legacy generic review context collector. | Excluded from runtime instructions except as evidence of review workflow shape. |
| `.claude/skills/testing-skill/` | Local workflow for VCR recording, playback verification, and cassette parsing. | Mention in handoff and source-maintenance context only; generated runtime skills should bundle their own safe helpers. |
| `.claude/skills/pre-push-review/` | Local review checklist based on CI review prompts. | Evidence for review expectations, not a runtime dependency. |
| `.claude/skills/address-feedback/` | Local PR feedback triage and thread resolution workflow. | Evidence for maintainer workflow, not a runtime dependency. |
| `pydantic_ai_slim/pydantic_ai/.agents/skills/building-pydantic-ai-agents/` | User-facing agent-building skill distributed with `pydantic-ai-slim`. | Update when public agent mechanics change; do not confuse it with repo-maintainer workflow skills. |

## Generated Skill Areas

Generated repo-specific runtime skills live under `skills/pydantic-ai/`. Review and verification artifacts live under `skills/tests/pydantic-ai/` and must not be mixed into runtime content.

When source changes affect public behavior or documentation, update the matching generated sub-skill and the root provenance/refresh guidance. When maintainer workflow itself changes, update this `repo-development` sub-skill and any relevant local workflow skill under `.claude/skills/`.
