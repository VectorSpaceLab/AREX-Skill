---
name: rnn-language-modeling
description: "Plan and troubleshoot DARTS recurrent language-modeling workflows
  for PTB and WikiText-2."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# RNN Language Modeling

Use this sub-skill when a task is about DARTS recurrent language modeling on Penn Treebank or WikiText-2: architecture search, training from a recurrent genotype, test perplexity evaluation, corpus layout, checkpoint behavior, optimizer schedule behavior, or RNN-specific failures.

## Routing

- Read [references/workflows.md](references/workflows.md) to plan PTB search, PTB train/test, the WikiText-2 recipe, major flags/defaults, checkpoint files, ASGD switching, rollback, and expected training signals.
- Read [references/data-formats.md](references/data-formats.md) to validate `train.txt` / `valid.txt` / `test.txt`, `<eos>` tokenization, `Dictionary` / `Corpus` behavior, and `batchify` / `get_batch` tensor shapes.
- Read [references/api-reference.md](references/api-reference.md) for `RNNModel`, `DARTSCell`, `RNNModelSearch`, `Architect`, dropout utilities, and checkpoint utilities.
- Read [references/troubleshooting.md](references/troubleshooting.md) for dataset assertions, the inverted CUDA flag, CPU-only caveats, checkpoint loading, NaN rollback, hidden-size assertions, batch/micro-batch mismatches, and memory pressure.

Route genotype catalog lookup, recurrent DOT rendering, and visualization details to the sibling `genotypes-and-visualization` sub-skill. Route global legacy runtime compatibility and pretrained checkpoint acquisition caveats to the root skill's shared references.
