# Embedding Model Reference

## Constructors and pairings

| API | Verified signature | Pairing / use |
| --- | --- | --- |
| `Node2Vec` | `(emb_size, generator=None, node_num=None, multiplicity=None)` | Keras embedding layer path with `Node2VecNodeGenerator` or explicit `node_num` and `multiplicity`. |
| `Attri2Vec` | `(layer_sizes, generator=None, bias=False, activation='sigmoid', normalize=None, input_dim=None, node_num=None, multiplicity=None)` | Attribute-aware embedding model; pair with Attri2Vec generators. |
| `DeepGraphInfomax` | `(base_model, corrupted_generator=None)` | Wraps a base StellarGraph model and exposes `in_out_tensors()` plus `embedding_model()`. |
| `WatchYourStep` | `(generator, num_walks=80, embedding_dimension=64, attention_initializer='glorot_uniform', attention_regularizer=None, attention_constraint=None, embeddings_initializer='uniform', embeddings_regularizer=None, embeddings_constraint=None)` | Attention over adjacency powers; pair with `AdjacencyPowerGenerator`. |
| `GraphWaveGenerator` | generator class | Structural role embeddings; see generator reference for shapes. |
| `UnsupervisedSampler` | `(G, nodes=None, length=2, number_of_walks=1, seed=None, walker=None)` | Produces unsupervised node pairs for GraphSAGE link-style training. |

## StellarGraph Keras Node2Vec vs external Word2Vec

The package supports two different Node2Vec-style patterns:

1. **Random-walk + external Word2Vec/Gensim**: generate walks with
   `BiasedRandomWalk`, convert node IDs to string tokens, train a Word2Vec model,
   and use learned vectors downstream.
2. **StellarGraph Keras `Node2Vec` layer**: use `Node2VecNodeGenerator` or
   `Node2VecLinkGenerator` and the `Node2Vec` Keras layer/model class.

Do not mix the APIs: a Gensim Word2Vec model is not a Keras `Node2Vec` model,
and the Keras generator does not train Gensim.

## DGI embedding extraction

`DeepGraphInfomax(base_model, corrupted_generator=None)` wraps an existing
StellarGraph model stack. After training the DGI model, call `embedding_model()`
to obtain a Keras model that maps original graph inputs to embeddings. Keep the
same generator/corrupted-generator sparse setting consistent.

## GraphWave and Watch Your Step

GraphWave and Watch Your Step are structural embedding approaches. They are good
fits when structural role or adjacency-power information matters more than node
attributes. Watch Your Step exposes `embedding_dimension` and `num_walks`, while
GraphWave uses its generator's graph-wavelet parameters.
