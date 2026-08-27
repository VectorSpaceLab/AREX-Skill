---
name: training-and-evaluation
description: "Guides pix2tex model training, resizer training, evaluation, YAML
  configuration, checkpoints, GPU memory planning, and optional training
  dependencies."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training and Evaluation

Use this sub-skill when the user wants to train or fine-tune the LaTeX-OCR
encoder-decoder model, train the image-resizer model, evaluate BLEU/edit
distance/token accuracy, tune config YAMLs, resume from checkpoints, or debug
training dependencies and GPU memory.

## Quick Route

1. Read [references/configuration.md](references/configuration.md) before editing
   YAML config fields.
2. Read [references/training-and-evaluation.md](references/training-and-evaluation.md)
   for train, resizer, and eval command recipes.
3. Read [references/model-architecture.md](references/model-architecture.md) for
   the hybrid/VIT encoder, transformer decoder, tokenizer, and checkpoint
   relationships.
4. Read [references/troubleshooting.md](references/troubleshooting.md) for
   missing extras, data/checkpoint issues, GPU memory, and long-run boundaries.
5. Run [scripts/summarize_pix2tex_config.py](scripts/summarize_pix2tex_config.py)
   to inspect a config safely before starting training.

## Minimal Training Command Pattern

```bash
pip install "pix2tex[train]"
python -m pix2tex.train --config path/to/config.yaml
```

Run this only after dataset pickles and tokenizer paths in the config are valid.
Training is long-running and can use W&B and GPU memory; confirm budget and
hardware first.

## Evaluation Pattern

```bash
python -m pix2tex.eval \
  --config path/to/config.yaml \
  --checkpoint path/to/weights.pth \
  --data path/to/val.pkl \
  --no-cuda \
  --num-batches 5
```

Use a small `--num-batches` first. Full evaluation requires the `[train]` extra
because metrics use `torchtext` and edit distance uses Levenshtein.

## Boundaries

- Dataset/tokenizer creation belongs in
  [../data-preparation/SKILL.md](../data-preparation/SKILL.md).
- User-facing inference after training belongs in
  [../ocr-inference/SKILL.md](../ocr-inference/SKILL.md).
- Do not start training, downloads, W&B logging, or full evaluation unless the
  user has approved the runtime cost and provided valid datasets/checkpoints.
