# Graph Explainability API Reference

## Datasets and Utilities

- `SynGraphDataset(root, name)`.
- `BA_LRP(root, num_per_class=10000)`.
- `MarginalSubgraphDataset(data, exclude_mask, include_mask, subgraph_build_func)`.
- `MoleculeDataset` and `SentiGraphDataset` for molecule and sentiment workflows.

## Explainers

- `DeepLIFT(model, explain_graph=False)`.
- `GNN_GI(model, explain_graph=False)`.
- `GNN_LRP(model, explain_graph=False)`.
- `GNNExplainer(model, epochs=100, lr=0.01, coff_edge_size=0.001, coff_edge_ent=0.001, coff_node_feat_size=1.0, coff_node_feat_ent=0.1, explain_graph=False, indirect_graph_symmetric_weights=False)`.
- `GradCAM(model, explain_graph=False)`.
- `PGExplainer(model, in_channels, device, explain_graph=True, epochs=20, lr=0.005, coff_size=0.01, coff_ent=0.0005, t0=5.0, t1=1.0, sample_bias=0.0, num_hops=None)`.
- `SubgraphX(model, num_classes, device, num_hops=None, verbose=False, explain_graph=True, rollout=20, min_atoms=5, c_puct=10.0, expand_atoms=14, high2low=False, local_radius=4, sample_num=100, reward_method='mc_l_shapley', subgraph_building_method='zero_filling', save_dir=None, filename='example', vis=True)`.
- `FlowX(model, epochs=500, lr=0.3, explain_graph=False, molecule=False)`.

## Metrics and Evaluation

- `XCollector(sparsity=None)`.
- `ExplanationProcessor(model, device)`.
- `control_sparsity(mask, sparsity=None)`.
- `compatible_state_dict(state_dict)` from `dig.xgraph.utils.compatibility`.
- `load_model(name)` from `dig.xgraph.models.model_manager`.
