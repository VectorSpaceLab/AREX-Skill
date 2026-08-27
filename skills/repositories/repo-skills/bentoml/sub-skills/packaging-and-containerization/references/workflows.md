# Packaging Workflows

## Build From a Build File

Project layout:

```text
project/
  bentofile.yaml
  service.py
  requirements.txt
```

Commands:

```bash
python scripts/validate_bentofile.py project/bentofile.yaml --project-dir project
bentoml build -f project/bentofile.yaml project
bentoml list
bentoml get my_service:latest
```

Use `-f/--bentofile` when the build file is not named `bentofile.yaml` or is not in the build context root. The positional `BUILD_CTX` is the directory whose files are matched by `include`, `exclude`, and `.bentoignore`.

## Generate a Starter Build File

```bash
python scripts/create_minimal_bentofile.py \
  --service service:MyService \
  --name my_service \
  --include service.py \
  --include "src/**" \
  --package numpy \
  --python-version 3.11 \
  --output bentofile.yaml
```

Then inspect and edit the generated file before running `bentoml build`.

## Build With the Python API

Use `bentoml.build(...)` when build options are computed programmatically:

```python
import bentoml

bento = bentoml.build(
    service="service:MyService",
    name="my_service",
    include=["service.py", "src/**"],
    exclude=["tests/", "*.key"],
    python={"requirements_txt": "./requirements.txt"},
    docker={"python_version": "3.11", "distro": "debian"},
    models=[{"tag": "classifier:latest", "alias": "classifier"}],
    args={"model_name": "classifier:latest"},
)
print(bento.tag)
```

This call does not automatically read `bentofile.yaml`.

## Convert CLI Flags to API Options

A CLI command like:

```bash
bentoml build -f bentofile.yaml --name fraud --version v1 --label team=ml --platform linux .
```

maps to:

```python
bentoml.bentos.build_bentofile(
    "bentofile.yaml",
    name="fraud",
    version="v1",
    labels={"team": "ml"},
    build_ctx=".",
    platform="linux",
)
```

For build-file-free API usage, move the build-file contents into `bentoml.build(...)` keyword arguments and keep `platform` as a top-level argument.

## Template Arguments

If Service code uses `bentoml.use_arguments(...)`, provide values in one of three places:

```yaml
args:
  model_name: "classifier:latest"
  gpu: 1
```

```bash
bentoml build --arg model_name=classifier:latest --arg gpu=1
bentoml build --arg-file bento_args.yaml
```

```python
bentoml.build("service:MyService", args={"model_name": "classifier:latest", "gpu": 1})
```

Missing required arguments fail when BentoML imports/evaluates the Service.

## Containerize a Built Bento

After building:

```bash
bentoml containerize my_service:latest
bentoml containerize my_service:latest --platform linux/amd64 --progress plain
```

`bentoml build --containerize` is a shortcut for build followed by containerize. Containerization is backend-agnostic, but it requires a working OCI builder such as Docker/BuildKit or another configured backend. Use `--platform` at containerization time for image target platforms, and use build-time `--platform` when dependency locking/build output must target a Python platform.

## Inspect the Local Store

```bash
bentoml list
bentoml get my_service:latest
bentoml get my_service:latest -o path
bentoml export my_service:latest ./my_service.bento
bentoml import ./my_service.bento
bentoml delete my_service:version --yes
```

The local Bento store is machine-local. Avoid baking absolute local store paths into public instructions; use tags such as `my_service:latest` or `name:version`.
