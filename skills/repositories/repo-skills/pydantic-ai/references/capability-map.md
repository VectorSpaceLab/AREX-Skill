# Capability Map

Use this reference to choose a sub-skill and understand coverage boundaries.

| Capability | Owner | Evidence distilled |
| --- | --- | --- |
| Agent construction, run modes, streaming, deps, instructions, usage limits, message-history continuation, `AgentSpec`, `TestModel`/`FunctionModel` testing | `sub-skills/agent-core/` | `pydantic_ai_slim/pydantic_ai/agent/`, run/result/usage modules, agent docs, deps/history/testing/spec docs, agent tests, examples. |
| Function tools, `RunContext` in tools, schemas, `ModelRetry`, `ToolReturn`, validators, approvals, deferred tools, tool search, reusable toolsets | `sub-skills/tools-and-toolsets/` | `tools.py`, `toolsets/`, function-schema/tool-search source, tools/toolsets/deferred docs, tool tests. |
| Structured output, output functions, `TextOutput`, `ToolOutput`, `NativeOutput`, `PromptedOutput`, `StructuredDict`, message parts, multimodal input, serialization | `sub-skills/outputs-and-messages/` | `output.py`, `_output.py`, `messages.py`, output/input/history/UI docs, output/message/schema tests. |
| Model/provider strings, provider classes, profiles, settings, fallback/concurrency/instrumentation wrappers, native tools, embeddings, optional SDKs | `sub-skills/models-and-providers/` | `models/`, `providers/`, `profiles/`, `native_tools/`, `embeddings/`, model/provider/install/native-tool docs, provider/model tests. |
| MCP/FastMCP, capabilities, hooks, Logfire, A2A, durable execution, AG-UI, Vercel AI, integration import diagnostics | `sub-skills/mcp-and-integrations/` | `mcp.py`, `toolsets/fastmcp.py`, `capabilities/`, `durable_exec/`, UI/A2A/instrumentation source, MCP/capability/hook/UI/durable docs and tests. |
| Pydantic Evals and pydantic-graph workflows | `sub-skills/evals-and-graph/` | `pydantic_evals/`, `pydantic_graph/`, evals/graph docs, examples, tests, live signatures. |
| CLI, web chat UI, custom agents, installed example recipes, `Agent.to_cli`, `Agent.to_web` | `sub-skills/cli-and-apps/` | `clai/`, `_cli/`, CLI/web/examples docs, CLI and example tests, CLI help checks. |
| Repository maintenance, contribution philosophy, targeted validation, VCR cassettes, docs examples, generated-skill refreshes | `sub-skills/repo-development/` | `AGENTS.md`, `agent_docs/`, package/docs/tests AGENTS files, `CONTRIBUTING.md`, `Makefile`, pyproject workspace, local Claude skills, test helpers. |

## Boundary Checks

- If a task says "agent" but is really about final output schema or message serialization, route to `outputs-and-messages` after reading `agent-core` basics.
- If a task says "tool" but uses provider-hosted web search, file search, code execution, memory, or native MCP, route to `models-and-providers` or `mcp-and-integrations` instead of `tools-and-toolsets`.
- If a task says "MCP toolset", start in `mcp-and-integrations` for lifecycle and protocol choices, then use `tools-and-toolsets` for generic wrapper behavior.
- If a task says "evaluation" in the sense of testing an LLM/agent output, use `evals-and-graph`; if it means repo pytest validation, use `repo-development`.
- If a task edits this repository, always read `repo-development` and the relevant user-facing sub-skill for the API area being changed.
