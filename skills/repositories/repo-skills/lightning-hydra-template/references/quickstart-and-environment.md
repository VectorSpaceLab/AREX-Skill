# Quickstart and Environment

## When to read

Read this when installing, inspecting, or smoke-checking a Lightning-Hydra-Template checkout or derived project before editing configs or running training.

## Public setup pattern

Typical fresh-checkout setup:

```bash
# optional but recommended: create an isolated Python environment first
pip install -r requirements.txt
pip install -e .
```

The template also includes `environment.yaml` for Conda-oriented installs. It pins broad major versions for Python, PyTorch, Lightning, TorchMetrics, Hydra, Rich, pre-commit, pytest, and the Hydra plugins.

## Core packages and optional groups

| Surface | Packages/evidence | Notes |
| --- | --- | --- |
| Training and data | `torch`, `torchvision`, `lightning`, `torchmetrics` | Required for the MNIST example and Lightning modules. |
| Config system | `hydra-core==1.3.2`, `hydra-colorlog==1.2.0`, `omegaconf` | Required for `@hydra.main`, config groups, CLI overrides, and colored Hydra logs. |
| Sweeps | `hydra-optuna-sweeper==1.2.0`, `optuna` dependency | Required for `hparams_search=mnist_optuna`; sweeps are optional and not failure-resistant. |
| Utilities | `rootutils`, `rich` | `rootutils` sets project root/PYTHONPATH/`.env`; Rich prints config trees and tag prompts. |
| Tests and maintenance | `pytest`, `pre-commit` | `sh` is optional and used only by some sweep tests on non-Windows systems. |
| Online loggers | `wandb`, `neptune-client`, `mlflow`, `comet-ml`, `aim>=3.16.2` | Documented but commented out; install only the logger you need and provide credentials/services. |

## Import and CLI checks

After installation, use safe checks before running training:

```bash
python - <<'PY'
from importlib.metadata import version, entry_points
print('src', version('src'))
print([ep for ep in entry_points(group='console_scripts') if ep.name in {'train_command', 'eval_command'}])
import src.train, src.eval
print('train/eval imports ok')
PY

train_command --help
eval_command --help
```

If the project has renamed the default `src` package, replace `src` in these checks with the new distribution/import names and verify the console scripts still point to the renamed modules.

## No-training inspection

Use the bundled project inspector from this skill directory:

```bash
python <this-skill>/scripts/check_lightning_hydra_project.py --repo-root . --config-name train.yaml --instantiate
python <this-skill>/scripts/check_lightning_hydra_project.py --repo-root . --config-name eval.yaml --override ckpt_path=/tmp/dummy.ckpt --instantiate
```

These checks compose Hydra configs and instantiate configured data/model/trainer objects. They deliberately do **not** call `prepare_data()`, `trainer.fit()`, or `trainer.test()`.

## Training commands are not offline-safe by default

The default MNIST datamodule downloads data in `prepare_data()`. Commands such as `python src/train.py`, `make train`, or fast-dev training may need network access or a pre-populated MNIST cache. For smoke tests without network, prefer config composition and target import checks.

## Accelerator checks

The template exposes `trainer=cpu`, `trainer=gpu`, `trainer=ddp`, `trainer=ddp_sim`, and `trainer=mps` config groups, plus a TPU command override example. Actual accelerator execution depends on hardware and the installed PyTorch build. Do not claim a GPU, MPS, TPU, or DDP run is verified just because config composition succeeds.
