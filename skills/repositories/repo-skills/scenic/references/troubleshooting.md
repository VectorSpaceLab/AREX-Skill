# Cross-Cutting Troubleshooting

## Import or install fails

| Symptom | Likely cause | What to do |
|---|---|---|
| `ModuleNotFoundError: scenic` | Package is not installed in the active environment. | Install Scenic in an isolated environment and rerun `scripts/inspect_scenic_package.py`. |
| `ModuleNotFoundError: flax`, `jax`, `ml_collections`, `clu`, `tensorflow` | Core runtime dependency is absent. | Install the missing core package; avoid installing every project `requirements.txt` unless a selected project needs it. |
| `pip install .` triggers network or optional dependency issues | `setup.py` includes git-based dependencies and install-time SimCLR download behavior in some paths. | Prefer an isolated environment; if only inspecting core APIs, install required core packages explicitly and install Scenic editable/no-deps in a private inspection environment. For real user environments, follow project docs and use normal package installation. |
| `pip check` reports conflicts after adding project requirements | Historical project pins conflict with the core stack. | Create a separate project-specific environment; do not keep downgrading one shared environment across unrelated projects. |

## JAX/TensorFlow backend issues

- `jax.devices()` shows only CPU even though a GPU exists: the installed `jaxlib` is CPU-only or the CUDA/driver stack is not visible. CPU is fine for config/API checks, but full accelerator training is not verified.
- TensorFlow logs about CUDA stubs or TF-TRT are not necessarily fatal for Scenic because `scenic.app` hides TensorFlow GPUs before JAX training to avoid memory reservation.
- For real GPU/TPU training, verify a tiny JAX accelerator operation before launching Scenic and use backend-specific JAX installation instructions.

## Config/run errors

| Symptom | Likely cause | Recovery |
|---|---|---|
| absl says `--config` or `--workdir` is required | Scenic app-level flags are missing. | Use `python -m scenic.main -- --config=<config.py> --workdir=<dir>` or the selected project main with both flags. |
| `KeyError` / `AttributeError` for `rng_seed`, `dataset_name`, `model_name`, `trainer_name` | Config lacks launch-critical fields or nests them differently for a project. | Run `sub-skills/running-and-training/scripts/scenic_config_probe.py <config.py>` and compare against the selected project's expected shape. |
| `Unrecognized model` | `config.model_name` is not registered in `scenic.model_lib.models` or the selected project main was not used. | Use `sub-skills/modeling-and-layers/scripts/model_registry_probe.py`; for project models, use the project-specific `main.py`/registry pattern documented in `baselines-and-projects`. |
| `Unknown dataset` | Dataset name is absent from the lazy import table and no custom registration module was imported. | Use `sub-skills/data-pipelines/scripts/check_dataset_registry.py --dataset-name <name>`; if custom, import the module that calls `@datasets.add_dataset`. |
| `Unrecognized trainer` or trainer import failure | Trainer name is misspelled, project main expected, or optional transfer dependencies import at module load. | Start with `running-and-training` troubleshooting; avoid importing all trainer modules for simple config checks. |
| LR schedule native tests fail at `tf.keras.experimental.CosineDecayRestarts` | The installed TensorFlow/Keras generation removed legacy `tf.keras.experimental` APIs used by older tests for comparison. | Treat as a TensorFlow/Keras compatibility issue for native testing. Pin a compatible stack for native tests, or validate the Scenic LR function directly for config/API preflight. |

## TensorFlow Addons / BigVision / transfer-stack failure

Some Scenic versions import transfer-learning and BigTransfer preprocessing when loading the trainer registry. That path can import `tensorflow_addons`. Modern TensorFlow/Keras 3 stacks can fail with errors like:

```text
ModuleNotFoundError: No module named 'keras.src.engine'
```

Use this decision tree:

1. If the task only needs config inspection, LR schedules, optimizer setup, dataset/model registry checks, or model API facts, do not import the trainer registry. Use the bundled probes instead.
2. If the task requires transfer training or BigTransfer preprocessing, create a dedicated environment with mutually compatible TensorFlow, Keras, and TensorFlow Addons versions. Do not mix this into a modern core JAX environment without checking `pip check` and a small import smoke.
3. If a project uses `big_vision` checkpoints or utilities, follow that project's dependency notes and verify that `big_vision` is importable before training.
4. If version pinning would require old JAX/TensorFlow/CUDA wheels, isolate the project in its own environment.

## Data, checkpoint, and project-tool stop conditions

Stop and ask for more inputs or choose a non-executing plan when:

- The workflow needs private datasets, cloud buckets, credentials, or checkpoints that are not available.
- A conversion/evaluation tool would write large TFRecords, mutate annotations, or run benchmark-scale evaluation.
- A project requirement file pins old CUDA/JAX/TensorFlow versions that conflict with the current environment.
- The user asks for paper-result reproduction rather than repository guidance; that is a downstream research task, not Creator-mode skill construction.

## Which sub-skill next?

- Config flags, launch commands, LR schedules, optimizers, checkpoints: `running-and-training`.
- Dataset names, TFDS/FlexIO/COCO layouts, unknown dataset errors: `data-pipelines`.
- BaseModel, registered models, layers, matchers, metrics/losses: `modeling-and-layers`.
- Choosing a baseline/project or handling project-specific requirements/tools: `baselines-and-projects`.
