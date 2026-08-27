# Training Workflow

## Launch patterns

The source-compatible trainer entrypoint is named `train.py`, but future agents should build launches through the bundled dry-run helper so dataset folders, assets, and high-risk options are checked before execution.

Common guarded command builders:

```bash
python scripts/build_training_command.py --repo-root /path/to/photo2cartoon-checkout --dataset photo2cartoon
```

```bash
python scripts/build_training_command.py --repo-root /path/to/photo2cartoon-checkout --dataset photo2cartoon --pretrained-weights /path/to/photo2cartoon_weights.pt
```

```bash
python scripts/build_training_command.py --repo-root /path/to/photo2cartoon-checkout --dataset photo2cartoon --batch-size 4 --gpu-ids 0 1 2 3
```

```bash
python scripts/build_training_command.py --repo-root /path/to/photo2cartoon-checkout --phase test --dataset photo2cartoon
```

The helper prints the source-compatible command and remains dry-run only unless `--execute` is explicitly supplied.

Notes:

- the repo docs still recommend `batch_size=1` even for multi-GPU runs
- boolean-style arguments use the repo's `str2bool` parser, so pass explicit values such as `--resume true` or `--decay_flag false`
- `--phase test` reuses the same result directory and loads the latest checkpoint before writing test images
- the two training streams are unpaired: `trainA` and `trainB` are iterated independently and do not require filename pairing

## CLI defaults

The important defaults are:

- `--phase train`
- `--light True`
- `--dataset photo2cartoon`
- `--iteration 1000000` — total step budget, not an epoch counter
- `--batch_size 1`
- `--print_freq 1000`
- `--save_freq 1000`
- `--decay_flag True`
- `--lr 0.0001`
- `--adv_weight 1`
- `--cycle_weight 50`
- `--identity_weight 10`
- `--cam_weight 1000`
- `--faceid_weight 1`
- `--ch 32`
- `--n_dis 6`
- `--img_size 256`
- `--img_ch 3`
- `--gpu_ids [0]`
- `--benchmark_flag False`
- `--resume False`
- `--rho_clipper 1.0`
- `--w_clipper 1.0`
- `--pretrained_weights ''`

Important nuance: `--n_dis` is printed by the trainer, but the current model file hardcodes the discriminator layer counts when it builds the networks.

## Result directory naming

`train.py` builds the run root from the script name and several CLI values.
With defaults, the root becomes:

```text
./experiment/train-size256-ch32-True-lr0.0001-adv1-cyc50-id1-identity10-cam1000
```

Under that root, the trainer creates:

- `photo2cartoon/model`
- `photo2cartoon/img`
- `photo2cartoon/test`

Training also writes visualization grids such as `A2B_%07d.png` and `B2A_%07d.png` into `photo2cartoon/img`, while test mode writes `A2B_%d.png` and `B2A_%d.png` into `photo2cartoon/test`.

The source training entrypoint also copies its own `train.py` file into the run root for provenance when executed in a target checkout.

Because the result directory includes `img_size`, `ch`, `light`, `lr`, and the loss weights, `--resume true` or `--phase test` must use the same launch configuration to find the previous run.

## Checkpoint and resume contract

There are two checkpoint patterns:

1. Periodic saves in `.../photo2cartoon/model/`
   - filename pattern: `photo2cartoon_params_%07d.pt`
   - contains six keys: `genA2B`, `genB2A`, `disGA`, `disGB`, `disLA`, `disLB`
2. A latest snapshot in the run root
   - filename pattern: `photo2cartoon_params_latest.pt`
   - written every 1000 steps

Behavior:

- `--pretrained_weights` loads the six module keys directly into the current model during training setup
- `--phase test` ignores `--pretrained_weights` and always loads the latest checkpoint from the run folder
- `--resume true` searches the model folder for the highest numbered `.pt` file and resumes from that step
- resume does **not** restore optimizer state; only model weights and the step index are recovered
- learning-rate decay is recomputed from the step count when training resumes
- if the checkpoint architecture does not match `light`, `ch`, or other shape-sensitive settings, `load_state_dict` will fail

## Loss mix

The trainer uses these weights:

- `adv_weight`: adversarial loss for both generators and discriminators
- `cycle_weight`: cycle-consistency reconstruction loss
- `identity_weight`: identity loss
- `cam_weight`: CAM loss
- `faceid_weight`: Face ID loss from `model_mobilefacenet.pth`

The Face ID branch can be disabled for experiments by setting `--faceid_weight 0`.

After each generator step, the trainer clips Soft-AdaLIN / LIN parameters with `rho_clipper` and `w_clipper`.

## GPU and batch-size cautions

- the trainer assumes CUDA and sets the primary device from the first entry in `--gpu_ids`
- multi-GPU uses `DataParallel`, but the code still recommends `batch_size=1`
- the step performs two generator passes, four discriminators, and Face ID extraction, so memory use rises quickly with larger batches
- if you hit OOM, reduce `batch_size` first, then `img_size`, then `ch`

## Validation before launch

Before starting training, confirm:

- the dataset validator passes for all four splits
- `models/model_mobilefacenet.pth` exists
- any `--pretrained_weights` file exists and contains the six expected keys
- the selected checkpoint path matches the current `result_dir`-building arguments
- you have a separate FID or validation plan if you need the best checkpoint, because `train.py` only saves checkpoints and does not auto-select the winner
