---
name: training-and-distillation
description: "Train or fine-tune ColBERT models, prepare and validate triples,
  use scored distillation examples, and plan GPU/resource settings. Use when
  tasks mention ColBERT Trainer, fine-tuning checkpoints, training triples,
  distillation scores, nway/bsize/accumsteps choices, or training-file
  validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# ColBERT Training And Distillation

Use this sub-skill when the user needs to configure or troubleshoot ColBERT training. It covers the `Trainer` API, JSONL examples/triples, scored distillation examples, resource planning, and safe helper scripts. Do not use it for post-training indexing/search, evaluation benchmarks, or tokenizer internals.

## Route Tasks

- For a runnable training starting point, read `references/training-workflows.md` and generate a script with `scripts/training_template.py`.
- For API details, checkpoint precedence, data shapes, and config fields, use `references/api-reference.md`.
- For validation before GPU work, run `scripts/validate_training_files.py` against triples, queries, and collection files.
- For launch, data, scored-example, OOM, and dependency failures, use `references/troubleshooting.md`.
- For indexing or searching a trained checkpoint, switch to the `indexing-and-search` sub-skill.
- For ranking metrics, LoTTE/MS MARCO evaluation, qrels, and dataset conventions outside training, switch to the `data-and-evaluation` sub-skill.
- For tokenization behavior, max lengths, dimensions, and model architecture details, switch to the `modeling-and-tokenization` sub-skill.

## Core API

The verified public training entry point is:

```python
from colbert import Trainer
from colbert.infra import ColBERTConfig, Run, RunConfig

with Run().context(RunConfig(nranks=1, experiment="my-training-run")):
    config = ColBERTConfig(bsize=32, nway=2, accumsteps=1)
    trainer = Trainer(triples="triples.train.jsonl", queries="queries.train.tsv", collection="collection.tsv", config=config)
    trainer.train(checkpoint="bert-base-uncased")
    checkpoint_path = trainer.best_checkpoint_path()
```

Important behavior: `Trainer.train(checkpoint=...)` is the checkpoint source used by training. If `ColBERTConfig(checkpoint=...)` is also set, the explicit `train(checkpoint=...)` argument wins.

## Bundled Helpers

- `scripts/validate_training_files.py` checks JSONL triples/examples plus query and collection TSV files for parseability, ID references, duplicate IDs, scored-example shape, and likely `nway` mismatches before launching training.
- `scripts/training_template.py` emits a safe argparse-based ColBERT training script template and warns about resource choices such as `bsize % nranks`, large `nway`, and GPU expectations.

## Training Scope

Basic ColBERTv1-style training usually uses unscored `[qid, positive_pid, negative_pid]` JSONL examples with `nway=2`. Advanced ColBERTv2-style training often uses many-way examples such as 64-way scored JSONL, `use_ib_negatives=True`, `distillation_alpha`, `doc_maxlen=180`, `dim=128`, and a source checkpoint such as `colbert-ir/colbertv1.9`.

Practical training requires CUDA/GPU resources. CPU-only environments are useful for imports, file validation, and template generation, but real fine-tuning, distillation scoring, and distributed training are GPU-heavy.
