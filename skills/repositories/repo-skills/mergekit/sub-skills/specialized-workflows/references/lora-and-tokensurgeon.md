# LoRA Extraction and Tokenizer Transplantation

## PEFT-compatible LoRA extraction

Use this route when a fine-tuned checkpoint and its base checkpoint are both
available and the desired artifact is an adapter rather than a full merged
model.

```bash
mergekit-extract-lora \
  --model FINETUNED_MODEL \
  --base-model BASE_MODEL \
  --out-path ADAPTER_DIR \
  [--max-rank R] \
  [--distribute-scale | --no-distribute-scale] \
  [--embed-lora | --no-embed-lora] \
  [--save-module MODULE]... \
  [-e REGEX]... [-i REGEX]... \
  [--sv-epsilon EPSILON] [--skip-undecomposable] \
  [common options]
```

`--model`, `--base-model`, and `--out-path` are required. The inspected
defaults are `--max-rank 128`, scale distribution enabled, embedding extraction
disabled, and `--sv-epsilon 0`. The command computes model-minus-base task
vectors and uses SVD. The effective per-module rank is bounded by `max-rank`
and can be reduced by `sv-epsilon`; the generated config records rank/alpha
patterns. `--distribute-scale` splits singular-value scale between A and B;
turn it off only when the consuming PEFT convention requires the scale on one
side.

Use `--include-regex` to limit extraction and `--exclude-regex` to omit matching
module names. If both are present, a module must pass include and not match
exclude. `--save-module MODULE` writes selected modules at full rank rather
than LoRA-decomposing them. `--embed-lora` extracts embedding weights as LoRA
weights; if fine-tuned and base vocabulary sizes differ, the inspected planner
turns this off and warns, so use `modules_to_save`/`--save-module` or resolve
the vocabulary mismatch instead. `--skip-undecomposable` skips optional
weights that cannot be decomposed; without it, an undecomposable required
weight stops the run.

The adapter directory contains safe-serialized `adapter_model` output (unless
serialization is explicitly changed), `adapter_config.json`, and a generated
`README.md` recording base/model provenance and invocation. It is intended for
PEFT-style loading against the matching base architecture. It is not a
standalone model and does not replace model IO or architecture validation.

Prerequisites are both readable, architecture-compatible model references,
Transformers config/class resolution, matching or intentionally handled
vocabularies, enough memory for SVD, and any approved optional LoRA merge or
quantization extras referenced by the model. Refuse to run when either side is
missing, the output collides with a source, or the base revision is not pinned
for a reproducible artifact. Route architecture, remote-code, and resource
errors to [model-io-and-architecture](../../model-io-and-architecture/SKILL.md).

## Tokenizer transplantation

Use this route when the base model's weights should operate with the donor
model's tokenizer vocabulary and token IDs. The command is:

```bash
mergekit-tokensurgeon MODEL DONOR OUT_PATH \
  [--k K] [--cosine-similarity | --no-cosine-similarity] \
  [--approximation-method METHOD] [--weight-scheme SCHEME] \
  [--subword-method METHOD] [--batch-size N] \
  [--prefix-match MODE] [--byte-match MODE] \
  [--magikarp | --no-magikarp] \
  [--new-vocab-noise FLOAT] [--new-vocab-scale FLOAT] \
  [common options]
```

`MODEL`, `DONOR`, and `OUT_PATH` are required positionals. The output keeps
base non-embedding weights, reconstructs input embeddings and language-model
head rows in donor vocabulary order, updates the base config vocabulary size,
and saves the donor tokenizer. The operation is experimental and can change
model behavior; it is not a simple row copy for donor-only tokens.

### Exact approximation choices

The CLI choice set is:

- `omp` (default): sparse Orthogonal Matching Pursuit over shared-vocabulary
  embeddings, up to `--k` neighbors/coefficients.
- `common_interpolation`: nearest shared tokens with
  `--weight-scheme` `distance_proportional`, `barycentric`, or `least_squares`;
  `--cosine-similarity` changes neighbor distance.
- `subword`: tokenize donor-only tokens with the base tokenizer and combine
  pieces using `--subword-method` `mean`, `sum`, `weighted_mean`, or
  `first_last`.
- `landmark_pca`: map donor embedding space through shared-token landmarks.
- `stb`: sparse token-basis transfer; it requires a usable shared basis.
- `mp_rope`: matching pursuit with RoPE-aware model config parameters.
- `john_hewitt`: sample from the base embedding distribution; covariance
  failure falls back to small random noise.
- `mean`, `zero`, `randn`: simple fallback initializations, with the expected
  quality trade-off and no learned alignment.

The inspected CLI defaults are `--k 64`, Euclidean neighbor search,
`--batch-size 512`, no prefix or byte matching, no Magikarp filter, and no
noise/scale override. `--prefix-match` and `--byte-match` each accept
`no`, `yes`, `embed`, or `lm_head`, allowing the shortcut for both matrices or
one matrix only. `--magikarp` removes poorly trained tokens from the shared
basis and zero-initializes tokens classified as junk. `--batch-size -1` disables
batching; use a bounded positive value under memory pressure.

### Prerequisites and stop conditions

Both model and donor must expose readable tokenizer files, compatible model
architecture metadata, input embeddings, and language-model head tensors unless
the architecture marks one optional. A donor-only vocabulary with no shared
vocabulary can make OMP/interpolation/PCA/STB ill-posed; choose a documented
fallback (`subword`, `mean`, `zero`, or `randn`) only after accepting its risk.
`mp_rope` additionally needs compatible attention-head and RoPE config values.
Check donor token IDs against embedding row counts: out-of-range donor IDs are
skipped/zeroed with warnings and are not a successful transplant.

Keep output separate from both sources. Do not use `--allow-crimes` to bypass
an architecture mismatch, and do not grant `--trust-remote-code` or Hub access
without an explicit network/credential decision. Validate tokenizer length,
special-token IDs, embedding/head row counts, and a tiny encode/decode or
forward fixture after a permitted run. For shared tokenizer field semantics in
ordinary YAML merges, route to [merge-configs](../../merge-configs/SKILL.md),
not here.
