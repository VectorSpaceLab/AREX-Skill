# Random Walks and Samplers

## Purpose

Use this reference when a task needs random walks, breadth-first samples,
metapath walks, temporal walks, or unsupervised positive/negative sampling.

## Walk APIs

| API | Verified signature | Typical use |
| --- | --- | --- |
| `UniformRandomWalk` | `(graph, n=None, length=None, seed=None)` then `run(nodes, *, n=None, length=None, seed=None)` | DeepWalk-style structure-only walks. |
| `BiasedRandomWalk` | `(graph, n=None, length=None, p=1.0, q=1.0, weighted=False, seed=None)` then `run(nodes, *, n=None, length=None, p=None, q=None, seed=None, weighted=None)` | Node2Vec-style walks with return/in-out bias. |
| `UniformRandomMetaPathWalk` | `(graph, n=None, length=None, metapaths=None, seed=None)` then `run(nodes, *, n=None, length=None, metapaths=None, seed=None)` | Heterogeneous metapath-guided walks. |
| `SampledBreadthFirstWalk` | `(graph, graph_schema=None, seed=None)` then `run(nodes, n_size, n=1, seed=None, weighted=False)` | GraphSAGE-style homogeneous neighborhood sampling. |
| `SampledHeterogeneousBreadthFirstWalk` | `(graph, graph_schema=None, seed=None)` then `run(nodes, n_size, n=1, seed=None)` | HinSAGE-style heterogeneous neighborhood sampling. |
| `TemporalRandomWalk` | `(graph, cw_size=None, max_walk_length=80, initial_edge_bias=None, walk_bias=None, p_walk_success_threshold=0.01, seed=None)` then `run(num_cw, ...)` | Continuous-time dynamic network walks over temporal edges. |
| `UnsupervisedSampler` | `(G, nodes=None, length=2, number_of_walks=1, seed=None, walker=None)` then `run(batch_size)` | Positive/negative node pairs for unsupervised GraphSAGE. |

## Uniform and biased walks

Use uniform walks for simple structure-only exploration:

```python
from stellargraph.data import UniformRandomWalk
walks = UniformRandomWalk(graph, seed=7).run(nodes=["a", "b"], n=2, length=4)
```

Use biased walks for Node2Vec-style exploration:

```python
from stellargraph.data import BiasedRandomWalk
walks = BiasedRandomWalk(graph, seed=7).run(
    nodes=["a", "b"], n=2, length=5, p=1.0, q=0.5, weighted=False
)
```

`p` controls return bias and `q` controls exploration away from the previous
node. Keep `weighted=True` only when the graph has meaningful edge weights.

## Metapath walks

Metapath walks require a heterogeneous graph and a sequence of node types. A
metapath should match the graph schema and the starting node type.

```python
from stellargraph.data import UniformRandomMetaPathWalk
walks = UniformRandomMetaPathWalk(graph, seed=11).run(
    nodes=["user:1"], n=2, length=4, metapaths=[["user", "group", "user"]]
)
```

If walks are empty or shorter than expected, check that each metapath transition
exists in the graph and that starting nodes have the requested type.

## Breadth-first samples

Breadth-first walkers are the sampling foundation for GraphSAGE/HinSAGE
mini-batch generators. Use them directly only when debugging neighborhood
sampling or building custom flows.

```python
from stellargraph.data import SampledBreadthFirstWalk
samples = SampledBreadthFirstWalk(graph, seed=3).run(nodes=["a"], n_size=[2, 2], n=1)
```

The length of `n_size` should match the number of neighbor-sampling layers in
subsequent model/generator logic.

## Temporal walks

Temporal walks require edges carrying numerical time information in the form
expected by the temporal graph path. Use them for CTDNE-style link prediction or
embedding workflows, not for ordinary static Node2Vec.

When temporal walks fail, first confirm:

- edge times exist and are numeric or converted before graph construction;
- `cw_size` and `max_walk_length` are feasible for the number of temporal edges;
- the graph has enough time-respecting paths for `p_walk_success_threshold`.

## UnsupervisedSampler

`UnsupervisedSampler` generates positive/negative node pairs from random walks
for unsupervised GraphSAGE-style training. The typical pattern is:

```python
from stellargraph.data import UnsupervisedSampler
from stellargraph.mapper import GraphSAGELinkGenerator

sampler = UnsupervisedSampler(graph, nodes=list(graph.nodes()), length=5, number_of_walks=1)
generator = GraphSAGELinkGenerator(graph, batch_size=32, num_samples=[10, 5])
train_gen = generator.flow(sampler)
```

If the generator rejects the sampler, verify that the graph has node features,
that `num_samples` matches the GraphSAGE layer count, and that the downstream
model route expects link-style unsupervised pairs.
