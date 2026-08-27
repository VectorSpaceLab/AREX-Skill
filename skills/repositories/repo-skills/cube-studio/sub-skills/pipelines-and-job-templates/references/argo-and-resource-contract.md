# Argo and resource contract

This reference distills the fields that tie CubeStudio pipelines to the generated Argo workflow objects and the container runtime.

## Workflow-level fields that matter most

- `name` / workflow name: used to identify the run instance
- `description`: becomes a human-readable annotation
- `namespace`: usually the pipeline namespace
- `parallelism`: limits concurrent DAG task execution
- `ttlStrategy`: controls how long completed runs stay in the cluster
- `imagePullSecrets`: derived from the repo's hubsecret / repository setup
- `serviceAccountName`: the account used to launch workflow pods

## Task / container fields that matter most

- `task.job_template.entrypoint`
- `task.job_template.workdir`
- `task.job_template.env`
- `task.args`
- `task.working_dir`
- `task.volume_mount`
- `task.resource_cpu`
- `task.resource_memory`
- `task.resource_gpu`
- `task.get_node_selector()`
- `task.skip`
- `task.timeout`
- `task.retry`

## Runtime environment variables frequently injected by pipelines

- `KFJ_TASK_ID`
- `KFJ_TASK_NAME`
- `KFJ_TASK_NODE_SELECTOR`
- `KFJ_TASK_VOLUME_MOUNT`
- `KFJ_TASK_IMAGES`
- `KFJ_TASK_RESOURCE_CPU`
- `KFJ_TASK_RESOURCE_MEMORY`
- `KFJ_TASK_RESOURCE_GPU`
- `KFJ_TASK_PROJECT_NAME`
- `USERNAME`
- `IMAGE_PULL_POLICY`
- `HUBSECRET`

## Resource semantics

- `resource_cpu` and `resource_memory` should remain within the form validators' simple numeric/`G`-suffixed expectations.
- `resource_gpu` is parsed as a quantity plus an optional GPU model in parentheses, and the node selector switches to GPU placement when the quantity is at least one.
- The task selector and pipeline selector should be read together; the final placement is a merge of project, cluster, and task intent.
- A skipped task is represented in Argo with a condition that prevents execution instead of removing the node.

## Output / metrics contract

CubeStudio templates often write outputs and visualization artifacts back to mounted workspace paths or a `/metric.json` style artifact. When a pipeline fails to show charts or tables, verify:

- the task wrote to the expected mounted path,
- the artifact path is reachable from the notebook or workspace layer,
- the metrics JSON shape matches the UI's expected entries.

## Native evidence

- `view_pipeline.py` and `model_job.py` define the workflow construction logic.
- `job-template/job/demo` shows a minimal example of file output and metrics output.
- `job-template/job/model_offline_predict` and `job-template/job/pytorch` show richer runtime launch patterns.
