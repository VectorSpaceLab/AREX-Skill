# Cross-Cutting Troubleshooting

Use this root troubleshooting guide when the failure appears before a specific workflow owner is clear. Then route to the nearest sub-skill for deeper recovery.

## Imports fail for `core`, `data`, or `model`

The repository is source-script based. Run commands from the checkout root or ensure the checkout root is on `PYTHONPATH`. If the user is using only bundled helper scripts, prefer helpers that do not import the repository.

## Missing dependency

| Symptom | Likely missing dependency | Next step |
|---|---|---|
| `ModuleNotFoundError: lmdb` | LMDB dataset support | Install `lmdb` or use only `datatype: img` workflows. |
| `ModuleNotFoundError: tensorboardX` | TensorBoard writer imported by model scripts | Install `tensorboardX` before running `sr.py`, `infer.py`, or `sample.py`. |
| `ImportError` from W&B logger | Optional W&B logging | Install `wandb` and log in only if the user asked for W&B. |
| Torch/TorchVision CUDA mismatch | Incompatible PyTorch build | Install a torch/torchvision pair matching the CUDA driver/runtime. |

## Config parser fails

The stock configs contain `//` comments. Use the config inspector or the repository parser behavior. Do not use plain `json.load()` on stock config files without stripping comments.

## Dataset path looks right but the loader fails

Route to `sub-skills/data-preparation/SKILL.md`. Most failures come from one of these mismatches:

- `datatype: img` but missing `lr_<L>`, `hr_<R>`, or `sr_<L>_<R>` directories;
- filenames/counts not aligned across triplet directories;
- `mode: LRHR` but no LR images are present;
- `datatype: lmdb` but missing `length` key or expected `hr_`, `sr_`, `lr_` keys;
- `data_len` larger than available images/keys.

## Checkpoint confusion

`path.resume_state` is a stem, not a full filename. The code appends `_gen.pth` for model weights and `_opt.pth` for training resume. Validation/inference can run with only generator weights; training resume needs both files.

## CUDA selected unexpectedly

If config `gpu_ids` is present and non-null, the model wrapper selects CUDA. Passing `-gpu` overrides the config and also exports `CUDA_VISIBLE_DEVICES`. CPU-only operation requires deliberate adaptation; do not describe it as a stock workflow.

## Long runs and apparent hangs

Stock configs use 2000 diffusion timesteps. Validation/inference/sample generation loop through reverse timesteps and can take a long time even after the model loads. For preflight checks, use the bundled command builders and tiny fixture helpers instead of launching full model runs.

## W&B side effects

The scripts only initialize W&B when `-enable_wandb` is passed. Additional table/checkpoint logging depends on script-specific flags:

- `sr.py -log_wandb_ckpt` for checkpoint artifacts during training;
- `sr.py -p val -log_eval` for evaluation tables;
- `infer.py -log_infer` for inference tables;
- `sample.py` has no `-log_eval` or `-log_infer` flag.

Do not pass W&B flags without user approval for network/credential use.
