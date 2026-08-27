---
name: data-preparation
description: "Use BERT-pytorch to build, load, and debug vocabularies and
  dataset inputs from tab-separated sentence pairs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# data-preparation

Use this sub-skill when the task is about corpus layout, vocabulary files, `bert-vocab`, `WordVocab`, `BERTDataset`, or pickle vocab troubleshooting.

## What this covers

- Build a vocabulary from a corpus with `bert-vocab` or the Python API.
- Read and write `WordVocab` pickle files.
- Inspect `BERTDataset` inputs and outputs.
- Diagnose malformed tab-separated rows, missing corpus files, and streaming-mode pitfalls.

## What to do first

- If the corpus is not two sentences per line separated by one tab, fix the corpus before building a vocab.
- If you are using streaming mode, pass an explicit `corpus_lines` value; for small jobs, prefer `on_memory=True`.
- Use `scripts/build_vocab_smoke.py` when you want a safe tiny fixture that proves both vocab creation and dataset loading.
- If the task is actually about model construction, training, or checkpoints, hand off to `../training/SKILL.md`.

## Read these references

- `references/corpus-format.md`: corpus layout, special tokens, dataset fields, and the tiny smoke recipe.
- `references/troubleshooting.md`: malformed rows, pickle problems, streaming-mode issues, and tokenization mistakes.
- `../training/SKILL.md`: follow this route after you have a valid corpus and vocab.

## Related scripts

- `scripts/build_vocab_smoke.py`: build a tiny vocab, reload it, and inspect one dataset item.
- `../../scripts/make_tiny_corpus.py`: create a deterministic two-line corpus fixture for experiments.

## Common outputs

- `WordVocab` stores special tokens at fixed ids: pad 0, unk 1, eos 2, sos 3, mask 4.
- `BERTDataset.__getitem__` returns `bert_input`, `bert_label`, `segment_label`, and `is_next` tensors.
- `WordVocab.load_vocab()` expects a pickle created by this package, not a text vocabulary.

## Boundary reminders

- Do not solve model initialization or checkpointing here.
- Do not hide corpus-format bugs behind training troubleshooting.
- Keep the route focused on data layout, vocab serialization, and dataset inspection.
