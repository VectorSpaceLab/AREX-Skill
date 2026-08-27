# Kubernetes Platform Workflows

These workflows assume the user can already define KFP DSL components and pipelines. If not, route the general DSL work to `pipeline-authoring` first.

## Workflow 1: Configure a task with Secret or ConfigMap data

Use this when a component needs existing Kubernetes data as an environment variable or mounted volume.

```python
from kfp import dsl
from kfp import kubernetes

@dsl.component
def train():
    import os
    print(os.environ["TRAINING_TOKEN"])

@dsl.pipeline
def pipeline():
    task = train()
    kubernetes.use_secret_as_env(
        task,
        secret_name="training-secret",
        secret_key_to_env={"token": "TRAINING_TOKEN"},
        optional=False,
    )
    kubernetes.use_config_map_as_volume(
        task,
        config_map_name="training-config",
        mount_path="/etc/training-config",
        optional=True,
    )
```

Compile and inspect the platform spec for `secretAsEnv` and `configMapAsVolume`. Do not claim that compilation created either resource; the Secret and ConfigMap must already exist at runtime unless the platform supplies them.

## Workflow 2: Share files with PVCs

Use `CreatePVC`, `mount_pvc`, explicit task ordering, and `DeletePVC` for PVC-backed file exchange.

```python
from kfp import dsl
from kfp import kubernetes

@dsl.component
def make_data():
    with open("/data/file.txt", "w") as handle:
        handle.write("data")

@dsl.component
def read_data():
    with open("/reused_data/file.txt") as handle:
        print(handle.read())

@dsl.pipeline
def pipeline():
    pvc = kubernetes.CreatePVC(
        pvc_name_suffix="-work",
        access_modes=["ReadWriteOnce"],
        size="5Gi",
        storage_class_name="standard",
    )

    writer = make_data()
    reader = read_data().after(writer)

    kubernetes.mount_pvc(writer, pvc_name=pvc.outputs["name"], mount_path="/data")
    kubernetes.mount_pvc(reader, pvc_name=pvc.outputs["name"], mount_path="/reused_data")

    kubernetes.DeletePVC(pvc_name=pvc.outputs["name"]).after(reader)
```

The mount helper emits `pvcMount` markers. The volume itself does not create a KFP artifact edge, so keep `.after(...)` when task order matters.

## Workflow 3: Add scheduling and pod-level constraints

Use these helpers when the task Pod must land on specific nodes, tolerate taints, expose metadata, or carry runtime policies.

```python
task = train()
kubernetes.add_node_selector(
    task,
    label_key="cloud.google.com/gke-accelerator",
    label_value="nvidia-tesla-t4",
)
kubernetes.add_toleration(
    task,
    key="accelerator",
    operator="Equal",
    value="nvidia",
    effect="NoSchedule",
)
kubernetes.add_pod_label(task, "workload", "training")
kubernetes.set_image_pull_policy(task, "IfNotPresent")
kubernetes.set_timeout(task, 3600)
kubernetes.set_security_context(task, run_as_non_root=True)
```

Expected platform markers include `nodeSelector`, `tolerations`, `podMetadata`, `imagePullPolicy`, `activeDeadlineSeconds`, and `securityContext`. Compile success does not prove that a matching node or tolerated taint exists.

## Workflow 4: Compile-only validation

1. Compile with the regular KFP compiler.
2. Load or inspect the generated YAML.
3. Find the Kubernetes platform section under `platforms.kubernetes.deploymentSpec.executors`.
4. Assert the relevant per-executor markers are present.
5. Report the result as compile-only evidence.

The bundled script performs this pattern safely; resolve `scripts/...` relative to this sub-skill directory:

```bash
python scripts/compile_kubernetes_config_pipeline.py \
  --output /tmp/kubernetes-platform-smoke.yaml
```

The smoke helper covers Secret env injection plus scheduling constraints and asserts that the generated YAML contains `secretAsEnv`, `nodeSelector`, and `tolerations`.

## Workflow 5: Use parameterized Kubernetes values deliberately

Some helper arguments can be pipeline parameters or task outputs, for example Secret names, ConfigMap names, PVC names, image pull secrets, node selector JSON, node affinity JSON, or toleration JSON.

```python
@dsl.pipeline
def pipeline(secret_name: str):
    task = train()
    kubernetes.use_secret_as_env(
        task,
        secret_name=secret_name,
        secret_key_to_env={"token": "TRAINING_TOKEN"},
    )
```

The compiled platform spec should show a `componentInputParameter` or `taskOutputParameter` reference. Validate the actual value contract elsewhere: it must name a resource that will exist in the target namespace at runtime.

## Coverage anchors for reviewers

Native coverage in the source repository exercises:

- Secret and ConfigMap env/volume serialization, optional flags, preservation across multiple helper calls, pipeline parameters, and task-output parameters;
- PVC mounting with literals, pipeline parameters, task outputs, `sub_path`, and generic ephemeral volumes;
- snapshot read/write compile comparisons for Secret, ConfigMap, PVC, EmptyDir, field-path env, image pull secrets, init containers, node selector, node affinity, security context, timeout, and tolerations;
- the core PVC sample with create -> mount -> read -> delete sequencing;
- SDK compilation tests comparing selected Kubernetes platform specs against golden YAML.
