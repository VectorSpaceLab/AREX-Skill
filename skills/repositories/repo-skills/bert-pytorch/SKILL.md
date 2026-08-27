---
name: bert-pytorch
description: "Use BERT-pytorch for corpus preparation, vocabulary building, and
  tiny BERT pretraining workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# bert-pytorch

Use this skill when the user mentions BERT-pytorch, `bert`, `bert-vocab`, `WordVocab`, `BERTDataset`, `BERT`, `BERTLM`, or `BERTTrainer`.

## Quick start

1. Install the package with `python -m pip install bert-pytorch` if it is not already available in your Python environment.
2. Run `python scripts/check_install.py` to confirm the package import, public exports, and console commands.
3. If the task is about corpus layout, vocabulary files, or dataset rows, go to `sub-skills/data-preparation/SKILL.md`.
4. If the task is about model construction, training, device choice, or checkpoints, go to `sub-skills/training/SKILL.md`.
5. Use `python scripts/make_tiny_corpus.py --output /tmp/bert-pytorch-corpus.txt` when you need a stable two-line fixture.

## Route map

- `sub-skills/data-preparation/SKILL.md`: build or load vocabularies, validate corpus format, inspect `BERTDataset`, and diagnose pickle or row-format problems.
- `sub-skills/training/SKILL.md`: instantiate `BERT`, `BERTLM`, and `BERTTrainer`; train on a tiny corpus/vocab pair; pick CPU or CUDA; and save checkpoints.

## Shared facts

- The corpus format is two sentences per line separated by a tab.
- Tokenization happens before the package; BERT-pytorch does not tokenize raw text for you.
- `bert-vocab` and `bert` are the documented console commands.
- `BERT` hidden size must be divisible by the number of attention heads.
- The `bert` CLI parses some boolean flags with `type=bool`; use the bundled smoke scripts or the Python API when you need an explicit CPU run or streaming mode.

## Shared references

- `references/repo-provenance.md`: source commit, package version, and evidence snapshot.
- `references/repo-routing-metadata.json`: router metadata for managed import.
- `references/api-reference.md`: public classes, functions, and object relationships.
- `references/cli-reference.md`: command names, flags, defaults, and safety notes.
- `references/troubleshooting.md`: cross-cutting install, import, CLI, corpus, and device issues.

## Shared scripts

- `scripts/check_install.py`: verify imports, API exports, and CLI help.
- `scripts/make_tiny_corpus.py`: create a deterministic two-line corpus fixture.

## When in doubt

- Start with the sub-skill that matches the first concrete noun in the request: corpus/vocab/data rows -> data preparation; model/training/checkpoint/device -> training.
- If the task mixes both, build the vocabulary first, then move to training.
- Read `references/troubleshooting.md` before guessing about missing files, malformed rows, or device failures.
