# Configuration contract

This reference is the compact authoring contract for the installed mergekit
0.1.4 configuration model. The YAML CLI reads the document with safe YAML
loading and validates it as `MergeConfiguration`; this validation does not
fetch model files.

## Choose exactly one topology

Every top-level document needs `merge_method` and exactly one of `models`,
`slices`, or `modules`.

### Whole-model input

Use `models` when every input contributes its complete architecture. Each entry
has a `model` reference and optional per-model `parameters`:

```yaml
merge_method: linear
models:
  - model: org/model-a@revision
    parameters: {weight: 0.6}
  - model: ./model-b
    parameters: {weight: 0.4}
dtype: bfloat16
```

A model reference can be a local path, a Hub-style path, or a path with one
`@revision` suffix. Reference parsing is not the same as checking that files
exist; route resolution, revisions, architecture, and trust decisions to the
model/IO sibling.

`base_model` is a separate optional reference. For methods that need a base,
include it in `models` when practical. If it is declared but absent from a
whole-model `models` list, mergekit normalizes the configuration by adding the
base as an input with no per-model settings.

### Layer slices

Use `slices` for a single-module layer assembly. Each output slice contains
same-length `sources`; each source has `model` and a half-open `layer_range`
`[start, end]`:

```yaml
merge_method: passthrough
slices:
  - sources:
      - model: ./model-a
        layer_range: [0, 12]
      - model: ./model-b
        layer_range: [12, 24]
    parameters:
      scale: 1.0
```

All sources in one output slice must contribute the same number of layers.
`OutputSliceDefinition` also accepts `base_model`, `residual_weight`, and
`parameters`. A slice-level base overrides the top-level base while planning
that slice. Numeric gradients use the output layer position, not the absolute
source layer index.

For an architecture with more than one configured module, route to explicit
`modules` rather than relying on top-level `slices`.

### Explicit modules

Use `modules` when the output architecture has multiple independently planned
modules or when each module needs a different source layout:

```yaml
merge_method: linear
modules:
  language_model:
    models:
      - model: ./model-a
        parameters: {weight: 0.5}
      - model: ./model-b
        parameters: {weight: 0.5}
  vision_tower:
    slices:
      - sources:
          - model: ./model-a
            layer_range: [0, 8]
```

Each module definition must contain exactly one of `models` or `slices` and
may have its own `parameters`. The module names must match the architecture's
known module names; unknown names are an architecture/IO issue, not a method
configuration issue.

## Parameter resolution

The planner asks the selected method for global and per-tensor parameters.
For a tensor in a slice, `ConfigReader.parameter` resolves the first usable
value in this order:

1. the matching source's `parameters` (only for that model/source);
2. the output slice's `parameters`;
3. the containing module's `parameters`;
4. top-level `parameters`;
5. the method's default, or an error when the method marks it required.

For a top-level `models` list, mergekit normalizes each model into a full-layer
source, so its `models[].parameters` participate at level 1. A source-specific
value therefore beats a slice, module, or global value. A base model's missing
required per-model setting is allowed in planner calls because the base is not a
non-base task vector; other required values must be supplied.

Global settings such as `normalize`, `t`, `lambda`, or `select_topk` are looked
up without a model. Per-model settings such as `weight`, `density`, `gamma`,
`epsilon`, or `scale` are looked up with that model. Do not place a value only
at a level that the selected method never requests; unsupported keys can be
silently irrelevant to the method.

## Conditional filters and gradients

A setting may be a scalar, a numeric list, or an ordered list of conditional
objects:

```yaml
parameters:
  t:
    - filter: self_attn
      value: [0.0, 0.5, 0.3, 0.7, 1.0]
    - filter: mlp
      value: [1.0, 0.5, 0.7, 0.3, 0.0]
    - value: 0.5
```

Rules:

- Numeric lists are linearly interpolated over `t` from the first to last
  element. For a slice with more than one output layer, `t` is its normalized
  position from 0 to 1; a one-layer slice uses `t = 1`.
- Conditional entries are checked in order. A missing filter or `*` matches;
  otherwise a filter matches when it is a substring of the tensor name. The
  first matching conditional value wins.
- A conditional list with no match yields no value at that precedence level,
  allowing a lower level or method default to apply. Always include an
  unfiltered fallback when a method requires the value.
- A list of scalar non-numeric values is selected discretely by the integer
  position derived from `t`; prefer numeric gradients for interpolation.
- Filters are evaluated against the tensor name, not a friendly layer label.
  Use stable fragments such as `self_attn`, `mlp`, `o_proj`, or `lm_head`, and
  verify that a fallback covers every other tensor.

The `models` example below combines a density gradient and a filtered weight:

```yaml
models:
  - model: ./a
    parameters:
      density: [1.0, 0.7, 0.1]
      weight: 1.0
  - model: ./b
    parameters:
      density: 0.5
      weight:
        - filter: mlp
          value: 0.5
        - value: 0.0
merge_method: ties
base_model: ./base
parameters:
  normalize: true
  int8_mask: true
```

## Dtype and output fields

- `dtype` is the input/gather dtype used while loading tensors and is also the
  fallback `torch_dtype` written into the output model config.
- `out_dtype`, when set, converts tensors at save time and takes precedence over
  `dtype` in the output config. Use a name accepted by the installed torch
  dtype parser, such as `float32`, `float16`, or `bfloat16`.
- A force dtype declared by an architecture weight can override both for that
  tensor. Do not use `out_dtype` to solve an architecture mismatch.
- `parameters` is the merge-method parameter map, not a model-reference map.
  Tokenizer configuration is separate under `tokenizer`.

## CLI and output policy

The exact entry point is:

```text
mergekit-yaml CONFIG_FILE OUT_PATH [OPTIONS]
```

The command writes model shards and a model config. By default it uses safe
`safetensors` serialization, copies or builds a tokenizer when configured (or
copies a donor tokenizer when `--copy-tokenizer` remains enabled), and writes a
model card plus `mergekit_config.yml` when `--write-model-card` is enabled.
`--no-safe-serialization`, `--no-copy-tokenizer`, and
`--no-write-model-card` are explicit opt-outs with downstream compatibility
costs.

Before executing, validate without downloads:

```text
python scripts/validate_merge_config.py CONFIG.yml  # from this sub-skill directory
# or: python sub-skills/merge-configs/scripts/validate_merge_config.py CONFIG.yml  # from skill root
```

Then run the merge only after method counts, references, dtype, tokenizer, and
resource flags have been reviewed.

## Authoring checklist

- Exactly one topology is populated.
- Every slice source has a model and equal-length layer range within its model.
- `merge_method` is one of the registered names in `merge-methods.md`.
- Required global and per-model parameters are present at an effective level.
- Conditional lists have an ordered fallback and use valid tensor-name filters.
- `base_model` satisfies the selected method and is available to the merge.
- Exactly one tokenizer style is used.
- `dtype` and `out_dtype` are intentional and serialization is safe by default.
- The output directory is new or intentionally replaceable, and the run command
  records the chosen device/backend flags.
