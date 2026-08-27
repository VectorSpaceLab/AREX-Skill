# COVID 2D troubleshooting

| Symptom | Likely cause | Safe response |
| --- | --- | --- |
| `TypeError: load_image() got an unexpected keyword argument 'augmentation'` | `COVIDxDataset.__getitem__` passes `augmentation=` even though `load_image` does not accept it | Treat the source branch as blocked until the call signature is aligned or a wrapper removes the extra keyword |
| `NameError: name 'pepx' is not defined` during `CovidNet` construction | The constructor calls `pepx(...)` instead of `PEPX(...)` | Treat `COVIDNET1` / `COVIDNET2` as blocked in the unmodified source; report the constructor typo before attempting a real run |
| torchvision starts looking for pretrained weights or network access | `CNN` instantiates torchvision backbones with `pretrained=True` | Do not instantiate `CNN` in offline smoke runs unless the weights are already cached locally |
| `FileNotFoundError` for manifests or images | The loader expects the manifest and image tree layout described in [`data-layout.md`](./data-layout.md) | Check the split filenames, class directories, and relative image paths before touching the model code |
| `KeyError` for a COVIDx label | The manifest label is not exactly `pneumonia`, `normal`, or `COVID-19` | Fix the manifest label tokens to match the source mapping |
| Shape mismatch in `CovidNet`'s classifier | The input resolution no longer matches the hard-coded flatten head | Keep 224x224-style inputs or redesign the classifier head |
| `AssertionError` inside `accuracy` | Model batch size and target length differ, or labels are not integer class indices | Make sure outputs are `[N, C]` logits and targets are `torch.long` class ids |
| TensorBoard tags look odd | `MetricTracker` prefixes tags with `mode + '/'`, then adds another `/` before the metric name | This is cosmetic; the metric values still log correctly |
| Averages look too coarse | `MetricTracker` averages per iteration, not per sample | If batch sizes differ, compute a separate sample-weighted metric outside the helper |
| `avg_Acc` is not useful | `MetricTracker` does not populate `total` in the current training loop | Prefer `accuracy(...)` or your own aggregate instead of `avg_Acc` |
| Custom CT transforms do not apply | `CovidCTDataset` ignores its `transform` argument | Subclass or wrap the dataset if you need a different augmentation policy |
| Source test parser rejects `CNN` | `tests/test_covid_ct.py` keeps stale `choices` in its CLI parser | Use the bundled smoke script or a custom driver instead of relying on that parser |
| `COVIDx` is configured with `classes=2` | The source test defaults are stale for the 3-class branch | Set `classes=3` whenever you route `dataset_name='COVIDx'` |

## Fast checks

1. Run [`scripts/smoke_covid_imports.py`](../scripts/smoke_covid_imports.py).
2. Confirm the manifests use the right label tokens and file names.
3. Verify `dataset_name` and `classes` match the branch you selected.
4. If the model branch is still failing, check the known source caveats above before debugging the training loop.
