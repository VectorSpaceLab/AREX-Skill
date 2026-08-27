# Bento Build File Reference

BentoML accepts build options in `bentofile.yaml`, `pyproject.toml` under `[tool.bentoml.build]`, or direct `bentoml.build(...)` keyword arguments. The direct API does not read `bentofile.yaml`; pass every option explicitly.

## Required Service Target

`service` is the only required build field for a build file. It points to the importable Service entry point:

```yaml
service: "service:MyService"
```

Use `module:ClassName` for a class decorated by `@bentoml.service`, or `module:svc` for a service object. If the module is inside a package, use a dotted module path such as `my_package.service:MyService` and ensure the package is included in the build context.

## Top-Level Fields

Common fields accepted by `BentoBuildConfig`:

```yaml
service: "service:MyService"
name: my_service
description: "file: ./README.md"
labels:
  owner: ml-platform
  stage: dev
include:
  - "service.py"
  - "src/**"
exclude:
  - "tests/"
  - "*.key"
models:
  - "summarization-model:latest"
  - tag: "reranker:v1"
    alias: "reranker"
envs:
  - name: HF_TOKEN
  - name: DB_HOST
    value: localhost
args:
  model_name: "meta-llama/Llama-3.3-70B-Instruct"
```

Important details:

- `description: "file: ./README.md"` requires that the referenced file exists relative to the build context.
- `labels` are immutable metadata for the built Bento.
- `models` accepts strings or dictionaries with `tag`, optional `filter`, and optional `alias`.
- `envs` accepts dictionaries with `name`, optional `value`, and optional `stage` of `all`, `build`, or `runtime`.
- `args` supplies values for `bentoml.use_arguments(...)` in Service code; CLI `--arg` values override config-file defaults.

## File Selection

`include` and `exclude` use gitignore-style patterns relative to `build_ctx`:

```yaml
include:
  - "service.py"
  - "src/**"
  - "config/*.json"
exclude:
  - "tests/"
  - "training_data/"
  - "*.secret"
```

If `include` is missing, BentoML behaves like `include: ["*"]` after defaults. `exclude` is applied after `include`, and `.bentoignore` files under the build context are also respected. Prefer narrow includes for production Bentos so notebooks, tests, secrets, and training data do not get packaged accidentally.

## Python Dependencies

```yaml
python:
  packages:
    - "numpy>=1.26"
    - "scikit-learn==1.4.2"
  requirements_txt: null
  lock_packages: true
  pack_git_packages: true
  index_url: "https://pypi.org/simple"
  extra_index_url:
    - "https://download.pytorch.org/whl/cpu"
  trusted_host:
    - "internal.example"
  find_links:
    - "./wheels"
  pip_args: "--pre"
  wheels:
    - "./wheels/custom-0.1.0-py3-none-any.whl"
```

Rules to remember:

- Do not add `bentoml` manually unless intentionally overriding the runtime BentoML version; BentoML adds its own requirement by default.
- If both `requirements_txt` and `packages` are set, BentoML warns and uses `requirements_txt` for package content.
- `trusted_host`, `find_links`, and `extra_index_url` may be strings or lists in YAML, but lists are clearer.
- `lock_packages` defaults to enabled unless `pack_git_packages` is explicitly false.
- Package locking targets Linux x86_64 by default when the build host differs; pass `--platform` to build for another supported platform.
- `python.is_src_layout: true` strips `src/` from copied package paths; use it for projects where imports expect packages at the import root.

## Conda Dependencies

```yaml
conda:
  channels:
    - conda-forge
  dependencies:
    - python=3.11
    - h2o
  pip:
    - "scikit-learn==1.4.2"
```

Or provide an exported environment file:

```yaml
conda:
  environment_yml: "./environment.yml"
```

If `environment_yml` is provided, it overrides `channels`, `dependencies`, and `pip`. BentoML does not automatically lock conda dependencies; specify versions when reproducibility matters. Conda packaging selects a Miniconda-capable base image and is not compatible with every distro.

## Docker and Image Fields

```yaml
docker:
  distro: debian
  python_version: "3.11"
  system_packages:
    - libblas-dev
    - liblapack-dev
  setup_script: "./setup.sh"
  base_image: null
  dockerfile_template: null
```

Supported distro names include `debian`, `alpine`, `ubi8`, and `amazonlinux`. A custom `base_image` overrides distro, Python version, CUDA version, and system package choices. `setup_script` must exist, include a shebang, and be executable on non-Windows systems because it is copied into the Bento and run during container image creation.

Prefer the Python SDK for new Services when the runtime image belongs close to Service code:

```python
image = bentoml.images.Image(python_version="3.11").python_packages("torch")

@bentoml.service(image=image, envs=[{"name": "HF_TOKEN"}])
class Summarization:
    pass
```

Use `bentofile.yaml` when you need declarative file selection, model aliases, or compatibility with CLI build workflows.
