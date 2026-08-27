# API reference: MedRAX orchestration

This reference records the orchestration surface implemented by MedRAX. It is
for adapting a local integration; it does not change the package APIs.

## `initialize_agent`

```python
initialize_agent(
    prompt_file,
    tools_to_use=None,
    model_dir="<configured-model-dir>",
    temp_dir="temp",
    device="cuda",
    model="chatgpt-4o-latest",
    temperature=0.7,
    top_p=0.95,
    openai_kwargs={},
) -> tuple[Agent, dict[str, BaseTool]]
```

The initializer parses `prompt_file`, obtains the `MEDICAL_ASSISTANT` section,
constructs selected tool instances, creates an in-memory `MemorySaver`, builds
`ChatOpenAI(model=model, temperature=temperature, top_p=top_p,
**openai_kwargs)`, and returns the `Agent` plus a name-to-instance mapping.
Use a newly created dictionary for `openai_kwargs`; do not mutate the function's
shared default dictionary.

`openai_kwargs` is forwarded to `ChatOpenAI`. The application fills it from
`OPENAI_API_KEY` as `api_key` and `OPENAI_BASE_URL` as `base_url`. A caller may
provide compatible additional ChatOpenAI keyword arguments only after checking
the installed `langchain-openai` version.

### Registered selection names

The selection argument recognizes these exact strings:

| Requested name | Constructor arguments used by initializer | Weight-free? | Route |
| --- | --- | --- | --- |
| `ChestXRayClassifierTool` | `device=device` | No | `chest-xray-analysis` |
| `ChestXRaySegmentationTool` | `device=device` | No | `chest-xray-analysis` |
| `LlavaMedTool` | `cache_dir=model_dir`, `device=device`, `load_in_8bit=True` | No | `chest-xray-analysis` |
| `XRayVQATool` | `cache_dir=model_dir`, `device=device` | No | `chest-xray-analysis` |
| `ChestXRayReportGeneratorTool` | `cache_dir=model_dir`, `device=device` | No | `chest-xray-analysis` |
| `XRayPhraseGroundingTool` | `cache_dir=model_dir`, `temp_dir=temp_dir`, `load_in_8bit=True`, `device=device` | No | `chest-xray-analysis` |
| `ChestXRayGeneratorTool` | `model_path=f"{model_dir}/roentgen"`, `temp_dir=temp_dir`, `device=device` | No | `chest-xray-analysis` |
| `ImageVisualizerTool` | no arguments | Yes | `image-data-utilities` |
| `DicomProcessorTool` | `temp_dir=temp_dir` | Yes | `image-data-utilities` |

“Weight-free” only means the constructor is documented as requiring no
additional model weights. DICOM processing or visualization may still need
ordinary Python dependencies and valid local input files.

### Selection behavior

The initializer uses `tools_to_use = tools_to_use or all_tools.keys()`. Therefore
both `None` and `[]` mean all nine registry entries. The initializer only adds a
tool when its requested name is a registry key and otherwise does nothing; it
does not warn or raise for an invalid requested name. Check after construction:

```python
requested = ["ImageVisualizerTool", "DicomProcessorTool"]
agent, tools_dict = initialize_agent(..., tools_to_use=requested)
missing = set(requested) - set(tools_dict)
if missing:
    raise RuntimeError(f"Unsupported or unavailable selections: {sorted(missing)}")
```

Avoid constructing tools just to discover availability, because construction can
load or download optional model weights. Validate names statically against the
table first and use the smoke-test pattern in `workflows.md`.

## Prompt parser contract

`load_prompts_from_file(file_path) -> dict[str, str]` parses headers of exactly
`[SECTION_NAME]`. It strips each input line, ignores blank lines, joins retained
lines with newlines, and raises `FileNotFoundError` for a missing file.

`initialize_agent` requires the parsed mapping to contain
`MEDICAL_ASSISTANT`, then accesses it with `prompts["MEDICAL_ASSISTANT"]`.
A file that has another section but lacks that one raises `KeyError`. Check the
section before agent construction.

`load_system_prompt(system_prompts_file, system_prompt_type, tools,
tools_json_path) -> str` is a separate helper. It loads a named section and
tool descriptions from JSON. Its fallback is the literal string
`GENERAL_ASSISTANT`, not the content of that named section; request an existing
section explicitly when using this helper.

## `Agent`

```python
Agent(
    model: BaseLanguageModel,
    tools: list[BaseTool],
    checkpointer: Any = None,
    system_prompt: str = "",
    log_tools: bool = True,
    log_dir: str | None = "logs",
)
```

Construction builds and compiles this graph:

```text
START -> process -- tool calls? yes --> execute --> process
                       \-- no ------------------> END
```

- `AgentState` has `messages`, an append-only list (`operator.add`).
- `process_request(state)` prepends a `SystemMessage` when `system_prompt` is
  nonempty, calls `self.model.invoke(messages)`, and appends the response.
- The tool map is `{tool.name: tool for tool in tools}`. Duplicate tool names
  overwrite earlier map entries; supply unique names.
- `model.bind_tools(tools)` is called during construction. Any binding failure
  happens before an invocation.
- `execute_tools(state)` processes every tool call on the latest response. A
  known name receives `.invoke(call["args"])`; an unknown name returns the
  literal result `invalid tool, please retry` in a `ToolMessage`.

The `workflow` attribute is the compiled LangGraph runnable. Supply
`{"configurable": {"thread_id": "..."}}` when invoking it with a
checkpointer. The exact thread ID must be stable to recover a MemorySaver state.

## Tool-call logging

When `log_tools=True`, construction assigns
`Path(log_dir or "logs")` and calls `mkdir(exist_ok=True)` (without
`parents=True`). After each execution node it serializes a list of tool result
records to `tool_calls_YYYYMMDD_HHMMSS.json`. Each entry has `timestamp`,
`tool_call_id`, `name`, `args`, and string `content`.

Choose a writable simple child directory, or create a nested parent directory
before construction. Separate execution batches that finish in the same second
can target the same filename; use distinct log directories or preserve logs
between runs if collision-free audit records are required. Log content may
contain image-derived data or user-provided paths, so apply appropriate data
handling and access controls.
