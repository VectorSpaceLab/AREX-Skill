# Self-Supervised Learning API Reference

## Encoders

- `Encoder(feat_dim, hidden_dim, n_layers=5, pool='sum', gnn='gin', node_level=False, graph_level=True, **kwargs)`.
- The wrapped `GIN`, `GCN`, and `ResGCN` implementations are exposed internally by `Encoder`.

## Contrastive Base Class

- `Contrastive(objective, views_fn, graph_level=True, node_level=False, z_dim=None, z_n_dim=None, proj=None, proj_n=None, neg_by_crpt=False, tau=0.5, device=None, choice_model='last', model_path='models')`.
- `train(encoder, data_loader, optimizer, epochs, per_epoch_out=False)` yields trained encoders per epoch.

## Derived Methods

- `GraphCL(dim, aug_1=None, aug_2=None, aug_ratio=0.2, **kwargs)`.
- `GRACE(dim, dropE_rate_1, dropE_rate_2, maskN_rate_1, maskN_rate_2, **kwargs)`.
- `InfoGraph(g_dim, n_dim, **kwargs)`.
- `MVGRL(g_dim, n_dim, diffusion_type='ppr', alpha=0.2, t=5, **kwargs)`.
- `NodeMVGRL(z_dim, z_n_dim, diffusion_type='ppr', alpha=0.2, t=5, batch_size=2, num_nodes=2000, **kwargs)`.
- `pGRACE(dim, proj_n_dim, centrality_measure, prob_edge_1, prob_edge_2, prob_feature_1, prob_feature_2, tau=0.1, dense=False, p_tau=0.7, **kwargs)`.

## View Functions and Objectives

- `NodeAttrMask`, `EdgePerturbation`, `Diffusion`, `DiffusionWithSample`, `UniformSample`, `RWSample`, `RandomView`, `Sequential`, `AdaEdgePerturbation`, `AdaNodeAttrMask`.
- `NCE_loss` and `JSE_loss` are the two exposed contrastive objectives.

## Datasets and Evaluators

- `TUDatasetExt(root, name, task, ...)`.
- `get_dataset(name, task, feat_str='deg', root=None)`.
- `get_node_dataset(name, norm_feat=False, root=None)`.
- `GraphSemisupervised`, `GraphUnsupervised`, and `NodeUnsupervised` expose the evaluation side of SSL workflows.
