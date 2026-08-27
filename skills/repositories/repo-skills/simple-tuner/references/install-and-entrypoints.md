# Install and entry points

Read this when a task starts with installing SimpleTuner, checking whether it is usable, choosing a platform extra, or deciding which command surface to use. This reference is distilled from the packaged metadata and public install guidance.

## Package facts

- Distribution name: `simpletuner`.
- Import package: `simpletuner`.
- Verified package version during skill creation: `4.7.0`.
- Supported Python range from package metadata: `>=3.12,<3.14`.
- Verified console entry points:
  - `simpletuner = st_cli:main`
  - `simpletuner-train = simpletuner.train:main`
  - `simpletuner-configure = simpletuner.configure:main`
  - `simpletuner-inference = simpletuner.inference:main`
- The `simpletuner` wrapper sets `SIMPLETUNER_SKIP_TORCH=1` before importing the main CLI so lightweight commands start faster.

## Install variant decision

Choose the public install command by target hardware and workflow:

| target | install shape | notes |
|---|---|---|
| NVIDIA CUDA 12-style runtime | `pip install 'simpletuner[cuda]'` | Standard GPU install path for most NVIDIA systems. |
| NVIDIA CUDA 13 / Blackwell | `pip install 'simpletuner[cuda13]' --extra-index-url https://download.pytorch.org/whl/cu130` | Required for newer CUDA 13 wheel stack. |
| CUDA 13 + TransformerEngine FP8 | `pip install 'simpletuner[cuda13-transformerengine]' --extra-index-url https://download.pytorch.org/whl/cu130` | Only when TransformerEngine FP8 support is intentionally needed. |
| AMD ROCm | `pip install 'simpletuner[rocm]' --extra-index-url https://download.pytorch.org/whl/rocm7.1` | ROCm systems may need AMD SMI library setup before runtime checks. |
| Apple Silicon | `pip install 'simpletuner[apple]'` | MPS/Apple route; avoid CUDA-only assumptions. |
| CPU-only | `pip install 'simpletuner[cpu]'` | Useful for CLI/config inspection but not recommended for real training throughput. |
| JPEG XL support | add `simpletuner[jxl]` | Optional image format support. |
| Contributor dependencies | `pip install 'simpletuner[dev]'` | For repo development only; route tests/docs to `repo-development`. |

For a source checkout, public docs describe creating a Python 3.13 virtual environment and then installing editable with platform extras. Do not bake a local venv name or activation path into user-facing public text.

## Minimal checks

Run the root helper when the task is only to inspect an installation:

```bash
python skills/disco/simple-tuner/scripts/check_simpletuner_environment.py --json
```

Add `--probe-torch` only when the user wants backend visibility; it imports torch and performs a tiny CUDA allocation when CUDA is available.

The smallest manual checks are:

```bash
python -c "import simpletuner; print(simpletuner.__version__)"
simpletuner --help
simpletuner --version
```

A successful import or CLI help does not prove that a large model can train. Real training also depends on GPU/accelerator availability, model downloads, dataset layout, and selected optional dependencies.

## Command surfaces

| command | best use | route |
|---|---|---|
| `simpletuner configure` | Interactive configuration setup. | `training-workflows` plus `data-and-config`. |
| `simpletuner train` | Wrapper training command with environment/example support. | `training-workflows`. |
| `simpletuner-train` | Direct training entry point for full CLI/config operation. | `training-workflows`. |
| `simpletuner examples list/copy` | Discover packaged example configs. | Root helper and `training-workflows`. |
| `simpletuner server` | Start WebUI/API server. | `webui-and-operations`. |
| `simpletuner jobs ...` | Local GPU-aware job queue. | `webui-and-operations`. |
| `simpletuner cloud ...` | Cloud job configuration and monitoring. | `webui-and-operations`. |
| `simpletuner auth`, `quota`, `notifications`, `backup`, `database`, `metrics`, `webhooks`, `worker` | Operations/admin surfaces. | `webui-and-operations`. |
| Source editing and tests | Contributor workflow. | `repo-development`. |

## Packaged examples

During creation, the installed package exposed 110 packaged examples. Use the helper to list them without opening the source checkout:

```bash
python skills/disco/simple-tuner/scripts/list_simpletuner_examples.py --filter flux --limit 20
```

The helper reports whether an example has a config file, dataloader, LyCORIS config, or prompt library. Use the result as a starting point only; model downloads and actual training still require user approval.
