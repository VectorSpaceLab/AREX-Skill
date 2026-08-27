---
name: knowledge-graphs
description: "Use TorchDrug for knowledge graph reasoning, triple datasets,
  embedding models, NeuralLP, KGC tasks, negative sampling, and filtered ranking
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Knowledge Graphs

Use this sub-skill when a user asks about knowledge graph reasoning, link prediction over triples, KGC datasets, filtered ranking metrics, negative sampling, or switching between TorchDrug embedding models and NeuralLP.

## When to Use

- The data is a set of `(head, relation, tail)` facts or benchmark knowledge graph triples.
- The task is knowledge graph completion, missing-link prediction, filtered ranking evaluation, or rule-style reasoning.
- The user mentions FB15k, FB15k-237, WN18, WN18RR, YAGO3-10, Hetionet, TransE, DistMult, ComplEx, RotatE, SimplE, KBGAT, or NeuralLP.
- The user needs task-parameter guidance for `KnowledgeGraphCompletion`, including `num_negative`, `fact_ratio`, `sample_weight`, `strict_negative`, `filtered_ranking`, or `full_batch_eval`.

## Quick Routing

- For generic graph tensors, packing, masking, graph construction, or `data.Graph` mechanics, use the sibling `graph-data` sub-skill.
- For `core.Engine`, optimizers, schedulers, checkpoints, logging, and multi-GPU training loops, use the sibling `training-engine` sub-skill.
- For KG-specific model/task/dataset decisions, start with [references/api-reference.md](references/api-reference.md).
- For end-to-end embedding and NeuralLP recipes, use [references/reasoning-workflows.md](references/reasoning-workflows.md).
- For bad triples, relation/entity indexing errors, negative sampling surprises, dataset download issues, or ranking-memory failures, use [references/troubleshooting.md](references/troubleshooting.md).

## Safe Helper

Run [scripts/plan_kg_reasoning.py](scripts/plan_kg_reasoning.py) to print a side-effect-free API skeleton for an embedding or NeuralLP workflow. It does not download datasets, import TorchDrug, allocate GPUs, or train models.
