---
name: nlu-glue-adaptation
description: "Construct and troubleshoot LoRA fine-tuning and evaluation
  workflows for RoBERTa or DeBERTa-v2 GLUE-style sequence classification."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# NLU GLUE adaptation

Use this sub-skill for the repository's LoRA-aware sequence-classification
workflow: model configuration, query/value projection replacement, GLUE task
commands, adapter checkpoint transfer, and training-resource checks.

## Route here

- Build a LoRA GLUE command for RoBERTa or DeBERTa-v2.
- Explain `--apply_lora`, `--lora_r`, `--lora_alpha`, and `--lora_path`.
- Port the repository's query/value adaptation into another Transformers
  version or a custom encoder.
- Diagnose missing checkpoints, label-head mismatches, or CUDA/distributed
  launch failures.

## Start fast

1. Install the base model's Transformers and dataset dependencies in the
   target environment, then verify that the runner's `--help` works before
   downloading a model.
2. Choose the model family and task. The archived recipes use LoRA on query and
   value projections and leave key projections unchanged.
3. Set `--apply_lora`, a positive `--lora_r`, and `--lora_alpha`. Use
   `--lora_path` only when transferring an adapter trained on a compatible base
   architecture/task.
4. Start with one GPU or a dry command. Add `--fp16` and distributed launch
   only after the model loads and a tiny batch succeeds.
5. Save output and logs in a new directory; do not overwrite a non-empty output
   directory unless resuming intentionally.

Generate a safe command without opening the archived shell launchers:

```bash
python scripts/build_glue_lora_command.py \
  --model roberta-base --task mnli --script run_glue.py --num-gpus 1
```

## Model-specific defaults

- RoBERTa recipes generally use `r=8`, `alpha=16`, sequence length 512, and a
  higher learning rate than ordinary full fine-tuning.
- DeBERTa-v2 XXL recipes use `r=16`, `alpha=32`, sequence length 256, fp16, and
  distributed launch. Treat those as resource-heavy starting points, not
  universal hyperparameters.
- For MRPC, RTE, and STS-B transfer workflows, the archived recipes expect a
  LoRA-adapted MNLI checkpoint. Ensure the adapter path and base model match.

## Reroute

- Layer constructor, trainable parameters, and state-dict details: use
  `../core-lora-api/SKILL.md`.
- GPT-2 data-to-text training and decoding: use
  `../nlg-gpt2-adaptation/SKILL.md`.

## References

- Read [GLUE workflows](references/glue-lora-workflows.md) for flags,
  launcher patterns, task/data layouts, and checkpoint transfer.
- Read [model integration](references/model-integration.md) for the exact
  query/value insertion behavior and porting checklist.
- Read [troubleshooting](references/troubleshooting.md) before changing rank,
  alpha, batch size, or model code to fix a runtime failure.

## Common request patterns

Use this sub-skill when the user asks to:

- adapt an existing RoBERTa/DeBERTa classification model with LoRA;
- translate an archived launcher into a safer single-device smoke command;
- attach an MNLI-trained LoRA checkpoint to MRPC, RTE, or STS-B;
- understand why a `run_glue.py` call needs `--apply_lora`, `--lora_r`, and
  `--lora_alpha` together; or
- trace a missing-key error back to a changed module path, task head, or model
  family.

## Exit checklist

Before returning, confirm the answer states:

1. which projections receive LoRA and which stay unchanged;
2. the command arguments that must match between training and transfer;
3. whether the suggested run assumes CUDA, distributed launch, or a CPU smoke;
4. where the adapter checkpoint should be loaded; and
5. what failure signals imply a bad base model, bad head, or stale launcher.
