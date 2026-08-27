# Training Workflows

## Native CPU smoke plan

Use a tiny, bounded smoke only after weight/data downloads are allowed or assets are already present:

```bash
python train.py --imgsz 64 --batch-size 32 --weights yolov3-tiny.pt --cfg yolov3-tiny.yaml --epochs 1 --device cpu --name smoke --exist-ok
```

The repository guidance sometimes uses `--batch` as an argparse abbreviation for `--batch-size`; prefer the full `--batch-size` flag in generated commands.

To build the command without running it:

```bash
python sub-skills/training/scripts/yolov3_command_builder.py --imgsz 64 --batch-size 32 --weights yolov3-tiny.pt --cfg yolov3-tiny.yaml --epochs 1 --device cpu --name smoke --exist-ok
```

## Custom dataset YAML

A standard dataset YAML needs `train`, `val`, and `names`. `nc` is optional in this repo because `utils.general.check_dataset()` derives it from `names`, but include it only when it matches the number of names:

```yaml
path: ../datasets/my-dataset
train: images/train
val: images/val
nc: 3
names: [cat, dog, person]
```

Run the checker before training:

```bash
python sub-skills/training/scripts/yolov3_dataset_yaml_check.py data/my-dataset.yaml --repo-root <yolov3-checkout>
```

Be careful with `download:` entries because they can run shell/Python download logic.

## Pretrained vs scratch

- Pretrained fine-tuning: keep `--weights yolov3-tiny.pt` or another `.pt` checkpoint and provide `--cfg` when changing architecture.
- Scratch training: pass an empty weights string and a model YAML, for example `--weights '' --cfg yolov3-tiny.yaml`.
- Resume: use `--resume` or `--resume path/to/last.pt` when checkpoint state exists.

## Important flags

- Data/model: `--weights`, `--cfg`, `--data`, `--hyp`.
- Runtime: `--epochs`, `--batch-size`, `--imgsz`, `--device`, `--workers`, `--cache`.
- Training behavior: `--rect`, `--resume`, `--nosave`, `--noval`, `--noautoanchor`, `--image-weights`, `--multi-scale`, `--single-cls`, `--optimizer`, `--cos-lr`, `--label-smoothing`, `--patience`, `--freeze`.
- Outputs: `--project`, `--name`, `--exist-ok`, `--save-period`, `--noplots`.
- Distributed: `--sync-bn` and `--local_rank` are DDP-specific; validate launcher and devices first.
