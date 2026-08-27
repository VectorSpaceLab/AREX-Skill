# Role-Playing API

The OWL package exports `OwlRolePlaying`, `OwlGAIARolePlaying`, `run_society`,
and `arun_society` from `owl.utils`. They customize CAMEL's role-playing
protocol; they are not a replacement for configuring the underlying model
backend.

## Constructors

`OwlRolePlaying` accepts keyword arguments and forwards the normal CAMEL
role-playing settings to its superclass. OWL-specific values include:

- `task_prompt`: the overall task injected into both system prompts and later
  auxiliary messages.
- `user_role_name` and `assistant_role_name`, defaulting to `user` and
  `assistant`.
- `output_language`, passed to the constructed `ChatAgent`s when set.
- `user_agent_kwargs` and `assistant_agent_kwargs`, each optionally containing
  a model or agent setting. If the parent `model` is present and a child kwargs
  mapping has no model, the parent model is inserted.
- Optional existing `assistant_agent` or `user_agent` objects. Their system
  messages and stop events are reconciled with the OWL settings.

`OwlGAIARolePlaying` keeps the same construction surface but changes the final
response instruction for GAIA: it asks for `<analysis>...</analysis>` and
`<final_answer>...</final_answer>` and emphasizes the exact answer format.

## Synchronous loop

`run_society(society, round_limit=15)` initializes the society with a prompt to
solve the task step by step, then calls `society.step` for at most `round_limit`
iterations. Each record stores user text, assistant text, and serialized tool
calls when available. It accumulates completion and prompt token counts into a
`token_info` mapping and returns `(answer, chat_history, token_info)`.

The loop stops when an assistant or user response is terminated, or when the
user-side response contains `TASK_DONE`. The final answer is the last assistant
message. A zero or missing token count can mean the backend did not return usage
metadata, not that the task used no tokens.

`arun_society` is the asynchronous counterpart and also recognizes the Chinese
completion marker `任务已完成`.

## Message protocol

The custom user system message instructs the user-side agent to emit one
`Instruction: ...` at a time and not to ask questions. The assistant-side agent
must begin with a concrete `Solution: ...`, use available tools, verify results,
and eventually cause `TASK_DONE`. OWL appends task context and reminders after
both sides respond. A custom worker prompt should preserve this role boundary;
do not tell the user-side agent to solve the whole task in one turn.

## Operational checks

- Keep `round_limit` bounded for tests and cost control.
- Inspect `chat_history` when a tool call, termination marker, or final answer
  is missing.
- Use `OwlGAIARolePlaying` only for GAIA-format tasks; route scoring and data
  preparation to [gaia-evaluation](../../gaia-evaluation/SKILL.md).
- A `ValueError` about a missing model/API key occurs during model construction,
  before the society loop can run. Read provider setup first.
