# Troubleshooting

## CUDA and PyTorch

- `torch.cuda.is_available()` is false or `torch.cuda.device_count() == 0`: install a CUDA-enabled wheel that matches the host GPU and driver.
- On modern A100-class machines, avoid old CUDA10-era wheels; use an A100-compatible CUDA wheel.
- If `cuda:0` allocation fails, confirm the driver, wheel, and visible devices before touching training code.

## DareBlopy and TFRecords

- `ModuleNotFoundError: dareblopy`: install DareBlopy and run from a checkout root or set `PYTHONPATH` to that root.
- `TFRecordsDataset` file errors usually mean `DATASET.PATH` / `PATH_TEST` or the resolution/part template is wrong.
- `AssertionError` from `TFRecordsDataset` means `PART_COUNT` is not divisible by the number of visible GPUs.
- If sample grids fail to load, check `DATASET.SAMPLES_PATH` or set it to `no_path` for a loader fallback.

## DDP and NCCL

- `launcher.run` spawns one process per visible GPU when more than one device is present.
- If startup hangs, check `CUDA_VISIBLE_DEVICES`, port conflicts on `12355`, and NCCL availability.
- If memory is tight, lower the chosen `LOD_2_BATCH_*GPU` entries.
- If you only want a smoke run, reduce the visible GPU set to one device before launching.

## Config and YACS key errors

- `-c` can be a bare config name or a YAML path; the launcher adds `.yaml` and checks `configs/<name>.yaml`.
- Trailing command-line values are merged with YACS, so typos are not ignored.
- Use the exact source key names, including `TRUNCATIOM_PSI` and `TRUNCATIOM_CUTOFF`.
- If the config summary looks odd, run the bundled `scripts/inspect_alae_config.py` helper before editing the trainer.

## Checkpoint warnings

- `No checkpoint found` means the run will start from scratch.
- `No state dict for model`, `State dict for model is None`, or `Failed to load` usually mean the checkpoint and config do not match.
- Because loading is `strict=False`, inspect warnings carefully after resume.
- If `last_checkpoint` points to the wrong file, edit the pointer or isolate a new `OUTPUT_DIR`.

## Output directory issues

- Check that `OUTPUT_DIR` exists and is writable.
- Training writes `log.txt`, `log.csv`, `plot.png`, sample images, and checkpoint files there.
- Do not reuse one output directory for unrelated experiments.

## Absent ablation route

- Ignore README references to `train_alae_separate.py`, `model_separate.py`, and `celeba_ablation_*.yaml`; those files are not available in this checkout.
