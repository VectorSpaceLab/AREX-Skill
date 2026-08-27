# DIG Capability Map

Use this map to route user requests to focused sub-skills without reopening the original repository.

| User goal or term | DIG namespace / APIs | Route |
| --- | --- | --- |
| 2D molecule generation, GraphAF, GraphDF, GraphEBM, JTVAE, random generation, property optimization, constrained optimization, RDKit validity | `dig.ggraph.dataset`, `dig.ggraph.method`, `dig.ggraph.evaluation`, `dig.ggraph.utils` | `sub-skills/molecular-graph-generation/SKILL.md` |
| 3D molecule coordinate prediction or generation, QM93D, MD17, protein EC/FOLD datasets, SchNet, SphereNet, DimeNet++, ComENet, ProNet, G-SphereNet | `dig.threedgraph`, `dig.ggraph3D` | `sub-skills/three-d-graphs/SKILL.md` |
| GraphCL, GRACE, InfoGraph, MVGRL, pGRACE, contrastive learning, view functions, graph/node SSL evaluation | `dig.sslgraph.method`, `dig.sslgraph.dataset`, `dig.sslgraph.evaluation`, `dig.sslgraph.utils` | `sub-skills/self-supervised-learning/SKILL.md` |
| Explaining GNN predictions, SubgraphX, PGExplainer, GNNExplainer, GNN-LRP, DeepLIFT, GradCAM, FlowX, fidelity/sparsity metrics | `dig.xgraph.method`, `dig.xgraph.dataset`, `dig.xgraph.evaluation`, `dig.xgraph.models` | `sub-skills/graph-explainability/SKILL.md` |
| GOOD-HIV, GOOD-PCBA, GOOD-ZINC, GOOD-CMNIST, GOOD-Motif, GOOD-Cora, GOOD-Arxiv, GOOD-CBAS, domain/shift splits | `dig.oodgraph` | `sub-skills/good-ood-datasets/SKILL.md` |
| Automated graph data augmentation, GraphAug, reward generator, augmentation generator, augmented classifier, S-Mixup, soft alignments | `dig.auggraph.dataset`, `dig.auggraph.method.GraphAug`, `dig.auggraph.method.SMixup` | `sub-skills/graph-augmentation/SKILL.md` |
| Fair representations, sensitive attributes, Graphair, NBA/POKEC, fairness metrics | `dig.fairgraph.dataset`, `dig.fairgraph.method`, `dig.fairgraph.utils.utils` | `sub-skills/fair-graph-learning/SKILL.md` |
| Large graph partitioning, OGB/Reddit/Flickr/Yelp/SBM loaders, GraphFMOB, GraphFMIB, feature momentum, METIS, async pool | `dig.lsgraph.dataset`, `dig.lsgraph.method.FM`, `dig.lsgraph.method.GraphFMOB` | `sub-skills/large-scale-graphs/SKILL.md` |

## Public API Highlights

- 2D generation datasets: `QM9`, `ZINC250k`, `ZINC800`, `MOSES`, `PygDataset`.
- 2D generation methods: `GraphAF`, `GraphDF`, `GraphEBM`, `JTVAE`, `Generator`.
- 2D evaluators: `RandGenEvaluator`, `PropOptEvaluator`, `ConstPropOptEvaluator`.
- SSL methods: `Contrastive`, `GraphCL`, `GRACE`, `InfoGraph`, `MVGRL`, `NodeMVGRL`, `pGRACE`.
- SSL support: `TUDatasetExt`, `get_dataset`, `get_node_dataset`, `GraphUnsupervised`, `GraphSemisupervised`, `NodeUnsupervised`, `Encoder`.
- XGraph explainers: `DeepLIFT`, `GNNExplainer`, `GNN_LRP`, `GNN_GI`, `GradCAM`, `PGExplainer`, `SubgraphX`, `MCTS`, `FlowX`.
- XGraph evaluators: `XCollector`, `ExplanationProcessor`, `control_sparsity`.
- 3D graph methods: `SchNet`, `DimeNetPP`, `SphereNet`, `ComENet`, `ProNet`, and runner class `run`.
- GOOD loaders: static `.load(root, domain, shift=...)` on each GOOD dataset class.

## Example-to-Bundled-Helper Mapping

The original repository examples are not runtime dependencies. This generated skill distills them into internal references and safe smoke scripts:

- GraphDF/GraphAF examples -> molecular generation workflow reference and `molecule_generation_smoke.py`.
- SSL notebooks -> SSL API/workflow references and `sslgraph_smoke.py`.
- SubgraphX tutorial and xgraph benchmark -> xgraph workflow/config references and `xgraph_metric_smoke.py`.
- ThreeDGraph tutorial and ProNet example -> 3D workflow reference and `three_d_smoke.py`.
- GOOD notebook -> GOOD dataset reference and `good_metadata_check.py`.
- GraphAug/S-Mixup scripts -> augmentation workflow/config reference and `augmentation_config_smoke.py`.
- Fairgraph scripts -> fairness workflow reference and `fairgraph_smoke.py`.
- Large-scale examples -> large-scale workflow reference and `lsgraph_feature_momentum_smoke.py`.
