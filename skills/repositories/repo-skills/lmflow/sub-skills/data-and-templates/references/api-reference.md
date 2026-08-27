# Dataset and Template API Reference

## `DatasetArguments`

Key fields that affect dataset handling:

- `dataset_path`
- `dataset_name`
- `train_file`
- `validation_file`
- `test_file`
- `block_size`
- `streaming`
- `overwrite_cache`
- `validation_split_percentage`
- `preprocessing_num_workers`
- `disable_group_texts`
- `keep_linebreaks`
- `train_on_prompt`
- `conversation_template`
- `dataset_cache_dir`
- `calculate_dataset_stats`

## `Dataset`

Frequently used methods:

- `Dataset(data_args, backend="huggingface")`
- `from_dict(dict_obj)`
- `create_from_dict(dict_obj)`
- `to_dict()`
- `to_list()`
- `map(...)`
- `save(file_path, format="json")`
- `sample(n, seed=42)`
- `train_test_split(test_size=0.2, shuffle=True, seed=42)`
- `drop_instances(indices)`
- `sanity_check(...)`

## Behavior Notes

- `Dataset.create_from_dict()` is the quickest way to assemble a tiny fixture for a future script or test.
- `Dataset.from_dict()` validates the required fields for the selected type.
- `Dataset.save()` writes the LMFlow dictionary format back to disk.
- `conversation_template` controls how conversation rows are formatted for model consumption.

## When To Read This Reference

- Before repairing a broken dataset.
- Before writing a tiny fixture for a workflow helper.
- Before deciding whether a support workflow belongs in this sub-skill or in a training/alignment sub-skill.
