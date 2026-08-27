# Classification Troubleshooting

## Dataset layout issues

- A missing `train/` or `val/` class directory usually means the ImageFolder layout is wrong.
- Named dataset strings may download data; switch to a local path if network access is not allowed.
- If class counts look wrong, inspect the directory names and ensure both splits share the same class set.

## Model-choice issues

- Use `yolov5*-cls.pt` for YOLOv5 classifiers.
- Use torchvision model names only when the training script explicitly supports them.
- A detection or segmentation checkpoint is not a classification checkpoint.
- `--pretrained` and `--freeze` alter training behavior; check them before blaming the optimizer.

## Device and size issues

- Use `--imgsz 224` for the documented classifier path unless the user has a different target.
- Remove `--half` on CPU.
- Reduce batch size if memory pressure appears.
- Use a CUDA device for realistic training or benchmarking; CPU is fine for parser checks.

## Output and run-directory issues

- Set `--project` and `--name` explicitly.
- Use `--exist-ok` only when overwriting or reusing a run directory is intended.
- Use `--nosave` for inspection-only prediction commands.

## Verification signals to expect

- CLI help prints parser usage.
- YOLOv5-cls and torchvision model names are accepted where documented.
- Classification outputs are class probabilities or top-k predictions.
