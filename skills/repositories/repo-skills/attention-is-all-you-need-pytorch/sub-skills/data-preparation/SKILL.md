---
name: data-preparation
description: "Prepares and inspects Multi30k and WMT-style BPE data for the
  attention-is-all-you-need-pytorch Transformer workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data Preparation

Use this sub-skill when a task asks how to preprocess translation data for this
repo, inspect a saved preprocessing pickle, reason about the legacy torchtext
schemas consumed by training or translation, or try the repository's BPE logic
without downloading WMT corpora.

## Route by task

- **Preprocess the default Multi30k German/English example**: read
  [references/workflows.md](references/workflows.md#default-non-bpe-multi30k-workflow).
  It covers the spaCy model prerequisites, legacy torchtext version expectations,
  and the command shape for the default non-BPE path.
- **Inspect an existing `*.pkl` preprocessing artifact**: run
  [scripts/inspect_preprocessed_pickle.py](scripts/inspect_preprocessed_pickle.py)
  and then read [references/data-formats.md](references/data-formats.md) to map
  the reported schema to training/translation consumers.
- **Understand BPE support**: read
  [references/workflows.md](references/workflows.md#wip-wmt-bpe-workflow) and
  [references/data-formats.md](references/data-formats.md#bpe-shared-field-pickle).
  The repository's BPE route is WIP and is suitable for training-data
  preparation experiments, not finished translation decoding.
- **Try BPE locally without WMT downloads**: run
  [scripts/bpe_tiny_demo.py](scripts/bpe_tiny_demo.py). It is a safe, deterministic
  adaptation of the repository's `learn_bpe`/`apply_bpe` behavior for tiny local
  corpora.
- **Debug preprocessing failures**: read
  [references/troubleshooting.md](references/troubleshooting.md) before retrying
  downloads, changing dependency versions, or assuming a pickle is corrupt.

## High-value facts

- The default executable path calls the non-BPE `main_wo_bpe` flow. It creates a
  single pickle containing settings, source/target torchtext `Field` objects,
  and `train`/`valid`/`test` example lists.
- The BPE flow is present but WIP. It requires switching the preprocessing entry
  point to the BPE `main` flow, downloads WMT-style archives, writes encoded
  `*.src`/`*.trg` files, and saves only a shared torchtext `Field` plus settings
  in the pickle.
- Token constants are fixed: padding `<blank>`, unknown `<unk>`, BOS `<s>`, and
  EOS `</s>`. These must exist in the relevant field vocabularies before
  training or translation.
- Custom `-data_src`/`-data_trg` files are rejected by the default non-BPE path;
  do not promise arbitrary local text preprocessing unless a new conversion path
  is intentionally implemented outside the stock command.

## Bundled helpers

```bash
# Refuses to unpickle until the caller explicitly acknowledges pickle trust.
python sub-skills/data-preparation/scripts/inspect_preprocessed_pickle.py --help
python sub-skills/data-preparation/scripts/inspect_preprocessed_pickle.py --pickle m30k_deen_shr.pkl --trust-pickle

# Safe BPE demonstration with built-in tiny corpus; no downloads or repo imports.
python sub-skills/data-preparation/scripts/bpe_tiny_demo.py --help
python sub-skills/data-preparation/scripts/bpe_tiny_demo.py --symbols 12 --min-frequency 2
```

Both scripts are deterministic, runnable from arbitrary current directories, and
avoid importing the original repository source. If a task needs model training,
checkpoint handling, or translation output, route to the sibling training or
translation sub-skill instead.
