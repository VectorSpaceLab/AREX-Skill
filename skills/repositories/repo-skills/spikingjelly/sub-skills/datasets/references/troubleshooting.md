# Dataset troubleshooting

## Fast triage

1. Print the class metadata before downloading anything:

   ```python
   from spikingjelly.datasets import DVS128Gesture
   print(DVS128Gesture.downloadable())
   print(DVS128Gesture.resource_url_md5())
   print(DVS128Gesture.get_H_W())
   ```

2. Check the staged directories: `root/download`, `root/extract`, raw `root/events_np` or `root/events_h5`, then processed frame roots such as `root/frames_number_20_split_by_number` or `root/duration_1000000`.
3. If the processed directory already exists but outputs look wrong, delete the relevant processed directory and rebuild. If `root/extract` already exists, SpikingJelly warns that it will not re-check extracted-file integrity.
4. Use `scripts/dataset_tiny_fixture_smoke.py` to confirm the package-level builder utilities work before debugging real data.

## Symptoms and fixes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `NotImplementedError: This dataset can not be downloaded...` | `downloadable()` is `False` for the selected dataset. | Call `resource_url_md5()`, download every listed file manually, and place it under `root/download` before constructing the dataset. |
| `The downloaded file ... is missing or corrupted` | File is absent, has a wrong name, or MD5 does not match. | Re-download into `root/download`. For manual sources, keep the exact filenames from `resource_url_md5()`. |
| Extraction succeeds but later preprocessing fails | `root/extract` was left from a previous incomplete run and is not integrity-checked. | Remove `root/extract` and the affected raw/processed dirs, then instantiate the dataset again. |
| `data_type must be "event" or "frame"` | Unsupported `data_type`. | Use only `data_type='event'` or `data_type='frame'`. |
| `When data_type="frame", one and only one...` | More than one frame strategy was passed, or none was passed. | Pick exactly one: `frames_number` + `split_by`, `duration`, or `custom_integrate_function`. |
| `split_by must be "time" or "number"` | Fixed-frame-count integration is missing its split policy. | Set `split_by='number'` for equal event counts or `split_by='time'` for equal timestamp windows. |
| Dataset constructor rejects `train=None` | The class requires an explicit split flag. | For classes such as `DVS128Gesture`, `NMNIST`, `DVSLip`, `ESImageNet`, `Bullying10kClassification`, and `SpikingHeidelbergDigits`, pass `train=True` or `train=False`. |
| Dataset constructor has no `train` argument | The dataset has no built-in split or exposes a different split API. | Use the class-specific constructor: `CIFAR10DVS(root, ...)`, `NCaltech101(root, ...)`, `ASLDVS(root, ...)`, `NAVGestureWalk/Sit(root, ...)`, or `HARDVS(root, train_test_val='train'|'val'|'test')`. Use `split_to_train_test_set` or a split wrapper when needed. |
| CIFAR10-DVS results do not match a paper using TEBN split | Plain `CIFAR10DVS` is unsplit. | Use `CIFAR10DVSTEBNSplit`; it uses samples `0..99` as test and `100..999` as train per class. |
| DVS128Gesture sample counts differ from another framework | Frameworks use different gesture-splitting logic. | SpikingJelly slices by `trials_to_train.txt` / `trials_to_test.txt` and CSV timestamp ranges; its documented count is 1176 train and 288 test. Compare only against the same preprocessing rule. |
| Frame batches fail to stack | Fixed-duration integration produced different sequence lengths. | Use `torch.utils.data.DataLoader(..., collate_fn=pad_sequence_collate)` and build masks with `padded_sequence_mask(lengths)`. |
| Custom integration creates an odd output directory | Default directory name is `custom_integrate_function.__name__`. | Pass `custom_integrated_frames_dir_name='stable_name'` explicitly, especially for lambdas, closures, or reused functions. |
| Custom integration loads but downstream shape is wrong | The function returned a non-frame shape. | Vision custom functions should normally return `[T, 2, H, W]`; SHD/SSC-style audio builders expect `[T, W]`. |
| `KeyError: 'frames'` when loading frames | A `.npz` was saved without the `frames` key. | Save integrated frame files as `np.savez(path, frames=frames)` or use SpikingJelly's file-integration helpers. |
| `KeyError` for `t`, `x`, `y`, or `p` | The raw event file is not normalized to the common event dict. | Use the dataset-specific loader/converter (`load_aedat_v3`, `load_ATIS_bin`, ESImageNet's `pos/neg` loader, or class `create_raw_from_extracted`). Do not feed arbitrary `.npz` files directly to generic builders unless they have the expected keys. |
| SHD/SSC event data look missing `y`/`p` | Neuromorphic audio datasets are one-dimensional event streams. | Use `events['t']` and `events['x']`; frame arrays are `[T, 700]`, not `[T, 2, H, W]`. |
| NAVGesture frame width seems unexpected | Source code uses `get_H_W() == (240, 304)` even though the camera note says 240x320. | Use the class-reported geometry when integrating; do not hard-code 320. |
| Preprocessing is too slow or uses too many threads | Dataset conversion uses `configure.max_threads_number_for_datasets_preprocess`. | Set `SJ_MAX_THREADS_NUMBER_FOR_DATASETS_PREPROCESS=<positive int>` before starting Python. |
| Frame/event `.npz` files are unexpectedly large or slow to read | `utils.np_savez` follows `SJ_SAVE_DATASETS_COMPRESSED`. | Set `SJ_SAVE_DATASETS_COMPRESSED=0` for faster uncompressed writes/reads, or keep the default compressed setting to save disk. Set before Python imports `spikingjelly.configure`. |
| `play_frame` never returns | It opens an interactive playback loop when `save_gif_to=None`. | For scripts, pass `save_gif_to='sample.gif'` or prefer `save_as_pic` for finite output. |
| A temporal-delete transform changes the wrong dimension | `batch_first` does not match input layout. | Use `batch_first=True` for `[N, T, ...]`; use `False` for `[T, N, ...]`. |

## Manual-data checklist

For manual datasets, create exactly this staging pattern before construction:

```text
root/
  download/
    <every file returned by DatasetClass.resource_url_md5()>
```

Then instantiate the dataset once to let SpikingJelly populate `extract` and `events_np` or `events_h5`. Do not pre-create partial raw or processed directories unless you know they are complete; existing directories cause SpikingJelly to skip some work.

Common manual classes: `DVS128Gesture`, `NMNIST`, `NCaltech101`, `ASLDVS`, `DVSLip`, `HARDVS`, `NAVGestureWalk`, and `NAVGestureSit`.

## Routing after data is healthy

- If the dataset loads but the training loop, optimizer, model, or distributed data loader fails, switch to `../training-and-scaleout/`.
- If the issue is sequence state, `reset_net`, `step_mode`, or SNN module shape semantics after loading frames, switch to `../core-snn/`.
- If the data are being used for ANN2SNN calibration or converted-model evaluation, switch to `../ann2snn/` after the sample layout is verified.
