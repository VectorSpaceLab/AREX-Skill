---
name: agents-tools
description: "Guides LazyLLM function-call tools, ToolManager, agents, sandbox
  metadata, SkillManager, MCP, search, SQL, HTTP, and built-in tools."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LazyLLM Agents and Tools

Use this sub-skill for LazyLLM function-call tools, `fc_register`, `ToolManager`, tool metadata, sandbox flags, file parameters, built-in tools, SQL/HTTP/search tools, `ReactAgent`, `ReWOOAgent`, `PlanAndSolveAgent`, `SkillManager`, skills CLI, and MCP integration.

## Start here when

- The task mentions `fc_register`, `lazyllm.tool`, `ToolManager`, `execute_in_sandbox`, tool schemas, `input_files_parm`, or `output_files_parm`.
- The user wants to build a React/ReWOO/PlanAndSolve agent or debug tool-calling traces.
- The task uses `lazyllm skills` commands, `SkillManager`, repo/user skill directories, or skills agent examples.
- The task mentions MCP clients/servers, `deploy mcp_server`, npm/npx, or external tool processes.
- The task asks about built-in search, SQL manager, HTTP nodes, sandboxed execution, or PowerMemory-style examples.

## Files to read

- [agent-tool-workflows.md](references/agent-tool-workflows.md) for deterministic tool registration and agent planning recipes.
- [mcp-and-skills.md](references/mcp-and-skills.md) for SkillManager, skills CLI, and MCP boundaries.
- [troubleshooting.md](references/troubleshooting.md) for schema, sandbox, MCP, provider, and tool-call errors.
- [scripts/tool_agent_smoke.py](scripts/tool_agent_smoke.py) for a no-network check of tool registration metadata.

## Safe workflow

1. **Register/inspect tools without an LLM first.** Use `fc_register` and verify metadata.
2. **Choose agent class only after tool contracts are stable.**
   - `ReactAgent`: iterative tool use with retries.
   - `ReWOOAgent`: plan then solve with tool observations.
   - `PlanAndSolveAgent`: planning and solving roles with optional separate LLMs.
3. **Separate schema from execution.** Tool registration and schema checks are safe; executing shell, HTTP, SQL, search, or MCP tools can be side-effecting.
4. **Treat LLM calls as optional.** Agent reasoning needs an LLM/provider or local model configured by [model-deployment](../model-deployment/SKILL.md).
5. **Treat MCP as external-process work.** Do not run npm/npx/MCP servers unless the user approves the command and environment.

## Verified signatures to remember

- `fc_register(f, *, rewrite_func=None, **kwargs)` registers callable tools and metadata.
- `ToolManager(tools, return_trace=False, sandbox=None)` manages callable or named tools.
- `SkillManager(dir=None, skills=None, max_skill_md_bytes=None, fs=None, sandbox=None)` loads LazyLLM skills.
- `ReactAgent(llm, tools=None, max_retries=5, return_trace=False, prompt=None, stream=False, return_last_tool_calls=False, skills=None, desc='', workspace=None, sandbox=None, force_summarize=False, force_summarize_context='', keep_full_turns=0, fs=None, skills_dir=None, enable_builtin_tools=True, extra_stop_condition=None, on_max_retries=None)`.
- `ReWOOAgent` and `PlanAndSolveAgent` accept optional `plan_llm`, `solve_llm`, `tools`, tracing, streaming, skills, sandbox, fs, and built-in tool controls.

## Tool metadata facts

LazyLLM tests verify:

- `execute_in_sandbox` defaults to true and can be disabled.
- `input_files_parm`, `output_files_parm`, and static `output_files` metadata are preserved.
- unsupported `fc_register` parameters raise assertions.
- writer/search/SQL/HTTP tools have local contract tests and should be validated before real external calls.

## Handoff checklist

When completing an agent/tool task, provide:

- tool names, docstrings, parameter schema expectations, and sandbox/file metadata,
- whether the tool was registered and inspected without LLM calls,
- selected agent class and LLM/backend status,
- explicit side-effect classification for shell, HTTP, SQL, search, MCP, or remote services,
- local smoke command and optional/unrun external verification.
