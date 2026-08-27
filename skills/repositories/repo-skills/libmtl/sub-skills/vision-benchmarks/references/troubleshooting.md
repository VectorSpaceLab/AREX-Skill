# vision-benchmarks Troubleshooting

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `FileNotFoundError` for `image/`, `label/`, `depth/`, or `normal/` | The preprocessed directory tree is incomplete | Restore the missing `.npy` folders or point `dataset_path` at the correct root. |
| Output tensors have the wrong spatial size | The decoder outputs were not resized back to the benchmark resolution | Keep the example's `process_preds(...)` override. |
| `PLE` raises a single-input error | `PLE` only supports `multi_input=False` | Use another architecture or switch to the Office benchmark family. |
| `MTAN` fails on a custom encoder | The encoder is not ResNet-shaped | Use a ResNet-based backbone or add the expected `resnet_network` attribute. |
| The script cannot find `utils.py`, `aspp.py`, or `segnet_mtan.py` | The example was run from the wrong directory | `cd` into the example directory before running the command. |
| First run stalls on backbone weights | The ResNet or torchvision weights need to be downloaded | Allow network access or prefill the model cache. |

## NYUv2-specific notes

- The benchmark uses DeepLabV3+ and SegNet+MTAN launch patterns.
- `--aug` is optional and changes the augmentation pipeline in the dataset
  loader.

## Cityscapes-specific notes

- Cityscapes uses the sibling NYU helper modules.
- The benchmark is still single-input, so `multi_input` must stay `False`.
- The dataset root path in the docs points at the preprocessed `cityscapes2`
  layout, not the raw benchmark release.
