---
name: mergekit
description: "Use mergekit to configure, validate, and operate language-model
  merges, checkpoint surgery, tokenizer changes, MoE construction, LoRA
  extraction, and optional evolutionary searches."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 3.0
---

# mergekit

Use this repo skill when a task names mergekit, `mergekit-yaml`, model merging,
TIES/DARE/DELLA/SLERP/task arithmetic, layer or tokenizer surgery, dense-to-MoE
conversion, LoRA extraction, or mergekit's optional evolutionary search.
mergekit 0.1.4 is a PyTorch/Transformers toolkit that writes a new checkpoint;
it does not train a model or replace downstream validation.

## Install and inspect first

Install the public package in an isolated Python 3.10+ environment. The base
package includes PyTorch, Transformers, safetensors, Accelerate, Pydantic,
Hugging Face Hub, PEFT, datasets, and related runtime dependencies. Add only
`[test]` for focused tests; `[evolve]` adds Ray/CMA/lm-eval/W&B and `[vllm]`
adds a pinned vLLM/evaluation path. Do not install every extra by default.

```bash
python -m pip install mergekit
python -c "import mergekit, torch, transformers; print(mergekit.__name__, torch.__version__, transformers.__version__)"
```

For a local checkout, an editable install is useful for development but the
runtime guidance in this skill uses installed console entry points. Before a
run, use the read-only diagnostics in
[sub-skills/model-io-and-architecture/scripts/mergekit_model_diagnostic.py](sub-skills/model-io-and-architecture/scripts/mergekit_model_diagnostic.py)
and [references/troubleshooting.md](references/troubleshooting.md).

## Choose the route

- [merge-configs](sub-skills/merge-configs/SKILL.md): standard YAML merges,
  method selection, slices/modules, parameters, dtype, tokenizer, chat
  templates, and `mergekit-yaml`.
- [model-io-and-architecture](sub-skills/model-io-and-architecture/SKILL.md):
  model references, architecture/key conversion, task planning, checkpoint IO,
  sharding, safe serialization, memory, CPU/CUDA, and multi-GPU decisions.
- [specialized-workflows](sub-skills/specialized-workflows/SKILL.md):
  `mergekit-pytorch`, `mergekit-moe`, `mergekit-multi`, LoRA extraction,
  `mergekit-tokensurgeon`, layer shuffle, and compatibility routes.
- [extension-and-evolution](sub-skills/extension-and-evolution/SKILL.md): custom
  merge methods/task graphs and bounded preflight for `mergekit-evolve`.

## Safe operating contract

1. Normalize model paths/Hub ids, revisions, output location, hardware, network,
   credentials, and overwrite policy before constructing a command.
2. Validate YAML or specialty config without downloads when possible. A parser
   pass is necessary but does not prove model files, tensor shapes, tokenizer,
   or architecture compatibility.
3. Choose a method whose model count/base-model requirements match the inputs;
   keep `models`, `slices`, and `modules` mutually exclusive at each level.
4. Treat `--trust-remote-code` and `--allow-crimes` as explicit risk decisions.
   Prefer safe `safetensors`, a new output directory, and a recorded command.
5. Select CPU/CUDA/device, lazy, shard, and write flags from actual RAM/VRAM and
   backend probes. Do not claim a written checkpoint is usable until its config,
   shards, tokenizer, and downstream load have been checked.

## Provenance and refresh

Read [references/repo-provenance.md](references/repo-provenance.md) before
refreshing this skill. It records the inspected mergekit commit, package
version, and evidence baseline; source or entry-point drift is a refresh signal.
The detailed method, CLI, tokenizer, architecture, and failure references are
owned by the nearest sub-skill and are intentionally not duplicated here.
