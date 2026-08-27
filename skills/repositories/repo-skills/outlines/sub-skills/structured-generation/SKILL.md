---
name: structured-generation
description: "Design and troubleshoot Outlines constrained-generation output
  types, generators, backends, and logits processors."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Structured Generation

Use this sub-skill when the task is to make an Outlines model return a specific structure: JSON, a Pydantic/dataclass/TypedDict schema, a `Literal`/`Enum`/`Choice`, a regular expression, or a context-free grammar. It also covers the `Generator` contract, backend selection, raw-output parsing, batch/stream behavior, and custom logits processors.

Route model setup elsewhere:

- Local/offline engines, tokenizers, GPU/MPS, and model downloads -> `../local-models/SKILL.md`.
- Hosted/server providers and credentials -> `../remote-providers/SKILL.md`.
- Prompt templates, `Application`, `Chat`, images, and workflow orchestration -> `../prompt-workflows/SKILL.md`.

## Fast Route

1. **Choose the output language.** Use Python types for simple data, `Literal`/`Enum`/`Choice` for finite choices, a Pydantic/dataclass/TypedDict/GenSON/`JsonSchema` for JSON, `Regex` for a regular language, or `CFG` for Lark-style grammars.
2. **Pick a compatible model route.** Local steerable models compile output types into logits processors. Server/black-box providers support only the structured-output formats their SDK/server exposes.
3. **Call directly or reuse a generator.** A model call and a generator call are equivalent in shape:

   ```python
   response = model(prompt, OutputType, max_new_tokens=200)
   generator = outlines.Generator(model, OutputType)
   response = generator(prompt, max_new_tokens=200)
   ```

4. **Parse the raw string yourself.** Outlines v1 returns text. For Pydantic schemas, call `Schema.model_validate_json(response)` after generation.
5. **Set the backend only for steerable models.** Defaults are JSON schema=`outlines_core`, regex=`outlines_core`, CFG=`llguidance`. Override with `backend="llguidance"` or `backend="xgrammar"` only after checking support.
6. **Use a custom processor only with steerable models.** `Generator(model, processor=processor)` is mutually exclusive with `output_type`; server models raise `NotImplementedError` for processors.
7. **Validate before generation.** Check a JSON schema/regex/grammar against representative samples before spending tokens or running a model.

## Load These References

- [`references/api-reference.md`](references/api-reference.md): constructor signatures, output-type conversion rules, direct model calls, `Generator`, batch/stream, and parsing contracts.
- [`references/backends.md`](references/backends.md): default and selectable backends, model compatibility, unsupported cases, and logits-processor flow.
- [`references/workflows.md`](references/workflows.md): schema-first and regex/CFG iteration patterns, Pydantic parsing, and structured workflow recipes.
- [`references/troubleshooting.md`](references/troubleshooting.md): symptoms, causes, and recovery for output-type, backend, parsing, and processor failures.

## Bundled Script

Use [`scripts/validate_structure.py`](scripts/validate_structure.py) for local, no-model validation of JSON samples against JSON Schema or text samples against a regex before you wire the structure into an Outlines call.

Examples:

```bash
python scripts/validate_structure.py json --schema '{"type":"object","required":["name"],"properties":{"name":{"type":"string"}}}' --data '{"name":"Ada"}'
python scripts/validate_structure.py regex --pattern '[0-9]{3}' --text '123'
```

The script does not import provider clients, download models, or call a network service.

## Non-Negotiable Checks

- Never claim a provider supports regex/CFG just because a local model does. Check provider capability first.
- Never use `backend="outlines_core"` for CFG; use `llguidance` or `xgrammar` with a compatible steerable model.
- Never set `JsonSchema(..., whitespace_pattern=...)` with `llguidance` or `xgrammar`; use `outlines_core` if whitespace control is required.
- Never execute model output as code while validating structure. Parse JSON, match regex, or validate with a schema.
- Never tell future agents to open original repository docs/examples/tests; this sub-skill and its bundled references/scripts are the runtime source.
