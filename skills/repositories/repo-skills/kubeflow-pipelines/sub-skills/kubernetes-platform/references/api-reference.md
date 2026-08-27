# kfp-kubernetes API Reference

This reference is for the public addon imported as:

```python
from kfp import kubernetes
```

Install it with `pip install kfp[kubernetes]` or `pip install kfp-kubernetes`. In the inspected package set, `kfp`, `kfp-kubernetes`, and `kfp-pipeline-spec` are all version `2.15.2`; keep `kfp` and `kfp-kubernetes` aligned unless a release note explicitly says otherwise.

## Public helper surface

The inspected `kfp.kubernetes.__all__` exports these helpers:

```python
[
    'add_ephemeral_volume', 'add_init_container', 'add_node_selector',
    'add_node_selector_json', 'add_node_affinity', 'add_node_affinity_json',
    'add_pod_annotation', 'add_pod_label', 'add_toleration',
    'add_toleration_json', 'CreatePVC', 'DeletePVC', 'empty_dir_mount',
    'mount_pvc', 'set_image_pull_policy', 'use_field_path_as_env',
    'set_image_pull_secrets', 'set_security_context', 'set_timeout',
    'use_config_map_as_env', 'use_config_map_as_volume',
    'use_secret_as_env', 'use_secret_as_volume',
]
```

Use only this public surface for operating guidance unless the user is doing repository-maintainer work.

## How helpers work

Most helpers accept a `dsl.PipelineTask` as their first argument, update `task.platform_config['kubernetes']`, and return the same task object. `CreatePVC` and `DeletePVC` are container components; calling them inside a pipeline returns a `PipelineTask` whose output can be wired into `mount_pvc` or delete sequencing.

Kubernetes platform config is emitted at compile time under a platform document/section like:

```yaml
platforms:
  kubernetes:
    deploymentSpec:
      executors:
        exec-some-task:
          secretAsEnv: []
          nodeSelector:
            labels: {}
```

## Helper groups and YAML markers

| Helper | Key arguments | Return behavior | Compiled marker |
|---|---|---|---|
| `use_secret_as_env(task, secret_name, secret_key_to_env, optional=False)` | Secret name as string/pipeline parameter/task output; map Secret key -> env var | returns `PipelineTask` | `secretAsEnv` |
| `use_secret_as_volume(task, secret_name, mount_path, optional=False)` | Secret name and mount path | returns `PipelineTask` | `secretAsVolume` |
| `use_config_map_as_env(task, config_map_name, config_map_key_to_env, optional=False)` | ConfigMap name as string/pipeline parameter/task output; map ConfigMap key -> env var | returns `PipelineTask` | `configMapAsEnv` |
| `use_config_map_as_volume(task, config_map_name, mount_path, optional=False)` | ConfigMap name and mount path | returns `PipelineTask` | `configMapAsVolume` |
| `CreatePVC(access_modes, size, pvc_name=None, pvc_name_suffix=None, storage_class_name='', volume_name=None, annotations=None, data_source=None)` | PVC spec fields; exactly one of fixed name or suffix when naming dynamically | calling it returns a `PipelineTask` with `outputs['name']` | ordinary create-PVC component task; mounted consumers emit `pvcMount` |
| `mount_pvc(task, pvc_name, mount_path, sub_path='')` | PVC name as string/pipeline parameter/task output | returns `PipelineTask`; adds dependency when PVC name comes from an upstream task output | `pvcMount` |
| `DeletePVC(pvc_name)` | PVC name, commonly `CreatePVC(...).outputs['name']` | calling it returns a `PipelineTask` | ordinary delete-PVC component task; use `.after(...)` for cleanup sequencing |
| `add_ephemeral_volume(task, volume_name, mount_path, access_modes, size, storage_class_name=None, labels=None, annotations=None)` | Generic ephemeral volume claim template fields | returns `PipelineTask` in source; signature has no return annotation | `genericEphemeralVolume` |
| `empty_dir_mount(task, volume_name, mount_path, medium=None, size_limit=None)` | EmptyDir volume and mount details | returns `PipelineTask` | `emptyDirMounts` |
| `add_node_selector(task, label_key, label_value)` | one node-selector label pair | returns `PipelineTask` | `nodeSelector.labels` |
| `add_node_selector_json(task, node_selector_json)` | dict or pipeline parameter with node selector JSON | returns `PipelineTask` | `nodeSelector.nodeSelectorJson` |
| `add_node_affinity(task, match_expressions=None, match_fields=None, weight=None)` | selector terms; operators `In`, `NotIn`, `Exists`, `DoesNotExist`, `Gt`, `Lt`; optional preferred weight 1-100 | returns `PipelineTask` | `nodeAffinity` |
| `add_node_affinity_json(task, node_affinity_json)` | Kubernetes NodeAffinity dict or pipeline parameter | returns `PipelineTask`; validates dict inputs against Kubernetes client model | `nodeAffinity.nodeAffinityJson` |
| `add_toleration(task, key=None, operator=None, value=None, effect=None, toleration_seconds=None)` | operator `Equal`/`Exists`; effect `NoExecute`/`NoSchedule`/`PreferNoSchedule` | returns `PipelineTask` in source; signature has no return annotation | `tolerations` |
| `add_toleration_json(task, toleration_json)` | dict/list or pipeline parameter containing toleration object(s) | returns `PipelineTask` in source; signature has no return annotation | `tolerations` |
| `add_pod_label(task, label_key, label_value)` | Pod metadata label | returns `PipelineTask` | `podMetadata.labels` |
| `add_pod_annotation(task, annotation_key, annotation_value)` | Pod metadata annotation | returns `PipelineTask` | `podMetadata.annotations` |
| `use_field_path_as_env(task, env_name, field_path)` | Downward API field path | returns `PipelineTask` | `fieldPathAsEnv` |
| `set_image_pull_policy(task, policy)` | one of `Always`, `Never`, `IfNotPresent` | returns `PipelineTask`; validates policy immediately | `imagePullPolicy` |
| `set_image_pull_secrets(task, secret_names)` | list of secret names or pipeline parameter channels | returns `PipelineTask` | `imagePullSecret` |
| `set_security_context(task, run_as_user=None, run_as_group=None, run_as_non_root=None)` | container identity fields | returns `PipelineTask`; validates at least one field, nonnegative ints, and bool type | `securityContext` |
| `set_timeout(task, seconds)` | integer seconds; `0` removes timeout fields from previous calls | returns `PipelineTask`; rejects negative values | `activeDeadlineSeconds` |
| `add_init_container(task, name, image, command=None, args=None, env=None, volume_mounts=None, restart_policy=None, resource_requests=None, resource_limits=None)` | init container or native sidecar details; `restart_policy` may be `Always` only | returns `PipelineTask`; validates name/image, absolute mount paths, duplicate names, and nonempty resource quantities | `initContainers` |

## Parameterized resource names

Secret names, ConfigMap names, PVC names, image pull secrets, JSON node selectors/affinity, and tolerations may be literals or pipeline channels where their signatures allow it. The helper registers channel inputs and, for upstream task outputs, may add task ordering. The compiler can serialize the parameter reference, but the cluster validates the eventual value only when a run is created and Pods are admitted.

## Compile-time validation limits

The helpers validate some SDK-level mistakes, but many Kubernetes constraints remain runtime-only:

- Secret/ConfigMap/PVC/StorageClass existence and access permissions are not checked by compilation.
- Kubernetes quantity strings such as `5Gi`, CPU/memory resource quantities, and StorageClass capabilities are admitted by Kubernetes, not fully proven by the SDK.
- Node selectors, affinities, and tolerations can compile even if no node satisfies them.
- Platform/admin security defaults may override user-specified `runAsUser`, `runAsGroup`, or `runAsNonRoot` at runtime.
