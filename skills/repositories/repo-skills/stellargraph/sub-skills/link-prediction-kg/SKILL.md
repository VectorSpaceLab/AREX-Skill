---
name: link-prediction-kg
description: "Guides StellarGraph link prediction, link regression, edge
  splitting, temporal link workflows, and knowledge graph completion with
  ComplEx, DistMult, RotatE, RotE, and RotH."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Link Prediction and Knowledge Graphs

Use this sub-skill when a StellarGraph task predicts edges/ratings/relations,
performs link regression/classification, splits graph edges into train/test
sets, or scores triples in a knowledge graph.

## Read first

- [`references/link-workflows.md`](references/link-workflows.md) for edge
  splitting, link generators, Keras link heads, temporal link prediction, and
  leakage checks.
- [`references/knowledge-graphs.md`](references/knowledge-graphs.md) for
  `KGTripleGenerator`, `ComplEx`, `DistMult`, `RotatE`, `RotE`, `RotH`, negative
  sampling, and ranking.
- [`references/api-reference.md`](references/api-reference.md) for verified
  signatures and link/KG object responsibilities.
- [`references/troubleshooting.md`](references/troubleshooting.md) for edge
  leakage, invalid endpoints, target-shape, negative sampling, and relation-type
  failures.
- [`scripts/link_prediction_smoke.py`](scripts/link_prediction_smoke.py) for a
  tiny GCN link-classification wiring check.

## Route here when the user asks to

- use `EdgeSplitter.train_test_split`;
- build link prediction with `GraphSAGELinkGenerator`, `HinSAGELinkGenerator`,
  `FullBatchLinkGenerator`, `Attri2VecLinkGenerator`, or `Node2VecLinkGenerator`;
- add `link_classification`, `link_regression`, or `link_inference` to source
  and destination node embeddings;
- perform knowledge graph completion with `KGTripleGenerator`, `ComplEx`,
  `DistMult`, `RotatE`, `RotE`, or `RotH`;
- use `SelfAdversarialNegativeSampling` or rank triples against all nodes;
- adapt CTDNE or temporal link-prediction workflows.

## Route elsewhere

- Raw graph and dataset construction: [`../graph-data-loading/SKILL.md`](../graph-data-loading/SKILL.md).
- Generator shape debugging: [`../sampling-generators/SKILL.md`](../sampling-generators/SKILL.md).
- Node classification: [`../node-classification-gnns/SKILL.md`](../node-classification-gnns/SKILL.md).
- Node embeddings before downstream edge tasks: [`../embedding-workflows/SKILL.md`](../embedding-workflows/SKILL.md).

## Operating workflow

1. Construct a graph with valid node IDs, edge IDs/types, and features required
   by the chosen embedding model.
2. Split edges for evaluation with `EdgeSplitter` or an equivalent leakage-safe
   method. Keep train and test positives/negatives separate.
3. Choose a link generator:
   - GCN/GAT/PPNP-style full-batch embeddings: `FullBatchLinkGenerator`;
   - GraphSAGE: `GraphSAGELinkGenerator`;
   - HinSAGE: `HinSAGELinkGenerator` with head node types;
   - Attri2Vec/Node2Vec link heads: matching link generators;
   - knowledge graph completion: `KGTripleGenerator`.
4. Build the base embedding model and call `in_out_tensors()`.
5. Attach a link head such as `link_classification`, `link_regression`, or
   `link_inference` to combine source/destination embeddings.
6. Compile and train/evaluate with generator `flow(link_ids, targets, ...)`.
7. For knowledge graph models, use negative sampling and ranking routines
   designed for triples rather than ordinary binary edge pairs.

## Safe check

```bash
python sub-skills/link-prediction-kg/scripts/link_prediction_smoke.py --help
python sub-skills/link-prediction-kg/scripts/link_prediction_smoke.py
```

The smoke uses a tiny graph and does not download datasets or train a notebook.
