# Batch Workflows

This reference covers public `hailtop.batch` orchestration: DAGs of shell/Python jobs, local versus service execution, resource files, resource groups, Docker images, resource requests, and safe local smoke patterns.

## Backend Choice

| Situation | Use | Why |
| --- | --- | --- |
| Debug a DAG, command interpolation, file dependencies, or small shell workflow | `hb.LocalBackend()` | Runs on the local machine without Batch Service credentials or cloud billing. |
| Submit a production Batch Service workflow with cloud inputs/outputs | `hb.ServiceBackend(billing_project=..., remote_tmpdir=..., regions=[...])` | Runs jobs on the Hail Batch Service and localizes cloud files through Batch. |
| Run Hail Query itself on the Batch backend via `hl.init_batch` | Route to setup/backends first | `hl.init_batch` is Hail Query backend selection, not a `hailtop.batch` DAG. |
| Package a Hail Table/MatrixTable script as one Batch job | Use this sub-skill for orchestration and route analysis logic to the relevant data sub-skill | Keeps analysis code separate from Batch scheduling. |

Installed API signatures confirm:

- `Batch(name=None, backend=None, attributes=None, requester_pays_project=None, default_image=None, default_memory=None, default_cpu=None, default_storage=None, default_regions=None, default_timeout=None, default_shell=None, default_python_image=None, default_spot=None, project=None, cancel_after_n_failures=None)`.
- `LocalBackend(tmp_dir='/tmp/', gsa_key_file=None, extra_docker_run_flags=None)`.
- `ServiceBackend(*args, billing_project=None, bucket=None, remote_tmpdir=None, google_project=None, token=None, regions=None, gcs_requester_pays_configuration=None, gcs_bucket_allow_list=None)`.

## Minimal Local DAG

```python
import hailtop.batch as hb

backend = hb.LocalBackend()
try:
    batch = hb.Batch(name='hello-local', backend=backend)
    job = batch.new_job(name='hello')
    job.command('echo "hello world"')
    batch.run()
finally:
    backend.close()
```

Use an explicit `LocalBackend` in examples when you want the code to be obviously local-only. `Batch()` without a backend can also use local execution by default, but explicit construction makes safety review easier.

## Service Submission Skeleton

```python
import hailtop.batch as hb

backend = hb.ServiceBackend(
    billing_project='BATCH_BILLING_PROJECT',
    remote_tmpdir='gs://BUCKET/hail-batch/tmp/',
    regions=['us-central1'],
)
try:
    batch = hb.Batch(name='hello-service', backend=backend, default_image='ubuntu:24.04')
    job = batch.new_job(name='hello')
    job.command('echo "hello world"')
    batch.run(wait=True)
finally:
    backend.close()
```

Service jobs require a billing project, a remote scratch directory, authentication, and storage permissions. Prefer a regional `remote_tmpdir` bucket and a matching `regions` value to avoid unexpected data-transfer costs.

## DAG Construction Patterns

- Create shell jobs with `batch.new_job(name='...')` and add one or more shell snippets with `job.command(...)`.
- Create explicit dependencies with `downstream.depends_on(upstream_a, upstream_b)`.
- Prefer implicit file dependencies when a downstream command references an upstream job resource file like `producer.ofile`.
- Use Python loops and helper functions to generate scatter/gather graphs; keep job names deterministic for status filtering.
- Use `batch.run()` only after the graph is fully declared; constructing jobs does not execute them.

Scatter/gather with implicit file dependencies:

```python
import hailtop.batch as hb

backend = hb.LocalBackend()
try:
    batch = hb.Batch(name='scatter-gather', backend=backend)
    parts = []
    for item in ['alpha', 'beta', 'gamma']:
        job = batch.new_job(name=f'emit-{item}')
        job.command(f'printf "%s\\n" {item!r} > {job.ofile}')
        parts.append(job.ofile)

    gather = batch.new_job(name='gather')
    gather.command('cat {inputs} > {output}'.format(inputs=' '.join(parts), output=gather.ofile))
    batch.write_output(gather.ofile, 'combined.txt')
    batch.run()
finally:
    backend.close()
```

## Files and Outputs

| Need | Batch API | Notes |
| --- | --- | --- |
| Local or cloud input file | `batch.read_input(path)` | Produces an input resource file suitable for f-string interpolation in commands. |
| Multi-file input with shared root | `batch.read_input_group(bed='...', bim='...', fam='...')` | Use for tools that expect sidecar files or common roots. |
| Temporary job output | `job.some_name` | Accessing an unused job attribute creates a `JobResourceFile`; avoid names that collide with job methods. |
| Declared output group | `job.declare_resource_group(prefix={'log': '{root}.log', 'txt': '{root}.txt'})` | Use `{root}` literally in the mapping; do not make the mapping itself an f-string. |
| Persist output after the run | `batch.write_output(resource, destination)` | Service backend output destinations should be cloud storage. Local backend can write local paths. |

All Batch-generated files are temporary unless written with `batch.write_output`. For Dockerized local jobs and service jobs, explicitly localize inputs with `read_input` or `read_input_group` instead of relying on a host path being visible inside the container.

## Resource Groups

Resource groups are essential for bioinformatics tools that use file families such as PLINK `.bed/.bim/.fam` or indexed compressed files.

```python
bfile = batch.read_input_group(
    bed='inputs/example.bed',
    bim='inputs/example.bim',
    fam='inputs/example.fam',
)
job = batch.new_job(name='count-fam')
job.command(f'wc -l {bfile.fam} > {job.ofile}')
batch.write_output(job.ofile, 'fam-line-count.txt')
```

Declared job resource group:

```python
job = batch.new_job(name='make-indexed-output')
job.declare_resource_group(result={'data': '{root}.txt', 'index': '{root}.idx'})
job.command(f'printf "data" > {job.result.data}')
job.command(f'printf "index" > {job.result.index}')
batch.write_output(job.result, 'outputs/result')
```

When an extension contains punctuation that is not a valid Python attribute, use dictionary syntax on the group, such as `group['txt.gz']`.

## Docker Images and Resources

- Set a default image at `Batch(default_image='ubuntu:24.04')` or per shell job with `job.image('ubuntu:24.04')`.
- Set default resources with `Batch(default_cpu=..., default_memory=..., default_storage=..., default_regions=..., default_timeout=..., default_spot=...)`.
- Override per job with `job.cpu(...)`, `job.memory(...)`, `job.storage(...)`, and `job.regions([...])`.
- On the service backend, extra storage is mounted for job use; plan paths and output writes accordingly.
- When using private images, ensure the Batch service account has image registry access before submission.

## Requester-Pays and Bucket Allow Lists

- For Batch DAG input/output localization, pass `requester_pays_project='PROJECT'` to `Batch(...)` when accessing requester-pays GCS buckets.
- For the service filesystem itself, use `ServiceBackend(gcs_requester_pays_configuration='PROJECT')` or the tuple form with an allow list if needed.
- Keep requester-pays project IDs as placeholders in reusable examples; never bake real billing identifiers into skill content.
- If only Hail Query reads requester-pays data, route backend configuration details to `../setup-and-backends/SKILL.md`.

## Python Jobs

Use `batch.new_python_job()` when a Python function can be serialized and executed by Batch. Bash jobs are simpler for command-line tools; Python jobs are useful for small Python transformations whose results feed downstream jobs. Convert Python job results to files with methods such as `as_str`, `as_repr`, or `as_json` before using `batch.write_output` or passing them to shell commands.

## Local Smoke Script

Use the bundled script as the first sanity check:

```bash
python scripts/batch_local_smoke.py --help
python scripts/batch_local_smoke.py --dry-run
python scripts/batch_local_smoke.py --run
```

The script creates temporary input/output files, builds a local-only DAG with `LocalBackend`, `read_input`, implicit file dependencies, `depends_on`, and `write_output`, and verifies the resulting text. It does not require cloud credentials.

## Service Planning Checklist

Before switching a local DAG to `ServiceBackend`:

- Confirm `billing_project` and `remote_tmpdir` are set through constructor arguments or `hailctl config`.
- Confirm cloud input and output paths are readable/writable by the service account.
- Set `regions` close to data and image storage.
- Choose Docker images with all tools installed; local host binaries are not available in service containers.
- Use `read_input`, `read_input_group`, and `write_output` for every file that crosses job boundaries or must persist.
- Decide whether `spot` behavior is acceptable for the workload.
- Add deterministic job names and attributes so `hailctl batch jobs`, `hailctl batch log`, and UI searches are useful.

## Source-Script Decision Notes

- The benchmark Batch script was treated as reference-only generation evidence: it shows service-scale image building, permission checks, scatter jobs, aggregation, and JSON output collection, but it is benchmark-scale and depends on cloud resources, Docker pushes, pytest benchmark packages, and maintainer checkout layout.
- Cloud diagnostic shell scripts are not bundled because they run external cloud commands and collect cluster logs. Their safe user-facing intent is distilled in `cloud-and-cli.md` and `troubleshooting.md`.
