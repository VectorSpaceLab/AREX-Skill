# Kubernetes Platform Troubleshooting

## `from kfp import kubernetes` fails

Likely causes:

- `kfp-kubernetes` is not installed in the Python environment used to compile.
- `kfp` and `kfp-kubernetes` are installed in different environments.
- A local file or directory named `kfp.py` or `kfp/` shadows the package.
- The addon version is skewed from the KFP SDK version.

Checks:

```python
import importlib.metadata as metadata
import kfp
from kfp import kubernetes

print(kfp.__version__)
print(metadata.version("kfp-kubernetes"))
print(kubernetes.__all__)
```

Fix by installing the addon into the same environment, preferably with `pip install kfp[kubernetes]` or an explicitly matched `kfp-kubernetes` release.

## Helper attached to the wrong object

Symptoms include attribute errors for `platform_config`, no Kubernetes markers in the compiled YAML, or confusion about why a helper appears to do nothing.

Correct pattern:

```python
task = my_component()          # PipelineTask
kubernetes.use_secret_as_env(task, "my-secret", {"token": "TOKEN"})
```

Incorrect targets:

- the decorated component function itself, such as `my_component`;
- a `dsl.ContainerSpec` returned from a container component definition;
- a pipeline function;
- a component spec loaded from YAML before it has been called into a task.

## Compile succeeded, but the run fails on the cluster

Compilation only proves that the SDK emitted platform configuration. Runtime failures can still happen when:

- the Secret, ConfigMap, PVC, StorageClass, image pull secret, VolumeSnapshot, or cloned PVC does not exist in the run namespace;
- the service account lacks permission to read or mount the resource;
- no node matches the node selector/affinity or toleration combination;
- a PVC cannot bind because of access mode, size, storage class, volume name, or data source constraints;
- Pod Security Standards, admission webhooks, or KFP administrator defaults override or reject security context fields.

Route live endpoint submission, run inspection, and namespace/resource checks to `client-and-registry` or `repo-development` depending on whether the user is operating KFP or maintaining the repository/deployment.

## Invalid Kubernetes quantity or resource fields

`size`, EmptyDir `size_limit`, init-container CPU/memory quantities, PVC access modes, and StorageClass names are largely Kubernetes contracts. The SDK may serialize invalid strings that Kubernetes later rejects.

Use standard Kubernetes quantity syntax (`5Gi`, `500Mi`, `250m`, `1`) and check the cluster's supported access modes/storage classes before treating a compiled spec as runnable.

## Invalid Secret, ConfigMap, or key mapping

Common mistakes:

- using a resource name that exists in a different namespace;
- mapping the wrong Secret or ConfigMap data key to an env var;
- expecting `optional=True` to create a missing resource;
- mounting a volume path that conflicts with application expectations.

`optional=True` only tells Kubernetes whether missing keys/resources are tolerated at runtime. It does not synthesize the object.

## Invalid node selector, affinity, or toleration inputs

- `add_node_selector` accepts a single label key/value pair and compiles it under `nodeSelector.labels`.
- `add_node_selector_json` accepts a dict or pipeline parameter, but a valid-looking JSON value can still produce unschedulable Pods.
- `add_node_affinity` validates selector operators and optional preferred weight; weight must be 1-100.
- `add_node_affinity_json` validates literal dict inputs against the Kubernetes client model; parameterized JSON is not fully known until runtime.
- `add_toleration` expects Kubernetes operator values `Equal` or `Exists` and effect values `NoExecute`, `NoSchedule`, or `PreferNoSchedule`.

If a Pod stays pending, inspect the compiled markers first, then inspect cluster nodes/taints only in an operating/runtime context.

## Invalid image pull or security settings

- `set_image_pull_policy` validates that the policy is `Always`, `Never`, or `IfNotPresent`.
- `set_image_pull_secrets` serializes secret names but does not prove the secret exists or can pull the image.
- `set_security_context` requires at least one field, rejects negative UID/GID values, rejects bools for UID/GID, and requires `run_as_non_root` to be a bool.
- Platform defaults can override SDK-provided `runAsUser`, `runAsGroup`, or `runAsNonRoot` at runtime.

## PVC sequencing mistakes

Mounting a PVC is not a data dependency in the KFP graph. If one task writes files and another reads them, call `.after(writer)` on the reader. If a PVC should be cleaned up, call `DeletePVC(...).after(last_reader)`.

## Compile smoke fails

If the bundled smoke script fails:

1. Read the first error line. Import/version errors mean the environment is missing aligned `kfp` and `kfp-kubernetes` packages.
2. If compilation succeeds but marker assertions fail, inspect the generated YAML and confirm that helper calls are made inside the pipeline function against the returned task.
3. Do not debug by submitting to a cluster; the smoke script is intentionally compile-only.
