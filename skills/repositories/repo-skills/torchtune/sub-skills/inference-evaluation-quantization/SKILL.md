---
name: inference-evaluation-quantization
description: "Use torchtune generation, Eleuther evaluation, and quantization
  workflows safely after checkpoints exist."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# inference-evaluation-quantization

Use this sub-skill when an agent already has model checkpoints and needs to run or plan torchtune generation, EleutherAI Eval Harness evaluation, post-training quantization conversion, or evaluation/generation of quantized checkpoints.

Do not use it to choose or launch training recipes. Route training setup to `../post-training-recipes/SKILL.md`, model component details to `../models-and-modules/SKILL.md`, and checkpointing internals to `../training-utilities-and-rlhf/SKILL.md` when available.

## Safe Default

Generation, evaluation, and quantization can download gated model assets, allocate GPUs, compile kernels, write checkpoints, or require optional packages. Build and inspect commands first; only execute after the user confirms checkpoint files, tokenizer files, credentials, device, dtype, output directory, and optional dependencies.

Use the bundled command builder to construct a non-executing command:

```bash
python sub-skills/inference-evaluation-quantization/scripts/build_inference_eval_command.py generate \
  ./custom_generation_config.yaml \
  --override checkpointer.checkpoint_dir=./runs/lora/epoch_0 \
  --override checkpointer.checkpoint_files=[model-00001-of-00002.safetensors,model-00002-of-00002.safetensors] \
  --override tokenizer.path=./runs/lora/epoch_0/original/tokenizer.model \
  --print-notes
```

The script prints `tune run ...`; it never executes recipes, imports `recipes`, reads checkpoints, downloads models, or touches GPUs.

## Route By Task

- For command/config construction for `generate`, `eleuther_eval`, `quantize`, and quantize-then-evaluate/generate sequences, read [references/workflows.md](references/workflows.md).
- For deciding between base checkpoints, merged LoRA weights, adapter-only outputs, and quantized checkpoint compatibility, read [references/checkpoint-flow.md](references/checkpoint-flow.md).
- For optional dependency, checkpointer/quantizer, tokenizer, prompt, GPU/memory, dtype, and output-dir failures, read [references/troubleshooting.md](references/troubleshooting.md).

## API And Recipe Facts

- Use `tune run generate --config <config>` for the stable generation recipe, `tune run eleuther_eval --config <config>` for EleutherAI harness evaluation, and `tune run quantize --config <config>` for torchtune quantization conversion.
- Do not `import recipes`; recipes are launched through `tune run`, copied with `tune cp`, inspected with `tune cat`, or executed through the CLI/runpy path.
- The public generation API includes `torchtune.generation.generate(model, prompt, max_generated_tokens, pad_id=0, temperature=1.0, top_k=None, stop_tokens=None, rng=None, compiled_generate_next_token=None)`, `sample(logits, temperature=1.0, top_k=None, q=None)`, and `generate_next_token(...)`.
- The generation recipe supports single-GPU generation; the Eleuther recipe supports single-GPU evaluation and quantization for text-only models.
- Eleuther evaluation requires the optional `lm-eval` package in the supported harness range; quantization workflows require torchao-backed quantizer components.

## Boundaries And Cross-Links

- Use `../cli-and-config/SKILL.md` for registry discovery, `tune cp`, `tune cat`, `tune validate`, and OmegaConf override syntax.
- Use `../post-training-recipes/SKILL.md` before this sub-skill when the model checkpoint has not been produced yet.
- Use `../training-utilities-and-rlhf/SKILL.md` for deeper checkpointer behavior, precision utilities, device utilities, logging, and checkpoint state conventions.
- Use `../models-and-modules/SKILL.md` for selecting model builders or understanding model architecture internals.
- Keep generated runtime instructions self-contained; do not rely on source-repo docs, recipe files, tests, or local checkout paths being available.
