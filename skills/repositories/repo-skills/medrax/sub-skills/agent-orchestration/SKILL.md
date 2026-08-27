---
name: agent-orchestration
description: "Initialize, configure, and safely exercise the MedRAX LangGraph
  agent with a selected tool registry, prompt sections, OpenAI-compatible chat
  model, checkpointed threads, and tool-call logs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MedRAX agent orchestration

Use this skill when a Researcher needs the MedRAX control plane rather than the
implementation details of a particular chest-X-ray model. It covers building an
`Agent`, selecting tools without accidentally loading optional weights, choosing
an OpenAI-compatible endpoint, loading the medical system prompt, invoking a
checkpointed thread, and inspecting tool-call logs.

Do not use this skill to explain a model's input/output semantics. Route those
questions to `chest-xray-analysis`. Route DICOM and visualization work to
`image-data-utilities`, UI/demo launch to `web-interface`, and benchmark cases
or metrics to `benchmark-evaluation`.

## Operating contract

- Work from an installed MedRAX package and a caller-owned prompt file. The
  bundled `resources/system_prompts.txt` is a portable template; do not require
  a source checkout or hard-coded checkout path.
- Keep model-weight directories, temporary files, logs, and credentials outside
  the skill tree. Never put API keys in code or prompt files.
- Treat medical output as decision support, not a diagnosis. Preserve tool
  results and uncertainty for the caller to review.
- Before constructing the real agent, run the bundled safe checker when the
  environment or dependency set is uncertain:
  `python scripts/check_medrax_import.py --project-root .`.
  It parses signatures and performs only lightweight imports; it does not create
  a `ChatOpenAI`, initialize a tool, download weights, or make a network call.

## Standard initialization

1. Confirm an accessible prompt file containing `[MEDICAL_ASSISTANT]` (or choose
   another explicit section) and a writable `temp_dir` if a selected utility
   needs temporary files.
2. Choose a small `tools_to_use` list. The exact registry in
   `main.initialize_agent` is documented in [api-reference.md](references/api-reference.md).
   Start with `ImageVisualizerTool` and `DicomProcessorTool` for orchestration
   smoke tests; add model-backed tools only after their own sibling skill and
   backend are ready.
3. Build `openai_kwargs` from the process environment. Pass `api_key` and,
   when needed, `base_url`; never print either value. A local OpenAI-compatible
   service commonly uses `OPENAI_BASE_URL=http://localhost:11434/v1` and a
   provider-specific placeholder key. See [workflows.md](references/workflows.md).
4. Call the adapted `scripts/medrax_agent_factory.py` function
   `build_agent(prompt_file, tools_to_use=..., model_dir=..., temp_dir=...,
   device=..., model=..., temperature=..., top_p=..., openai_kwargs=...)`;
   it returns `(agent, tools_dict)` and refuses an implicit all-tools selection.
   When integrating with the original application, the equivalent
   `main.initialize_agent` signature is recorded in [api-reference.md](references/api-reference.md).
5. Invoke the compiled graph with a message state and a stable configurable
   thread identifier, for example:
   `agent.workflow.invoke({"messages": [HumanMessage(content="...")]},
   {"configurable": {"thread_id": "smoke-001"}})`.
   Keep the same `thread_id` to continue a conversation; use a new one for an
   isolated run. Exact invocation and fake-model examples are in the workflow
   reference.

## Safety and selection rules

- `tools_to_use=None` selects every registered tool. In this implementation,
  an empty list is also replaced by every tool because selection uses
  `tools_to_use or all_tools.keys()`; use a non-empty explicit list when
  excluding model-backed tools.
- Unknown names are silently ignored by `initialize_agent`. Compare
  `set(requested) - set(tools_dict)` after initialization and fail closed in a
  wrapper if any were omitted.
- Do not select `LlavaMedTool`, `XRayPhraseGroundingTool`,
  `ChestXRayGeneratorTool`, `XRayVQATool`, `ChestXRayReportGeneratorTool`, or
  other weight-backed tools merely to test graph wiring. Their constructors may
  download or load large models. The two utility tools are the safe default.
- `Agent` binds every constructed tool through `model.bind_tools(tools)`. A
  model that cannot bind LangChain tool schemas is not a compatible backend.
- Use `MemorySaver()` as the in-memory checkpointer for a process-local test.
  It is not a durable or multi-process store; do not present it as persistence.

## Agent state machine and logs

`Agent` stores `messages` as an append-only `AgentState` field. The compiled
LangGraph starts at `process`, invokes the bound model, routes to `execute` if
the last response has tool calls, executes each call by registered name, then
returns to `process`. An unknown call name yields a `ToolMessage` containing
`invalid tool, please retry`; it is not executed. A response with no tool calls
ends the graph.

With `log_tools=True` (the `initialize_agent` default), `log_dir` defaults to
`logs`; the agent creates that directory and writes timestamped
`tool_calls_YYYYMMDD_HHMMSS.json` files containing `tool_call_id`, `name`,
`args`, `content`, and an ISO timestamp. Set `log_tools=False` for a no-log
synthetic test. Ensure `log_dir` exists or its parent is writable; avoid
sensitive arguments in logs and treat log files as sensitive operational data.

For API details, tool registry entries, prompt parsing, and failure recovery,
use the linked references rather than guessing parameter names. For a
source-independent construction path, import `build_agent` from
`scripts/medrax_agent_factory.py`; importing that module alone performs no model,
tool, or network operation. Its command-line default only prints safe help.
