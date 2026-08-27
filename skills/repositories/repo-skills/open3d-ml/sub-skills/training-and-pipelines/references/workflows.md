# Training and Pipeline Workflows

## Direct semantic-segmentation workflow

Use this when you already have a dataset object and want to work directly with a
model and pipeline.

```python
import open3d.ml.torch as ml3d

model = ml3d.models.RandLANet(num_points=128, num_classes=3, in_channels=3,
                              dim_output=[8, 16, 32, 64])
dataset = ml3d.datasets.SemanticKITTI(dataset_path="/path/to/dataset")
pipeline = ml3d.pipelines.SemanticSegmentation(model, dataset=dataset,
                                               device="cpu")
```

From there you can call `run_inference(data)`, `run_test()`, or `run_train()`
depending on the workflow and data volume.

### CPU vs GPU

- Use `device="cpu"` for import and API smoke checks.
- Use a CUDA/GPU device only when the task really needs backend runtime
  evidence or faster inference/training.
- TensorFlow support is optional and backend-dependent.

## Direct object-detection workflow

```python
import open3d.ml.torch as ml3d
from open3d.ml.utils import Config

cfg = Config.load_from_file("path/to/pointpillars_kitti.yml")
model = ml3d.models.PointPillars(**cfg.model, device="cpu")
dataset = ml3d.datasets.KITTI(dataset_path="/path/to/dataset")
pipeline = ml3d.pipelines.ObjectDetection(model, dataset=dataset,
                                          device="cpu")
```

The object-detection pipeline can then run inference or evaluation on
`bounding_boxes`-style inputs.

## Config-driven workflow

The repo's config flow uses three sections:

- `dataset`
- `model`
- `pipeline`

The bundled helper `scripts/build_run_pipeline_command.py` does not launch a
training run. Instead, it validates a config or model/dataset/pipeline trio and
prints a command-shape summary that future agents can adapt in their own
projects.

Example:

```bash
python scripts/build_run_pipeline_command.py torch -c path/to/config.yml \
  --dataset-path /path/to/dataset --split test --device cpu
```

## Registry-driven selection

The key choice is the exact class name inside the registry:

- `SemanticSegmentation`
- `ObjectDetection`
- `RandLANet`
- `KPFCNN`
- `PointPillars`
- `PointRCNN`

If a lookup fails, confirm the framework string and the model class name.

## Model-selection notes

- RandLANet and KPConv are common semantic-segmentation choices.
- PointPillars and PointRCNN are the object-detection families covered in this
  repo.
- SparseConvUnet, PointTransformer, and PVCNN are available for segmentation
  workflows when the surrounding data and backend support them.

## Checkpoint and cache conventions

- `ckpt_path` is the common checkpoint field.
- `main_log_dir` and cache directories should be explicit in long-running
  workflows.
- Avoid training on a large dataset until the config and dataset layout have
  already been validated.
