---
name: training
description: "Use BERT-pytorch to instantiate the model, train on a tiny corpus,
  choose CPU or CUDA, and save checkpoints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# training

Use this sub-skill when the task is about `bert`, `BERT`, `BERTLM`, `BERTTrainer`, model construction, device choice, training, or checkpoint saving.

## What this covers

- Instantiate `BERT` and `BERTLM`.
- Build a `BERTTrainer` around a `DataLoader`.
- Choose CPU or CUDA explicitly for a smoke run.
- Save checkpoints and understand the `.ep{epoch}` suffix.
- Diagnose hidden-size, attention-head, CUDA, and checkpoint-path errors.

## What to do first

- Build or load a valid vocab and corpus first; if those are missing, hand off to `../data-preparation/SKILL.md`.
- Use `scripts/train_smoke.py` for a safe one-epoch smoke run with explicit device selection.
- Use CPU smoke when you only need a deterministic quick check.
- Use CUDA smoke only when `torch.cuda.is_available()` is true and the host really has a compatible GPU setup.

## Read these references

- `references/training-workflow.md`: model/trainer flow, device selection, and checkpoint semantics.
- `references/troubleshooting.md`: CLI bool flags, hidden/head mismatch, GPU, memory, and save-path issues.
- `../data-preparation/SKILL.md`: if the corpus or vocab is the actual blocker.

## Related scripts

- `scripts/train_smoke.py`: build a tiny dataset, train one epoch, and save a checkpoint.
- `../../scripts/make_tiny_corpus.py`: create a deterministic tiny corpus fixture when you want to run the smoke script against a known input.

## Common outputs

- `BERT.forward()` returns the encoded sequence tensor before the language-model heads.
- `BERTLM.forward()` returns next-sentence and masked-language-model log probabilities.
- `BERTTrainer.save(epoch, file_path)` writes `file_path + ".ep{epoch}"`.
- `BERTTrainer` chooses `cuda:0` only when CUDA is available and requested.

## Boundary reminders

- Do not solve corpus layout or vocab serialization here.
- Do not bury device-selection guidance inside the data-preparation route.
- Keep the route focused on model instantiation, training, and checkpointing.
