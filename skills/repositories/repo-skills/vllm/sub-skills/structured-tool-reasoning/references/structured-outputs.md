# Structured Outputs in vLLM

Use structured outputs when the user needs vLLM to constrain generated text to a known shape. vLLM supports this through OpenAI-compatible request fields for serving and `SamplingParams(structured_outputs=StructuredOutputsParams(...))` for offline inference.

## Request Surfaces

### OpenAI-compatible chat/completions

For Chat Completions, pass constraints either through `response_format` or through `extra_body={"structured_outputs": ...}` in the OpenAI Python client.

JSON schema through `response_format`:

```python
completion = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Return one car as JSON."}],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "car-description",
            "schema": {
                "type": "object",
                "properties": {
                    "brand": {"type": "string"},
                    "model": {"type": "string"},
                    "car_type": {"type": "string", "enum": ["sedan", "SUV", "Truck", "Coupe"]},
                },
                "required": ["brand", "model", "car_type"],
                "additionalProperties": False,
            },
        },
    },
)
print(completion.choices[0].message.content)
```

Other constraints through `structured_outputs`:

```python
completion = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Classify the sentiment: vLLM is wonderful!"}],
    extra_body={"structured_outputs": {"choice": ["positive", "negative"]}},
)

completion = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Generate one example .com email."}],
    extra_body={"structured_outputs": {"regex": r"[a-z0-9.]{1,20}@\w{3,20}\.com\n"}, "stop": ["\n"]},
)
```

### OpenAI-compatible completions

The same `extra_body={"structured_outputs": ...}` shape is used for Completions. Prefer Chat Completions for tool calling and reasoning because those fields are chat/response-oriented.

### Offline inference

Offline inference uses `StructuredOutputsParams` inside `SamplingParams`:

```python
from vllm import LLM, SamplingParams
from vllm.sampling_params import StructuredOutputsParams

llm = LLM(model="HuggingFaceTB/SmolLM2-1.7B-Instruct")
sampling_params = SamplingParams(
    max_tokens=64,
    structured_outputs=StructuredOutputsParams(
        json={
            "type": "object",
            "properties": {"answer": {"type": "string"}},
            "required": ["answer"],
            "additionalProperties": False,
        }
    ),
)
outputs = llm.generate("Return a JSON answer for: 2 + 2", sampling_params)
print(outputs[0].outputs[0].text)
```

Installed public API facts confirm `vllm.LLM(..., structured_outputs_config=None, ...)` and `SamplingParams(..., structured_outputs=..., thinking_token_budget=..., ...)` are valid surfaces. GPU/model execution remains hardware-gated.

## Constraint Types

- `choice`: output must be exactly one of the listed strings. Good for labels, routing decisions, and enums.
- `regex`: output must match a regex accepted by the selected backend. Regex dialect differs by backend.
- `json`: output must follow a JSON schema. Prefer this for objects, arrays, typed fields, and enum constraints.
- `grammar`: output must follow a context-free grammar, typically EBNF-style for supported backends.
- `structural_tag`: output must place a schema-constrained JSON object between configured begin/end tags. This is also used internally by strict tool calling for parsers with structural-tag support.

Deprecated pre-v0.12 request fields such as `guided_json`, `guided_regex`, `guided_choice`, `guided_grammar`, `guided_whitespace_pattern`, `structural_tag`, and `guided_decoding_backend` should be migrated to `structured_outputs` or `StructuredOutputsParams`.

## JSON Schema Guidance

Use a small, explicit schema:

```json
{
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "age": {"type": "integer"},
    "skills": {"type": "array", "items": {"type": "string"}}
  },
  "required": ["name", "age", "skills"],
  "additionalProperties": false
}
```

Practical rules:

- Include `type`, `properties`, `required`, and `additionalProperties: false` for objects.
- Keep schemas shallow when possible; deeply nested schemas increase compilation cost and model burden.
- Put the desired schema and examples in the prompt as well as in `response_format`; constraints guarantee syntax more than semantic quality.
- For strict tool-call schemas, mark all properties as required and represent optional fields with nullable types such as `{"type": ["string", "null"]}`.
- If using Pydantic, pass `MyModel.model_json_schema()` rather than handwritten schema when possible, then review the generated keywords for backend compatibility.

Common high-risk keywords include recursive references, `patternProperties`, complex `anyOf`/`oneOf`/`allOf`, `multipleOf`, and tight string length constraints. If generation fails or backend compilation rejects the schema, simplify to primitive `type`, `enum`, `properties`, `items`, `required`, `additionalProperties`, and basic numeric bounds first.

## JSON Object vs JSON Schema

Use `response_format={"type": "json_schema", ...}` when exact keys and types matter. Use a JSON-object style only when the user only needs syntactically valid JSON and can validate fields later. JSON object mode does not replace schema validation by the application.

## Regex Guidance

Backend regex dialects differ:

- `xgrammar`, `guidance`, and `outlines` use Rust-style regex behavior.
- `lm-format-enforcer` uses Python `re` behavior.

Keep regex constraints anchored and simple. Add `stop` tokens if the regex intentionally ends with a delimiter such as a newline.

## Grammar Guidance

A minimal grammar:

```text
root ::= select_statement
select_statement ::= "SELECT " column " from " table " where " condition
column ::= "col_1 " | "col_2 "
table ::= "table_1 " | "table_2 "
condition ::= column "= " number
number ::= "1 " | "2 "
```

Troubleshoot grammar failures by reducing to one production, confirming the root rule name, using explicit spaces, and adding branches back one at a time.

## Backend Selection

Serving supports `--structured-outputs-config.backend`; the default is `auto`. Source and tests show common backends include `xgrammar`, `guidance`, `lm-format-enforcer`, and `outlines`, with `xgrammar` commonly used as the default-capable backend. Choose explicitly only when needed:

```bash
vllm serve <model> --structured-outputs-config.backend xgrammar
```

Backend implications:

- `auto`: easiest default; lets vLLM choose based on request details.
- `xgrammar`: strong default for JSON, regex, grammar, structural tags, and reasoning-aware structured output support.
- `guidance`: useful alternative for supported regex/grammar/JSON cases.
- `lm-format-enforcer`: can be useful but tests note intermittent incomplete JSON in some scenarios.
- `outlines`: present in structured-output test coverage but may be backend/version dependent.

Do not promise that every JSON Schema keyword works on every backend. Validate the request shape locally with `scripts/validate_structured_request.py`, then run a model-backed smoke only in the user's target environment.

## Structured Outputs with Reasoning

Reasoning models can be used with structured outputs when the server is started with a compatible reasoning parser. For some models, reasoning must be separated into the `reasoning` field or structured output may be skipped/disabled. For Qwen3 Coder reasoning mode, explicitly enable structured outputs in reasoning mode when needed:

```bash
vllm serve <model> \
  --reasoning-parser qwen3 \
  --structured-outputs-config.enable_in_reasoning=True
```

See [reasoning-parsers.md](reasoning-parsers.md) for parser names and thinking controls.

## Quick Validation Checklist

- Request uses exactly one primary constraint path: `response_format` JSON schema or `structured_outputs` constraint, unless intentionally combining with tools/reasoning.
- JSON schema has `type: object`, explicit `properties`, `required`, and `additionalProperties: false` for object outputs.
- Regex and grammar are small enough to debug and match the chosen backend dialect.
- Deprecated `guided_*` fields are not used.
- Server backend is `auto` unless the user has a concrete backend reason.
- Model-backed tests are marked hardware/model-download gated.
