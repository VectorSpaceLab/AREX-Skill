# Training, validation, inference, and result workflows

This repository centers on a single `main.py` workflow. Use the root run helper from the generated skill tree rather than invoking the source checkout directly.

If `--root_path` is set, the runtime prepends it to `video_path`, `annotation_path`, `result_path`, `resume_path`, and `pretrain_path` before launching.

## Quick decision table

| Task | Main flags | What to watch |
| --- | --- | --- |
| Train from scratch | `--model`, `--model_depth`, `--n_classes`, `--batch_size`, `--checkpoint` | Make sure `result_path` exists before launch; `opts.json` is written immediately. |
| Resume training | `--resume_path` | The checkpoint `arch` must match `model-model_depth` exactly. |
| Fine-tune a pretrained checkpoint | `--pretrain_path`, `--n_pretrain_classes`, `--n_classes`, `--ft_begin_module` | `n_pretrain_classes` must match the source checkpoint label count. |
| Validate only | `--no_train` | Leave `--no_val` unset. Validation uses `batch_size // n_val_samples`, so keep the batch size large enough for the requested `n_val_samples`. |
| Run inference | `--no_train --no_val --inference --output_topk` | `--inference_batch_size` defaults to `batch_size`; effective work grows with the number of sliding clips. |
| Score results | `scripts/evaluate_results.py` | The result JSON must contain per-video `label` / `score` entries. |
| Strip DataParallel prefixes | `scripts/strip_dataparallel.py` | Use only for `module.`-prefixed checkpoints. |

## Training from scratch

From the repo skill root, create the result directory first and then launch the root wrapper:

```bash
mkdir -p results
python scripts/run_main.py \
  --root_path ~/data \
  --video_path kinetics_videos/jpg \
  --annotation_path kinetics.json \
  --result_path results \
  --dataset kinetics \
  --model resnet \
  --model_depth 50 \
  --n_classes 700 \
  --batch_size 128 \
  --n_threads 4 \
  --checkpoint 5
```

Useful choices:

- `--model` selects the family: `resnet`, `resnet2p1d`, `preresnet`, `wideresnet`, `resnext`, or `densenet`.
- `--model_depth` chooses the family-specific depth. See `references/model-catalog.md` for the full matrix.
- `--checkpoint` controls how often `save_<epoch>.pth` is written.
- `--tensorboard` enables TensorBoard logs in the result directory.

## Resume training

Use `resume_path` when the checkpoint already matches the exact model architecture:

```bash
python scripts/run_main.py \
  --root_path ~/data \
  --video_path kinetics_videos/jpg \
  --annotation_path kinetics.json \
  --result_path results \
  --dataset kinetics \
  --resume_path results/save_100.pth \
  --model resnet \
  --model_depth 50 \
  --n_classes 700 \
  --batch_size 128 \
  --n_threads 4 \
  --checkpoint 5
```

Notes:

- `resume_path` restores the model, optimizer, scheduler, and epoch counter.
- `--overwrite_milestones` can be used if the milestone schedule should be refreshed after resume.
- A resume checkpoint must report the same `arch` string as the current run.

## Fine-tuning from pretrained weights

Pretrained weights are loaded before the final classification head is swapped to the target class count. Keep the source-class count and target-class count separate:

```bash
python scripts/run_main.py \
  --root_path ~/data \
  --video_path ucf101_videos/jpg \
  --annotation_path ucf101_01.json \
  --result_path results \
  --dataset ucf101 \
  --n_classes 101 \
  --n_pretrain_classes 700 \
  --pretrain_path models/resnet-50-kinetics.pth \
  --ft_begin_module fc \
  --model resnet \
  --model_depth 50 \
  --batch_size 128 \
  --n_threads 4 \
  --checkpoint 5
```

Use these rules:

- `--pretrain_path` triggers fine-tuning mode.
- `--n_pretrain_classes` must match the checkpoint's original label count.
- `--n_classes` is the new target dataset class count.
- `--ft_begin_module` is the first top-level module to keep trainable. For ResNet-style models, `fc` is the usual head-only choice; for DenseNet, use `classifier`.

## Validation-only runs

To validate without training, set `--no_train` and keep `--no_val` off. The validation loader uses multiple temporal samples per video, so the batch size is divided by `n_val_samples` internally.

```bash
python scripts/run_main.py \
  --root_path ~/data \
  --video_path kinetics_videos/jpg \
  --annotation_path kinetics.json \
  --result_path results \
  --dataset kinetics \
  --resume_path results/save_200.pth \
  --model resnet \
  --model_depth 50 \
  --n_classes 700 \
  --no_train \
  --batch_size 128 \
  --n_threads 4
```

## Inference and output shapes

Inference runs the validation-style loader with a sliding temporal window:

- `--inference_crop center` keeps the center crop.
- `--inference_crop nocrop` switches to fully convolutional inference with one video per mini-batch.
- `--inference_stride` sets the clip stride.
- `--output_topk` controls how many class scores are saved per clip or per video.
- `--output_topk <= 0` means all classes.
- `--inference_no_average` keeps segment-level outputs instead of averaging across a video.

Averaged output shape:

```json
{
  "results": {
    "video_id": [
      {"label": "class_name", "score": 0.93},
      {"label": "class_name2", "score": 0.04}
    ]
  }
}
```

No-average output shape:

```json
{
  "results": {
    "video_id": [
      {
        "segment": [1, 17],
        "result": [
          {"label": "class_name", "score": 0.93}
        ]
      }
    ]
  }
}
```

`scripts/evaluate_results.py` expects the averaged per-video form, not the `--inference_no_average` segment form.

## Scoring a recognition result

Use the bundled evaluator for top-k accuracy:

```bash
python scripts/evaluate_results.py \
  ~/data/kinetics.json \
  ~/data/results/val.json \
  --subset val \
  -k 1 \
  --ignore
```

Checklist:

- The ground-truth JSON must contain `labels` and `database`.
- The `subset` argument must match the annotation file's split labels exactly.
- The result JSON must be the averaged per-video structure above.
- `--ignore` drops ground-truth entries that do not have a matching result video id.

## Checkpoint cleanup

When a checkpoint was saved from `DataParallel`, strip the leading `module.` prefix before reuse in a single-device or inspection-only context:

```bash
python scripts/strip_dataparallel.py results/save_200.pth --dst_file_path results/save_200.clean.pth
```

Use the cleaned file when:

- You want to inspect keys without the wrapper prefix.
- You need a bare checkpoint for downstream tooling.
- The file was saved from a `nn.DataParallel` run and the consumer does not expect wrapper prefixes.

## Distributed-mode notes

- `--distributed` uses `torch.multiprocessing.spawn` and expects an OpenMPI-style `OMPI_COMM_WORLD_RANK` in the worker environment.
- Launch one process per GPU.
- `--batchnorm_sync` only works when `--distributed` is enabled.
- Inside the worker, batch size and thread count are divided across GPUs.
- `--no_cuda` is for CPU debugging only; it is not a substitute for distributed training.

## Dataset-layout prerequisite

This workflow assumes the video tree and annotation JSON already exist. If frame extraction or annotation generation is missing, switch to [data-preparation](../../data-preparation/SKILL.md) first.
