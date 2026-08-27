# Agent Workflow API Reference

This reference summarizes the smolagents agent APIs most often needed when building workflows. It focuses on agent orchestration, memory, planning, and serialization. Tool implementation, model provider setup, executor security, and CLI/UI wrappers belong to sibling sub-skills.

## Class Selection

| Class | Choose it when | Main action format |
| --- | --- | --- |
| `CodeAgent` | The model should produce Python snippets that call tools and `final_answer(...)`; the workflow benefits from variables, loops, or intermediate code state. | Python code parsed from code blocks and executed by a Python executor. |
| `ToolCallingAgent` | The model/provider supports native tool calls or you want JSON-like function calls instead of generated code. | `ChatMessage.tool_calls` or parsed tool-call JSON. |
| `MultiStepAgent` | You are subclassing or reasoning about shared run behavior. Direct user workflows usually instantiate `CodeAgent` or `ToolCallingAgent`. | Abstract ReAct loop shared by both concrete agents. |

Both concrete agents inherit shared `MultiStepAgent` behavior: tools, model, memory, managed agents, callbacks, planning, final-answer checks, logging, `run()`, `save()`, `to_dict()`, `from_dict()`, `from_folder()`, `from_hub()`, and `push_to_hub()`.

## Shared Constructor Parameters

`MultiStepAgent` shared parameters available through `CodeAgent` and `ToolCallingAgent` include:

```python
agent = CodeAgent(
    tools=[],
    model=model,
    max_steps=20,
    add_base_tools=False,
    managed_agents=[],
    step_callbacks=None,
    planning_interval=None,
    name=None,
    description=None,
    provide_run_summary=False,
    final_answer_checks=[],
    return_full_result=False,
)
```

Important shared decisions:

- `tools`: list of `Tool` instances; `final_answer` is automatically present unless a custom final-answer tool is provided.
- `model`: model object with `generate(...)`; streaming also requires `generate_stream(...)`.
- `max_steps`: maximum action steps before the agent asks the model to synthesize a final answer from memory.
- `managed_agents`: list of agents callable like tools by the manager; each must have a valid Python-identifier `name` and a `description`.
- `step_callbacks`: either a list registered for `ActionStep` or a mapping from memory step classes such as `PlanningStep` to callback(s).
- `planning_interval`: `None` disables explicit planning; an integer runs a planning step at step 1 and then every interval.
- `final_answer_checks`: functions called as `check(final_answer, memory, agent=agent)`; failures are logged into memory and the run continues until a valid final answer or `max_steps`.
- `return_full_result`: controls whether `run()` returns only output or a `RunResult` unless overridden per call.

## CodeAgent-Specific Parameters

```python
agent = CodeAgent(
    tools=[],
    model=model,
    additional_authorized_imports=["math"],
    planning_interval=3,
    executor_type="local",
    executor_kwargs={},
    max_print_outputs_length=2000,
    stream_outputs=False,
    use_structured_outputs_internally=False,
    code_block_tags=None,
)
```

Key points:

- `additional_authorized_imports` augments the import allowlist for generated code. Use precise package names; wildcard imports are powerful and should be treated as a security decision.
- `executor_type` accepts `local`, `blaxel`, `e2b`, `modal`, or `docker`, but executor setup and sandboxing trade-offs belong to `execution-and-safety`.
- Remote code execution does not support managed agents in this version; combine managed agents with local execution only.
- `stream_outputs=True` requires the model to implement `generate_stream(...)`.
- `use_structured_outputs_internally=True` switches to structured code-generation prompts.
- `code_block_tags="markdown"` uses Markdown Python fences; a tuple can provide custom open/close tags; default prompts expect XML-like code tags.

## ToolCallingAgent-Specific Parameters

```python
agent = ToolCallingAgent(
    tools=[],
    model=model,
    planning_interval=None,
    stream_outputs=False,
    max_tool_threads=None,
)
```

Key points:

- The model should return `ChatMessage.tool_calls` or be parseable by `model.parse_tool_calls(...)`.
- `tools_and_managed_agents` combines normal tools and managed agents for model tool selection.
- Multiple tool calls in one model message are executed in parallel through a thread pool; `max_tool_threads` limits concurrency.
- Returning a final answer together with other tool calls, or returning multiple final answers in one action, raises an execution error and the agent can retry.

## `run()` Behavior

```python
result = agent.run(
    task="Solve the user task",
    stream=False,
    reset=True,
    images=None,
    additional_args=None,
    max_steps=None,
    return_full_result=None,
)
```

- `stream=False`: executes internally and returns the final output or `RunResult`.
- `stream=True`: returns a generator; iterate it to execute the run. Yields model stream deltas, tool calls, tool outputs, `ActionStep`, `PlanningStep`, and final-answer step objects depending on agent type and configuration.
- `reset=True`: clears prior memory and monitor metrics before adding the new task.
- `reset=False`: preserves memory for continuation/resume workflows.
- `additional_args`: updates `agent.state` and appends a note to the task telling the agent which variables are available.
- `max_steps`: per-run override of the constructor default.
- `return_full_result`: per-run override of the constructor default.

When `return_full_result=True`, the returned `RunResult` has:

- `output`: final answer.
- `state`: usually `success`, or `max_steps_error` when the last memory error is max-step exhaustion.
- `steps`: serializable dictionaries from `agent.memory.get_full_steps()`.
- `token_usage`: total input/output tokens when every action/planning step has usage, otherwise `None`.
- `timing`: run start/end/duration.

## Memory Objects

`agent.memory` is an `AgentMemory` with:

- `system_prompt`: a `SystemPromptStep` regenerated from current prompt templates when a run starts.
- `steps`: ordered `TaskStep`, `PlanningStep`, and `ActionStep` entries.
- `get_succinct_steps()`: step dictionaries excluding `model_input_messages`.
- `get_full_steps()`: full step dictionaries including model input messages.
- `return_full_code()`: concatenated code actions from `CodeAgent` action steps.
- `replay(logger, detailed=False)`: pretty replay; `agent.replay(detailed=True)` calls it with the agent logger.

Useful step fields include `step_number`, `model_output`, `tool_calls`, `code_action`, `observations`, `action_output`, `error`, `token_usage`, `timing`, and `is_final_answer`.

## Serialization APIs

Use these APIs for agent-level serialization:

```python
agent.save("agent_bundle")
reloaded = CodeAgent.from_folder("agent_bundle", planning_interval=5)
agent_dict = agent.to_dict()
clone = CodeAgent.from_dict(agent_dict, max_steps=10)
```

`save(output_dir)` writes a self-contained agent bundle containing:

- `agent.json`
- `prompts.yaml`
- `requirements.txt`
- `app.py`
- `tools/` code files
- `managed_agents/` bundles when present

`from_folder(folder, **kwargs)` reloads the bundle and lets `kwargs` override constructor values such as `planning_interval` or `max_steps`. `from_dict(...)` uses registered model and agent class names; unknown model or agent classes raise helpful `ValueError`s.

`from_hub(repo_id, trust_remote_code=True, **kwargs)` loads an agent from a Hub Space snapshot and delegates to `from_folder()`. It requires `trust_remote_code=True` because downloaded code is executed locally.

`push_to_hub(repo_id, private=None, token=None, create_pr=False)` uploads the saved agent bundle to a Hub Space. Authentication, repository permissions, and network policy are outside this sub-skill.

Serialization caveats:

- `to_dict()` logs that `step_callbacks` and `final_answer_checks` are ignored; recreate them manually after loading.
- Tool initialization parameters may not all round-trip through generated tool code.
- `CodeAgent.to_dict()` includes authorized imports, executor type, executor kwargs, and print-output length.
- Managed agents are serialized recursively.
