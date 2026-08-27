# Training Workflows

## Before Training

1. Choose the source checkpoint for `Trainer.train(checkpoint=...)`.
2. Prepare `queries.tsv`, `collection.tsv`, and JSONL triples/examples.
3. Pick `nway`, `bsize`, `accumsteps`, and `nranks` together.
4. Validate files with `scripts/validate_training_files.py` before using GPUs.
5. Confirm CUDA availability and memory budget for the selected recipe.

Training and indexing normally require GPUs. CPU-only environments are suitable for import checks, script generation, and data validation only.

## Basic ColBERTv1-Style Fine-Tuning

Use this path for ordinary positive/negative triples, smaller experiments, and users who have unscored data.

Typical ingredients:

- Triples/examples: one JSON array per line, `[qid, positive_pid, negative_pid]`.
- `nway=2`.
- Cross-entropy loss because examples are unscored.
- Source checkpoint such as `bert-base-uncased` or another compatible BERT/ColBERT checkpoint.
- `bsize` divisible by `nranks`.

Minimal shape:

```python
from colbert import Trainer
from colbert.infra import ColBERTConfig, Run, RunConfig

with Run().context(RunConfig(nranks=1, experiment="basic-training")):
    config = ColBERTConfig(bsize=32, nway=2, accumsteps=1, root="./experiments")
    trainer = Trainer(triples="triples.train.jsonl", queries="queries.train.tsv", collection="collection.tsv", config=config)
    trainer.train(checkpoint="bert-base-uncased")
    print(trainer.best_checkpoint_path())
```

Validate first:

```bash
python scripts/validate_training_files.py --triples triples.train.jsonl --queries queries.train.tsv --collection collection.tsv --nway 2
```

## Advanced ColBERTv2-Style Training

Use this path for many-way examples, in-batch negatives, and distillation-style scored supervision.

README-style advanced settings include:

- `nway=64` for 64-way examples.
- `bsize=32`, `accumsteps=1`, and `nranks=4` in the example recipe.
- `lr=1e-5`, `warmup=20000`, `doc_maxlen=180`, `dim=128`.
- `similarity="cosine"`, `attend_to_mask_tokens=False`.
- `use_ib_negatives=True`.
- Source checkpoint passed to `trainer.train(checkpoint="colbert-ir/colbertv1.9")`.

Generate a template with the bundled helper:

```bash
python scripts/training_template.py --colbertv2-style --nranks 4 --bsize 32 --checkpoint colbert-ir/colbertv1.9 --output train_colbertv2.py
```

Then inspect placeholders and validate data:

```bash
python scripts/validate_training_files.py --triples examples.64.jsonl --queries queries.train.tsv --collection collection.tsv --nway 64 --sample 10000
```

## Scored Distillation Examples

Scored examples encode each passage as `[pid, score]` after the query ID:

```json
[1001, [42, 12.4], [314, 3.1], [2718, -0.2]]
```

When scored examples are present and `ignore_scores=False`, training uses a distillation objective based on teacher-score distributions. `distillation_alpha` scales scores before the target distribution is formed. If scores are noisy or have an extreme range, lower `distillation_alpha` or inspect the score-generation pipeline before using a large GPU run.

Check for these issues before launch:

- Every passage entry in an example is either all scored or all unscored.
- `nway` matches the intended number of passage entries consumed per example.
- Query IDs exist in `queries.tsv`.
- Passage IDs exist in `collection.tsv`.
- Collection IDs align with zero-based row positions unless the data loader has been adapted.

## Choosing `bsize`, `nranks`, `accumsteps`, and `nway`

ColBERT checks `bsize % nranks == 0` and uses `bsize / nranks` per rank. Higher `nway`, longer `doc_maxlen`, larger `bsize`, and `use_ib_negatives=True` increase memory use.

Practical adjustment order:

1. Keep `nway` aligned with the data; do not silently reduce it unless changing the training objective is acceptable.
2. Reduce `bsize` until it fits GPU memory while staying divisible by `nranks`.
3. Increase `accumsteps` to recover effective batch size if optimization stability suffers.
4. Reduce `doc_maxlen` only if passage truncation is acceptable for the task.
5. Reduce `nranks` only when fewer GPUs are available, then re-check `bsize % nranks`.

## Preparing Triples From Rankings

ColBERT includes utilities that sample positives and negatives from ranked lists. These utilities assume ranked input is sorted per query and sample negative passages from configurable depth windows. Treat them as preprocessing references: verify labels, depth ranges, and qid/pid coverage before training.

Generated triples should be shuffled and capped to a manageable size. Very large files are normal for full training, but validate a sample first and run full validation when feasible.

## Safe Native Verification Strategy

Do not run full training as a verification smoke test unless the user explicitly has GPUs and accepts the runtime cost. Prefer:

- Import checks for `colbert`, `colbert.infra`, and `Trainer`.
- `scripts/validate_training_files.py` on tiny synthetic fixtures.
- `scripts/training_template.py` output review.
- README training snippets treated as reference-only when no GPU is available.
