# Training Troubleshooting

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `KeyError: 'LOCAL_RANK'` or `WORLD_SIZE` when starting `train.py` or even `--help` | `mmaudio.sample` reads distributed env vars at import time. | Launch through `torchrun --standalone ...` or set the distributed env vars before calling the script. |
| `Unknown model: large_44k_v2` | The training path only accepts model names ending in `16k` or `44k`. | Use `small_16k`, `small_44k`, `medium_44k`, or `large_44k`. |
| The run resumes an older checkpoint even though `weights=` was passed | An existing `output/<exp_id>/<exp_id>_ckpt_last.pth` shadows `weights=`. | Use a fresh `exp_id`, delete the old checkpoint, or pass the exact `checkpoint=` file you want. |
| Both `checkpoint=` and `weights=` were set | The intent is ambiguous. | Keep only one: `checkpoint=` for full resume, `weights=` for model-only initialization. |
| `batch_size` seems to shrink on multi-GPU runs, or the effective per-GPU batch is not what you expected | `train.py` divides the configured batch size by world size. | Pass a total batch size that is divisible by the number of GPUs. |
| `batch_size` becomes zero on small multi-GPU smoke runs | The total batch size is smaller than the world size. | Increase `batch_size` or reduce the world size. |
| `NCCL` init hangs or `torchrun` never reaches the training loop | Distributed launch is misconfigured or stale env vars are present. | Use `torchrun --standalone`, stay on a single node, and clear hand-set rank env vars if you are not using `torchrun`. |
| `FileNotFoundError` or `torch.load` errors for `ext_weights/...` | Required external assets are missing. | Populate `ext_weights/` with `empty_string.pth`, the correct VAE, Synchformer, and vocoder files. |
| Validation or final sample fails with av-bench import/cache errors | `av_bench` is not installed or the evaluation caches are missing. | Install the package and make sure the `gt_cache` paths in the data config exist. |
| `example_train=True` still cannot find the example data | The bundled example memmap outputs were never created. | Build the example memmaps first; the training route does not create them. |
| `mini_train=True` did not produce the mini dataset you expected | The current loader logic overwrites that branch. | Use `example_train=True` instead. |
| `torch.compile` makes the run sluggish to start or fails on the first step | Compile warm-up or backend incompatibility. | Disable `compile` for smoke and debugging. |
| The smoke run is still longer than expected or fails after the last optimization step | The training loop may be bounded, but the script still performs the post-training sample path against the extracted VGGSound test cache. | Treat the command as a bounded training-loop smoke, not a zero-eval dry run. |
| Audio or feature loading is extremely slow | Memmap random reads are too expensive for the storage path. | Use fast NVMe or enough system memory to cache the memmaps. |

## Quick checks

- Verify the command is launched with `torchrun` before debugging anything else.
- Verify the chosen model matches the feature layout behind the loaded memmaps.
- Verify that a reused `exp_id` is not silently resuming from an older checkpoint.
- Verify that the selected `batch_size` is compatible with the requested world size.

## Evidence labels

`docs/TRAINING.md`, `train.py`, `mmaudio/runner.py`, `mmaudio/sample.py`, `mmaudio/data/data_setup.py`, `config/base_config.yaml`, `config/train_config.yaml`, `config/data/base.yaml`.
