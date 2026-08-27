# Dataset Workflows

## Read a dataset

A typical dataset workflow is:

1. Choose the dataset class from `ml3d.datasets`.
2. Pass a `dataset_path` and any dataset-specific options.
3. Ask for a split such as `training`, `validation`, `test`, or `all`.
4. Read `get_data(idx)` and `get_attr(idx)` from the split.

Example pattern:

```python
import open3d.ml.torch as ml3d

dataset = ml3d.datasets.SemanticKITTI(dataset_path="/path/to/SemanticKITTI")
train = dataset.get_split("training")
item = train.get_data(0)
meta = train.get_attr(0)
```

## Custom dataset pattern

The custom dataset pattern in this repo follows the same base classes:

- Implement a dataset class that returns a split object.
- Implement a split object with `__len__`, `get_data`, and `get_attr`.
- Keep the split directory layout and label mapping explicit.

For `Custom3D`, the most important choice is how you store `.npy` files.
The train/validation split needs labels, while test-only data can omit them.

## Preprocessing and validation

Use preprocessing only when the workflow truly requires it:

- dataset format conversion
- bbox database generation for object-detection augmentation
- train/val/test split materialization
- sanity checks before a long training run

Do not assume the upstream conversion or download scripts are safe to run as-is
inside a future agent session. They may require large external datasets,
network access, or a dataset-specific SDK.

## Object-detection data preparation

Object-detection workflows often need:

- point clouds with intensity or other channels
- calibration metadata
- a list of bounding-box objects

If you build a custom object-detection dataset, make sure the box class and the
point layout are aligned before you hand the data to a model.

## Handoff to training

Dataset outputs are usually consumed by the training sub-skill in one of two
ways:

- the direct API path: construct a dataset object and pass it to a pipeline
- the config-driven path: specify the dataset in a YAML config and let the
  registry build it for you

## Handoff to visualization

A dataset split can also feed the visualization sub-skill directly:

- as a dataset visualization source
- as a prediction comparison source
- as a tiny custom fixture for labels, predictions, and bounding boxes
