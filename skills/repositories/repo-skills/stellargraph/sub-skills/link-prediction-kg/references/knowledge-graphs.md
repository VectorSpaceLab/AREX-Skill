# Knowledge Graph Completion

## Purpose

Use this reference for StellarGraph workflows that model triples `(source,
relation, target)` rather than ordinary binary links. These workflows use
`KGTripleGenerator` and knowledge graph embedding models.

## Core pattern

```python
from stellargraph.mapper import KGTripleGenerator
from stellargraph.layer import ComplEx
from tensorflow.keras import Model, optimizers, losses, metrics

generator = KGTripleGenerator(graph, batch_size=1024)
kg_model = ComplEx(generator, embedding_dimension=200)
x_inp, x_out = kg_model.in_out_tensors()
model = Model(inputs=x_inp, outputs=x_out)
model.compile(
    optimizer=optimizers.Adam(learning_rate=0.001),
    loss=losses.BinaryCrossentropy(from_logits=True),
    metrics=[metrics.BinaryAccuracy(threshold=0.0)],
)
train_gen = generator.flow(train_edges, negative_samples=10, shuffle=True, seed=7)
```

The graph should encode relation types so triples can be mapped to source node,
relation, and target node IDs. Use the generator's `flow` method rather than
ordinary link generators.

## Model choice

| Model | Use when | Notes |
| --- | --- | --- |
| `ComplEx` | Need asymmetric relation modeling with complex embeddings | Constructor uses normal initializer by default. |
| `DistMult` | Relations are mostly symmetric or a simpler bilinear model is enough | Constructor uses uniform initializer by default. |
| `RotatE` | Rotation-based relation composition is desired | Has `margin` and `norm_order` parameters. |
| `RotE`, `RotH` | Experimental Euclidean/hyperbolic rotational variants | Treat as experimental; verify on small data before relying on them. |

## Negative sampling

`KGTripleGenerator.flow(edges, negative_samples=None, sample_strategy="uniform",
shuffle=False, seed=None)` controls negative triple generation. If
`negative_samples` is `None`, only positive triples are supplied; most training
setups need negatives.

Use `sample_strategy="uniform"` unless the task has evidence for a different
strategy. Keep a fixed `seed` when comparing results.

## Ranking and embeddings

KG model objects expose methods such as:

- `embedding_arrays()` and `embeddings()` for inspecting learned entity/relation
  embeddings;
- `in_out_tensors()` for Keras model wiring;
- `rank_edges_against_all_nodes(test_data, known_edges_graph, tie_breaking="random")`
  for filtered-style ranking evaluation.

When ranking, pass a graph of known edges to avoid counting known true triples as
false negatives. Choose and report `tie_breaking` behavior because ranking can
change when many scores tie.

## Losses

`SelfAdversarialNegativeSampling` is available in `stellargraph.losses` for
self-adversarial negative sampling workflows. Use it only when the model output
and negative sampling setup match the loss assumptions.

## Boundary with ordinary link prediction

Use ordinary link generators and `link_classification` when a task predicts
whether an edge exists between two nodes. Use KG models when the relation type is
part of the prediction target or triples must be ranked/scored by relation.
