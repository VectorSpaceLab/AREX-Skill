# Runtime stack and GPU guidance

## Source evidence

This reference is distilled from `docs/INSTALL.md`, `docs/TRAIN_EVAL.md`, `README.md`, `requirements.txt`, and the environment report captured for this repo checkout.

## Public UniAD v2.0 runtime stack

The public v2.0 install target is:

| Component | Version |
| --- | --- |
| Python | 3.9 |
| PyTorch | `2.0.1+cu118` |
| torchvision | `0.15.2` |
| torchaudio | `2.0.2` |
| mmcv-full | `1.6.1` |
| mmdet | `2.26.0` |
| mmsegmentation | `0.29.1` |
| mmdet3d | `1.0.0rc6` |

Repository runtime dependencies called out in `requirements.txt` include `opencv-python`, `einops`, `casadi`, `pytorch-lightning`, `ipython`, `yapf`, `motmetrics`, `torchmetrics`, `networkx`, and `pandas`.

## Import and backend expectations

- The repo is imported by placing the repository root on `PYTHONPATH` and importing `projects.mmdet3d_plugin`.
- The train/eval workflows depend on CUDA PyTorch and MMCV CUDA ops for truthful reproduction.
- CPU is only a substitute for static config parsing, CLI rendering, and other non-execution checks.
- The public skill should not claim full result reproduction without CUDA-capable execution.

## GPU and memory guidance

### Recommended launch size

- UniAD recommends at least 8 GPUs for both stage1 and stage2 training.
- Evaluation examples also assume 8 GPUs.
- Fewer GPUs are allowed, but the run becomes slower and metrics may shift slightly.

### Stage1 track/map

- Rough training memory: about 50 GB on 8 A100 GPUs.
- Rough wall-clock: about 2 days for 6 epochs on 8 A100 GPUs.
- Memory-saving hint from the source docs: lowering `queue_length` from 5 to 3 reduces memory to about 30 GB and can fit V100 32GB cards, at the cost of some tracking performance.

### Stage2 end-to-end

- Rough training memory: about 17 GB on 8 A100 GPUs.
- Rough wall-clock: about 4 days for 20 epochs on 8 A100 GPUs.
- The stage2 docs note that the BEV encoder is frozen, which is why the memory footprint is much lower.
- The source docs state that stage2 can run on V100 or 3090-class devices.

## Workdir and log behavior

- The distributed and SLURM wrappers derive a per-config work dir by replacing `configs` with `work_dirs` in the config path and appending a trailing slash.
- Wrapper logs land in `.../logs/train.<timestamp>` or `.../logs/eval.<timestamp>`.
- Direct `tools/train.py` runs use `./work_dirs/<config-basename>` only when the config and CLI both leave `work_dir` unset.
- `tools/train.py` also copies the resolved config into the work dir before training begins.

## Determinism and metric drift

- Both Python entry points accept `--seed` and `--deterministic`.
- The train wrapper forces `--deterministic`.
- The source docs explicitly warn that evaluation on a different number of GPUs than 8 can produce slightly different results.
- Treat the published metric values as reference targets, not as a bit-for-bit guarantee across all launch topologies.

## Inspection caveat

A private verification environment for this checkout may use a different CUDA wheel pair if the public v2.0 pair is not available as a prebuilt wheel during inspection. In that case:

- treat the alternative wheel pair as probe-only,
- keep the public stack above as the runtime target,
- and do not advertise the probe stack as the published v2.0 environment.

The environment report for this checkout also noted a known `pip check` metadata conflict around `networkx` versus `mmdet3d` pinning. That mismatch is a packaging caveat, not a reason to rewrite the public stack guidance in the skill.
