# CLI reference

Evidence anchors: `sdk/python/kfp/cli/cli.py`, `sdk/python/kfp/cli/compile_.py`, `sdk/python/kfp/cli/component.py`, `sdk/python/setup.py`, `docs/sdk/source/cli.rst`, `sdk/python/kfp/cli/compile_test.py`, `sdk/python/kfp/cli/component_test.py`, installed CLI help facts, and live installed help probes.

## No-client compile commands

`kfp` groups are split in source into client-backed commands and no-client commands. `dsl`, `component`, and `diagnose-me` are no-client commands; `pipeline`, `run`, `experiment`, and `recurring-run` can initialize a client even for help in this version. For compile work, use only `kfp dsl compile` or the bundled wrapper unless the user explicitly asks for live service operations.

## `kfp dsl compile`

Purpose: compile a pipeline or component written in a local `.py` file.

```bash
kfp dsl compile --py PIPELINE.py --output PIPELINE.yaml [OPTIONS]
```

Main options verified from source and installed help:

| Flag | Required | Meaning |
|---|---:|---|
| `--py FILE` | yes | Local path to the Python file to import. Source help says local absolute path; installed Click accepts existing files. |
| `--output FILE` | yes | Path to write the compiled result. Prefer `.yaml`/`.yml`. |
| `--function TEXT` | no | Name of the pipeline or component to compile when the module has multiple candidates. |
| `--pipeline-parameters TEXT` | no | JSON dict string of input overrides, for example `{"text":"Hello KFP!"}`; quote it for your shell as shown in examples. |
| `--disable-type-check` | no | Passes `type_check=False` to the compiler. |
| `--disable-execution-caching-by-default` | no | Sets default execution caching off; also backed by `KFP_DISABLE_EXECUTION_CACHING_BY_DEFAULT`. |
| `--kubernetes-manifest-format` | no | Output Kubernetes `PipelineVersion` manifest YAML, optionally with `Pipeline`. |
| `--help` | no | Show command help. |

Entry-point selection behavior from `compile_.py`:

- If exactly one pipeline exists in the module, it is compiled.
- If there are no pipelines and exactly one component exists, that component is compiled.
- If there are multiple pipelines/components or none, the CLI raises an error asking for `--function`.
- If `--function` names a missing object, the CLI raises `Pipeline function or component "..." not found`.

## Kubernetes manifest / compile-manifest options

These flags affect output only when `--kubernetes-manifest-format` is also set. If any are provided without the format flag, the CLI prints a warning and writes ordinary PipelineSpec YAML.

| Flag | Meaning |
|---|---|
| `--pipeline-name TEXT` | Name for the Kubernetes `Pipeline` resource; defaults to the PipelineSpec name. |
| `--pipeline-display-name TEXT` | Display name for the `Pipeline` resource; defaults to pipeline name. |
| `--pipeline-version-name TEXT` | Name for the `PipelineVersion` resource; defaults to pipeline name. |
| `--pipeline-version-display-name TEXT` | Display name for the `PipelineVersion`; defaults to version name or pipeline display name. |
| `--namespace TEXT` | Namespace on emitted Kubernetes resources. |
| `--include-pipeline-manifest` | Include a `Pipeline` document in addition to the always-emitted `PipelineVersion`. |

Example:

```bash
kfp dsl compile \
  --py pipeline.py \
  --output pipeline-version.yaml \
  --function iris_pipeline \
  --kubernetes-manifest-format \
  --pipeline-name iris-pipeline \
  --pipeline-display-name "Iris Pipeline" \
  --pipeline-version-name iris-pipeline-v1 \
  --pipeline-version-display-name "Iris Pipeline v1" \
  --namespace kubeflow \
  --include-pipeline-manifest
```

## Deprecated `dsl-compile`

`sdk/python/setup.py` still installs:

```text
dsl-compile = kfp.cli.compile_:main
```

It is a legacy alias. Installed help and tests show it prints:

```text
`dsl-compile` is deprecated. Please use `kfp dsl compile` instead.
```

Use `dsl-compile` only to diagnose older user commands; rewrite new guidance to `kfp dsl compile`.

## Bundled wrapper

The bundled wrapper calls either the public installed `kfp` console CLI (falling back to the installed CLI main function) or the public `Compiler` API. It does not import from the original checkout.

```bash
python skills/disco/kubeflow-pipelines/sub-skills/compiler-and-cli/scripts/compile_pipeline_file.py \
  --py pipeline.py \
  --output pipeline.yaml \
  --function my_pipeline \
  --pipeline-parameters '{"text":"Hello KFP!"}'
```

Useful wrapper flags:

| Flag | Meaning |
|---|---|
| `--backend cli` | Default; invoke installed `kfp` CLI module with validated arguments. |
| `--backend api` | Import the target file and call `Compiler().compile` directly. |
| `--dry-run` | Print the CLI command that would be invoked; CLI backend only. |

## `kfp component build` surface

Purpose: build shareable containerized v2 Python-based components from a directory. This is not a simple compile-only action; it scans files, writes metadata/config/build files, and may build or push a container image.

```bash
kfp component build COMPONENTS_DIRECTORY [OPTIONS]
```

Installed help/source options:

| Flag | Meaning |
|---|---|
| `--component-filepattern TEXT` | File glob used to search for KFP components; default is `**/*.py`. |
| `--kfp-package-path PATH` | Pip-installable path to the KFP package. |
| `--overwrite-dockerfile` | Always regenerate `Dockerfile`. |
| `--build-image / --no-build-image` | Build the container image; default is build. |
| `--platform TEXT` | Docker build platform; default `linux/amd64`. |
| `--push-image / --no-push-image` | Push built image; default is push. |

Operational constraints from `component.py` and tests:

- Docker Python package is required when `--build-image` is active; use `--no-build-image` to skip Docker build/push.
- All discovered components must have one uniform `base_image` and one uniform `target_image`.
- Missing `base_image` or `target_image` is an error.
- The command may write `component_metadata/`, `kfp_config.ini`, `runtime-requirements.txt`, `.dockerignore`, and `Dockerfile`.
- Treat build/push as mutating and environment-dependent; ask before executing and do not route live image publishing through this compile sub-skill unless explicitly requested.
