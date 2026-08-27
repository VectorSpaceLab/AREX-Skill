# Training and Evaluation Troubleshooting

## Training starts but fails in dataset construction

Use the `data-preparation` sub-skill. `BddDataset` starts from `MASKROOT/<split>`; missing drivable masks can be the first failure even when images and detection JSONs exist.

## CLI arguments do not change data roots or thresholds

`tools/train.py` and `tools/test.py` parse several arguments that `update_config` does not apply in the current source. If `--dataDir`, `--prevModelDir`, `--conf_thres`, or `--iou_thres` appear ignored, patch `cfg` directly or update `lib/config/default.py`/`update_config` intentionally.

## Modern torch loss smoke fails with `result type Float can't be cast to the desired output type long int`

Observed with modern torch during `build_targets`:

```text
gj.clamp_(0, gain[3] - 1)
gi.clamp_(0, gain[2] - 1)
```

`gj` and `gi` are long tensors while `gain[...]` is a float tensor. Older torch tolerated this more often; newer torch may reject in-place clamp with float bounds.

Recovery options:

1. Use the README-era torch baseline if exact historical behavior is required.
2. Patch the source locally to use integer bounds, for example `int((gain[3] - 1).item())` and `int((gain[2] - 1).item())` in `build_targets`.
3. Re-run `scripts/train_smoke.py --check-loss` after patching.

## `torch.meshgrid` indexing warning

Modern torch may warn that `torch.meshgrid` will require an `indexing` argument. This comes from `Detect._make_grid`. It is a warning for now; a forward-compatible local patch is to call `torch.meshgrid(..., indexing="ij")`.

## CUDA requested but unavailable

Symptoms:

- `AssertionError: CUDA unavailable, invalid device ... requested`.
- `torch.cuda.is_available()` is false.

Recovery:

- For smoke checks or CPU inference, pass `--device cpu` where supported.
- For practical training, install a CUDA-capable torch/torchvision wheel pair matching the driver and Python version.
- Confirm `nvidia-smi`, torch CUDA version, and a tiny CUDA tensor allocation before launching training.

## Batch size and GPU-count issues

`select_device` can assert when batch size is not divisible by visible GPU count. Training/evaluation also multiply per-GPU batch size by `len(cfg.GPUS)`, so stale `GPUS=(0,1)` can produce unexpectedly large CPU or single-GPU batches.

Recovery:

- Set `cfg.GPUS` to the intended visible device tuple.
- Reduce `TRAIN.BATCH_SIZE_PER_GPU` and `TEST.BATCH_SIZE_PER_GPU` for memory-limited runs.
- In CPU smoke contexts, use a tiny helper script rather than `tools/train.py`.

## Auto-anchor is slow or crashes

`NEED_AUTOANCHOR=True` requires labels from the training dataset and runs k-means/evolution. It is not a parser smoke test.

Recovery:

- Leave `NEED_AUTOANCHOR=False` unless anchor recomputation is required.
- Validate dataset labels first.
- Reduce experiment scope or inspect `lib/utils/autoanchor.py` if labels contain tiny/invalid boxes.

## Evaluation checkpoint format mismatch

If `tools/test.py` raises missing `state_dict`, you may be passing `final_state.pth` instead of an epoch checkpoint. Use an `epoch-*.pth` checkpoint saved by `save_checkpoint`, or adapt the loading code for bare state dicts.
