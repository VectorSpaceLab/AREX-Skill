# Function Calling and ReAct

## Qwen's function-calling model

The repository implements OpenAI-style function calling by converting tool metadata and message history into a ReAct prompt. The model emits text containing `Action:` and `Action Input:`; the server parser converts that back into an OpenAI-style `function_call` response.

This means function calling is prompt-driven. Validate tool schemas and message order before blaming the model.

## ReAct template essentials

A tool description is rendered like:

```text
{name_for_model}: Call this tool to interact with the {name_for_human} API. What is the {name_for_human} API useful for? {description_for_model} Parameters: {parameters}
```

The instruction uses this loop:

```text
Question: ...
Thought: ...
Action: one of [tool_names]
Action Input: ...
Observation: ...
Thought: I now know the final answer
Final Answer: ...
```

If tool arguments should be JSON, include that requirement in `description_for_model`, for example `Format the arguments as a JSON object.`

## OpenAI-compatible message constraints

The local API server accepts roles `system`, `user`, `assistant`, and `function`, but the converted history must alternate correctly:

- There must be at least one `user` message.
- A `function` role message must follow an `assistant` message that called a function.
- User/assistant history must form complete pairs before the latest user query.
- When `functions` are present, server-side streaming is rejected; use `stream=False`.

## Function schema fields

Useful fields are:

- `name` or `name_for_model`: machine name used in `Action:`.
- `name_for_human`: human-readable tool name.
- `description` or `description_for_model`: include argument formatting rules here.
- `parameters`: list of parameter descriptions with `name`, `description`, `required`, and JSON-schema-like `schema`.

## Fine-tuning samples for function calling

The function-calling fine-tune example does not put `function` role messages in the training data. It embeds the ReAct instruction into user/assistant conversations. Use the validator script to catch accidental function-role samples before passing data to `finetune.py`.

## Hugging Face Agent pattern

The repository's QWenAgent example wraps Qwen as a Transformers Agent. It replaces `Human:` and `Assistant:` with temporary markers before generation to avoid reserved-token conflicts, then maps them back. Preserve this workaround when adapting the pattern to older Qwen checkpoints.
