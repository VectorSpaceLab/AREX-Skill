---
name: sampling-generators
description: "Guides StellarGraph random walks, samplers, Keras generators, flow
  inputs, batch shapes, and generator-to-model compatibility decisions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Sampling and Generators

Use this sub-skill when a task involves StellarGraph random walks, sampled
neighborhoods, `UnsupervisedSampler`, or Keras-compatible generators that feed
node, link, graph, knowledge graph, or time-series models.

## Read first

- [`references/generator-reference.md`](references/generator-reference.md) for
  generator signatures, `flow` inputs, output shape patterns, and model pairing.
- [`references/random-walks.md`](references/random-walks.md) for uniform,
  Node2Vec-style biased, metapath, breadth-first, and temporal walks.
- [`references/troubleshooting.md`](references/troubleshooting.md) when failures
  mention graph type, node/link IDs, `num_samples`, `n_size`, sparse adjacency,
  Keras `Sequence`, or batch dimensions.
- [`scripts/generator_shape_smoke.py`](scripts/generator_shape_smoke.py) for a
  safe tiny fixture that constructs representative generators and prints batch
  shapes without training or downloads.

## Route here when the user asks to

- choose between `FullBatchNodeGenerator`, `FullBatchLinkGenerator`,
  `GraphSAGENodeGenerator`, `GraphSAGELinkGenerator`, `HinSAGE*Generator`,
  `Attri2Vec*Generator`, `Node2Vec*Generator`, `ClusterNodeGenerator`,
  `RelationalFullBatchNodeGenerator`, `KGTripleGenerator`,
  `PaddedGraphGenerator`, or `SlidingFeaturesNodeGenerator`;
- debug `flow(...)` arguments, target shapes, shuffling, seeds, `use_ilocs`,
  sparse vs dense adjacency, or neighbor-sampling lists;
- sample random walks with `UniformRandomWalk`, `BiasedRandomWalk`,
  `UniformRandomMetaPathWalk`, `SampledBreadthFirstWalk`,
  `SampledHeterogeneousBreadthFirstWalk`, or `TemporalRandomWalk`;
- prepare generator outputs before wiring a TensorFlow/Keras model.

## Route elsewhere

- Raw graph construction and dataset loading belong to
  [`../graph-data-loading/SKILL.md`](../graph-data-loading/SKILL.md).
- Node model selection and Keras heads belong to
  [`../node-classification-gnns/SKILL.md`](../node-classification-gnns/SKILL.md).
- Link prediction and KG scoring logic belong to
  [`../link-prediction-kg/SKILL.md`](../link-prediction-kg/SKILL.md).
- Embedding training/extraction belongs to
  [`../embedding-workflows/SKILL.md`](../embedding-workflows/SKILL.md).
- Graph classification and time-series model workflows belong to
  [`../graph-time-series-workflows/SKILL.md`](../graph-time-series-workflows/SKILL.md).

## Operating workflow

1. Confirm the graph object is valid and has the node/edge types and features
   expected by the target model.
2. Choose the generator family from the model and task:
   - full-batch homogeneous GCN/GAT/PPNP/APPNP: `FullBatchNodeGenerator` or
     `FullBatchLinkGenerator`;
   - inductive/sampled homogeneous GraphSAGE: `GraphSAGENodeGenerator` or
     `GraphSAGELinkGenerator`;
   - directed GraphSAGE: directed GraphSAGE generators with separate in/out
     samples;
   - heterogeneous HinSAGE: `HinSAGENodeGenerator` or `HinSAGELinkGenerator`;
   - graph classification: `PaddedGraphGenerator`;
   - RGCN: `RelationalFullBatchNodeGenerator`;
   - knowledge graph completion: `KGTripleGenerator`;
   - graph time series: `SlidingFeaturesNodeGenerator`.
3. Match generator parameters to the model constructor: `num_samples`, `in_samples`,
   `out_samples`, `method`, `sparse`, `clusters`, `window_size`, or graph list.
4. Use the generator's `flow(...)` method with IDs and targets shaped for the
   task; inspect the first batch before compiling/training a Keras model.
5. Move to the owning model sub-skill only after the generator batch structure
   is understood.

## Common decisions

- `sparse=True` full-batch generators produce sparse adjacency placeholders and
  are usually memory-friendlier; `sparse=False` is simpler for tiny debugging.
- `method="gcn"`, `method="sgc"`-style preprocessing, `method="self_loops"`,
  and APPNP/PPNP methods change adjacency normalization; select the method that
  matches the model reference.
- `num_samples` length should match the number of GraphSAGE/HinSAGE layers.
- Node/link IDs passed to `flow` are external IDs by default. Use `use_ilocs`
  only when you deliberately work with internal locations.

## Safe checks

```bash
python sub-skills/sampling-generators/scripts/generator_shape_smoke.py --help
python sub-skills/sampling-generators/scripts/generator_shape_smoke.py
```

The script builds tiny synthetic graphs and prints representative batch shapes;
it is designed to fail early if the installed package, TensorFlow/Keras, or
basic generator contracts are broken.
