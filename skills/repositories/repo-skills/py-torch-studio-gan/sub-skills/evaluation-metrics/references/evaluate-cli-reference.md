# Standalone `src/evaluate.py` CLI reference

The standalone evaluator compares a generated/target ImageFolder (`--dset2`) against a real/reference ImageFolder (`--dset1`) or precomputed reference caches.

## Core command patterns

Full real-vs-generated report:

```bash
CUDA_VISIBLE_DEVICES=0 python /path/to/PyTorch-StudioGAN/src/evaluate.py \
  -metrics is fid prdc \
  --dset1 /path/to/real_imagefolder \
  --dset2 /path/to/generated_imagefolder
```

FID and PRDC using cached real/reference features and moments:

```bash
CUDA_VISIBLE_DEVICES=0 python /path/to/PyTorch-StudioGAN/src/evaluate.py \
  -metrics fid prdc \
  --dset1_feats /path/to/reference_feats.npz \
  --dset1_moments /path/to/reference_moments.npz \
  --dset2 /path/to/generated_imagefolder
```

Friendly resizer with DDP:

```bash
export MASTER_ADDR=localhost
export MASTER_PORT=2222
CUDA_VISIBLE_DEVICES=0,1 python /path/to/PyTorch-StudioGAN/src/evaluate.py \
  -metrics is fid prdc \
  --post_resizer friendly \
  --dset1 /path/to/real_imagefolder \
  --dset2 /path/to/generated_imagefolder \
  -DDP
```

Use the bundled command builder to assemble these commands without executing metrics: [evaluate_image_folders_command.py](../scripts/evaluate_image_folders_command.py).

## Argument catalog

| Flag | Default | Meaning | Use notes |
| --- | --- | --- | --- |
| `-metrics`, `--eval_metrics` | `fid` | Space-separated metric list. Current meaningful values are `is`, `fid`, `prdc`; `prdc` produces improved precision/recall plus density/coverage. | The parser accepts one or more words. Prefer lowercase. |
| `--post_resizer` | `legacy` | Resizer applied inside the evaluation backbone path. Allowed values: `legacy`, `clean`, `friendly`. | Must match the intended metric convention. See [backbones, resizers, and caches](backbones-resizers-and-caches.md). |
| `--eval_backbone` | `InceptionV3_tf` | Evaluation network. Allowed values: `InceptionV3_tf`, `InceptionV3_torch`, `ResNet50_torch`, `SwAV_torch`, `DINO_torch`, `Swin-T_torch`. | Non-default backbones often trigger hub/download/cache behavior. |
| `--dset1` | none | Real/reference image folder. | Required unless selected metrics can be satisfied by the appropriate cache files. |
| `--dset1_feats` | none | Real/reference feature cache. | Needed to compute PRDC without `--dset1`. StudioGAN reads key `real_feats`. |
| `--dset1_moments` | none | Real/reference moment cache. | Needed to compute FID without `--dset1`. StudioGAN reads keys `mu` and `sigma`. |
| `--dset2` | none | Generated/target image folder. | Required for every useful standalone metric run. |
| `--batch_size` | `256` | Evaluation batch size before DDP splitting. | With DDP, StudioGAN uses `batch_size // world_size`; choose a value divisible by visible GPU count. |
| `--seed` | random if `-1` | Random seed. | Affects data/order-dependent pieces but not metric model weights. |
| `-DDP`, `--distributed_data_parallel` | off | Spawn one evaluation process per visible GPU. | Requires multi-GPU CUDA setup and `MASTER_ADDR`/`MASTER_PORT` environment variables. |
| `--backend` | `nccl` | DDP backend. | `nccl` is CUDA-oriented; `gloo` can be used only if the local PyTorch setup supports the requested device path. |
| `-tn`, `--total_nodes` | `1` | Total nodes for distributed evaluation. | Keep at `1` unless coordinating a multi-node run. |
| `-cn`, `--current_node` | `0` | Current node rank. | Multi-node only. |
| `--num_workers` | `8` | DataLoader workers. | Lower this for tiny tests, constrained systems, or fork/worker failures. |

## Input-combination rules from the implementation

StudioGAN asserts these combinations before running metrics:

| Requested metrics | Minimum reference input when `--dset1` is absent | Why |
| --- | --- | --- |
| `fid` | `--dset1_moments` | FID needs real/reference mean and covariance. |
| `prdc` | `--dset1_feats` | PRDC needs real/reference feature embeddings. |
| `fid prdc` | both `--dset1_moments` and `--dset1_feats` | Moments do not substitute for features, and features do not substitute for moments. |
| `is` only | Prefer `--dset1`; otherwise at least one cache path satisfies the evaluator's initial reference-input assertion even though the cache is not used for dset2 IS. | The standalone source asserts that `--dset1` must be present when neither cache path is provided, even though IS is reported for dset2. |

Additional practical requirements:

- `--dset2` is required by the data-loading path even though the parser default is `None`.
- `--dset1` and `--dset2` must be torchvision ImageFolder-like roots with class subdirectories.
- Cache files produced by StudioGAN are `.npz` files. The current code indexes named arrays from `np.load(...)`; a plain `.npy` array is not a safe substitute.

## Output signals

Successful standalone runs print dataset sizes and per-metric values, for example:

- `Inception score of dset2 ...`
- `FID between dset1 and dset2 ...` or `FID between pre-calculated dset1 moments and dset2 ...`
- `Improved Precision ...`, `Improved Recall ...`, `Density ...`, `Coverage ...`

Do not compare results across different backbones, resizers, real-reference splits, or cache provenance as if they were the same metric protocol.
