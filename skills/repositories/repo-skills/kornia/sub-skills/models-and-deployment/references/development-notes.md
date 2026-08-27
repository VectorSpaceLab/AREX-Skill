# Development Notes For Model And Deployment Work

Use this reference when modifying or extending Kornia model/deployment surfaces.
It is written for future repository work, not for ordinary inference usage.

## Public API obligations

When adding or changing a public model, builder, config, processor, deployment
helper, or application wrapper:

1. Add a public docstring with input shapes, output shapes, dtype/device
   expectations, pretrained/download behavior, and failure modes.
2. Add the symbol to the matching generated Sphinx documentation page for its
   package section, with an `autoclass` or `autofunction` entry.
3. If the model is also a high-level application workflow, update the matching
   application documentation with a minimal no-download or clearly
   download-marked example.
4. If the model has pretrained weights, document exactly which calls download,
   what cache/local-checkpoint alternatives exist, and whether weights are
   optional for API shape checks.
5. If the model claims ONNX, CUDA, MPS, half precision, `torch.compile`, or Ivy
   transpilation support, add a targeted verification path for that claim.

## Import and dependency hygiene

- Preserve Kornia's top-level import-order convention: filters and geometry are
  core and must be imported before other convenience modules to avoid circular
  dependencies.
- Keep base package imports limited to base dependencies where possible. Put
  heavy or optional imports behind lazy loaders or local imports.
- Do not make model-class import require a network-only or large optional
  package unless the class cannot function without it.
- Keep `transformers`, `diffusers`, `huggingface_hub`, `safetensors`, ONNX/ORT,
  Ivy, segmentation-model, super-resolution, and tracker extras optional and
  feature-scoped.
- Do not let a default constructor trigger pretrained weights unless the
  documented API already owns that behavior and the caller has chosen a
  high-level application path.

## Config and builder design

Prefer this layering:

1. A config dataclass or `from_name` method for model shape and variant choices.
2. A raw `nn.Module` for tensor-in/tensor-out behavior.
3. A high-level wrapper for preprocessing, postprocessing, visualization, and
   save/export helpers.
4. A builder that combines the raw module and processors while exposing
   `pretrained=False` or an equivalent no-download path.

Make no-download construction explicit in examples. Do not hide a download in a
config constructor.

## Output and visualization contracts

- Separate numerical outputs from visualization outputs.
- Keep raw model outputs as tensors, tuples, dictionaries, or dataclasses with
  explicit shapes.
- Use `visualize(..., output_type="torch"|"pil")` for rendered previews.
- Use `save(...)` only for image-like artifacts and make the output directory an
  explicit caller choice.
- If adding a new `output_type`, update shared conversion utilities and tests;
  do not silently return NumPy arrays from a path documented as torch/PIL only.

## ONNX and deployment contracts

For a new `to_onnx` path, record:

- concrete pseudo-shape used for tracing;
- input and output names;
- dynamic axes;
- opset/IR expectations;
- whether preprocessing/postprocessing are included;
- whether the exported graph is the full model or a subgraph;
- optional package requirements for export and runtime.

Do not claim ONNX Runtime acceleration until the target provider is actually
available. A graph that exports on CPU is not proof that a CUDA, TensorRT, or
OpenVINO provider works.

## `torch.compile` and deployment checks

- `ModelBase.compile(...)` returns a compiled model-like object.
- Some application wrappers mutate internal modules during `compile(...)`
  instead of returning a new wrapper; read the wrapper behavior before relying on
  the return value.
- For prompt pipelines, compilation may cover only tensor-heavy submodules while
  leaving prompt preprocessing uncompiled.
- Always compare eager and compiled outputs with deterministic inputs before
  reporting a compile path as usable.

## Testing shape recommendations

A robust model/deployment change normally needs:

- import smoke tests for configs and classes;
- no-download tensor smokes for raw models or wrappers;
- cardinality tests for each output shape;
- exception tests for invalid shapes, unsupported variants, and bad
  `output_type` values;
- backend-specific tests only where the backend is claimed;
- ONNX export/runtime tests only when the optional packages are installed;
- explicit pretrained tests marked or isolated so they cannot run without
  accepted network/cache access.

## Weight catalog maintenance

When adding a pretrained model or changing a checkpoint:

1. Add a stable model identifier and fallback/local-checkpoint behavior.
2. Ensure no-download examples still use `pretrained=False` or config-only paths.
3. Update the downloader/test catalog used by CI and docs only when the new
   weights are required for doctests or accepted pretrained tests.
4. Make feature-matching weights part of the feature-matching workflow rather
   than the generic model/deployment workflow.
