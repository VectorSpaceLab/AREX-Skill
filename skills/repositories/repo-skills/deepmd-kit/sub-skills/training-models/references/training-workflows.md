# DeePMD-kit Training Workflows

Use this reference after selecting a model family/backend. It covers safe command drafting, training input structure, restart/init/fine-tune choices, monitoring, freeze, pretrained, multi-task, and distributed launch patterns.

## Training Input Shape

Most single-task training inputs have these top-level sections:

| Section | Purpose | Common checks |
| --- | --- | --- |
| `model` | `type_map`, descriptor/model family, fitting network. | Descriptor supports backend; `type_map` matches data; `sel` is validated or auto/stat planned. |
| `learning_rate` | Schedule such as exponential decay. | Fine-tuning usually starts lower than from-scratch training. |
| `loss` | Target and prefactors, commonly `ener`. | Label availability matches nonzero prefactors. |
| `optimizer` | Optional/backend-dependent optimizer settings. | DPA workflows often use Adam/AdamW-style settings. |
| `training` | Data systems, validation, steps, checkpoint/log frequencies. | Paths are valid in the user project; `disp_file`, `save_freq`, and `numb_steps` are appropriate for budget. |

Multi-task PyTorch inputs replace single-task model/loss/data structure with:

| Section | Purpose | Common checks |
| --- | --- | --- |
| `model.shared_dict` | Shared descriptors, type maps, or fitting components. | Shared keys are referenced consistently. |
| `model.model_dict` | Per-task model heads/branches. | Each task key has matching loss and data. |
| `loss_dict` | Per-task losses. | Every task key exists in `model_dict`. |
| `training.data_dict` | Per-task train/validation data. | Every task has data; validation may be omitted intentionally only with clear rationale. |
| `training.model_prob` or epoch controls | Task sampling weights/epochs. | Mutually exclusive controls are not mixed. |

## Drafting Commands Without Running

Prefer the bundled helper when the user asks for a command but not execution:

```bash
python scripts/draft_training_command.py --backend pt --input input.json
```

Useful variants:

```bash
python scripts/draft_training_command.py --backend tf --input input.json --restart model.ckpt
python scripts/draft_training_command.py --backend pt --input input.json --init-model model.ckpt.pt
python scripts/draft_training_command.py --backend pt --input input.json --finetune DPA-3.2-5M --model-branch OMat24 --use-pretrain-script
python scripts/draft_training_command.py --backend pt --input input.json --distributed-nproc 4 --skip-neighbor-stat
python scripts/draft_training_command.py --backend pd --input input.json --distributed-nproc 4
```

The helper only prints commands and notes. It does not read input data, validate JSON, download pretrained models, or start training.

## Basic Training Commands

| Backend | Single-process train | Freeze after training | Notes |
| --- | --- | --- | --- |
| TensorFlow | `dp --tf train input.json` | `dp --tf freeze -o model.pb` | `dp train` may default to TensorFlow, but explicit `--tf` is clearer. |
| PyTorch | `dp --pt train input.json` | `dp --pt freeze -o model.pth` | Use for DPA3, DPA4, multi-task, current DDP workflows. |
| JAX | `dp --jax train input.json` | backend/version dependent | Confirm model support before using. |
| Paddle | `dp --pd train input.json` | `dp --pd freeze -o model` | Produces Paddle model artifacts from prefix. |

For smoke validation, reduce training length in the input rather than relying on interrupting a production config. A useful smoke config should create at least one `lcurve.out` row and one checkpoint if freeze is part of the workflow.

## Restart, Init, And Fine-Tune Semantics

| Option | Use when | Command shape | Common mistake |
| --- | --- | --- | --- |
| `--restart PREFIX` | Continuing the same interrupted run. | `dp --pt train input.json --restart model.ckpt.pt` | Using a frozen model as a restart checkpoint. |
| `--init-model PREFIX` | Starting a new run from checkpoint weights. | `dp --pt train input.json --init-model model.ckpt.pt` | Expecting optimizer/training state to continue exactly. |
| `--finetune MODEL` | Adapting a pretrained/frozen model to new data with bias adjustment. | `dp --pt train input.json --finetune pretrained.pt` | Ignoring `type_map` and architecture compatibility. |
| `--use-pretrain-script` | Let input inherit descriptor/fitting parameters embedded in pretrained model. | `dp --pt train input.json --finetune pretrained.pt --use-pretrain-script` | Using with a model that lacks embedded model definition. |
| `--model-branch BRANCH` | Choosing a multi-task pretrained/freeze branch. | `dp --pt train input.json --finetune multitask.pt --model-branch branch_a` | Omitting branch and getting `RANDOM` or random fitting behavior. |
| `--force-load` | PyTorch checkpoint load with missing tensors initialized from scratch. | `dp --pt train input.json --init-model old.pt --force-load` | Treating it as a safe default instead of an explicit compatibility compromise. |

Checkpoint prefixes and frozen model files are not interchangeable. Checkpoints are for training continuation/initialization. Frozen models are for inference/deployment and sometimes fine-tuning depending on backend support.

## Neighbor Statistics And `sel`

Before production training, ensure `sel` is selected by data evidence:

```bash
dp --pt neighbor-stat -s TRAIN_SYSTEM_DIR -r 6.0 -t O H
```

Use the same backend family and `type_map` order planned for training. If the model input uses `sel: auto` or `auto:factor`, avoid `--skip-neighbor-stat` because skipping disables automatic neighbor-stat handling. For bounded smoke runs on known toy data, `--skip-neighbor-stat` can avoid startup cost, but record that sel checking was skipped.

## Monitoring `lcurve.out`

Training reports errors every `training.disp_freq` steps in `training.disp_file`, commonly `lcurve.out`. Interpret columns according to the loss type:

| Signal | Good sign | Bad sign |
| --- | --- | --- |
| `rmse_val` / `rmse_trn` | Finite and generally decreasing after early transient. | `nan`, `inf`, explosive growth, validation much worse than training. |
| Energy RMSE | Decreases with reasonable scale per atom for energy models. | Missing energy labels with nonzero energy prefactor. |
| Force RMSE | Often dominates early training, then decreases. | Missing `force.npy/raw` while force prefactor is nonzero. |
| Virial RMSE | Present only when virial is trained/evaluated. | Nonzero virial prefactors without virial labels. |
| Learning rate | Follows configured decay. | No decay when convergence expects one, or too high for fine-tuning. |
| Task-specific columns | DOS/property/tensor/Hessian/spin columns match chosen loss. | Columns absent or `nan` because labels/config do not match. |

When monitoring a user run, report both the trend and the next action: continue, reduce learning rate, inspect labels, adjust loss weights, fix `type_map`, or stop and reroute to data validation.

## Freezing Workflows

Freeze in the directory or checkpoint folder where training wrote checkpoints, using the same backend family.

```bash
dp --tf freeze -o model.pb
dp --pt freeze -o model.pth
dp --pd freeze -o model
```

For multi-task PyTorch/Paddle models, select the head/branch to freeze:

```bash
dp --pt freeze -o model_branch.pth --head CHOSEN_BRANCH
# --model-branch is an alias for --head in freeze
dp --pt freeze -o model_branch.pth --model-branch CHOSEN_BRANCH
```

After freezing, route `dp test`, `DeepPot`, descriptor evaluation, model deviation, conversion, compression, and deployment checks to `inference-model-ops` unless the user only needs immediate freeze-command guidance.

## Built-In Pretrained Models

The pretrained CLI can download built-in model files into a cache:

```bash
dp pretrained download DPA-3.2-5M
# optional explicit cache location
dp pretrained download DPA-3.2-5M --cache-dir ./models
```

Operational rules:

- Use `dp pretrained download -h` to see names available in the installed version.
- Downloading may require network. Ask before downloading unless the user confirmed cached/offline access or explicitly authorized network use.
- The command prints the local model path on success; use that path for fine-tuning if needed.
- Some APIs can resolve built-in model names directly, but training/fine-tuning workflows should still make cache/network behavior explicit.

## DPA3 Fine-Tuning Pattern

1. Confirm PyTorch backend and DPA3/pretrained model support.
2. Confirm the pretrained model file/name is available locally or ask before downloading.
3. Confirm downstream `type_map`; target elements should be compatible with the pretrained model. New or missing types may initialize randomly depending on backend/rules and must be called out.
4. If architecture details are not known, prefer `--use-pretrain-script` when the pretrained model embeds a model definition.
5. Use a lower `start_lr` than training from scratch and fewer steps at first.
6. For multi-task pretrained models, inspect or ask for available branches and pass `--model-branch`.
7. Run a smoke/bounded fine-tune before scaling.

Single-task pattern:

```bash
dp --pt train input.json --finetune pretrained.pt --use-pretrain-script
```

Multi-task branch pattern:

```bash
dp --pt show multitask_pretrained.pt model-branch
dp --pt train input.json --finetune multitask_pretrained.pt --model-branch CHOSEN_BRANCH --use-pretrain-script
```

If the selected branch is `RANDOM`, state clearly that the fitting head is randomly initialized rather than inherited from a pretrained branch.

## Multi-Task Training Pattern

Use PyTorch unless the installed package explicitly supports another target. A minimal multi-task review must verify:

- `model.shared_dict` contains the shared descriptor/type-map/fitting pieces.
- `model.model_dict` has one key per task/head.
- `loss_dict` has the same task keys.
- `training.data_dict` has the same task keys and valid training systems.
- `training.model_prob` or `training.num_epoch_dict` is present only when intended.
- Freeze and fine-tune branch names are stable and documented.

Example command:

```bash
dp --pt train multi_input.json
```

For fine-tuning from a multi-task pretrained model while retaining older tasks, create a multi-task input where the downstream task uses `finetune_head` to identify the pretrained branch to inherit from. Do not guess branch names; inspect with `dp --pt show MODEL model-branch` when a local model is available.

## Distributed Training Patterns

| Backend | Launcher | Basic command |
| --- | --- | --- |
| TensorFlow | Horovod/MPI | `horovodrun -np 4 dp --tf train input.json` |
| PyTorch | `torchrun` | `torchrun --nproc_per_node=4 --no-python dp --pt train input.json` |
| Paddle | Paddle launch | `python -m paddle.distributed.launch --gpus="0,1,2,3" dp --pd train input.json` |
| JAX | installation-specific | Confirm supported launcher and model constraints before drafting. |

Distributed checklist:

- Validate single-process config first unless the failure is distributed-only.
- Match processes to GPUs and scheduler allocation.
- Confirm all nodes can see training data and checkpoint directory.
- For PyTorch ZeRO/FSDP settings, configure `training.zero_stage` in the input and use `torchrun`.
- For TensorFlow Horovod, learning-rate scaling may change effective optimization; review `scale_by_worker` and decay steps.
- For Paddle, tune `NUM_WORKERS` and file-locking environment variables when data loading stalls.

## Example Water Data Warning

Water examples are useful for command and parser smoke tests, but the bundled tutorial data are intentionally small. Do not present them as production training evidence. If a user asks for a quick water baseline, draft a short bounded run and explicitly mark it as workflow validation only.

## Handoff Template

Use this shape when returning a training plan:

- Model/backend: `se_e2_a` with `--pt`, because ...
- Input status: drafted/reviewed file, important sections, unresolved data labels.
- Neighbor-stat: planned command or skipped with reason.
- Train command: exact command and whether it was run or only drafted.
- Monitoring: `lcurve.out` status and trend if run.
- Checkpoint/freeze: expected checkpoint prefix and freeze command.
- Route-outs: data validation, post-freeze inference/test, or deployment integration.
