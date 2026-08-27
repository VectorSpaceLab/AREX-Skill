# Ray Jobs and Runtime Environment Operations

Use this reference for submitting applications to an existing Ray cluster, connecting the Jobs CLI/API to the dashboard, packaging working directories and dependencies, and diagnosing runtime environment setup.

## Jobs Address Model

Ray Jobs submit to the Ray dashboard/API server over HTTP. The address is commonly `http://127.0.0.1:8265` for a local cluster or a locally forwarded remote dashboard.

Set the address once:

```bash
export RAY_API_SERVER_ADDRESS="http://127.0.0.1:8265"
```

Or pass it per command:

```bash
ray job submit --address="http://127.0.0.1:8265" -- python script.py
ray job status --address="http://127.0.0.1:8265" <submission_id>
ray job logs --address="http://127.0.0.1:8265" <submission_id>
```

`RAY_JOB_HEADERS` may contain JSON request headers for authenticated gateways:

```bash
export RAY_JOB_HEADERS='{"Authorization": "Bearer <token>"}'
```

Do not confuse the dashboard/API URL with a Ray Client URI such as `ray://host:10001` or a GCS/bootstrap address used by some Ray Core/cluster commands.

## Minimal Job Lifecycle

Use a working directory whenever the entrypoint depends on local files or modules, especially on remote clusters:

```bash
export RAY_API_SERVER_ADDRESS="http://127.0.0.1:8265"
ray job submit --working-dir ./app -- python script.py
```

For long-running jobs:

```bash
ray job submit --no-wait --working-dir ./app -- python worker.py
ray job status <submission_id>
ray job logs <submission_id>
ray job stop <submission_id>
```

Operational notes:

- `ray job submit` runs the entrypoint on the cluster head node by default and streams stdout/stderr unless `--no-wait` is set.
- The `--` separator marks the start of the entrypoint command. Arguments after `--` belong to the user program, not the Ray CLI.
- `--entrypoint-num-cpus`, `--entrypoint-num-gpus`, `--entrypoint-memory`, and `--entrypoint-resources` reserve resources for the entrypoint process itself; tasks and actors launched by the job still need their own Ray resource annotations.
- Keep the submission ID from the CLI output; subsequent `status`, `logs`, `stop`, and `delete` operations use it.
- `ray job delete` deletes stopped job metadata/log association from memory; do not use it while actively debugging unless the user confirms.

## Runtime Environment Fields

Runtime environments can be supplied to Jobs with a YAML file or JSON string:

```bash
ray job submit --runtime-env runtime_env.yaml -- python script.py
ray job submit --runtime-env-json='{"pip": ["requests==2.26.0"]}' -- python script.py
```

Common fields:

| Field | Purpose | Notes |
| --- | --- | --- |
| `working_dir` | Directory or archive made available to the job/tasks/actors. | Local directories are zipped/uploaded for Jobs and Ray Client; remote URI archives can also be used. |
| `py_modules` | Python modules/packages added to worker `PYTHONPATH`. | Supports local paths or remote archives/wheels. |
| `pip` | Pip requirements as a list, requirements file, or dict with `packages`, `pip_check`, and `pip_version`. | Mutually exclusive with top-level `conda` and `uv`. |
| `conda` | Conda environment name, YAML path, or config dictionary. | Ray injects compatibility metadata; put pip dependencies inside the conda spec if using conda. |
| `uv` | Package list handled by Ray's uv runtime environment support. | Mutually exclusive with top-level `pip` and `conda`. |
| `env_vars` | Environment variables set for workers. | Useful for application-level config, not secrets unless the cluster security model is understood. |
| `container` | Container image and run options for workers. | Can only be combined with `config` or `env_vars`. |
| `image_uri` | Container/image URI handled by Ray's image plugin. | Compatible only with fields supported by the active image plugin. |
| `config` | Runtime-env setup behavior. | Supports `setup_timeout_seconds`, `eager_install`, and `log_files`. |

Runtime environment conflicts are validated. In particular, top-level `pip`, `conda`, and `uv` cannot be specified at the same time. A job-level runtime environment and a driver/task/actor runtime environment may be merged, but conflicting fields can raise errors.

## Working Directory Guidance

Use `--working-dir` for most remote job submissions:

```bash
ray job submit --working-dir ./my_app -- python main.py
```

Use a runtime-env file when dependencies and files need to travel together:

```yaml
working_dir: ./my_app
pip:
  - requests==2.26.0
env_vars:
  APP_ENV: staging
config:
  setup_timeout_seconds: 600
```

Then submit:

```bash
ray job submit --runtime-env runtime_env.yaml -- python main.py
```

Packaging cautions:

- Keep `working_dir` small; avoid large datasets, caches, virtualenvs, build artifacts, and credentials.
- If uploads fail or are slow, use a remote `.zip`, `.tar.gz`, `.tgz`, or wheel URI that the cluster can access, or trim the directory with runtime-env excludes when appropriate.
- Relative imports inside the job should resolve from the uploaded working directory. If a module is still missing, inspect both the entrypoint command and runtime-env `working_dir`/`py_modules` settings.
- Runtime-env creation happens through dashboard/runtime-env agents on the cluster; failures may appear in job logs, dashboard events, or runtime-env state/log entries.

## Programmatic Jobs API

The Python API is useful when a tool needs to submit or inspect Jobs without shelling out:

```python
from ray.job_submission import JobSubmissionClient

client = JobSubmissionClient("http://127.0.0.1:8265")
submission_id = client.submit_job(
    entrypoint="python script.py",
    runtime_env={"working_dir": "./app", "pip": ["requests==2.26.0"]},
)
print(client.get_job_info(submission_id).status)
print(client.get_job_logs(submission_id))
```

Use the SDK only when Python code is part of the requested solution. For operational triage, the CLI is easier to audit and quote.

## Remote VM Cluster Access

For clusters launched with Ray's VM cluster launcher, a cluster YAML identifies the head node and SSH configuration. Dashboard access is usually established by forwarding the head node's dashboard port to the local machine:

```bash
ray dashboard cluster.yaml
export RAY_API_SERVER_ADDRESS="http://127.0.0.1:8265"
ray job list
```

`ray dashboard` is a long-running port-forwarding operation. Before running it, confirm the cluster YAML, local port, remote port, cluster name override, and whether an existing port-forward already exists.

Cluster launcher commands such as `ray up`, `ray down`, `ray exec`, `ray attach`, and `ray submit` can create, destroy, or execute on remote VMs. Treat them as mutating and require explicit approval and target confirmation.

## KubeRay Access Concepts

For Ray on Kubernetes, Jobs still use the dashboard/API server HTTP endpoint. Common access patterns are:

- Local port-forwarding from a Ray head service/pod dashboard port to `127.0.0.1:8265`.
- An internal service URL from a client running inside the same cluster/network.
- An ingress or gateway that exposes the dashboard/API endpoint with appropriate authentication and network policy.

Do not create or modify Kubernetes resources unless the user explicitly requests it and provides namespace/context constraints. If the user only asks how to connect, explain the dashboard/API endpoint requirement and ask them for the service name, namespace, and preferred access method.

## Debug Checklist for Jobs

When `ray job status` or `ray job logs` cannot connect or cannot find the job:

1. Verify the Ray CLI and Jobs commands exist: `ray job --help`.
2. Verify the dashboard/API address is HTTP and reachable from the client: `RAY_API_SERVER_ADDRESS` or `--address`.
3. Check whether the dashboard was started and forwarded to the expected port.
4. Confirm the submission ID belongs to the same cluster/dashboard endpoint.
5. Use `ray job list` to discover active/known jobs.
6. If runtime-env setup failed, inspect `ray job logs <submission_id>`, `ray list runtime-envs`, and relevant cluster logs.
7. If state/log output is partial, reduce scope with `--limit`, `--filter`, `--timeout`, or a more specific `ray logs` target.
