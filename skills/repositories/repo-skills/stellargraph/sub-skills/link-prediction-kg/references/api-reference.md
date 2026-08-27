# Link and Knowledge Graph API Reference

## Link split and head APIs

| API | Verified signature | Use |
| --- | --- | --- |
| `EdgeSplitter` | `(g, g_master=None)` | Creates train/test edge splits and sampled negative edges. |
| `EdgeSplitter.train_test_split` | `(p=0.5, method='global', probs=None, keep_connected=False, edge_label=None, edge_attribute_label=None, edge_attribute_threshold=None, attribute_is_datetime=None, seed=None)` | Returns split graph, edge IDs/pairs, and labels for link prediction. |
| `link_classification` | `(output_dim=1, output_act='sigmoid', edge_embedding_method='ip')` | Builds a Keras layer/function for binary or multiclass edge classification. |
| `link_regression` | `(output_dim=1, clip_limits=None, edge_embedding_method='ip')` | Builds a numeric link regression head. |
| `link_inference` | `(output_dim=1, output_act='linear', edge_embedding_method='ip', clip_limits=None, name='link_inference')` | General link inference head; `link_classification` and `link_regression` wrap it. |

Common `edge_embedding_method` values include inner product (`ip`) and other
combination methods supported by `LinkEmbedding`; choose the method before
finalizing the Dense/regression output.

## Link generators

| Generator | Constructor | Flow |
| --- | --- | --- |
| `FullBatchLinkGenerator` | same parameters as `FullBatchNodeGenerator` | `flow(link_ids, targets=None, use_ilocs=False)` |
| `GraphSAGELinkGenerator` | `(G, batch_size, num_samples, seed=None, name=None, weighted=False)` | `flow(link_ids, targets=None, shuffle=False, seed=None)` |
| `DirectedGraphSAGELinkGenerator` | `(G, batch_size, in_samples, out_samples, seed=None, name=None, weighted=False)` | directed link `flow(...)` |
| `HinSAGELinkGenerator` | `(G, batch_size, num_samples, head_node_types=None, schema=None, seed=None, name=None)` | heterogeneous link `flow(...)` |
| `Attri2VecLinkGenerator` | `(G, batch_size, name=None)` | context-node/link flow for Attri2Vec |
| `Node2VecLinkGenerator` | `(G, batch_size, name=None)` | context-node/link flow for Node2Vec |

`link_ids` are usually pairs of node IDs for ordinary link prediction. Keep
source/target order meaningful for directed or heterogeneous workflows.

## Knowledge graph APIs

| API | Verified signature | Use |
| --- | --- | --- |
| `KGTripleGenerator` | `(G, batch_size)` | Produces triple batches and negative samples for KG models. |
| `KGTripleGenerator.flow` | `(edges, negative_samples=None, sample_strategy='uniform', shuffle=False, seed=None)` | Feeds positive triples plus sampled negatives. |
| `ComplEx` | `(generator, embedding_dimension, embeddings_initializer='normal', embeddings_regularizer=None)` | Complex-valued KG embedding model. |
| `DistMult` | `(generator, embedding_dimension, embeddings_initializer='uniform', embeddings_regularizer=None)` | Bilinear diagonal KG scoring model. |
| `RotatE` | `(generator, embedding_dimension, margin=12.0, norm_order=2, embeddings_initializer='normal', embeddings_regularizer=None)` | Rotational KG embedding model. |
| `RotE`, `RotH` | `(generator, embedding_dimension, embeddings_initializer='normal', embeddings_regularizer=None)` | Experimental Euclidean/hyperbolic rotational variants. |
| `SelfAdversarialNegativeSampling` | loss class | Loss for self-adversarial negative sampling workflows. |

KG model instances expose `in_out_tensors()`, `embeddings()`,
`embedding_arrays()`, and ranking helpers such as `rank_edges_against_all_nodes`
for evaluation. Use them with a KG generator, not ordinary node/link generators.

## Temporal link prediction

Use `TemporalRandomWalk` from the sampling route for CTDNE-style temporal link
workflows. Temporal graph edges need time information and the downstream link
workflow often trains embeddings outside the ordinary GNN node-classification
path.
