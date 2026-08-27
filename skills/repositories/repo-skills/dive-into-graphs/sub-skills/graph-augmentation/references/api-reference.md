# Graph Augmentation API Reference

## Dataset Helpers

- `DegreeTrans(dataset, in_degree=False)`.
- `AUG_trans(augmenter, device, pre_trans=None, post_trans=None)`.
- `Subset(subset, transform=None)`.
- `TripleSet(dataset, transform=None)`.

## GraphAug Runners

- `RunnerAugCls(data_root_path, dataset_name, conf)`.
- `RunnerGenerator(data_root_path, dataset_name, conf)`.
- `RunnerRewardGen(data_root_path, dataset_name, conf)`.

## S-Mixup

- `smixup(data_root_path, dataset, GMNET_conf)`.

## Configuration Surfaces

- Dataset names: `NCI1`, `COLLAB`, `MUTAG`, `PROTEINS`, `IMDB_BINARY`, `NCI109`, `AIDS`.
- Augmentation types: `node_fm`, `node_drop`, `edge_per`.
- Model types: `gin`, `gcn`, `gmnet`, `genet`.
