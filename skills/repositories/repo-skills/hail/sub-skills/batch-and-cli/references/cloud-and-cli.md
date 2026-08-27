# Cloud and CLI Reference

This reference covers packaged `hailctl` user workflows related to Batch, configuration, authentication, Dataproc, HDInsight, and Hail file description. Verified help checks passed for `hailctl --help`, `hailctl auth --help`, `hailctl batch --help`, `hailctl config --help`, `hailctl dataproc --help`, `hailctl describe --help`, `hailctl hdinsight --help`, and `python -m hailtop.hailctl --help` when the installed entry point was on `PATH`.

## Command Families

| Command family | Use for | Safety class |
| --- | --- | --- |
| `hailctl --help`, `python -m hailtop.hailctl --help` | Entry-point and packaging sanity checks | Help-only, safe. |
| `hailctl version` | Installed Hail/Hailtop version display | Read-only, safe. |
| `hailctl config ...` | Hail configuration variables and profiles | Local config mutation for `set`, `unset`, profile changes. |
| `hailctl auth ...` | Hail service login, logout, token/user inspection | Credential mutation and browser/token flow for login/logout. |
| `hailctl batch ...` | Batch Service list/get/log/jobs/wait/cancel/delete/init/submit and billing inspection | Service read, service mutation, or cloud billing depending on subcommand. |
| `hailctl dataproc ...` | Hail-configured Google Dataproc clusters | GCP command execution and cloud resources. Use `--dry-run` where available before mutation. |
| `hailctl hdinsight ...` | Hail-configured Azure HDInsight clusters | Azure command execution and cloud resources. |
| `hailctl describe FILE` | Describe Hail Table/MatrixTable files | Read-only against data path, may need requester-pays project for GCS. |

The installed top-level Typer application also includes `curl` and `dev`, but public runtime guidance should avoid private development or infrastructure commands unless the user explicitly asks for Hail service development operations.

## Configuration Workflows

Use `hailctl config` when a user wants persistent Hail settings rather than passing constructor parameters each time.

Common patterns:

```bash
hailctl config list
hailctl config get batch/billing_project
hailctl config set batch/billing_project BATCH_BILLING_PROJECT
hailctl config set batch/remote_tmpdir gs://BUCKET/hail-batch/tmp/
hailctl config set batch/regions us-central1
hailctl config unset batch/regions
hailctl config profile list
hailctl config profile create project-a
hailctl config profile load project-a
```

Important validated variables include:

- `batch/billing_project`: Batch billing project name.
- `batch/remote_tmpdir`: cloud storage URI for Batch Service scratch data, such as `gs://BUCKET/batch-tmp/`.
- `batch/regions`: comma-separated regions for service jobs.
- `batch/backend`: `local` or `service` for Batch defaults.
- `gcs_requester_pays/project` and `gcs_requester_pays/buckets`: requester-pays project and allow-list style settings.
- `gcs_bucket_allow_list`: bucket allow list for cold-storage policy exceptions.
- `query/backend`: `local`, `spark`, or `batch`; route Hail Query backend selection to setup/backends.

Configuration writes local Hail config files. Avoid showing or copying real config paths in reusable skill content, and do not record secrets or tokens in configuration examples.

## Authentication Workflows

`hailctl auth --help` verified the `login`, `copy-paste-login`, and `logout` commands. Source evidence also exposes user/token inspection and administrative role/user operations, but normal user workflows should focus on login/logout and credential status.

Typical service setup:

```bash
gcloud auth application-default login
hailctl auth login
```

Use `copy-paste-login` only when a browser-based flow is not available and the user has a token from the appropriate Hail auth flow. Treat `logout` as credential mutation. Do not paste tokens or credential files into prompts, scripts, or skill content.

## Batch Service CLI

Verified `hailctl batch --help` reports the Batch Service management family. Source evidence shows these public subcommands:

- `hailctl batch list`: list batches, with query, pagination, and output formatting options.
- `hailctl batch get BATCH_ID`: fetch batch status/details.
- `hailctl batch jobs BATCH_ID`: list jobs with optional state, exit code, name, limit, pagination, and output filters.
- `hailctl batch job BATCH_ID JOB_ID`: show a job status/specification.
- `hailctl batch log BATCH_ID JOB_ID`: retrieve logs, optionally selecting `input`, `main`, or `output` containers and raw bytes.
- `hailctl batch attempts BATCH_ID JOB_ID`: list attempts for a job.
- `hailctl batch wait BATCH_ID`: wait until a batch completes and print status.
- `hailctl batch cancel BATCH_ID`: cancel a batch.
- `hailctl batch delete BATCH_ID`: delete a batch from service/UI records; billing for already-running work may still apply.
- `hailctl batch init`: initialize a Batch environment using cloud tooling.
- `hailctl batch submit [OPTIONS] COMMAND -- [ARGS]...`: submit a single-command service job.
- `hailctl batch billing ...`: billing project inspection subcommands such as list/get.

`hailctl batch submit` accepts options for Docker image, `-v SRC:DST` volume/file mounts, name, CPU, memory, storage, machine type, spot behavior, workdir, cloudfuse mounts, environment variables, billing project, remote tmpdir, requester-pays project, regions, attributes, shell, output format, wait, and quiet mode. Treat it as service submission, not as a local Batch smoke.

Safe planning example:

```bash
hailctl batch submit \
  --name example-batch \
  --billing-project BATCH_BILLING_PROJECT \
  --remote-tmpdir gs://BUCKET/hail-batch/tmp/ \
  --region us-central1 \
  --image ubuntu:24.04 \
  --wait \
  echo -- "hello from Batch"
```

## Dataproc CLI

Verified `hailctl dataproc --help` reports the Hail Dataproc cluster family. Source evidence shows commands for `start`, `stop`, `list`, `connect`, `submit`, `diagnose`, `modify`, and a deprecated nested `describe` alias.

Safety guidance:

- `start`, `stop`, and `modify` create, delete, or alter GCP resources. Use `--dry-run` where available before running cloud mutations.
- `submit` sends a Python script to an existing cluster and may run costly Spark work.
- `connect` opens local tunnels or services to an existing cluster.
- `diagnose` collects cluster and log data; review destination and privacy before sharing outputs.
- `describe` is available as a deprecated Dataproc alias; prefer top-level `hailctl describe FILE` for Hail Table/MatrixTable files.

Dataproc commands require Google Cloud SDK (`gcloud`) and cloud configuration such as project, region, or zone. Missing `gcloud`, unset region/zone, or inaccessible buckets should be handled as environment/configuration issues rather than Hail analysis failures.

## HDInsight CLI

Verified `hailctl hdinsight --help` reports the Hail HDInsight cluster family. Source evidence shows `start`, `stop`, `submit`, and `list`.

Safety guidance:

- `start` creates Azure HDInsight resources and may generate or accept cluster access passwords.
- `stop` deletes the cluster and backing container.
- `submit` sends work to an existing HDInsight cluster and requires the cluster web password.
- `list` invokes Azure CLI resource listing.

Do not store generated passwords, Azure resource names, or storage-account secrets in reusable examples.

## Describe Command

`hailctl describe FILE` describes Hail MatrixTable and Table files. Verified help includes a required `FILE` argument and `--requester-pays-project-id` / `-u` for billing GCS requester-pays reads.

Example:

```bash
hailctl describe path/to/dataset.ht
hailctl describe -u GCP_PROJECT gs://BUCKET/path/to/dataset.mt
```

Use this for schema/metadata inspection. Route actual Table or MatrixTable transformations to the data sub-skills.

## Source-Script Decision Notes

- `diagnose.sh` is reference-only. It models cloud diagnostic intent, but runs external cloud commands and collects cluster logs, so this skill distills safe `hailctl dataproc diagnose` guidance instead of bundling it.
- Dataproc and GCP test shell scripts are excluded from runtime content because they require credentials and mutate cloud resources.
- The Batch benchmark script is reference-only. Its Batch service patterns inform scatter/resource planning, but the script itself depends on repository layout, Docker image building/pushing, pytest benchmark collection, cloud storage permissions, and service-scale execution.

## Cloud Side-Effect Rules

- Always identify whether a command is help-only, local-config mutation, credential mutation, service read, or cloud-resource mutation.
- Prefer `--help`, `--dry-run`, `hailctl config get`, and `hailctl config list` for discovery.
- Ask for explicit confirmation before running commands that create/delete clusters, submit service jobs, cancel/delete batches, initialize cloud environments, or change active profiles.
- Never paste access tokens, service-account keys, cloud passwords, browser login codes, or real billing identifiers into reusable artifacts.
