# Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Found 0 files in subfolders` | Flat ImageNet validation folder or missing class subdirectories | Create `train/<class>/` and `val/<class>/` structures before using folder mode |
| `FileNotFoundError: train.zip` or map file | `--zip` enabled but zip layout incomplete | Ensure `train.zip`, `val.zip`, `train_map.txt`, and `val_map.txt` are under the same data root |
| Bad cached zip labels | Map lines are malformed or labels are not integers | Run the bundled validator in `--mode zip` and inspect the reported line |
| JSON decode error for ImageNet-22K | 22K map file is missing or not JSON | Validate with `--mode imagenet22k-json`; ensure the map contains `[path, label]` entries |
| `KeyError: model` when loading checkpoint | File is not a Swin checkpoint dictionary | Inspect checkpoint keys before using `--resume` or `--pretrained` |
| Classifier head mismatch warnings | Checkpoint class count differs from current config | For 21841-to-1000 transfers this is expected; otherwise confirm whether reinitializing the head is desired |

Do not turn these into full data-processing scripts inside the skill. The validator is intentionally read-only and schema-focused.
