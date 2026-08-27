# Dataset contribution API reference

## Public names

- `DatasetSaver(dataset_name, is_hetero, version, root='submission')`

## Method order

- `save_graph_list(graph_list)`
- `save_target_labels(target_labels)`
- `save_split(split_dict, split_name)`
- `copy_mapping_dir(mapping_dir)`
- `save_task_info(task_type, eval_metric, num_classes=None)`
- `get_meta_dict()`
- `zip()`
- `cleanup()`

## Important constraints

- The dataset name must use one of the `ogbg-`, `ogbn-`, or `ogbl-` prefixes.
- `save_target_labels()` is not needed for `ogbl` link prediction datasets.
- `copy_mapping_dir()` expects a `README.md` inside the mapping directory.
- `get_meta_dict()` should only be called after the earlier steps have
  succeeded.
