---
name: compiler-and-cli
description: "Compile Kubeflow Pipelines Python DSL pipelines or components to
  PipelineSpec YAML or Kubernetes manifests using the public Compiler API and
  CLI."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Kubeflow Pipelines compiler and CLI

Use this sub-skill when the user already has a KFP Python pipeline/component and needs to compile it, diagnose compilation, or understand the compile-related CLI surface.

## Own this scope

- Compile `@dsl.pipeline`, `@dsl.component`, or `@dsl.container_component` objects to PipelineSpec YAML with `kfp.compiler.Compiler().compile`.
- Compile a Python file with `kfp dsl compile`; explain the legacy `dsl-compile` alias.
- Choose an entry point with `--function` when a file has more than one pipeline/component.
- Pass input overrides with `pipeline_parameters` / `--pipeline-parameters`, toggle type checking, and request Kubernetes native Pipeline/PipelineVersion manifests.
- Explain `kfp component build` help, prerequisites, generated files, and Docker side effects at a high level.

## Route away

- Authoring or restructuring the DSL pipeline/component itself -> `pipeline-authoring`.
- Uploading packages, creating runs, registry operations, or client-backed CLI commands -> `client-and-registry`.
- Kubernetes task helper APIs such as secrets, PVCs, tolerations, pod labels, or platform configs -> `kubernetes-platform`.
- Repo maintenance, generated-code refresh, SDK test/generation commands -> `repo-development`.

## Fast operating procedure

1. Confirm the input is an existing `.py` file or an in-process decorated pipeline/component object. If the user needs code written first, route to `pipeline-authoring`.
2. For a file compile, prefer the bundled wrapper because it uses only the installed KFP package and validates JSON before invoking the public CLI/API:

   ```bash
   python skills/disco/kubeflow-pipelines/sub-skills/compiler-and-cli/scripts/compile_pipeline_file.py \
     --py path/to/pipeline.py \
     --output pipeline.yaml \
     --function pipeline_func \
     --pipeline-parameters '{"text":"Hello KFP!"}'
   ```

3. Equivalent direct CLI:

   ```bash
   kfp dsl compile --py path/to/pipeline.py --output pipeline.yaml \
     --function pipeline_func --pipeline-parameters '{"text":"Hello KFP!"}'
   ```

4. Equivalent in-process API:

   ```python
   from kfp import compiler

   compiler.Compiler().compile(
       pipeline_func=my_pipeline,
       package_path="pipeline.yaml",
       pipeline_parameters={"text": "Hello KFP!"},
       type_check=True,
   )
   ```

5. For Kubernetes native manifests, include the format flag. Naming and namespace flags are ignored by the CLI unless this flag is present:

   ```bash
   kfp dsl compile --py path/to/pipeline.py --output pipeline-version.yaml \
     --function pipeline_func \
     --kubernetes-manifest-format \
     --pipeline-name my-pipeline \
     --pipeline-display-name "My Pipeline" \
     --pipeline-version-name my-pipeline-v1 \
     --pipeline-version-display-name "My Pipeline v1" \
     --namespace kubeflow \
     --include-pipeline-manifest
   ```

## Decision rules

- Use the CLI/wrapper for a Python file; use `Compiler().compile` when the pipeline/component object is already imported in Python.
- `--pipeline-parameters` must be a JSON object whose keys match pipeline/component inputs. Invalid JSON fails before compile; unknown inputs fail during PipelineSpec override.
- Leave type checking enabled by default. Use `--disable-type-check` / `type_check=False` only when the user explicitly accepts weaker compile-time interface checks.
- A normal compile writes PipelineSpec YAML (`pipelineInfo`, `root`, `components`, `deploymentSpec`). Kubernetes manifest format writes Kubernetes `PipelineVersion` and, with `--include-pipeline-manifest`, also `Pipeline` documents.
- `dsl-compile` is still installed as a deprecated console script; prefer `kfp dsl compile` in new commands.
- `kfp component build` can generate component metadata, Dockerfile, requirements, config, and optionally build/push images. Treat it as mutating and Docker-dependent; do not run it unless the user asks and prerequisites are present.

## Verification checks

- Check the output file exists and ends in `.yaml`/`.yml` for supported YAML compilation.
- For PipelineSpec YAML, parse YAML and look for `pipelineInfo` plus `root`; platform-specific configs may appear as an additional YAML document.
- For Kubernetes manifest output, parse all YAML documents and look for `kind: PipelineVersion`; if `--include-pipeline-manifest` was used, also expect `kind: Pipeline`.
- Compilation itself does not contact a KFP service or Kubernetes cluster. If the next step is upload/run, route to `client-and-registry`.

## References

- `references/api-reference.md` — `Compiler.compile`, `KubernetesManifestOptions`, output behavior, API examples.
- `references/cli-reference.md` — `kfp dsl compile`, `dsl-compile`, manifest flags, `kfp component build` surface.
- `references/troubleshooting.md` — entry-point selection, JSON, type checks, manifest flag confusion, deprecated alias, Docker build prerequisites.
