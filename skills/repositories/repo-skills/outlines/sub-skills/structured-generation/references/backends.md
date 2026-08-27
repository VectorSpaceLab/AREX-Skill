# Structured-generation backends

## Default and selectable backends

Outlines chooses a structured-generation backend only for steerable/local models. The backend name is passed through `Generator(..., backend=...)` or the direct model call.

Verified defaults in this checkout:

- JSON schema -> `outlines_core`
- Regex -> `outlines_core`
- CFG -> `llguidance`

Selectable backends in this source revision:

- `outlines_core`
- `llguidance`
- `xgrammar`

## Compatibility summary

| Backend | Models | JSON schema | Regex | CFG | Notes |
|---|---|---:|---:|---:|---|
| `outlines_core` | Transformers, LlamaCpp, MLXLM | yes | yes | no | Default for JSON schema and regex; cannot handle CFG. |
| `llguidance` | Transformers, LlamaCpp, MLXLM | yes | yes | yes | Default for CFG; rejects `whitespace_pattern`. |
| `xgrammar` | Transformers, MLXLM | yes | yes | yes | Rejects `whitespace_pattern`; does not support LlamaCpp in this revision. |

## When to choose a backend

- Use `outlines_core` for ordinary regex or JSON-schema generation when you do not need CFG.
- Use `llguidance` for CFG, and also when you want a backend that supports all three major structured languages on the local steerable models in this repo.
- Use `xgrammar` when the environment has it and the selected local model is compatible; it is an alternative backend rather than a universal default.

## Important limitations

- `JsonSchema(..., whitespace_pattern=...)` is only valid where the backend explicitly supports whitespace control. If a task needs whitespace control, avoid `llguidance`/`xgrammar`.
- `CFG` is not supported by `outlines_core`.
- Server/black-box providers do not use these backends. Their structured-output logic is provider-specific and belongs in the provider skill.
- Custom `OutlinesLogitsProcessor` instances are only for steerable/local models; provider wrappers do not accept them.

## Validation sequence for a user task

1. Determine the target output language.
2. Decide whether the model is steerable/local or provider/server based.
3. Pick the minimum backend that supports the requested language and model family.
4. Validate the schema/regex/grammar against a concrete sample before generating.
5. Run a tiny generation or parse check only after the structure is known-good.

## Failure patterns and responses

- **`outlines_core` + CFG**: switch to `llguidance` or `xgrammar`.
- **`llguidance`/`xgrammar` + `whitespace_pattern`**: drop the whitespace override or switch to `outlines_core`.
- **Backend mismatch for model family**: check the local-model route, especially when the model is LlamaCpp or MLXLM.
- **Processor already supplied**: do not also pass `output_type`; construct the processor directly and use `Generator(model, processor=...)`.
