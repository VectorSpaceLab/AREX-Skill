# Training and evaluation workflows

## Canonical command forms

Single-GPU training:

```bash
python -m easycv.tools.train CONFIG --work_dir WORK_DIR
```

Distributed training:

```bash
python -m easycv.tools.train CONFIG --work_dir WORK_DIR --launcher pytorch
```

Evaluation:

```bash
python -m easycv.tools.eval CONFIG CHECKPOINT --eval
```

Python wrappers:

```python
import easycv.tools

easycv.tools.train(CONFIG, gpus=8, fp16=True)
easycv.tools.eval(CONFIG, CHECKPOINT, gpus=8, fp16=False)
```

## Common arguments

| Argument | Purpose |
| --- | --- |
| `--work_dir` | Where logs and checkpoints are written. |
| `--resume_from` | Resume from a checkpoint and continue training. |
| `--load_from` | Warm-start from a checkpoint without resuming optimizer state. |
| `--fp16` | Enable mixed precision when the backend supports it. |
| `--launcher` | Choose `none`, `pytorch`, `slurm`, or `mpi`. |
| `--seed` / `--diff-seed` / `--deterministic` | Reproducibility controls. |
| `--model_type` | Replace the config path with a template key from the model-zoo map. |
| `--user_config_params` | Override config values inline. |

## Workflow notes

- Use `model_type` only when you want one of the documented starter configs.
- Prefer an explicit config path when you are already working from a known recipe.
- Replace dataset root variables before launch; the train command does not infer them.
- Validation happens through `eval_pipelines` and the config's evaluation hooks.
- The evaluation command expects a checkpoint and a config that knows how to build the dataset and metrics.

## Task-family examples

- Classification: set ImageNet or CIFAR roots and choose a classification config.
- Detection: update COCO, VOC, or iTAG paths and choose a detection config.
- Segmentation: point at COCO / VOC-style layouts and check `eval_pipelines`.
- Pose: ensure the detection or pose dataset metadata matches the chosen config.
- SSL and metric learning: confirm the filelist or TFRecord layout before launch.
- Video / OCR / 3D: verify the task-specific dataset structure and any custom metadata.

## Logging and visualization

Training configs commonly use TensorBoard or W&B hooks. Read the visualization docs when you need to enable or debug those hooks.

## Safe first checks

- `python -m easycv.tools.train --help`
- `python -m easycv.tools.eval --help`
- `python -c "from easycv.utils.config_tools import CONFIG_TEMPLATE_ZOO; print(len(CONFIG_TEMPLATE_ZOO))"`

