# Registration Workflows

## Purpose

Read this when configuring or debugging Torch Points3D registration models,
datasets, and commands. Registration combines Hydra selectors, pair/fragment
data layouts, metric-learning losses, and optional sparse/Open3D backends.

## Data config families

| Config family | Dataset class pattern | Typical use |
| --- | --- | --- |
| `fragment3dmatch*` | `general3dmatch.General3DMatchDataset` | Fragment-level 3DMatch training/evaluation variants; dense, partial, and sparse configurations exist. |
| `patch3dmatch` | `general3dmatch.General3DMatchDataset` | Patch-level local descriptor training. |
| `fragmentkitti_sparse` | `kitti.KittiDataset` | KITTI fragment registration with sparse data. |
| `modelnet_sparse_ss` | `modelnet.SiameseModelNetDataset` | Siamese ModelNet registration experiments. |
| `test3dmatch*` | `test3dmatch.Test3DMatchDataset` | 3DMatch test/evaluation workflows. |
| `testeth`, `eth_base`, `eth2_base` | `testeth.ETHDataset` / `ETH2Dataset` | ETH test-set evaluation. |
| `testtum`, `testtum_ss` | `testtum.TUMDataset` | TUM test-set evaluation. |
| `testkaist` | `testkaist.KaistDataset` | KAIST test-set evaluation. |
| `testplanetary` | `testplanetary.PlanetaryDataset` | Planetary/IRALab-style evaluation. |

These configs are under the `registration` task, so commands should use
`task=registration`, `data=registration/<config>`, and a model group under
`models=registration/<family>`.

## Model config families

| Model group | Example entry | Backend notes |
| --- | --- | --- |
| `registration/kpconv` | `KPFCNN` | Partial-dense KPConv stack; compiled kernels required. |
| `registration/pointnet2` | `pointnet2_charlesmsg` | Dense PointNet2-style registration model. |
| `registration/pointnet2_patch` | `minipointnet2`, `minipointnet2_small_0` | Patch descriptor variants. |
| `registration/minkowski` | Minkowski fragment entries | Requires `MinkowskiEngine`. |
| `registration/spconv3d` | `ResUnet32` | SparseConv3d backend requirements. |
| `registration/ms_svconv_base` | `MS_SVCONV_*` entries | Multi-scale sparse convolution variants; backend-specific. |

Many registration configs use metric-learning components such as
`ContrastiveHardestNegativeLoss`, `BatchHardMiner`, or `TripletMarginLoss`.
Verify those dependencies and config blocks during composition.

## Command template

```bash
python train.py \
  task=registration \
  models=registration/kpconv \
  data=registration/fragment3dmatch_partial \
  model_name=KPFCNN \
  training.cuda=-1 \
  training.num_workers=0 \
  training.wandb.log=False \
  training.tensorboard.log=False \
  training.tensorboard.pytorch_profiler.log=False \
  debugging=early_break
```

Use this as a shape, not as a promise that the data exists. Real registration
runs need prepared fragments, correspondences, or pair metadata.

## Pair and fragment data contracts

Registration datasets commonly produce paired source/target point clouds and
fields such as:

- `pos` and `x` for each point cloud.
- `pair_ind` for positive correspondence indices.
- `size_pair_ind` for pair counts.
- Fragment identifiers, transforms, overlap metadata, or feature paths depending on the test dataset.

Dense pair batches, PyG pair batches, and multiscale pair batches are different
containers. Match the dataset variant to the model's convolution format.

## FPS utility smoke

The safe native-backed utility path samples correspondence indices using point
positions:

```python
import torch
from torch_points3d.datasets.registration.utils import fps_sampling
pos = torch.tensor([[0,0,0],[0.5,0.5,0],[0.4,0.2,0],[2,2,2],[-1,-2,-0.01]]).float()
pair_ind = torch.tensor([[0,0],[1,1],[2,2],[3,3],[4,4]]).long()
idx = fps_sampling(pair_ind, pos, 3)
```

The bundled `fps_registration_smoke.py` asserts that the selected pairs are the
same reference pairs used by the repository's unit test.

## Sparse registration caveat

Sparse registration configs can require `MinkowskiEngine`, `torchsparse`, CUDA,
and checkpoint/data files. A CPU FPS utility pass does not validate sparse
registration models. Probe optional backends and run a task-specific smoke only
after the user's environment is prepared for that backend.
