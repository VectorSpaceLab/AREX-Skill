# Compiler and CLI troubleshooting

Use this when a compile or compile-adjacent CLI command fails. If the underlying issue is pipeline authoring, route to `pipeline-authoring` after identifying the compile symptom.

## Missing `--function` or wrong function

Symptoms:

- `Expected one pipeline or one component in module ... Please specify which pipeline or component to compile using --function.`
- `Pipeline function or component "NAME" not found in module FILE.py.`

Cause: `kfp dsl compile` imports the file and collects decorated pipeline/component objects. It can auto-select exactly one pipeline, or exactly one component when there are no pipelines. Multiple candidates require `--function`.

Fix:

```bash
kfp dsl compile --py pipeline.py --output pipeline.yaml --function exact_object_name
```

Do not rewrite the user's DSL just to satisfy compilation unless they ask for authoring help.

## JSON parsing failures in `--pipeline-parameters`

Symptoms:

- `Failed to parse --pipeline-parameters argument: ...`
- Python `json.decoder.JSONDecodeError`, often from unmatched quotes or shell quoting.

Cause: the CLI expects one JSON object string. It is not Python literal syntax.

Fix:

```bash
kfp dsl compile --py pipeline.py --output pipeline.yaml \
  --pipeline-parameters '{"text":"Hello KFP!","count":3}'
```

If scripting, construct the JSON with `python -m json.tool` or `json.dumps`. The bundled wrapper validates that the parsed value is a JSON object before calling KFP.

## Parameter names do not match inputs

Symptom:

- `Pipeline parameter NAME does not match any known pipeline input.`
- Artifact defaults are rejected.

Cause: `pipeline_parameters` overrides root input defaults only. Keys must match root parameter inputs, not task names, component output names, or artifacts.

Fix: inspect the pipeline function signature or compiled input definitions, then pass only valid parameter inputs. For authoring mismatches, route to `pipeline-authoring`.

## Type-check failures vs disabling checks

Symptoms:

- `InconsistentTypeException`
- messages about incompatible argument types, missing annotations, or artifact/parameter mismatch.

Cause: `Compiler.compile(..., type_check=True)` and CLI default type checking validate component interfaces while constructing/compiling the graph.

Fix order:

1. Prefer fixing the DSL type annotations or wiring (`pipeline-authoring`).
2. If the user explicitly accepts weaker checks, compile with:

   ```bash
   kfp dsl compile --py pipeline.py --output pipeline.yaml --disable-type-check
   ```

   or:

   ```python
   compiler.Compiler().compile(my_pipeline, "pipeline.yaml", type_check=False)
   ```

Record that this bypasses compile-time interface checking; it does not prove runtime correctness.

## Manifest-format flag confusion

Symptoms:

- User passes `--pipeline-name`, `--pipeline-version-name`, `--namespace`, or display-name flags but gets ordinary PipelineSpec YAML.
- CLI warning: `Kubernetes manifest options were provided but --kubernetes-manifest-format was not set. These options will be ignored.`

Cause: manifest naming/namespace flags are guarded by `--kubernetes-manifest-format`.

Fix:

```bash
kfp dsl compile --py pipeline.py --output pipeline-version.yaml \
  --kubernetes-manifest-format \
  --pipeline-name my-pipeline \
  --pipeline-version-name my-pipeline-v1 \
  --namespace kubeflow \
  --include-pipeline-manifest
```

Expected manifest output has `kind: PipelineVersion`; with `--include-pipeline-manifest`, it also has `kind: Pipeline`.

## Deprecated command alias confusion

Symptoms:

- User runs `dsl-compile` and sees a deprecation message.
- Existing scripts still use `dsl-compile`.

Cause: `dsl-compile` is still installed as a legacy console script pointing to the same compile implementation, but help states it is deprecated.

Fix: replace new guidance with `kfp dsl compile`. Keep `dsl-compile --help` only for diagnosing old environments.

## Output path and format errors

Symptoms:

- `The output path ... should end with ".yaml".`
- JSON deprecation warnings.
- Platform-specific features fail when output is `.json`.

Cause: the compiler's supported path is YAML (`.yaml`/`.yml`). JSON output remains deprecated and cannot serialize platform-specific features.

Fix: write to a YAML path and parse YAML documents when checking output.

## Component build Docker and image prerequisites

Symptoms:

- `The docker Python package was not found...`
- component build exits when `base_image` or `target_image` is missing.
- component build exits when discovered components use inconsistent `base_image` or `target_image` values.

Cause: `kfp component build` is a build workflow, not just PipelineSpec compilation. With default `--build-image`, it needs Docker support and image names. It scans components and writes build files.

Fix:

- For help-only or metadata-only workflows, use:

  ```bash
  kfp component build components/ --no-build-image --no-push-image
  ```

- Ensure all discovered components share the same `base_image` and `target_image`, or restrict discovery with `--component-filepattern`.
- Install Docker prerequisites only when the user approves image building/pushing.
