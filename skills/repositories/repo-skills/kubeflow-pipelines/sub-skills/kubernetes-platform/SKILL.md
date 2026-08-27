---
name: kubernetes-platform
description: "Attach Kubernetes-specific kfp-kubernetes task configuration to
  Kubeflow Pipelines PipelineTask objects and verify the compiled platform YAML
  without requiring a cluster."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Kubernetes Platform

Use this sub-skill when the user already has a Kubeflow Pipelines DSL task and needs `kfp-kubernetes` platform configuration: Secrets, ConfigMaps, PVCs, ephemeral volumes, node placement, tolerations, pod metadata, image pull settings, field-path env vars, security context, timeout, or init containers.

## Route first

Stay in this sub-skill for:

- installing/importing the `kfp-kubernetes` addon and checking its public `kfp.kubernetes` helper surface;
- applying Kubernetes helpers to `dsl.PipelineTask` objects returned by component calls;
- compile-only verification that the generated YAML contains Kubernetes platform markers.

Route away when the request is really about:

- general DSL components, pipeline structure, type hints, task dependencies, or artifacts -> `pipeline-authoring`;
- compiler flags, CLI wrapper details, package paths, or manifest-format options -> `compiler-and-cli`;
- submitting/running against a live KFP endpoint or proving runtime Secret/PVC/ConfigMap existence -> `client-and-registry` or `repo-development` depending on context;
- repository maintainer internals, backend manifests, deployment configuration, or generated Kubernetes resources -> `repo-development`.

## Operating checklist

1. Verify imports and package alignment before advising on helper behavior:
   ```python
   import importlib.metadata as metadata
   import kfp
   from kfp import kubernetes

   assert metadata.version("kfp-kubernetes") == kfp.__version__
   print(kubernetes.__all__)
   ```
   Install with `pip install kfp[kubernetes]` or `pip install kfp-kubernetes` when the addon is absent.
2. Attach helpers only to a `PipelineTask`, for example `task = my_component()`. Do not pass the component function, a `ContainerSpec`, or the pipeline function itself.
3. Prefer public helpers exported from `kfp.kubernetes.__all__`; see `references/api-reference.md` for signatures, return behavior, and YAML marker names.
4. Compile the pipeline and inspect the platform document/section. Kubernetes helper calls serialize under `platforms.kubernetes.deploymentSpec.executors.<executor>`, not in ordinary component code.
5. State the verification boundary: compile success proves that the DSL emitted platform configuration, but it does not create cluster resources or prove that a Kubernetes Secret, ConfigMap, PVC, StorageClass, node label, toleration target, or admission policy exists.

## Fast compile smoke

Run the bundled smoke helper in an environment with matching `kfp` and `kfp-kubernetes` installed. Resolve the script path relative to this sub-skill directory:

```bash
python scripts/compile_kubernetes_config_pipeline.py \
  --output /tmp/kubernetes-platform-smoke.yaml
```

The script compiles a tiny pipeline, asserts that helper calls return the same `PipelineTask`, and checks for representative `secretAsEnv`, `nodeSelector`, and `tolerations` markers in the YAML. It never contacts a Kubernetes cluster.

## Reference map

- `references/api-reference.md`: installation, public helpers, signatures, return behavior, and platform YAML markers.
- `references/workflows.md`: practical compile-only workflows for Secrets/ConfigMaps, PVCs/volumes, scheduling, pod configuration, and validation boundaries.
- `references/troubleshooting.md`: import/version failures, wrong-object usage, compile-vs-runtime confusion, and invalid Kubernetes inputs.

## Native evidence anchors

This skill is grounded in the `kfp-kubernetes` README/setup metadata, the exported `kfp.kubernetes` source modules, Sphinx API stubs, installed package facts, unit tests for Secret/ConfigMap/volume helpers, snapshot compile/read-write coverage, the core PVC sample, and SDK compilation tests that compare generated platform specs.
