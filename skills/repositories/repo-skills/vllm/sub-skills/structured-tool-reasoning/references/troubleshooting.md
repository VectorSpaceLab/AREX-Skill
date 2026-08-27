# Structured Tool Reasoning Troubleshooting

Use this guide when structured outputs, tool calls, reasoning fields, or streaming parser behavior do not match expectations.

## Fast Symptom Map

| Symptom | Likely cause | First check |
| --- | --- | --- |
| Server rejects structured request | Bad request shape, deprecated `guided_*` field, unsupported schema keyword | Run `python scripts/validate_structured_request.py --input request.json` |
| JSON output violates expected fields | JSON object mode or weak prompt used instead of JSON schema | Use `response_format.type=json_schema` with explicit `required` |
| Backend compilation fails | Unsupported JSON Schema keyword, recursive schema, invalid grammar/regex | Simplify schema or grammar; try backend `auto`/`xgrammar` |
| No `tool_calls` under `tool_choice="auto"` | Missing server flags, parser mismatch, template incompatibility, model chose text | Check `--enable-auto-tool-choice`, parser, chat template, prompt |
| Tool arguments malformed | Auto mode without strict schema constraints or weak model format | Add `strict: true`, strict schema style, or use named/required choice |
| Streaming tool call JSON parse fails | Arguments arrive in chunks | Accumulate `delta.tool_calls[].function.arguments` before `json.loads` |
| No `reasoning` field | Wrong parser, thinking disabled, model lacks reasoning format, old field name | Check `--reasoning-parser`, template kwargs, `message.reasoning` |
| Structured outputs ignored with reasoning | Reasoning text remains in content or structured output disabled in reasoning mode | Use compatible parser and `enable_in_reasoning=True` when needed |

## Local Request Validation

Before contacting a server, validate user-provided request fragments:

```bash
python scripts/validate_structured_request.py --input request.json
python scripts/validate_structured_request.py --json '{"response_format":{"type":"json_object"}}'
python scripts/validate_structured_request.py --example unsupported-schema
python scripts/validate_structured_request.py --example tool-streaming
```

Expected result format:

```text
OK: request shape looks usable
WARN: ...
ERROR: ...
```

The helper is intentionally conservative: warnings identify common vLLM/backend risks that may still run in a specific environment.

## Unsupported Schema Keywords

High-risk keywords for structured outputs and tool schemas include:

- Recursive `$ref` graphs or self-referential schemas.
- `patternProperties` and complex property-name constraints.
- Deep or ambiguous `anyOf`, `oneOf`, and `allOf` unions.
- `multipleOf` and backend-specific numeric/string validation keywords.
- Tight `minLength`/`maxLength` requirements combined with complex generation.

Repair strategy:

1. Reduce to `type`, `properties`, `items`, `required`, `enum`, and `additionalProperties: false`.
2. Move semantic validation into application code after generation.
3. Use nullable types for optional tool fields, for example `{"type": ["string", "null"]}`.
4. Add prompt text describing the fields so model intent aligns with the constrained grammar.
5. Reintroduce constraints one at a time under the target backend.

## Invalid Grammar or Regex

For grammar failures:

- Confirm the root production is named as expected by the backend, commonly `root` in EBNF examples.
- Quote literal spaces intentionally; missing spaces can make valid-looking SQL or DSL examples impossible.
- Start with a one-rule grammar and add branches incrementally.
- Avoid mixing Lark-style and EBNF-style grammar syntax unless the selected backend explicitly supports it.

For regex failures:

- Remember dialect differences: `xgrammar`, `guidance`, and `outlines` follow Rust-style regex behavior, while `lm-format-enforcer` follows Python `re` behavior.
- Anchor and simplify the regex.
- Add `stop` when the regex is intended to end at a newline or delimiter.
- Test the pattern outside vLLM only as a rough check; backend dialect can still differ.

## Wrong Backend or Missing Dependencies

Structured-output serving defaults to backend `auto`. Use explicit backend flags only with a reason:

```bash
vllm serve <model> --structured-outputs-config.backend xgrammar
```

Troubleshooting backend choices:

- If a request works under `auto`, do not force a backend.
- If `lm-format-enforcer` returns incomplete JSON in a workload, try `xgrammar` or simplify the schema; source tests note intermittent incomplete JSON for some model/backend combinations.
- If a backend import fails, install the backend dependency in the user's deployment environment; do not bake local environment paths into skill instructions.
- If reasoning and structured outputs conflict, use a reasoning-compatible parser/backend and enable structured outputs in reasoning mode when applicable.

## Parser Name Mismatch

Tool and reasoning parser names are exact IDs. Mismatch signs:

- Server start fails with unknown parser.
- Responses contain raw tool syntax in `content` instead of `tool_calls`.
- `reasoning` is empty while raw `<think>`-style text appears in `content`.
- Streaming emits content chunks but no tool-call deltas.

Repair:

1. Match parser ID to model family from [tool-calling.md](tool-calling.md) or [reasoning-parsers.md](reasoning-parsers.md).
2. Confirm the model's tokenizer/chat template uses the same tool-call format as the parser.
3. Try a minimal single-tool request before debugging multi-tool or parallel calls.
4. Try non-streaming before streaming to separate parser extraction from chunk assembly.

## Chat Template Incompatible with Tool Calling

A parser cannot compensate for a template that does not serialize tools or previous tool messages correctly.

Signals:

- Auto tool calling returns ordinary assistant text.
- Follow-up requests after tool execution fail because prior assistant/tool messages are not formatted as expected.
- Named/required tool choice works but auto mode does not.
- Model emits the wrong syntax for the selected parser.

Repair:

- Use the model's built-in tool template when available, including `--chat-template tool_use` for tokenizers that expose a tool-use template.
- Provide a deployment-owned custom chat template if needed.
- Keep parser and template from the same model family.
- Do not reference original repository example-template paths from runtime instructions; copy/adapt templates into the user's deployment if they are required.

## Streaming Tool Calls Parsed as Complete Calls

Streaming tool calls are deltas. Names and IDs can appear once, while arguments arrive over many chunks. Some chunks have only argument text and no function name.

Bad pattern:

```python
for chunk in stream:
    json.loads(chunk.choices[0].delta.tool_calls[0].function.arguments)
```

Good pattern:

```python
calls = {}
for chunk in stream:
    for piece in chunk.choices[0].delta.tool_calls or []:
        key = piece.id or str(piece.index)
        state = calls.setdefault(key, {"name": None, "arguments": ""})
        if piece.function and piece.function.name:
            state["name"] = piece.function.name
        if piece.function and piece.function.arguments:
            state["arguments"] += piece.function.arguments
```

Only parse `state["arguments"]` after the stream finishes or after application-specific completion detection.

## Reasoning Content Not Requested or Not Returned

Checklist:

- Server started with `--reasoning-parser <matching-parser>`.
- Client uses Chat Completions, Responses, or Anthropic Messages; reasoning is not a generic text-completions field.
- Model actually emits reasoning tokens and thinking is enabled for that model family.
- Client checks `message.reasoning`, not the deprecated `reasoning_content` field.
- Streaming code uses `getattr(delta, "reasoning", None)` for client compatibility.
- If tools are also enabled, tool calls are parsed from content, not reasoning.

## Combining Structured Outputs, Tools, and Reasoning

When multiple features interact, isolate layers:

1. Run a minimal non-streaming structured-output request without tools or reasoning.
2. Run a minimal non-streaming tool request without reasoning.
3. Run a minimal reasoning request without tools or structured output.
4. Combine reasoning with structured output and verify `reasoning` is separated from final constrained `content`.
5. Combine reasoning with tools and verify reasoning chunks are separate from `tool_calls`.
6. Add streaming last and accumulate deltas by field.

## Hardware-Gated Verification

Model-backed verification requires user-provided models, weights, and hardware. CPU/precompiled inspection can prove public imports, CLI help, and function signatures, but it does not prove GPU serving quality, decoding throughput, or a specific model's tool-use behavior.

## Hard Usability Cases for Verification Planning

- Unsupported schema repair: given a schema with `anyOf`, recursive references, and `patternProperties`, a future agent should simplify it into a vLLM-compatible JSON schema, run the bundled validator, and explain which validation moved to application code.
- Streaming no-tool-calls triage: given a streaming client that reads only the first chunk and a server command missing `--enable-auto-tool-choice`, a future agent should identify the missing flag, parser/template checks, and fix chunk accumulation without running a model.
