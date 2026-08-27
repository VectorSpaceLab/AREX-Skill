---
name: mixtral-offloading
description: "Use dvmazur/mixtral-offloading for source-only CUDA/HQQ/Triton
  Mixtral-8x7B expert offloading workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# mixtral-offloading

Use this repo skill when a task involves the `dvmazur/mixtral-offloading`
repository: efficient Mixtral-8x7B inference through mixed HQQ quantization,
Triton matmul kernels, and MoE expert offloading between GPU and CPU memory.

## Read this when

- The user asks to run or adapt the Mixtral offloading demo notebook locally.
- The task names `OffloadConfig`, `QuantConfig`, `build_model`,
  `HQQLinearTritonSavable`, `ExpertCache`, `MixtralExpertWrapper`, or
  `SparseMoeWrapper`.
- The user is debugging CUDA/Triton/HQQ errors in a source-only checkout.
- The user needs a safe smoke check that avoids model downloads and long
  interactive generation.

## First checks

1. This repository is source-only: it has no installable package metadata and no
   CLI. Future agents should install the runtime requirements and add the user's
   checkout root to `PYTHONPATH` before importing `src.*` modules.
2. Actual offloaded inference is a CUDA workflow. CPU-only checks can validate
   imports, config math, and packing helpers, but not Mixtral generation or
   Triton kernel execution.
3. The full demo depends on external Hugging Face model/tokenizer artifacts and
   a quantized safetensors state directory. Do not download large artifacts or
   start an interactive chat loop without explicit approval.

Minimal public setup pattern:

```bash
python -m pip install -r requirements.txt
PYTHONPATH="/path/to/user/mixtral-offloading" python -c "from src.build_model import build_model; print('ok')"
python /path/to/this-skill/scripts/check_environment.py --repo-root /path/to/user/mixtral-offloading --require-cuda
```

Run [scripts/check_environment.py](scripts/check_environment.py) for dependency,
source-import, and optional CUDA checks.

## Route map

- Use [sub-skills/inference-workflow/SKILL.md](sub-skills/inference-workflow/SKILL.md)
  to convert the demo into a script, validate a quantized state directory,
  choose `offload_per_layer`, build the model, and structure generation loops.
- Use [sub-skills/quantization-kernels/SKILL.md](sub-skills/quantization-kernels/SKILL.md)
  to inspect HQQ quantized layers, packing helpers, state-dict hooks, and
  Triton matmul wrapper issues.
- Use [sub-skills/expert-cache/SKILL.md](sub-skills/expert-cache/SKILL.md) to
  debug LRU expert-cache capacity, storage movement, eviction groups, and sparse
  MoE routing.

## Repo-level references

- [references/installation-and-runtime.md](references/installation-and-runtime.md)
  covers source-only installation, `PYTHONPATH`, dependency versions, CUDA
  expectations, and safe smoke checks.
- [references/api-reference.md](references/api-reference.md) summarizes the
  public source modules and key signatures; use sub-skills for deeper workflows.
- [references/demo-workflow.md](references/demo-workflow.md) summarizes the
  original demo's purpose, resource assumptions, and translation into reusable
  guidance.
- [references/troubleshooting.md](references/troubleshooting.md) covers
  cross-cutting install/import, CUDA, model-state, HQQ, and source-only errors.
- [references/repo-provenance.md](references/repo-provenance.md) records the
  source snapshot and evidence paths used to build this skill.

## Common task recipes

### User wants to run the demo as a script

1. Read the installation reference and verify dependencies/CUDA.
2. Read the inference workflow reference.
3. Render a skeleton with the inference sub-skill script.
4. Validate the state directory before calling `build_model`.
5. Start with short generation and low `max_new_tokens`.

### User hits a quantization or Triton error

1. Run the packing round-trip helper from the quantization sub-skill.
2. If CUDA behavior matters, run its Triton smoke against the user's checkout.
3. Inspect HQQ group sizes, packed weight shapes, and tensor contiguity.
4. Route model-level issues back to inference only after the kernel check passes.

### User is extending expert offloading

1. Use the expert-cache plan helper to validate cache sizes and UIDs.
2. Read cache/storage invariants before changing prefetch or eviction policy.
3. Keep storage type/size/device consistent across all cached experts.
4. Treat realistic cache construction as CUDA-backed unless using source-only
   reasoning.

## Avoid using this skill when

- The request is general Transformers usage unrelated to this repository's
  HQQ/Triton/offloading code.
- The user needs fine-tuning, training, serving infrastructure, or quantization
  methods not implemented here.
- The task is only to evaluate base Mixtral models without this repo's
  safetensors/offloading state layout.
