# Jobs and Sandboxes

Read this reference for hosted compute, scheduled execution, interactive
Sandboxes, and shared SandboxPool design. The API facts below were checked
against the installed public package and its documentation/tests. Examples that
call the Hub are **credentialed and side-effecting**; use them only with an
explicit target, token, budget, and cleanup plan.

## Jobs: inputs, outputs, and state

`run_job` has this representative signature:

```python
run_job(
    *, image, command, env=None, secrets=None, flavor=None, timeout=None,
    name=None, labels=None, volumes=None, expose=None, ssh=False,
    resource_group_id=None, namespace=None, token=None
) -> JobInfo
```

- `image` is a Docker image such as `python:3.12` or a supported Space image
  reference. `command` is an argv list; preserve executable and arguments as
  separate list elements. The default flavor is `cpu-basic`.
- `env` is ordinary job configuration. `secrets` are secret environment values
  sent through the encrypted server-side Job mechanism. Do not place tokens in
  labels, commands, logs, or ordinary environment values.
- `timeout` accepts seconds as a number or a string ending in `s`, `m`, `h`, or
  `d`, for example `300` or `"2h"`. The default Job timeout is 30 minutes;
  training and other long tasks must set a deliberate upper bound.
- `name` becomes a `name` label. It cannot be combined with a `name` key in
  `labels`; other labels are key/value metadata and are replaced when labels
  are updated.
- `volumes` is a list of `Volume` objects. `expose` publishes container ports
  through the Jobs proxy and requires read access to the Job namespace. `ssh`
  enables an SSH endpoint, but requires write access and a registered SSH key.
  `resource_group_id` applies organization resource and spending controls.
- `namespace` defaults to the authenticated user's namespace. An explicit
  namespace is safer for automation because it makes ownership and cleanup
  unambiguous. `token=False` disables auth only for APIs where anonymous access
  is valid; it does not grant access to private or write operations.

`JobInfo` returns the id, creation/start/finish times, image or Space id,
command, arguments, environment, secret metadata where returned, flavor,
volumes, labels, owner, initiator, status, durations, URLs, exposed URLs, and
possibly `status.ssh_url`. Treat a returned Job as accepted/scheduling, not as
successful execution.

The lifecycle stages are:

```text
SCHEDULING -> RUNNING -> COMPLETED
                    \-> CANCELED | ERROR | DELETED
SCHEDULING ----------> CANCELED | ERROR | DELETED
```

`JobStage.COMPLETED`, `CANCELED`, `ERROR`, and `DELETED` are terminal. Check
`job.status.stage` and `job.status.message`; a failed or canceled Job is not
converted into a Python exception by `wait_for_job`.

### Inspect and wait

```python
from huggingface_hub import (
    fetch_job_logs, fetch_job_metrics, inspect_job, list_jobs, wait_for_job,
)

job = inspect_job(job_id="JOB_ID", namespace="OWNER", token=token)
for line in fetch_job_logs(job_id=job.id, namespace="OWNER", follow=False, tail=100, token=token):
    print(line, end="")
finished = wait_for_job(job.id, namespace="OWNER", timeout=3600, poll_interval=2, token=token)
if finished.status.stage != "COMPLETED":
    raise RuntimeError(f"Job did not complete: {finished.status.stage} {finished.status.message}")
```

`list_jobs` is an iterable and supports `status`, `labels`, `timeout`,
`namespace`, and `token`. `wait_for_job` accepts one id or a list of ids and
preserves list order. Its `stages` option can stop at a non-terminal target,
for example `[JobStage.RUNNING]`, while terminal failure still stops the wait.
Reject negative `timeout` and non-positive `poll_interval` before making a
request. `fetch_job_logs(follow=False)` drains currently available output;
`follow=True` blocks and retries the SSE stream. Metrics are an iterable of
resource snapshots rather than a final aggregate; keep the Job status as the
source of truth for completion.

`cancel_job` is a remote mutation. Use it for abandoned or failed work, then
inspect status. Do not repeatedly cancel based only on a transient log-stream
failure.

### Hardware and volumes

Call `HfApi.list_jobs_hardware()` before selecting a non-default flavor. Each
`JobHardwareInfo` exposes `name`, CPU, RAM, ephemeral storage, optional
accelerator details, and unit cost. Representative current enum values include
`cpu-basic`, `cpu-upgrade`, `cpu-performance`, `cpu-xl`, `t4-small`,
`t4-medium`, `a10g-small`, `a10g-large`, `a100-large`, `a100x4`, `a100x8`,
`l4x1`, `l4x4`, `l40sx1`, `l40sx4`, `h200`, and multi-accelerator variants.
The service's available list is authoritative; the enum can lag a server-side
catalog.

A volume is constructed as follows:

```python
from huggingface_hub import Volume

inputs = Volume(type="dataset", source="owner/dataset", mount_path="/data", revision="main")
outputs = Volume(type="bucket", source="owner/bucket", mount_path="/outputs", read_only=False)
```

`type` is `bucket`, `model`, `dataset`, or `space`; `source` is the repository
or bucket id; `mount_path` must be an absolute container path. Repositories are
normally read-only; `revision`, `read_only`, and bucket subpath `path` are
optional. `Volume.to_dict()` produces the API's camel-case payload and
`to_uri()` produces the CLI `hf://...` form.

`sync_job_volume` uploads a local directory to a Jobs artifacts bucket and
returns a mountable Volume; `sync_bucket` pulls results back. Both upload or
transfer data and are side-effecting/networked. Validate paths and output
mounts locally first, use read-only mounts for inputs, and never sync secrets or
unreviewed host directories.

### UV Jobs and schedules

`run_uv_job(script, *, script_args=None, dependencies=None, python=None,
image=None, env=None, secrets=None, flavor=None, timeout=None, name=None,
labels=None, volumes=None, expose=None, ssh=False, resource_group_id=None,
namespace=None, token=None)` is experimental. `script` can be a local path,
URL, or command; the default image is a UV image with Python 3.12. A remote URL
or dependency list adds network and supply-chain risk; prefer a reviewed local
script and pinned dependencies.

Scheduled Jobs use the same job spec and add a schedule:

```python
from huggingface_hub import HfApi

api = HfApi(token=token)
scheduled = api.create_scheduled_job(
    image="python:3.12",
    command=["python", "-c", "print('scheduled')"],
    schedule="@hourly",  # or a validated cron expression
    suspend=True,         # safe initial state for review, still creates remotely
    concurrency=False,
    namespace="OWNER",
)
```

`create_scheduled_job` and `create_scheduled_uv_job` accept `suspend`,
`concurrency`, environment/secrets, flavor, timeout, labels, volumes, exposed
ports, resource group, namespace, and token. Supported aliases include
`@annually`, `@yearly`, `@monthly`, `@weekly`, `@daily`, and `@hourly`; a cron
expression is passed to the service. Validate the schedule with a local parser
or a known-good fixture before creating it.

Scheduled lifecycle operations are:

```python
api.list_scheduled_jobs(namespace="OWNER", token=token)
api.inspect_scheduled_job(scheduled_job_id=sid, namespace="OWNER", token=token)
api.suspend_scheduled_job(scheduled_job_id=sid, namespace="OWNER", token=token)
api.resume_scheduled_job(scheduled_job_id=sid, namespace="OWNER", token=token)
run = api.trigger_scheduled_job(scheduled_job_id=sid, namespace="OWNER", token=token)
api.update_scheduled_job_labels(scheduled_job_id=sid, labels={"env": "prod"}, namespace="OWNER", token=token)
api.delete_scheduled_job(scheduled_job_id=sid, namespace="OWNER", token=token)
```

Listing and inspection are read operations. Create, suspend/resume, trigger,
label update, and delete mutate remote state. `trigger_scheduled_job` starts
one immediate run without changing the schedule. If `concurrency=False` and a
run is active, the service may return HTTP 409; inspect the scheduled record and
existing Job before retrying. A `ScheduledJobInfo` includes `job_spec`,
schedule, suspend/concurrency settings, owner, and status with last run and
next run time.

## Sandboxes

Sandboxes are experimental, best-effort isolation over Jobs. An image only
needs `/bin/sh`; it need not contain Python or an agent. Do not use a Sandbox
as a guarantee that secrets remain hidden from code inside it. Prefer a
short-lived, least-privileged token and a trusted image; `forward_hf_token=True`
explicitly places an HF token in the sandbox as `HF_TOKEN`.

### Dedicated sandbox

```python
from huggingface_hub import Sandbox

with Sandbox.create(
    image="python:3.12",
    flavor="cpu-basic",
    idle_timeout="10m",
    env={"MODE": "check"},
    volumes=[],
    start_timeout=120,
    token=token,
) as sbx:
    result = sbx.run(["python", "-c", "print(42)"], check=True)
    print(result.stdout)
```

`Sandbox.create` returns a ready `Sandbox` and accepts `image`, `flavor`,
`idle_timeout`, per-sandbox `env`, encrypted `secrets`, `volumes`, `namespace`,
`forward_hf_token`, `start_timeout`, and `token`. It creates a billable Job and
waits for the in-job server to be ready. Default idle timeout is 600 seconds;
`None` disables idle eviction, but the Job still has a fixed 24-hour maximum
lifetime. If startup fails after the Job starts, the implementation attempts
cancellation; verify the remote state if the client itself lost connectivity.

`Sandbox.run` accepts a string or argv list. A string is shell-like by default,
while a list is direct argv; `shell=True` requires a string and `shell=False`
requires a list. `cwd`, command `env`, `timeout`, `stdin`, output callbacks,
`check`, and `background` are supported. A nonzero foreground command raises
`SandboxCommandError` unless `check=False`, which returns a result with
`exit_code`, `stdout`, and `stderr`. `background=True` returns a
`SandboxProcess`; only `env`, `cwd`, and `shell` apply in that mode. Inspect
`processes()` and call `process.kill()` when the process is no longer needed.

`sbx.files` provides local-to-sandbox and sandbox-to-local transfer plus
`write`, `read_text`, `list`, `stat`, `exists`, `mkdir`, and `delete`. Validate
local destinations and avoid downloading untrusted output into an important
working directory. `proxy_url_for(port, path, scheme=...)` reaches a server
started inside the sandbox; send `proxy_headers` with the request. Dedicated
sandboxes can listen on a local TCP port. Pooled sandboxes must use the
provided `$SBX_PROXY_DIR/<port>.sock` Unix socket.

### Reattach and termination

```python
sbx = Sandbox.connect("SANDBOX_ID", namespace="OWNER", token=token)
try:
    print(sbx.run(["sh", "-lc", "printf ready"]).stdout)
finally:
    sbx.close()  # releases the client; does not terminate a reattached sandbox
```

`Sandbox.connect` requires a running sandbox and the appropriate namespace
access. `Sandbox.kill(id, ...)` is a remote termination shortcut; an attached
instance's `kill()` terminates a sandbox it owns. A context manager kills a
newly-created sandbox, but an attached handle only closes its local HTTP
client. Treat `kill` as idempotent but still inspect if billing or orphaned
work matters.

### SandboxPool

Use a pool for many cooperative, cheap CPU sandboxes. A pool host is a shared
Job; it cannot provide GPU, per-sandbox volumes, or the dedicated Job secret
channel. Pool-level `image`, `flavor`, `sandboxes_per_host`, `warm_up`,
`max_hosts`, `name`, host `idle_timeout`, namespace, `start_timeout`, and token
are set in the constructor. `pool.create` accepts only per-sandbox `env`,
`idle_timeout`, and `forward_hf_token`.

```python
from huggingface_hub import SandboxPool

with SandboxPool(
    image="python:3.12", flavor="cpu-basic", sandboxes_per_host=20,
    warm_up=1, max_hosts=2, name="review-batch", token=token,
) as pool:
    boxes = [pool.create(env={"TASK": str(i)}) for i in range(4)]
    print(boxes[0].run(["python", "-c", "print('ok')"]).stdout)
```

`warm_up` pre-provisions hosts and starts billing; a pool may grow hosts on
demand until `max_hosts`. A full pool raises `SandboxError` rather than
silently exceeding that ceiling. Pooled env values are delivered at sandbox
creation and are not the dedicated encrypted secret path; do not put sensitive
values there. Use the same image/flavor/name to discover warm hosts across
processes. `SandboxPool.connect(pool_id, ...)` rebuilds configuration from a
running host or cache and does not own shared hosts; closing a connected pool
must not kill them. Explicit pool deletion is required to terminate shared host
Jobs.

`pool.create()` packs into hosts with available capacity. `pool.close()` is
idempotent: a newly-created pool releases its owned hosts, while a connected
handle releases only local clients. A stale local cache must not resurrect a
gone pool; recreate a new pool after confirming no live host remains.

## CLI orientation

The corresponding groups are `hf jobs` and `hf sandbox`. Read their local help
before composing flags because aliases and option names evolve:

```bash
hf jobs hardware
hf jobs run --help
hf jobs scheduled --help
hf jobs wait --help
hf sandbox create --help
hf sandbox pool --help
```

The following examples are remote and should not be run during safe checks:

```bash
hf jobs run --name smoke python:3.12 python -c 'print("hello")'
hf sandbox create --help  # help is safe; creation is not
hf sandbox pool create python:3.12 --flavor cpu-basic  # starts a billable host
```

Use a mock HTTP client for payload assertions. The native behavior worth
rechecking in a mock includes wait polling and terminal failures, volume URI
serialization, Sandbox command shell inference, background process cleanup,
pool packing, pool adoption, stale cache rejection, and maximum-host handling.
