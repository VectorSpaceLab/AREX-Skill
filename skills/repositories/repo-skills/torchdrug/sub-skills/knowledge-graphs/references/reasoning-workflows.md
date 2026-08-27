# Knowledge Graph Reasoning Workflows

TorchDrug treats knowledge graph reasoning as knowledge graph completion over integer-indexed triples. Built-in benchmark datasets provide a single `KnowledgeGraphDataset` with standard `train`, `valid`, and `test` splits. Models score candidate `(head, tail, relation)` triples through `tasks.KnowledgeGraphCompletion`, while `core.Engine` owns training and evaluation mechanics.

## Dataset and Split Pattern

Use built-in datasets when the user names a TorchDrug KG benchmark:

```python
from torchdrug import datasets

dataset = datasets.FB15k237("~/kg-datasets/")
train_set, valid_set, test_set = dataset.split()
```

Common entry points are `datasets.FB15k`, `datasets.FB15k237`, `datasets.WN18`, `datasets.WN18RR`, `datasets.YAGO310`, and `datasets.Hetionet`. They download text files into the provided cache directory, load all splits with one shared entity/relation vocabulary, and return `torch.utils.data.Subset` objects from `split()`.

For custom triples, use `data.KnowledgeGraphDataset` and load all splits together when possible so entity and relation ids stay consistent across train/valid/test. The TSV loader reads text rows as `(head_token, relation_token, tail_token)` but the dataset stores graph edges internally as `(head_id, tail_id, relation_id)`. If constructing integer triplets directly with `load_triplet`, pass `(head_id, tail_id, relation_id)` and keep ids consecutive from zero.

## Embedding Recipe

Embedding models learn entity and relation vectors and normally use the full training set both as labels and as the fact graph:

```python
import torch
from torchdrug import core, datasets, models, tasks

dataset = datasets.FB15k237("~/kg-datasets/")
train_set, valid_set, test_set = dataset.split()
model = models.RotatE(
    num_entity=dataset.num_entity,
    num_relation=dataset.num_relation,
    embedding_dim=2048,
    max_score=9,
)
task = tasks.KnowledgeGraphCompletion(
    model,
    num_negative=256,
    adversarial_temperature=1,
    strict_negative=True,
    filtered_ranking=True,
)
optimizer = torch.optim.Adam(task.parameters(), lr=2e-5)
solver = core.Engine(task, train_set, valid_set, test_set, optimizer, gpus=[0], batch_size=1024)
solver.train(num_epoch=200)
solver.evaluate("valid")
```

Decision notes:

- Use `TransE`, `DistMult`, `ComplEx`, `RotatE`, or `SimplE` for standard embedding baselines; use `KBGAT` when graph-attention message passing over KG edges is desired.
- Every embedding model needs `num_entity=dataset.num_entity`, `num_relation=dataset.num_relation`, and a model-specific `embedding_dim`.
- `RotatE` commonly uses a larger `embedding_dim` and `max_score`; smaller dimensions are valid when memory or speed matters.
- `DistMult`, `ComplEx`, and `SimplE` support `l3_regularization`; `TransE`, `RotatE`, and `KBGAT` expose `max_score` instead.

## NeuralLP Recipe

`models.NeuralLP` learns chain-like logical rules. It does not take `num_entity`; it uses the fact graph supplied by the task and requires a careful split between facts and labels:

```python
import torch
from torchdrug import core, datasets, models, tasks

dataset = datasets.FB15k237("~/kg-datasets/")
train_set, valid_set, test_set = dataset.split()
model = models.NeuralLP(
    num_relation=dataset.num_relation,
    hidden_dim=128,
    num_step=3,
    num_lstm_layer=2,
)
task = tasks.KnowledgeGraphCompletion(
    model,
    fact_ratio=0.75,
    num_negative=256,
    sample_weight=False,
    strict_negative=True,
    filtered_ranking=True,
)
optimizer = torch.optim.Adam(task.parameters(), lr=1.0e-3)
solver = core.Engine(task, train_set, valid_set, test_set, optimizer, gpus=[0], batch_size=64)
solver.train(num_epoch=10)
solver.evaluate("valid")
```

When switching from `RotatE` or another embedding model to `NeuralLP`, change both the model fields and the task settings:

- Replace `num_entity`, `embedding_dim`, and `max_score` with `num_relation`, `hidden_dim`, `num_step`, and `num_lstm_layer`.
- Set `fact_ratio`, typically around `0.75`, so part of the training graph remains as background facts while the remainder becomes training labels.
- Set `sample_weight=False` for the tutorial-style NeuralLP setup; degree-based weighting is more natural for embedding-model negatives than rule-learning labels.
- Use smaller batches than large embedding runs because NeuralLP repeatedly propagates over the fact graph and can consume substantial memory.

## Task Parameters

`tasks.KnowledgeGraphCompletion` centralizes training loss, negative sampling, and evaluation:

```python
tasks.KnowledgeGraphCompletion(
    model,
    criterion="bce",
    metric=("mr", "mrr", "hits@1", "hits@3", "hits@10"),
    num_negative=128,
    margin=6,
    adversarial_temperature=0,
    strict_negative=True,
    fact_ratio=None,
    sample_weight=True,
    filtered_ranking=True,
    full_batch_eval=False,
)
```

Use `criterion="bce"` for the common binary classification objective with one positive and sampled negatives. Use `criterion="ce"` for cross entropy over positive-plus-negatives, or `criterion="ranking"` with `margin` for margin ranking loss. A dict of criteria can combine losses with weights.

Negative sampling choices:

- `num_negative` controls sampled corrupt entities during training, and also the evaluation chunk size unless `full_batch_eval=True`.
- `strict_negative=True` avoids sampled negatives that already appear as known facts in the task fact graph.
- `strict_negative=False` is faster and less memory-heavy but can train on false negatives.
- `adversarial_temperature>0` enables self-adversarial weighting of negative samples for `criterion="bce"`; `0` disables it.

Fact graph choices:

- `fact_ratio=None` uses the training split as both facts and labels after excluding validation and test triples from the fact graph.
- `fact_ratio` randomly removes part of the training split from the fact graph and keeps it as labels; use this for NeuralLP-style reasoning where facts are background knowledge.
- Avoid `fact_ratio` for standard embedding baselines unless the user intentionally wants less background graph evidence.

## Metrics and Evaluation

Default metrics are `mr`, `mrr`, `hits@1`, `hits@3`, and `hits@10`. TorchDrug ranks each test triple against corrupt-tail and corrupt-head candidates.

With `filtered_ranking=True`, candidates that are known true triples elsewhere in the full graph are masked out before computing rank. This is the standard protocol used by the TorchDrug reasoning benchmark. `filtered_ranking=False` gives unfiltered ranks and can look worse on dense graphs because other true facts are counted as negatives.

Evaluation scores are computed against all entities. `full_batch_eval=False` splits candidates into chunks of `num_negative` entities, reducing peak memory. `full_batch_eval=True` evaluates all entities in one batch and can be faster on small graphs or large GPUs, but it is the first option to turn off when evaluation runs out of memory.

## Scalability Notes

- Large datasets such as YAGO3-10 and Hetionet can stress entity embeddings, full-ranking evaluation, and strict-negative masks.
- Reduce `embedding_dim`, `batch_size`, or `num_negative` before changing model semantics.
- Keep `full_batch_eval=False` for large entity vocabularies unless memory has been measured.
- NeuralLP propagates over the fact graph; reduce `num_step`, `hidden_dim`, or batch size when memory grows unexpectedly.
- Dataset download and preprocessing happen at dataset construction time; use a stable cache directory for repeated experiments.
