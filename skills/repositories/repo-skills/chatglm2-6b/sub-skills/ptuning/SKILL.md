---
name: ptuning
description: "Guides ChatGLM2-6B P-Tuning v2, chat fine-tuning data, prediction
  commands, prefix/full checkpoint loading, and optional DeepSpeed fine-tuning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# ChatGLM2-6B P-Tuning and Fine-Tuning

Use this route when the task involves P-Tuning v2, chat fine-tuning data,
ADGEN-style data, bundled P-Tuning runner arguments, prefix checkpoint loading,
prediction, or optional full-parameter DeepSpeed fine-tuning. Use
[`chat-and-demos`](../chat-and-demos/SKILL.md) for ordinary base-model chat and
[`api-serving`](../api-serving/SKILL.md) when a prepared model should be served.

## Safe workflow

1. Validate data before launching `torchrun`:
   `python sub-skills/ptuning/scripts/validate_ptuning_data.py --file train.json --format chat --history-column history`.
2. Build a command string without executing it from the generated skill root:
   `python sub-skills/ptuning/scripts/build_ptuning_command.py train --train-file train.json --validation-file dev.json --output-dir output/run`.
3. Confirm model weights/cache, CUDA availability, and the intended checkpoint
   type. P-Tuning v2 saves a prefix encoder, not a full model; full fine-tuning
   checkpoints load differently.
4. Run expensive training/evaluation only after checking data columns,
   `pre_seq_len`, quantization, GPU memory, and output paths.

Read [`data-formats.md`](references/data-formats.md) for ADGEN/chat schemas,
[`command-templates.md`](references/command-templates.md) for launch patterns,
[`checkpoint-workflows.md`](references/checkpoint-workflows.md) for prefix vs
full checkpoints, and [`troubleshooting.md`](references/troubleshooting.md) for
schema, OOM, DeepSpeed, quantization, and Gradio issues.

## Boundaries

This sub-skill distills the repository's P-Tuning scripts into bundled
references, validators, command builders, and a bundled runner under
`scripts/ptuning_runner/`. It does not train or evaluate as a smoke test, does
not download ADGEN/model weights, and does not make DeepSpeed a required
dependency. Full training, prediction, and web demo launch are GPU/model/data
dependent and should be treated as deliberate runtime actions, not verification
shortcuts.
