# Embedding Workflow Troubleshooting

## Missing optional `gensim`

**Symptoms**

- `ModuleNotFoundError: No module named 'gensim'` in Node2Vec/Metapath2Vec
  notebook-style workflows.

**Recovery**

- Install demo dependencies only when external Word2Vec training is needed:
  `python -m pip install "stellargraph[demos]"` or install `gensim` explicitly.
- If the task only needs random walks, run the bundled random-walk smoke and skip
  Word2Vec training.

## No node features for attribute/GNN embeddings

**Symptoms**

- Attri2Vec, GraphSAGE, GCN/GAT+DGI, or related generator fails feature checks.

**Recovery**

- Use Node2Vec/DeepWalk/GraphWave style structure-only embeddings, or add
  numeric node features before graph construction.
- Print `graph.node_feature_sizes()` and choose a compatible embedding route.

## Walks are empty or too short

**Recovery**

- Confirm starting nodes exist and have the expected type.
- Reduce walk length or number of walks for tiny/sparse graphs.
- For Metapath2Vec, verify metapath node-type transitions against the graph
  schema.

## Keras embedding shape errors

**Recovery**

- Use the matching generator for `Node2Vec` or `Attri2Vec`.
- For manual `Node2Vec(emb_size, node_num, multiplicity)`, provide both
  `node_num` and `multiplicity` when no generator is passed.
- Inspect one generator batch before model compilation.

## Downstream identity loss

**Symptom**

- Embeddings no longer align with original nodes after conversion to arrays.

**Recovery**

- Store embeddings in a DataFrame indexed by external node IDs.
- When using internal ilocs, convert back with graph ID conversion methods before
  returning results.
