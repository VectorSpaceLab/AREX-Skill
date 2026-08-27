# ECCV2022-RIFE model and data API notes

These API notes are distilled from the source and live import/signature inspection. The repository is source-only: it does not provide a pip distribution or console entry points. Use a checkout whose root contains `model/RIFE.py`, `inference_img.py`, and `inference_video.py`.

## Import surface

Primary imports used across the repo:

```python
from model.RIFE import Model
from dataset import VimeoDataset
```

The `model/` directory is importable from a checkout root even though it has no `__init__.py`, because Python can treat it as a namespace package when the checkout root is on `sys.path`.

## Device selection

`model.RIFE` defines its module-level device at import time:

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
```

Implications:

- Inference can run on CPU or CUDA, but CUDA is used automatically when visible.
- To force CPU for a smoke check, hide GPUs before importing `model.RIFE`, for example with `CUDA_VISIBLE_DEVICES=""`.
- `train.py` is different: it sets `device = torch.device("cuda")`, initializes an NCCL process group, and is CUDA-only.

## `Model` class

Verified signatures:

```python
Model(local_rank=-1, arbitrary=False)
Model.inference(self, img0, img1, scale=1, scale_list=None, TTA=False, timestep=0.5)
Model.update(self, imgs, gt, learning_rate=0, mul=1, training=True, flow_gt=None)
```

### Construction

- `Model(arbitrary=False)` uses the standard `IFNet` path.
- `Model(arbitrary=True)` uses `IFNet_m` for arbitrary-timestep/RIFE_m-style inference paths used by the HD 4X benchmark.
- If `local_rank != -1`, the model wraps the flow network in `DistributedDataParallel` on that local rank.
- Construction immediately moves the network to the module-level device selected at import time.

### Checkpoint loading and saving

```python
model.load_model(path, rank=0)  # reads path/flownet.pkl when rank <= 0
model.save_model(path, rank=0)  # writes path/flownet.pkl when rank == 0
```

Notes:

- The current `model.RIFE.Model.load_model` expects `flownet.pkl` inside the checkpoint directory.
- The load converter keeps keys containing `module.` and strips that prefix, matching DDP-saved state dicts. A checkpoint without those keys can fail even if the filename exists.
- The inference scripts try HD model imports before falling back to `model.RIFE.Model`; in this checkout the active `model.RIFE_HD*` import paths are absent, so do not assume HD checkpoint compatibility unless matching Python files are supplied and tested.

### Inference tensors

`Model.inference` expects two image tensors:

```python
img0.shape == img1.shape == (N, 3, H, W)
img0.dtype and img1.dtype are floating point
values are normally scaled to 0..1
```

It returns an interpolated image tensor shaped `(N, 3, H, W)` after refinement and clamping to `[0, 1]`. The source CLIs pad inputs before calling the model and crop outputs back to original dimensions; direct API callers should handle padding themselves, especially for non-multiple-of-32 image sizes.

Important parameters:

| Parameter | Meaning |
| --- | --- |
| `scale` | Processing scale used to adjust the internal `[4, 2, 1]` scale list; video CLI exposes this as `--scale`. |
| `scale_list` | Optional explicit three-level scale list. If omitted, `[4, 2, 1]` is divided by `scale`. |
| `TTA` | If true, also runs flipped inference and averages the result. The source CLIs leave it false. |
| `timestep` | Arbitrary timestep parameter accepted by the model; primarily meaningful for arbitrary/RIFE_m-style paths. |

## `Model.update` training contract

`Model.update` is used by `train.py`.

- `imgs` is a 6-channel tensor with `img0` in channels `:3` and `img1` in channels `3:`.
- `gt` is the 3-channel ground-truth middle frame.
- In training mode, it sets the optimizer learning rate, runs the network with concatenated `imgs` and `gt`, computes laplacian/teacher/distillation losses, backpropagates, and steps the optimizer.
- In evaluation mode, it skips optimizer steps and returns predictions plus an info dictionary.

The return shape is:

```python
pred, info = model.update(...)
```

The `info` dictionary includes `merged_tea`, `mask`, `mask_tea`, `flow`, `flow_tea`, `loss_l1`, `loss_tea`, and `loss_distill`.

## `VimeoDataset`

Verified signature:

```python
VimeoDataset(dataset_name, batch_size=32)
```

Data layout expected by `dataset.py`:

```text
vimeo_triplet/
  tri_trainlist.txt
  tri_testlist.txt
  sequences/<sequence-key>/im1.png
  sequences/<sequence-key>/im2.png
  sequences/<sequence-key>/im3.png
```

`VimeoDataset('train')` uses the first 95% of `tri_trainlist.txt`; `VimeoDataset('validation')` uses the remaining 5%; `VimeoDataset('test')` uses `tri_testlist.txt`. Training entries are cropped to `224x224`, augmented with flips/rotations/channel order changes, and returned as `(torch.cat((img0, img1, gt), 0), timestep)`.

## Safe smoke helper

Use the bundled root helper to verify imports and a tiny random inference without checkpoints:

```bash
python scripts/smoke_model_api.py --repo-root <checkout> --device auto --size 32
python scripts/smoke_model_api.py --repo-root <checkout> --device cpu --size 32
python scripts/smoke_model_api.py --repo-root <checkout> --device cuda --arbitrary --size 32 --json
```

The smoke output validates the API/backend only. It uses randomly initialized weights and does not prove interpolation quality, checkpoint compatibility, official benchmark metrics, or training correctness.
