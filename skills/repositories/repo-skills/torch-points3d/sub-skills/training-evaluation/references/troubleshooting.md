# Training and Evaluation Troubleshooting

## Hydra selectors do not compose

**Symptoms**

- Missing mandatory values for `task`, `models`, `data`, or `model_name`.
- `model_name <name> isn t within [...]`.
- Dataset config has no `task` or `class` after composition.

**Recovery**

Run a selector smoke before training:

```bash
python sub-skills/training-evaluation/scripts/compose_config_smoke.py \
  --task segmentation \
  --models segmentation/pointnet2 \
  --data segmentation/shapenet-fixed \
  --model-name pointnet2_charlesssg
```

Then make the training command use the same four selectors. If a group does not
exist in the user's checkout/config tree, choose a group listed by the smoke
script or update the config tree before launching training.

## Training contacts W&B or writes profiler/TensorBoard artifacts

**Symptoms**

- The process prompts/logs into W&B.
- TensorBoard event files or profiler traces appear during a short smoke.
- Runs are slower than expected due to profiler activity.

**Recovery**

Override all logging/profiler fields for smoke work:

```bash
training.wandb.log=False \
training.tensorboard.log=False \
training.tensorboard.pytorch_profiler.log=False
```

Only enable them when the user wants experiment tracking artifacts.

## CUDA requested but CPU is used or CUDA fails

**Symptoms**

- Trainer logs CPU even though `cuda=0` was set.
- CUDA/PyG extension import or symbol errors.

**Recovery**

Torch Points3D chooses CUDA only when the config requests a non-negative CUDA
index and `torch.cuda.is_available()` is true. Verify PyTorch and extension
wheels match the installed CUDA runtime. For a CPU smoke, set `training.cuda=-1`
or `cuda=-1` in eval.

## Checkpoint load fails

**Symptoms**

- `The provided path ... didn't contain the checkpoint_file <model_name>.pt`.
- `This weight name isn't within the checkpoint`.
- Loading old checkpoints fails on OmegaConf container pickles.

**Recovery**

1. Run `summarize_runs.py --outputs-dir <outputs>` and verify the checkpoint filename.
2. Set `model_name` to the basename without `.pt`.
3. Set `weight_name` to an available metric token or `latest`.
4. If old OmegaConf containers are the issue, convert a copy with `convert_checkpoint_omegaconf.py`.

## Dataset initialization blocks a training/eval smoke

**Symptoms**

- Dataset constructor starts a large download or preprocessing job.
- Missing raw data files.
- `verify_data` fails because expected attributes are absent.

**Recovery**

Switch to the datasets sub-skill. Validate `dataroot`, data layout, transforms,
and feature fields before rerunning `Trainer`. For synthetic/API checks, use the
model API smoke instead of a full `Trainer` path.

## `precompute_multi_scale` crashes

**Symptoms**

- Collate or multiscale transform errors.
- Error says multiscale is only supported for partial-dense format.

**Recovery**

Set `training.precompute_multi_scale=False` unless using KPConv/partial-dense
models with valid multi-scale strategies. For eval config, set
`precompute_multi_scale=False` if the checkpoint/model does not require it.

## Forward inference writes no predictions

**Symptoms**

- Forward loop skips because test loaders are empty.
- Dataset has no `FORWARD_CLASS`.
- Output directory exists but no `*_pred.npy` files appear.

**Recovery**

Run `forward_preflight.py`, verify checkpoint/data paths, then inspect the
dataset's forward class and `predict_original_samples` behavior. If the dataset
has labels and the user only needs evaluation metrics, use `eval.py` instead of
forward inference.
