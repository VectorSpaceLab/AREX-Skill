# Knowledge Graph API Reference

This reference summarizes the TorchDrug APIs most relevant to knowledge graph reasoning. For generic graph tensor operations, use the sibling `graph-data` sub-skill. For `core.Engine` training mechanics, use the sibling `training-engine` sub-skill.

## Dataset Entry Points

`data.KnowledgeGraphDataset` represents one knowledge graph and exposes:

- `load_tsv(tsv_file, verbose=0)`: reads rows as `(head_token, relation_token, tail_token)` and builds consecutive entity and relation vocabularies.
- `load_tsvs(tsv_files, verbose=0)`: reads multiple TSV files with shared vocabularies and stores per-file counts for split reconstruction.
- `load_triplet(triplets, entity_vocab=None, relation_vocab=None, inv_entity_vocab=None, inv_relation_vocab=None)`: loads integer triples as `(head_id, tail_id, relation_id)`.
- `num_entity`, `num_relation`, and `num_triplet`: expose graph sizes.
- `graph`: the underlying `data.Graph` whose `edge_list` columns are `(head, tail, relation)`.

Built-in KG datasets subclass `KnowledgeGraphDataset`, download train/valid/test files, call `load_tsvs`, and implement `split()` by slicing the concatenated graph in file order:

| API | Domain | Notable scale |
| --- | --- | --- |
| `datasets.FB15k(path, verbose=1)` | Freebase subset | 14,951 entities, 1,345 relations, 592,213 triples |
| `datasets.FB15k237(path, verbose=1)` | Filtered FB15k | 14,541 entities, 237 relations, 310,116 triples |
| `datasets.WN18(path, verbose=1)` | WordNet | 40,943 entities, 18 relations, 151,442 triples |
| `datasets.WN18RR(path, verbose=1)` | Filtered WN18 | 40,943 entities, 11 relations, 93,003 triples |
| `datasets.YAGO310(path, verbose=1)` | YAGO3-10 subset | 123,182 entities, 37 relations, 1,089,040 triples |
| `datasets.Hetionet(path, verbose=1)` | Biomedical Hetionet | 45,158 entities, 24 relations, 2,025,177 triples |

## Model Entry Points

All KG models score triples through `forward(graph, h_index, t_index, r_index, all_loss=None, metric=None)`. `KnowledgeGraphCompletion` supplies the graph and index tensors.

### Embedding Models

- `models.TransE(num_entity, num_relation, embedding_dim, max_score=12)`: translational baseline; tune `embedding_dim` and `max_score`.
- `models.DistMult(num_entity, num_relation, embedding_dim, l3_regularization=0)`: bilinear diagonal model; simple and efficient but symmetric in relation scoring.
- `models.ComplEx(num_entity, num_relation, embedding_dim, l3_regularization=0)`: complex-valued bilinear model; useful for asymmetric relations.
- `models.RotatE(num_entity, num_relation, embedding_dim, max_score=12)`: complex rotation model; strong default for many KGC benchmarks.
- `models.SimplE(num_entity, num_relation, embedding_dim, l3_regularization=0)`: canonical polyadic style reciprocal embedding model.
- `models.KBGAT(num_entity, num_relation, embedding_dim, hidden_dims, max_score=12, **kwargs)`: graph-attention model over KG edges; accepts additional `GraphAttentionNetwork` keyword arguments.

Use `dataset.num_entity` and `dataset.num_relation` directly. Mismatches between these fields and the dataset graph usually produce index errors or invalid scores.

### NeuralLP

- `models.NeuralLP(num_relation, hidden_dim, num_step, num_lstm_layer=1)` is an alias for TorchDrug's `NeuralLogicProgramming` implementation.
- It models chain-like rules up to `num_step` relations and uses LSTM attention over relation choices.
- It internally augments the graph with inverse relations during scoring, but the constructor expects the original dataset relation count.
- It asserts that the fact graph relation count equals `num_relation`; this fails when the dataset/task/model are built from different vocabularies.

## Task Entry Point

`tasks.KnowledgeGraphCompletion(model, criterion="bce", metric=("mr", "mrr", "hits@1", "hits@3", "hits@10"), num_negative=128, margin=6, adversarial_temperature=0, strict_negative=True, fact_ratio=None, sample_weight=True, filtered_ranking=True, full_batch_eval=False)`

Parameter decision notes:

- `model`: one of the KG scorers above, or a compatible module with the same forward contract.
- `criterion`: `"bce"` is the common default; `"ce"` and `"ranking"` are also supported; a dict can weight multiple criteria.
- `metric`: use `mr`, `mrr`, and `hits@K` strings such as `hits@10`.
- `num_negative`: higher values can improve sampled training signal but increase memory; during chunked evaluation it also controls entity-candidate chunk size.
- `margin`: only affects `criterion="ranking"`.
- `adversarial_temperature`: use a positive value for self-adversarial negative weighting with BCE; leave at `0` to disable.
- `strict_negative`: default `True`; avoids known positives in sampled negatives by querying the fact graph.
- `fact_ratio`: default `None`; set a float such as `0.75` for NeuralLP-style background fact splitting.
- `sample_weight`: default `True`; degree-based down-weighting for embedding losses. Tutorial NeuralLP uses `False`.
- `filtered_ranking`: default `True`; standard filtered protocol for KG benchmarks.
- `full_batch_eval`: default `False`; set `True` only when full all-entity scoring fits memory.

During preprocessing, the task records `num_entity`, `num_relation`, the full graph, and a `fact_graph`. Validation and test triples are removed from `fact_graph`; with `fact_ratio`, part of the training split is also removed from facts and kept as train labels.

## Custom Dataset Contract

For a custom KG dataset, ensure these invariants before creating the model and task:

1. Entity ids are consecutive integers from `0` to `num_entity - 1`.
2. Relation ids are consecutive integers from `0` to `num_relation - 1`.
3. All splits share the same vocabulary and graph object, or are represented as subsets of one loaded `KnowledgeGraphDataset`.
4. Text TSV rows use `(head, relation, tail)`, but direct integer graph edges use `(head, tail, relation)`.
5. `dataset.num_entity` and `dataset.num_relation` are passed unchanged into the model constructor.
6. `train_set`, `valid_set`, and `test_set` passed to `core.Engine` match the task's dataset and split assumptions.

## Model Selection Guide

- Start with `RotatE` for a strong embedding baseline on FB15k-237, WN18RR, YAGO3-10, or Hetionet.
- Use `TransE` for a fast translational baseline or when interpretability of vector translations matters.
- Use `DistMult` or `ComplEx` for compact bilinear baselines; prefer `ComplEx` for asymmetric relation patterns.
- Use `SimplE` when comparing against reciprocal CP-style embeddings.
- Use `KBGAT` when the user explicitly wants attention over graph neighborhoods, and budget extra memory for message passing.
- Use `NeuralLP` when the user asks for differentiable rule learning, chain-like logical reasoning, or interpretable relation paths.
