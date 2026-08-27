# Compiler API reference

Evidence anchors: `sdk/python/kfp/compiler/compiler.py`, `sdk/python/kfp/compiler/compiler_utils.py`, `sdk/python/kfp/compiler/pipeline_spec_builder.py`, `sdk/python/kfp/compiler/compiler_test.py`, `sdk/python/test/compilation/pipeline_compilation_test.py`, and installed `kfp==2.15.2` signature probe.

## Public compile entry point

```python
from kfp import compiler

compiler.Compiler().compile(
    pipeline_func,
    package_path,
    pipeline_name=None,
    pipeline_display_name=None,
    pipeline_parameters=None,
    type_check=True,
    kubernetes_manifest_options=None,
    kubernetes_manifest_format=False,
)
```

Installed signature verified:

```text
Compiler.compile(self, pipeline_func: kfp.dsl.base_component.BaseComponent, package_path: str, pipeline_name: Optional[str] = None, pipeline_display_name: Optional[str] = None, pipeline_parameters: Optional[Dict[str, Any]] = None, type_check: bool = True, kubernetes_manifest_options: Optional['KubernetesManifestOptions'] = None, kubernetes_manifest_format: bool = False) -> None
```

### Arguments and behavior

| Argument | Meaning | Notes |
|---|---|---|
| `pipeline_func` | Decorated KFP pipeline or component object. | Must be a `BaseComponent` produced by `@dsl.pipeline`, `@dsl.component`, or `@dsl.container_component`; unsupported objects raise a `ValueError`. |
| `package_path` | Output path. | YAML paths ending in `.yaml` or `.yml` are supported. JSON output exists but is deprecated and cannot carry platform-specific features. |
| `pipeline_name` | Override `pipelineInfo.name`. | API-only convenience; CLI manifest naming flags are separate and are ignored unless manifest format is enabled. |
| `pipeline_display_name` | Override `pipelineInfo.displayName`. | API-only PipelineSpec override. |
| `pipeline_parameters` | Dict of input-name to default override. | Keys must match root input parameters. Artifact defaults are not supported; unknown names raise `ValueError`. |
| `type_check` | Enable compile-time interface type checks. | Defaults to `True`. Set `False` only when intentionally bypassing type compatibility checks. |
| `kubernetes_manifest_options` | `KubernetesManifestOptions` object. | Used only when `kubernetes_manifest_format=True`. |
| `kubernetes_manifest_format` | Write Kubernetes native resource manifests. | Produces a `PipelineVersion` document and optionally a `Pipeline` document instead of plain PipelineSpec YAML. |

The method returns `None` and writes the package to `package_path`.

## Kubernetes manifest options

```python
from kfp.compiler.compiler_utils import KubernetesManifestOptions

KubernetesManifestOptions(
    pipeline_name=None,
    pipeline_display_name=None,
    pipeline_version_name=None,
    pipeline_version_display_name=None,
    namespace=None,
    include_pipeline_manifest=False,
)
```

Defaults are derived after the PipelineSpec is available:

- `pipeline_name` defaults to `pipeline_spec.pipeline_info.name`.
- `pipeline_display_name` defaults to `pipeline_name`.
- `pipeline_version_name` defaults to `pipeline_name`.
- `pipeline_version_display_name` defaults to `pipeline_version_name` or the pipeline display name.
- `namespace` is optional.
- `include_pipeline_manifest=False` means only the `PipelineVersion` document is emitted.

Manifest YAML fields verified in source/tests:

- `apiVersion: pipelines.kubeflow.org/v2beta1`
- `kind: Pipeline` when `include_pipeline_manifest=True`
- `kind: PipelineVersion` always in manifest format
- `metadata.name` and optional `metadata.namespace`
- `spec.displayName`, `spec.pipelineName`, and embedded `spec.pipelineSpec`
- `spec.platformSpec` when a non-empty platform spec exists

## Common API patterns

### Compile PipelineSpec YAML

```python
from kfp import compiler

compiler.Compiler().compile(
    pipeline_func=my_pipeline,
    package_path="pipeline.yaml",
    pipeline_parameters={"url": "gs://bucket/input.txt"},
)
```

### Disable type checks deliberately

```python
compiler.Compiler().compile(
    pipeline_func=my_pipeline,
    package_path="pipeline.yaml",
    type_check=False,
)
```

Use this only after explaining that the compile step will no longer catch some incompatible parameter/artifact wiring.

### Compile Kubernetes native manifests

```python
from kfp import compiler
from kfp.compiler.compiler_utils import KubernetesManifestOptions

opts = KubernetesManifestOptions(
    pipeline_name="iris-pipeline",
    pipeline_display_name="Iris Pipeline",
    pipeline_version_name="iris-pipeline-v1",
    pipeline_version_display_name="Iris Pipeline v1",
    namespace="kubeflow",
    include_pipeline_manifest=True,
)

compiler.Compiler().compile(
    pipeline_func=iris_pipeline,
    package_path="iris-pipeline-version.yaml",
    kubernetes_manifest_options=opts,
    kubernetes_manifest_format=True,
)
```

## Output inspection checklist

- Plain PipelineSpec YAML should include `pipelineInfo`, `root`, and `components`; container executors normally appear under `deploymentSpec`.
- Platform-specific features are serialized as a second YAML document for normal YAML output.
- Kubernetes manifest format should parse as one or two Kubernetes resource documents, not a plain top-level PipelineSpec.
- Compilation does not upload, run, or validate cluster resources.
