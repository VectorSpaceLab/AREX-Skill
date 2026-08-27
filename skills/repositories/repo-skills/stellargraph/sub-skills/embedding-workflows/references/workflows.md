# Embedding Workflows

## Node2Vec / DeepWalk with random walks

Generate walks with `UniformRandomWalk` for DeepWalk-style embeddings or
`BiasedRandomWalk` for Node2Vec-style embeddings. External Word2Vec/Gensim
training is optional and requires demo-style dependencies.

```python
from stellargraph.data import BiasedRandomWalk

walks = BiasedRandomWalk(graph, seed=7).run(
    nodes=list(graph.nodes()), n=10, length=80, p=1.0, q=1.0
)
# Convert nodes to strings before external Word2Vec training if needed.
walks = [[str(node) for node in walk] for walk in walks]
```

Use this route when graph structure alone is the signal. If node features should
matter, consider Attri2Vec or GraphSAGE/DGI.

## Metapath2Vec

For heterogeneous graphs, use metapaths to constrain walks:

```python
from stellargraph.data import UniformRandomMetaPathWalk

walks = UniformRandomMetaPathWalk(graph, seed=7).run(
    nodes=list(graph.nodes(node_type="user")),
    n=5,
    length=100,
    metapaths=[["user", "group", "user"]],
)
```

Check node types and edge schema first; empty walks usually mean the metapath is
not valid for the graph.

## Attri2Vec

Attri2Vec uses node attributes and can support node representation learning and
link-style context prediction.

```python
from stellargraph.mapper import Attri2VecNodeGenerator
from stellargraph.layer import Attri2Vec

generator = Attri2VecNodeGenerator(graph, batch_size=32)
attri2vec = Attri2Vec(layer_sizes=[128], generator=generator)
x_inp, x_out = attri2vec.in_out_tensors()
```

Use the matching link generator when training context/link pairs.

## Unsupervised GraphSAGE

Unsupervised GraphSAGE uses random-walk pairs as positive examples and sampled
negative pairs through the sampler/generator path.

```python
from stellargraph.data import UnsupervisedSampler
from stellargraph.mapper import GraphSAGELinkGenerator
from stellargraph.layer import GraphSAGE, link_classification

sampler = UnsupervisedSampler(graph, nodes=list(graph.nodes()), length=5, number_of_walks=1)
generator = GraphSAGELinkGenerator(graph, batch_size=32, num_samples=[10, 5])
graphsage = GraphSAGE([64, 64], generator=generator)
x_inp, x_out = graphsage.in_out_tensors()
pred = link_classification(output_dim=1, output_act="sigmoid", edge_embedding_method="ip")(x_out)
train_gen = generator.flow(sampler)
```

After training, use a Keras model that returns the embedding tensor for selected
nodes.

## Deep Graph Infomax

DGI wraps a base GNN encoder and trains it with corrupted inputs.

```python
from stellargraph.mapper import CorruptedGenerator, FullBatchNodeGenerator
from stellargraph.layer import GCN, DeepGraphInfomax

generator = FullBatchNodeGenerator(graph, method="gcn")
base_model = GCN([64], generator=generator)
corrupted_generator = CorruptedGenerator(generator)
infomax = DeepGraphInfomax(base_model, corrupted_generator)
x_inp, x_out = infomax.in_out_tensors()
```

After DGI training, call `infomax.embedding_model()` to create the embedding
extraction model. Keep sparse/dense generator settings consistent.

## GraphWave

Use GraphWave for structural role embeddings. Pair `GraphWaveGenerator` with the
GraphWave workflow and keep parameters small for diagnostics; real graphs can be
memory intensive.

## Watch Your Step

Watch Your Step uses adjacency powers and attention:

```python
from stellargraph.mapper import AdjacencyPowerGenerator
from stellargraph.layer import WatchYourStep

generator = AdjacencyPowerGenerator(graph, num_powers=10)
wys = WatchYourStep(generator, num_walks=80, embedding_dimension=64)
x_inp, x_out = wys.in_out_tensors()
```

Use it for structure-heavy node embeddings where adjacency-power information is
useful.

## Downstream use

Always preserve node identity when returning embeddings:

```python
embedding_df = pandas.DataFrame(embeddings, index=node_ids)
```

For link prediction from embeddings, move to the link-prediction route and build
edge-level features from pairs of node embeddings.
