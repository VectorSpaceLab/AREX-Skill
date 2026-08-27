# Structured-generation troubleshooting

## Import or optional dependency failures

Symptoms:

- `ModuleNotFoundError` for `outlines_core`, `llguidance`, `xgrammar`, `transformers`, `llama_cpp`, `mlx_lm`, or provider SDKs.
- Top-level imports work but a backend/model path fails later.

Actions:

1. Install the base package first: `pip install outlines`.
2. Install only the optional extra required by the selected route, such as `outlines[transformers]`, `outlines[llamacpp]`, `outlines[xgrammar]`, or provider SDK packages.
3. If the failure is a model runtime dependency, route to `../../local-models/SKILL.md` or `../../remote-providers/SKILL.md` rather than broad-installing every extra.

## Unsupported output type

Symptoms:

- Provider says a type is unavailable.
- OpenAI-style providers reject `Regex`, `CFG`, `int`, or `Literal` where only JSON schemas are supported.
- Dottxt requires an output type/model id; TGI rejects CFG.

Actions:

1. Check whether the model is local/steerable or provider/server based.
2. For provider/server models, use the provider matrix before retrying.
3. Convert simple choice or typed output into a JSON schema if the provider only supports JSON mode/schema.
4. If regex/CFG is essential, use a compatible local steerable model or provider that exposes that language.

## Schema generation succeeds but parsing fails

Symptoms:

- `json.JSONDecodeError` or `Pydantic ValidationError` after generation.
- Output is cut off, has extra prose, or omits required keys.

Actions:

1. Remember: Outlines returns raw text. Parse with `Schema.model_validate_json(raw)` only after checking `raw` is complete.
2. Increase `max_new_tokens` or provider-specific token budget.
3. Simplify required fields and remove unsupported JSON Schema keywords for the selected provider.
4. For OpenAI/Mistral strict schema paths, ensure nested object schemas set `additionalProperties: false` when required by the provider adapter.
5. Log the raw string in a safe, non-secret way for debugging; do not execute it.

## Regex does not match real examples

Symptoms:

- Model output is structurally valid but semantically unhelpful.
- Local validation reveals only a prefix matched.
- Regex is too broad, too narrow, or missing anchors.

Actions:

1. Validate with `scripts/validate_structure.py regex`, which uses full-string matching.
2. Keep positive and negative examples near the code/test that constructs the regex.
3. Prefer `Regex(...).matches(sample)` for a quick Outlines-side check.
4. Use the regex DSL for composable structure, but do not obscure the final target language from reviewers.

## CFG/backend mismatch

Symptoms:

- `NotImplementedError: Outlines Core does not support context-free grammar`.
- XGrammar or llguidance errors during grammar compilation.

Actions:

1. Use `backend="llguidance"` or `backend="xgrammar"` for CFG.
2. Check local-model compatibility: XGrammar supports Transformers and MLX-LM in this revision, not LlamaCpp.
3. Keep grammars small, validate them independently, and reduce ambiguous recursion while debugging.

## `whitespace_pattern` failure

Symptoms:

- `llguidance` or `xgrammar` raises that whitespace control is unsupported.

Actions:

- Use the default backend for JSON schema (`outlines_core`) when `JsonSchema(..., whitespace_pattern=...)` is required.
- Or remove `whitespace_pattern` if the model/provider does not need strict whitespace control.

## Custom logits processor failure

Symptoms:

- `ValueError` when both `output_type` and `processor` are passed.
- `NotImplementedError` on a provider/server model.
- Tensor shape/device errors inside `process_logits`.

Actions:

1. Use exactly one of `output_type` or `processor`.
2. Use only local steerable models.
3. Instantiate the processor with `model.tensor_library_name`.
4. Implement `process_logits` so it returns the same tensor-library type and respects 1D/2D logits normalization done by the base processor.
5. If a processor holds state, implement or call `reset()` before reuse.

## Provider-vs-local confusion

Symptoms:

- A recipe works with Transformers but not with OpenAI.
- Streaming or batch works in one wrapper but not another.

Actions:

- Route structure design here, provider capability to `../../remote-providers/SKILL.md`, and local runtime setup to `../../local-models/SKILL.md`.
- Do not assume the feature matrix from one wrapper applies to another.
