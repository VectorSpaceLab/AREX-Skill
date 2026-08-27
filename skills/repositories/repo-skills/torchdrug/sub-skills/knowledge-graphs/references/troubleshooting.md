# Knowledge Graph Troubleshooting

## Dataset Downloads

Built-in datasets download train, validation, and test text files when the dataset object is constructed. If construction fails before training starts:

- Check network access and whether the dataset host is reachable. Some datasets use GitHub raw URLs; Hetionet uses Dropbox links.
- Use a writable cache directory and keep it stable between runs so downloads and MD5 checks do not repeat unnecessarily.
- Remove only the failed partial file if an MD5 mismatch occurs; then instantiate the dataset again.
- Avoid putting dataset caches inside ephemeral working directories for long experiments.

## Entity and Relation Indexing

Most custom-data failures come from inconsistent ids or column ordering.

- TSV loaders expect text rows in `(head, relation, tail)` order and build shared vocabularies automatically.
- Direct integer loading with `load_triplet` expects triples in `(head_id, tail_id, relation_id)` order because `data.Graph.edge_list` stores edges as `(source, target, relation)`.
- Entity and relation ids must be consecutive from zero. Gaps or one-based ids can produce out-of-range embeddings or wrong `num_entity` / `num_relation` values.
- Train, validation, and test triples must share one vocabulary. If each split is loaded separately, the same token may receive different ids and filtered ranking becomes invalid.
- For custom classes, build one `KnowledgeGraphDataset`, call `load_tsvs` or `load_triplet` once over all splits, and return split subsets that point back to the same dataset.

## `num_relation` or `num_entity` Mismatch

Symptoms include index errors in embedding lookup, NeuralLP assertion failures, or metrics that fail during evaluation.

- Construct KG models with `dataset.num_entity` and `dataset.num_relation`; do not hard-code benchmark counts unless they were computed from the exact loaded dataset.
- `NeuralLP` takes only `num_relation`, but it asserts that the fact graph relation count matches that constructor value.
- Do not pass the doubled inverse-relation count into `NeuralLP`; TorchDrug adds inverse relations internally during forward scoring.
- If a custom dataset has reserved or unused relation ids, compact the relation vocabulary before loading it into TorchDrug.

## `strict_negative` Behavior

`strict_negative=True` samples corrupt entities that are not known positives in the task fact graph. This is safer for KGC benchmarks but can be expensive on dense or large graphs.

- If training is slow or memory-heavy, lower `num_negative` first.
- Set `strict_negative=False` only when speed matters more than avoiding false negatives.
- Remember that strict sampling checks against `fact_graph`, not arbitrary external facts outside the loaded dataset.
- Very dense relation patterns may leave few valid negatives; reduce batch size or negative count if sampling becomes unstable.

## `fact_ratio` Misuse

`fact_ratio` changes the training data semantics. It is not just a regularization knob.

- Use `fact_ratio=None` for standard embedding baselines unless the user intentionally wants to hide part of the training graph from the fact graph.
- Use a float such as `0.75` for NeuralLP so the model has background facts for reasoning and separate labels for learning.
- `fact_ratio` is applied to the training subset after validation/test triples are excluded from facts.
- Because the held-out training portion is sampled randomly, set PyTorch random seeds outside the task if exact reproducibility matters.

## `sample_weight` Choices

With `sample_weight=True`, TorchDrug down-weights triplets from high-degree entity/relation combinations. This is the default for embedding tasks.

- Keep `sample_weight=True` for common embedding recipes unless matching a paper configuration that disables it.
- Use `sample_weight=False` for the tutorial-style NeuralLP recipe.
- If sample weighting raises unexpected shape or index errors, inspect custom triples for invalid ids before changing the flag.

## Filtered Ranking Expectations

Filtered ranking masks other known true triples before computing ranks. It is the default and the protocol used in TorchDrug's reasoning benchmark.

- `filtered_ranking=True` usually reports better and more standard MRR / HITS than unfiltered evaluation.
- `filtered_ranking=False` can penalize a model for ranking another true triple above the test triple.
- Filtered ranking depends on the full loaded graph, so split vocabularies or missing facts can make scores misleading.
- MR is lower-is-better, while MRR and HITS@K are higher-is-better.

## GPU and Memory Failures

Knowledge graph completion evaluates each test triple against all entities for corrupt-head and corrupt-tail ranking. Memory scales with batch size, entity count, model size, and evaluation chunking.

- Keep `full_batch_eval=False` on large graphs; this chunks entity candidates by `num_negative`.
- Reduce `batch_size`, `num_negative`, and `embedding_dim` when CUDA memory is exhausted.
- For `KBGAT`, reduce hidden dimensions, attention heads, or batch size because graph attention stores message-passing activations.
- For `NeuralLP`, reduce `hidden_dim`, `num_step`, or batch size because recurrent graph propagation can dominate memory.
- If evaluation OOMs but training works, lower `num_negative` for smaller evaluation chunks or keep evaluation on CPU if speed is acceptable.

## Metrics Fail or Look Impossible

When metrics error or look implausible:

1. Print `dataset.num_entity`, `dataset.num_relation`, and `len(train_set)`, `len(valid_set)`, `len(test_set)`.
2. Check that every triple index satisfies `0 <= head < num_entity`, `0 <= tail < num_entity`, and `0 <= relation < num_relation`.
3. Verify direct integer triples use `(head, tail, relation)` rather than `(head, relation, tail)`.
4. Confirm validation/test subsets reference the same parent dataset as the training subset.
5. Compare `filtered_ranking=True` and `False` only after the vocabulary and split contract are correct.
