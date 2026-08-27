---
name: training
description: "Plan and launch DINO training or fine-tuning on COCO-style
  detection data with validated single-process, distributed, or Submitit/Slurm
  commands, configuration choices, checkpoint semantics, and safe recovery
  guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DINO training orchestration

Use this sub-skill when a Researcher must train or fine-tune DINO on COCO
2017 or a compatible COCO-style detection dataset. It covers selecting the
shipped 4-scale/5-scale and ResNet/Swin/ConvNeXt configurations, composing a
safe command, choosing one process, `torch.distributed`, or Submitit/Slurm,
and interpreting checkpoints and logs. It does not itself prepare dataset
schemas, compile the CUDA operator, run evaluation, or download weights.

## Route first

| Request or observation | Route |
|---|---|
| Dataset root, annotation/category layout, target tensors, or custom dataset implementation | Stop and use [data-model-setup](../data-model-setup/SKILL.md); return here only after its data/model gate passes. |
| CUDA deformable-attention build/import, compiler, PyTorch, or GPU compatibility | Use [data-model-setup](../data-model-setup/SKILL.md) before planning a run. |
| Scale/backbone choice, class count, batch size, optimizer, schedule, fine-tuning, or launch mode | Read [configuration.md](references/configuration.md), then [workflows.md](references/workflows.md). |
| COCO AP evaluation, prediction, visualization, or inference output interpretation beyond the evaluation command | Route to [inference-evaluation](../inference-evaluation/SKILL.md). |
| A command or run failure | Read [troubleshooting.md](references/troubleshooting.md), preserve the output directory, and classify the failure before retrying. |

Do not treat an evaluation printed during training as a substitute for the
inference/evaluation workflow. Do not start a long job from the bundled
planner: `scripts/build_dino_command.py` validates and prints only.

## Operating procedure

1. **Record the run contract.** Capture the DINO checkout, config path, data
   root, output directory, intended class-ID convention, device count,
   per-process batch size, world size, checkpoint source, and stopping rule.
   Keep the exact command in the run record. A non-empty `--output_dir` is
   required by the current `main.py` save path.
2. **Pass the setup gate.** Ask [data-model-setup](../data-model-setup/SKILL.md)
   to validate the COCO-style root and required splits, target tensors, the
   selected config/model shape, and the CUDA
   `MultiScaleDeformableAttention` extension. The verified inspection host
   has Python 3.11, CUDA-enabled PyTorch 2.5.1+cu121 on an A100, and an
   importable custom op, but it has no COCO data or checkpoint available.
3. **Select one config.** Use `DINO_4scale.py` for the normal ResNet-50
   baseline, `DINO_5scale.py` for the five-level ResNet-50 variant,
   `DINO_4scale_swin.py` for Swin-L, or `DINO_4scale_convnext.py` for
   ConvNeXt-XL. Read [configuration.md](references/configuration.md) before
   changing `num_classes`, `dn_labelbook_size`, scale, backbone, or schedule.
4. **Select one launch mode.** Use a plain `python main.py` command for one
   process, `python -m torch.distributed.run` for a planned multi-GPU job, or
   `python run_with_submitit.py` only when a compatible Slurm service and
   shared-folder setup are known to exist. The inspection environment proves
   that Submitit imports, not that Slurm can submit.
5. **Validate before launching.** From the checkout root, run the planner from
   this skill directory, for example:

   ```bash
   python skills/disco/dino/sub-skills/training/scripts/build_dino_command.py \
     --repo-root . --config config/DINO/DINO_4scale.py \
     --coco-path /data/COCO --output-dir runs/dino-r50-ms4 \
     --mode single --allow-missing-data
   ```

   Remove `--allow-missing-data` for an actual run. Review the JSON summary,
   warnings, and `COMMAND (not launched)` line. The planner rejects missing
   configs, invalid scale/feature-level combinations, unsafe checkpoint
   combinations, missing backbone assets, invalid overrides, and accidental
   global-batch assumptions. It never downloads, compiles, or launches.
6. **Launch and observe.** Run the printed command manually only after the
   setup gate and command review. `main.py` builds the model and datasets,
   trains each epoch, evaluates on the validation loader, and writes logs and
   checkpoints under the output directory. Do not reuse one output directory
   for unrelated jobs.
7. **Stop or resume deliberately.** Stop at a completed epoch when possible.
   Keep `checkpoint.pth` and the logs. A later run using the same output
   directory automatically treats that file as `--resume`; use a fresh output
   directory when starting from a pretrain checkpoint instead. Read the
   resume/fine-tune and safe-stopping sections in [workflows.md](references/workflows.md).

## Non-negotiable semantics

- `batch_size` in a config is **per process**, not the global batch. The
  effective batch is `batch_size * nodes * GPUs per node` for distributed and
  Submitit runs. The shipped 4-scale setting is 2 images/process and the
  shipped 5-scale setting is 1 image/process; the reference multi-device
  recipes target a global batch of 16. The code does not automatically scale
  learning rates when this changes.
- `--resume` is a full-state path. It loads `checkpoint['model']` strictly and,
  for training checkpoints containing them, restores optimizer, scheduler, and
  starts at `checkpoint['epoch'] + 1`. An existing
  `<output_dir>/checkpoint.pth` silently takes precedence by being assigned to
  `args.resume` inside `main.py`.
- `--pretrain_model_path` is a partial model initialization path and is used
  only when `--resume` is absent. It loads the nested `model` state with
  `strict=False`; `--finetune_ignore` removes keys containing any supplied
  substring. It does not restore optimizer, scheduler, or epoch. For a new
  class set, the usual ignore tokens are `label_enc.weight` and `class_embed`.
- `num_classes` is the maximum dataset category ID plus one, not necessarily
  the count of category names. For custom data, the repository README's
  conservative rule is `dn_labelbook_size >= num_classes + 1`; the shipped
  COCO configs are a documented reference exception with both values set to
  91. Follow the custom-data rule and make the mapping explicit.
- Python config files are executed by the repository's `SLConfig` loader.
  `--options key=value` is for config values such as `batch_size` or
  `backbone_dir`; direct command-line flags are for `coco_path`, `output_dir`,
  checkpoint paths, and other parser arguments. Put `--options` last.

## Outputs and handoff

At minimum, report the exact config, effective global batch, launch mode,
checkpoint source, output directory, setup-gate result, planner result, and
whether a real job was launched. Expect `config_cfg.py`,
`config_args_raw.json`, `config_args_all.json`, `info.txt`, and `log.txt` in a
normal output directory. Training updates `checkpoint.pth`, writes periodic
`checkpoint####.pth` files, and may write `checkpoint_best_regular.pth` and
EMA variants. Evaluation state is written under `eval/` and `eval.pth`; these
artifacts are inputs to the sibling inference/evaluation route, not a claim
of an accepted benchmark here.

If a launch fails, preserve the command and output directory, classify it with
[troubleshooting.md](references/troubleshooting.md), and state whether the
failure happened before model construction, during data loading, during the
CUDA op, at distributed initialization, or while restoring a checkpoint.
Record omissions explicitly: this skill was not verified with a full COCO
run, long training, a downloaded checkpoint, or an active Slurm service.

## Evidence consulted

This route is grounded in `README.md` installation/data/run/custom-training
sections; `main.py`; `engine.py`; `run_with_submitit.py`; the four shipped
DINO configs and `coco_transformer.py`; `util/get_param_dicts.py`;
`util/misc.py`; and the `DINO_train*.sh` and `DINO_eval*.sh` launchers. The
bundled planner is a safe adaptation of those launchers and intentionally
omits their unused legacy `dn_scalar`, `dn_label_coef`, and `dn_bbox_coef`
overrides unless a caller explicitly asks for an unknown option.
