---
name: packaging-and-containerization
description: "Build BentoML Services into Bentos, author bentofile.yaml or
  equivalent build options, configure runtime images/dependencies, manage local
  Bento stores, and containerize safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Packaging and Containerization

Use this sub-skill when the task is about turning a BentoML Service into a Bento artifact or OCI image: `bentoml build`, `bentoml.build(...)`, `bentofile.yaml`, `pyproject.toml [tool.bentoml.build]`, dependency/runtime image settings, file inclusion, local Bento store operations, or `bentoml containerize`.

Do not use this sub-skill for writing the Service/API itself, running clients or servers, BentoCloud deployment, or framework-specific model import/export details. Route those to `service-authoring`, `serving-and-clients`, `cli-and-cloud`, or `model-management`.

## Fast Path

1. Identify the entry Service import path, usually `service:ClassName` for a class decorated with `@bentoml.service` or `module:svc` for an exported service object.
2. Prefer runtime image configuration in Python with `bentoml.images.Image(...)` attached to `@bentoml.service(image=...)` for new SDK Services.
3. Use `bentofile.yaml` or `[tool.bentoml.build]` when the project needs declarative build metadata, file patterns, models, or compatibility with existing workflows.
4. Run safe local validation before building: parse the YAML, check required files, inspect include/exclude patterns, and confirm dependency files exist.
5. Build with `bentoml build`, `bentoml build -f path/to/bentofile.yaml BUILD_CTX`, or `bentoml.build(...)`.
6. Containerize only when Docker or another OCI backend is available: `bentoml containerize BENTO_TAG` or `bentoml build --containerize`.

## Safe Local Checks

- `python scripts/validate_bentofile.py bentofile.yaml --project-dir .` validates field shapes, required paths, and common packaging mistakes without running BentoML, Docker, network access, or dependency resolution.
- `python scripts/create_minimal_bentofile.py --service service:MyService --package numpy --include service.py` prints a starter `bentofile.yaml` to stdout or writes it with `--output bentofile.yaml`.
- `bentoml build --bentofile bentofile.yaml --name NAME --version VERSION .` creates a Bento in the local Bento store and may resolve dependencies; treat it as more expensive than static validation.
- `bentoml containerize BENTO_TAG --platform linux/amd64` requires a container backend and may pull base images or run Docker/BuildKit.

## Core Workflows

- Authoring field-level build files: see `references/bentofile-reference.md`.
- Choosing CLI/API/container commands and build contexts: see `references/workflows.md`.
- Diagnosing build and image failures: see `references/troubleshooting.md`.

## Minimal Examples

A minimal `bentofile.yaml`:

```yaml
service: "service:MyService"
include:
  - "service.py"
python:
  packages:
    - "numpy"
docker:
  python_version: "3.11"
```

Equivalent direct build API shape:

```python
import bentoml

bento = bentoml.build(
    service="service:MyService",
    include=["service.py"],
    python={"packages": ["numpy"]},
    docker={"python_version": "3.11"},
)
```

A modern runtime image in `service.py`:

```python
import bentoml

image = bentoml.images.Image(python_version="3.11").python_packages("numpy")

@bentoml.service(image=image)
class MyService:
    pass
```

## Build Context Rules

- Relative paths in `include`, `exclude`, `requirements_txt`, `environment_yml`, `setup_script`, `dockerfile_template`, wheels, and descriptions using `file:` are resolved relative to the build context.
- If `include` is absent, BentoML includes all files under the build context, then applies `exclude`, `.bentoignore`, and built-in ignores such as `.git/`, virtualenvs, `__pycache__/`, and `.DS_Store`.
- `exclude` always applies after `include`; use it to remove secrets, tests, training data, notebooks, and large artifacts.
- For `src/` layout projects, `pyproject.toml` auto-detection can mark `python.is_src_layout`, and explicit `python: {is_src_layout: true}` strips the leading `src/` when packaging code.

## Side-Effect Boundaries

- Static YAML checks and file existence checks are safe.
- `bentoml build` writes to the local Bento store and can run package locking; it may access package indexes or local model stores.
- `bentoml build --containerize`, `bentoml containerize`, and `bentoml.container.build` require an OCI builder and may pull or build images.
- `bentoml push`, `bentoml pull`, and `bentoml deploy` are cloud/network operations and belong in cloud/deployment workflows.
