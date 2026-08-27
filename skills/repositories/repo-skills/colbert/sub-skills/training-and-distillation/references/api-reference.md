# Training API Reference

## Public Entry Point

Use `Trainer(triples, queries, collection, config=None)` from `colbert` for training and fine-tuning.

```python
from colbert import Trainer

trainer = Trainer(triples=triples_path, queries=queries_path, collection=collection_path, config=config)
trainer.train(checkpoint="bert-base-uncased")
checkpoint_path = trainer.best_checkpoint_path()
```

Verified signature: `Trainer(triples, queries, collection, config=None)`.

### Checkpoint Precedence

`Trainer.train(checkpoint=...)` configures the checkpoint used by the training run. A checkpoint stored on `ColBERTConfig` is overwritten by the explicit `train()` argument. When the user supplies both, treat the `train(checkpoint=...)` value as authoritative and call out the mismatch before launching a costly run.

```python
config = ColBERTConfig(checkpoint="ignored-in-trainer-train")
trainer = Trainer(triples=triples, queries=queries, collection=collection, config=config)
trainer.train(checkpoint="actual-source-checkpoint")
```

## Run Context

Use `Run().context(RunConfig(...))` around training so ColBERT can set experiment metadata, rank configuration, and output locations.

```python
from colbert.infra import Run, RunConfig

with Run().context(RunConfig(nranks=4, experiment="msmarco")):
    trainer.train(checkpoint="colbert-ir/colbertv1.9")
```

`nranks` corresponds to distributed training ranks, normally one process per GPU. ColBERT asserts that global `bsize` is divisible by `nranks`, then divides it into per-rank batch size internally.

## Data Inputs

### Queries TSV

Each non-empty row should contain at least two tab-separated fields:

```text
qid<TAB>query text
```

Query IDs are looked up by triples/examples. IDs can be integers or strings in some ColBERT data objects, but the common TSV/MS MARCO convention uses integer IDs.

### Collection TSV

Each non-empty row should contain at least two tab-separated fields:

```text
pid<TAB>passage text
```

ColBERT collection loading commonly expects passage IDs to align with zero-based row positions. If a file has an `id` header, handle it deliberately and validate the resulting IDs before training.

### Training Examples JSONL

`Trainer` passes the triples path through ColBERT's `Examples.cast(..., nway=config.nway)`. Each line must be a JSON array with a query ID followed by passage IDs or scored passage entries.

Basic unscored 2-way examples:

```json
[1001, 42, 314]
```

Advanced scored 4-way example shape:

```json
[1001, [42, 9.7], [314, 1.2], [2718, 0.4], [7, -0.1]]
```

For `nway=N`, ColBERT consumes the first `N` passage entries after the query ID. Extra entries may be truncated by the examples loader, so validate that the intended `nway` matches the data generation recipe.

## Loss Behavior

- If examples include teacher scores and `ignore_scores=False`, ColBERT uses KL-divergence against log-softmaxed scores, scaled by `distillation_alpha`.
- If examples are unscored or `ignore_scores=True`, ColBERT uses cross-entropy with the first passage treated as the positive target.
- If `use_ib_negatives=True`, an additional in-batch negative loss is added.

Do not mix scored and unscored passage entries within a single example unless there is a deliberate preprocessing reason and downstream code is known to accept it.

## Important Config Fields

- `bsize`: global batch size before division by `nranks`; must be divisible by `nranks`.
- `accumsteps`: gradient accumulation steps; larger values can reduce memory pressure at the cost of more forward passes per optimizer step.
- `nway`: number of passages per query example; must match JSONL example shape and loss expectations.
- `lr`: learning rate; advanced ColBERTv2-style examples commonly use `1e-5`.
- `warmup`: scheduler warmup steps; advanced examples often use `20000` for large runs.
- `maxsteps`: maximum number of training steps.
- `doc_maxlen`: document token length; advanced ColBERTv2-style examples commonly use `180`.
- `query_maxlen`: query token length; default-style values are usually much shorter than documents.
- `dim`: embedding dimension; ColBERTv2-style examples commonly use `128`.
- `similarity`: commonly `cosine` for ColBERTv2-style training.
- `use_ib_negatives`: adds in-batch negative loss.
- `distillation_alpha`: multiplier applied to teacher scores before the distillation target distribution.
- `ignore_scores`: forces cross-entropy behavior even when scored entries are present.
- `attend_to_mask_tokens`: advanced README examples set this to `False`.

## Distillation Utilities

ColBERT includes scorer utilities for teacher scoring. A scorer loads a cross-encoder model, scores query-passage pairs, and can write per-query scored outputs for distillation. These workflows are GPU-heavy because the scoring model is moved to CUDA. Treat distillation-score generation as a separate resource-planned preprocessing job, not as a safe CPU smoke test.

## Checkpoint Output

`trainer.train()` stores the run's best checkpoint path internally. Call `trainer.best_checkpoint_path()` after `train()` completes. Do not assume `train()` itself returns the path in all public API usage; use the accessor for stable code.
