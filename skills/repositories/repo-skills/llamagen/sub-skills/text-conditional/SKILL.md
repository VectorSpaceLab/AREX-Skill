---
name: text-conditional
description: "Router for LlamaGen caption-conditioned training, sampling, prompt
  batches, and t2i evaluation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Text-Conditional

Use this sub-skill for the text-conditioned LlamaGen path: stage-1 and stage-2 training, prompt sampling, and evaluation of caption-conditioned generations.

## Owns
- Stage-1 and stage-2 t2i training.
- COCO and Parti prompt sampling.
- T5 embedder behavior, padding, and cache layout for the text-conditioning path.
- t2i evaluation inputs, outputs, and packaging expectations.
- Checkpoint / precision / `--from-fsdp` guidance for the text-conditioned path.

## Routes out
- Tokenizer training, finetuning, reconstruction, and code/image round trips -> `tokenizers`
- Precomputed code or T5 feature extraction, OpenImages manifests, and cache prep -> `data-preparation`
- ImageNet class-conditional generation, serving, and c2i evaluation -> `class-conditional`
- Remote publishing or upload helpers -> excluded

## Best entry points
- Training: `scripts/train_t2i_stage1.sh`, `scripts/train_t2i_stage2.sh`
- Sampling: `scripts/sample_t2i_coco.sh`, `scripts/sample_t2i_parti.sh`
- Evaluation: `scripts/evaluate_t2i.sh`
- T5 behavior: `references/t5.md`
- Prompt / batch layout: `references/evaluation.md`
- Workflow selection: `references/workflows.md`

## Read before answering
- `references/workflows.md`
- `references/cli-reference.md`
- `references/t5.md`
- `references/evaluation.md`
- `references/troubleshooting.md`

## Fast routing rules
- If the user asks to create or refresh text features, route to `data-preparation`.
- If the user asks for VQ, VQGAN, VAE, or Consistency Decoder reconstruction, route to `tokenizers`.
- If the user asks for ImageNet c2i training, sampling, serving, or c2i evaluation, route to `class-conditional`.
- If the user asks about t2i only, stay here and use the bundled wrappers.
- Keep `--no-left-padding`, prompt CSV/TSV formatting, and evaluation folder layout in mind before running a job.
