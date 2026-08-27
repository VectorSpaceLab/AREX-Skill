---
name: embedding-workflows
description: "Guides StellarGraph unsupervised representation learning with
  Node2Vec, DeepWalk-style walks, Metapath2Vec, Attri2Vec, GraphSAGE
  unsupervised sampling, Deep Graph Infomax, GraphWave, and Watch Your Step."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Embedding Workflows

Use this sub-skill when the goal is to learn or extract node, edge, or graph
embeddings before downstream clustering, visualization, classification, or link
prediction.

## Read first

- [`references/workflows.md`](references/workflows.md) for Node2Vec/DeepWalk,
  Metapath2Vec, Attri2Vec, unsupervised GraphSAGE, DGI, GraphWave, and Watch
  Your Step recipes.
- [`references/model-reference.md`](references/model-reference.md) for verified
  constructors and generator pairings.
- [`references/troubleshooting.md`](references/troubleshooting.md) for optional
  dependency, no-feature graph, random-walk, and embedding extraction issues.
- [`scripts/random_walk_smoke.py`](scripts/random_walk_smoke.py) for a safe
  random-walk smoke without `gensim` training or downloads.

## Route here when the user asks to

- produce Node2Vec/DeepWalk or Metapath2Vec walks/embeddings;
- use the StellarGraph Keras `Node2Vec` or `Attri2Vec` model classes;
- train unsupervised GraphSAGE using `UnsupervisedSampler`;
- wrap a base model with `DeepGraphInfomax` and extract embeddings;
- compute GraphWave or Watch Your Step embeddings;
- use embeddings in scikit-learn, visualization, or downstream link/node tasks.

## Route elsewhere

- Random walk parameter debugging: [`../sampling-generators/SKILL.md`](../sampling-generators/SKILL.md).
- Supervised node classification: [`../node-classification-gnns/SKILL.md`](../node-classification-gnns/SKILL.md).
- Link prediction consuming embeddings: [`../link-prediction-kg/SKILL.md`](../link-prediction-kg/SKILL.md).
- Graph classification using graph-level labels: [`../graph-time-series-workflows/SKILL.md`](../graph-time-series-workflows/SKILL.md).

## Operating workflow

1. Decide whether embeddings should use only graph structure, node attributes,
   heterogeneous metapaths, or a GNN encoder.
2. Validate graph IDs and features. Structure-only walks can work without node
   features; Attri2Vec, GraphSAGE, DGI base models, and many GNN encoders require
   numeric node features.
3. Choose the route:
   - Node2Vec/DeepWalk: random walks plus external Word2Vec/Gensim or the Keras
     `Node2Vec` path;
   - Metapath2Vec: heterogeneous metapath walks plus external Word2Vec/Gensim;
   - Attri2Vec: `Attri2VecNodeGenerator`/`Attri2VecLinkGenerator` and
     `Attri2Vec`;
   - unsupervised GraphSAGE: `UnsupervisedSampler` + `GraphSAGELinkGenerator` +
     `GraphSAGE`;
   - DGI: base GCN/GAT/GraphSAGE/HinSAGE model plus `DeepGraphInfomax`;
   - GraphWave: `GraphWaveGenerator` for structural embeddings;
   - Watch Your Step: `AdjacencyPowerGenerator` and `WatchYourStep`.
4. Keep embedding extraction separate from downstream evaluation. Save or pass a
   DataFrame/array indexed by node IDs so downstream tasks do not lose identity.

## Safe check

```bash
python sub-skills/embedding-workflows/scripts/random_walk_smoke.py --help
python sub-skills/embedding-workflows/scripts/random_walk_smoke.py
```

The smoke verifies random-walk generation and does not train Word2Vec or a neural
model.
