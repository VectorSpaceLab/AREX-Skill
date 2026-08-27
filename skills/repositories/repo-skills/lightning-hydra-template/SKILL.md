---
name: lightning-hydra-template
description: "Operate Lightning-Hydra-Template projects: Hydra configs,
  Lightning training/evaluation, data/model customization, tests, CI, and
  template maintenance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Lightning-Hydra-Template Repo Skill

Use this skill when a task involves a project based on **Lightning-Hydra-Template**: a PyTorch Lightning + Hydra template with `configs/`, `src/train.py`, `src/eval.py`, Lightning `DataModule`/`LightningModule` examples, pytest smoke tests, and MLOps-style logging/callback/sweep configuration.

This skill is self-contained operating guidance. Treat paths such as `configs/train.yaml` and `src/train.py` as files in the **user's target checkout or derived project**, not as links to the construction repository.

## First checks

1. Confirm you are in a target project that resembles the template: it should have `configs/`, `src/`, `tests/`, `.project-root`, `requirements.txt` or `environment.yaml`, and usually `setup.py`.
2. Install or verify the project environment. The public template path is usually:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```
   Use the project's own environment policy if it has diverged from the template.
3. Run a no-training inspection before expensive work:
   ```bash
   python <this-skill>/scripts/check_lightning_hydra_project.py --repo-root . --config-name train.yaml --instantiate
   python <this-skill>/scripts/check_lightning_hydra_project.py --repo-root . --config-name eval.yaml --override ckpt_path=/tmp/dummy.ckpt --instantiate
   ```
4. For a current/staleness check on this generated skill, read [repository provenance](references/repo-provenance.md).
5. For environment setup, dependency groups, and public import checks, read [quickstart and environment](references/quickstart-and-environment.md). For the template file layout, read [template file map](references/template-file-map.md). For cross-cutting failures, read [troubleshooting](references/troubleshooting.md).

## Route by task

| User task | Read next | Why |
| --- | --- | --- |
| Edit Hydra defaults, choose config groups, convert CLI overrides to experiment YAML, debug `MissingConfigException`, set log paths, or run multiruns/Optuna sweeps. | [configure-experiments](sub-skills/configure-experiments/SKILL.md) | Owns Hydra composition, overrides, debug configs, sweeps, tags, and path interpolation. |
| Train, resume, evaluate checkpoints, choose callbacks/loggers/accelerators, inspect CLI help, or build safe repeated-run commands. | [train-evaluate](sub-skills/train-evaluate/SKILL.md) | Owns `src.train`, `src.eval`, `train_command`, `eval_command`, checkpoint/logging semantics, and accelerator choices. |
| Add a new dataset, replace MNIST, add a LightningModule or network component, rename the `src` package, or fix `_target_` imports. | [customize-data-model](sub-skills/customize-data-model/SKILL.md) | Owns DataModule/LightningModule/component APIs, optimizer/scheduler partials, target strings, and data/model config wiring. |
| Pick no-network tests, adapt pytest fixtures, update CI/pre-commit, diagnose `RunIf` skips, or maintain package metadata after template changes. | [test-maintain-template](sub-skills/test-maintain-template/SKILL.md) | Owns pytest/CI/Makefile workflow, package rename checklist, and maintenance gates. |

## Public runtime surfaces verified for this skill

- Distribution metadata: default template distribution `src==0.0.1`.
- Import package: `src` with `src.train`, `src.eval`, `src.data.mnist_datamodule`, `src.models.mnist_module`, and `src.models.components.simple_dense_net`.
- Console entry points from `setup.py`: `train_command = src.train:main` and `eval_command = src.eval:main`.
- Main config groups visible through Hydra help: `data`, `model`, `callbacks`, `logger`, `trainer`, `paths`, `extras`, `hydra`, `debug`, `experiment`, and `hparams_search`.
- Safe config/API inspection composes train/eval configs and instantiates datamodule, model, and trainer without calling `prepare_data()`, `fit()`, or `test()`.

## Safe operating rules

- Do not treat default training commands as no-network: the MNIST example can download data.
- Prefer config composition, CLI `--help`, and target-import checks before running training.
- Disable online loggers in smoke tests unless credentials and optional packages are explicitly available: use `logger=null` or `logger=csv`.
- Keep accelerator claims scoped. CPU config/API checks are portable; CUDA, MPS, TPU, DDP, and online loggers require hardware, packages, services, or credentials.
- If the user has renamed the default `src` package, update all `_target_` strings, imports, `setup.py` entry points, and CI coverage paths together.

## Bundled scripts

- [scripts/check_lightning_hydra_project.py](scripts/check_lightning_hydra_project.py): shared target-checkout inspector; composes configs, checks imports/entry points, optionally instantiates objects and probes CUDA.
- Sub-skill scripts provide narrower helpers for config rendering, scheduled command previews, `_target_` scanning, and smoke-test selection.
