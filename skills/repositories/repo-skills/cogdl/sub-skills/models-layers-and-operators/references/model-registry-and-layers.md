# Model Registry and Layer Reference

## Purpose

Read this when you need a verified map of CogDL model families, the main
layer signatures, or the `build_model` / parser-augmentation path.

## Verified public APIs

- `build_model(args)` imports the registry entry named by `args.model` and
  returns the model instance built from the model class's `build_model_from_args`.
- `try_adding_model_args(model, parser)` imports the registry module and lets
  the model class extend the parser with model-specific flags when defined.
- `SUPPORTED_MODELS` is the canonical registry map. The inspected checkout
  exposed 74 model names.

## Model families with representative names

| Family | Representative names | Typical task shape |
| --- | --- | --- |
| Semi-supervised / node classification | `gcn`, `gat`, `graphsage`, `gcnii`, `grand`, `grace`, `sign`, `sagn`, `ppnp`, `pprgo`, `mixhop`, `gdc_gcn`, `deepergcn`, `drgat`, `drgcn`, `dropedge_gcn`, `revgcn`, `revgat`, `revgen`, `unsup_graphsage`, `dgi`, `mvgrl`, `gcnmix`, `mlp`, `sgc`, `actgcn`, `unet`, `graphsaint`, `m3s`, `correct_smooth_mlp` | Node classification and unsupervised/semi-supervised graph learning |
| Graph classification | `gin`, `diffpool`, `infograph`, `patchy_san`, `sortpool`, `graph2vec`, `dgk` | Graph-level classification / pooling |
| Network embedding / graph embeddings | `deepwalk`, `node2vec`, `netmf`, `netsmf`, `prone`, `prone++`, `grarep`, `hope`, `line`, `sdne`, `spectral`, `dngr` | Embedding generation and embedding evaluation |
| Knowledge graph / link prediction | `transe`, `distmult`, `complex`, `rotate`, `compgcn`, `rgcn`, `lightgcn` | Triple, graph, or recommendation-style link tasks |
| Heterogeneous / multiplex / traffic / clustering | `gtn`, `han`, `gatne`, `metapath2vec`, `pte`, `hin2vec`, `stgcn`, `stgat`, `agc`, `daegc`, `gae`, `vgae`, `gcc` | Heterogeneous graphs, traffic, multiplex, clustering, and pretraining |

## Verified layer signatures

- `GCNLayer(in_features, out_features, dropout=0.0, activation=None, residual=False, norm=None, bias=True, **kwargs)`
- `GATLayer(in_feats, out_feats, nhead=1, alpha=0.2, attn_drop=0.5, activation=None, residual=False, norm=None)`
- `BaseLayer.forward(self, graph, x)`

These are the signatures observed from the installed package. Keep custom
GNN recipes aligned with these argument names and the `Graph` object passed
in the forward call.

## Model-selection notes

- If you only need a quick classifier, `gcn` and `gat` remain the safest
  baseline choices.
- If the user wants embeddings without labels, choose an embedding model such
  as `prone`, `netmf`, or `deepwalk` and route downstream evaluation back to
  the experiment or pipeline sub-skills.
- If the user wants a graph-level classifier, prefer `gin` or another graph
  pooling model and make sure the data sub-skill has created graph-level
  `Graph` objects.
- If the user asks about `autognn`, remember that it lives in the registry and
  is driven from the experiment/CLI surface rather than from this sub-skill.

## Registry inspection shortcut

Use the bundled script when you need the exact names or want to filter by a
substring instead of scanning the full table by eye.
