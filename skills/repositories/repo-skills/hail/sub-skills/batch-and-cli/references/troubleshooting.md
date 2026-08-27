# Batch and CLI Troubleshooting

Use this reference when `hailtop.batch` DAGs fail, local smoke tests do not run, service submissions lack credentials/configuration, `hailctl` commands behave unexpectedly, or cloud commands should be skipped.

## Triage Order

1. Classify the path: local Batch DAG, Batch Service DAG, `hailctl config/auth`, `hailctl batch`, Dataproc, HDInsight, or `hailctl describe`.
2. Reproduce safely with `--help`, `--dry-run`, `hailctl config get`, `hailctl config list`, or `scripts/batch_local_smoke.py --dry-run` before cloud mutation.
3. Confirm `hailtop.batch` imports and the relevant installed signatures match the intended API.
4. For service/cloud paths, confirm auth, billing, remote tmpdir, region, storage permissions, and requester-pays configuration before debugging application code.
5. Route Hail Query backend failures to `../setup-and-backends/SKILL.md`; route Table/MatrixTable/VDS logic failures to the data sub-skills.

## LocalBackend Failures

| Symptom | Likely cause | Response |
| --- | --- | --- |
| `ModuleNotFoundError: hailtop` or `No module named hailtop.batch` | Hail package is not installed or the wrong Python environment is active | Use root environment diagnostics and setup guidance; do not treat it as a Batch DAG bug. |
| `LocalBackend` writes fail under `/tmp` or temp paths | Local tmp directory missing permissions or space | Construct `LocalBackend(tmp_dir='PATH')` with a writable scratch directory; keep paths user-provided, not hard-coded. |
| Dockerized local job cannot see a host input path | Input was not declared with Batch resource APIs | Use `batch.read_input(...)` or `batch.read_input_group(...)`; do not rely on raw host paths inside containers. |
| `docker` not found or image pull fails | Local job uses `job.image(...)` or defaults requiring Docker | Remove the image for a shell-only local smoke, install/start Docker, or switch to a service backend with an accessible image. |
| Shell path does not exist | Custom `shell=` value is invalid | Use a real shell such as `/bin/bash`; tests show nonsense shells raise exceptions. |
| Command not found inside container | Tool is absent from the selected image | Use an image containing the tool or install it in the command before use; local host binaries are not automatically available. |
| Empty or whitespace command ignored | `job.command(...)` received only whitespace | Build commands explicitly and validate strings before adding them to jobs. |

Run the bundled smoke locally:

```bash
python scripts/batch_local_smoke.py --dry-run
python scripts/batch_local_smoke.py --run
```

If `--run` fails before executing a job, inspect import/backend setup. If it fails after execution, inspect command quoting, temp directory permissions, or output write location.

## File and Dependency Mistakes

| Symptom | Likely cause | Response |
| --- | --- | --- |
| Downstream job runs too early | No explicit dependency and no referenced upstream resource file | Use `downstream.depends_on(upstream)` or reference the upstream output file in the downstream command. |
| Output disappears after `batch.run()` | Batch job outputs are temporary by default | Add `batch.write_output(job_resource, destination)` for every file that must persist. |
| Resource group becomes a single file | `declare_resource_group` was omitted | Declare the group with mappings such as `{'bed': '{root}.bed', 'bim': '{root}.bim'}` before using it. |
| Curly braces in resource group mapping are wrong | Mapping was accidentally made an f-string | Use literal `{root}` in the mapping; interpolate the resource group later in commands. |
| Attribute error or unexpected job method collision | Output name collides with a `Job`/`BashJob` method or property | Use neutral output names like `out`, `ofile`, `result`, or declared resource groups. |
| Paths with spaces break commands | Shell interpolation is unquoted | Prefer Batch resource objects and robust shell quoting. Test with the local smoke or a tiny local job before service submission. |

## ServiceBackend Configuration

| Symptom | Likely cause | Response |
| --- | --- | --- |
| `billing_project` parameter must be set | No constructor argument and no `hailctl config` value | Pass `ServiceBackend(billing_project='...', remote_tmpdir='...')` or set `hailctl config set batch/billing_project ...`. |
| Remote tmpdir validation fails | Scratch URI missing, malformed, or inaccessible | Use a valid cloud storage URI such as `gs://BUCKET/hail-batch/tmp/`; confirm service account read/write access. |
| Authentication failure | Missing `gcloud auth application-default login`, missing `hailctl auth login`, expired token, or wrong profile | Re-run auth flow in the intended environment; avoid copying tokens into artifacts. |
| Service job cannot read/write bucket | Service account lacks storage permissions | Grant the Batch service identity appropriate bucket/object access, then retry a minimal job. |
| Unexpected network/egress costs or slow localization | Compute region differs from data/image location | Set `Job.regions`, `Batch(default_regions=...)`, `ServiceBackend(regions=...)`, `HAIL_BATCH_REGIONS`, or `hailctl config set batch/regions ...`. |
| Private image pull fails | Batch service account lacks registry access | Grant registry read access or use a public image containing the required tools. |
| Batch UI shows `Failure` or `Error` | Main command nonzero, container setup failure, OOM, or localization issue | Inspect `hailctl batch log BATCH_ID JOB_ID` and container-specific logs (`input`, `main`, `output`). |
| Job is cancelled/deleted unexpectedly | User or automation called cancel/delete | Use `hailctl batch get` and `hailctl batch jobs` to inspect state; deletion from UI does not undo costs for work already performed. |

Prefer constructor arguments for one-off scripts and `hailctl config` for persistent per-profile defaults. Keep billing projects and bucket names as placeholders in reusable examples.

## Requester-Pays and Bucket Allow Lists

| Symptom | Likely cause | Response |
| --- | --- | --- |
| GCS read fails with requester-pays billing error | No requester-pays project configured | For Batch DAG localization, use `Batch(requester_pays_project='PROJECT')`; for service filesystem access, use `ServiceBackend(gcs_requester_pays_configuration='PROJECT')` or config variables. |
| Only some buckets should be billed | Missing allow-list style configuration | Use `gcs_requester_pays/buckets` or the tuple-style requester-pays configuration where appropriate. |
| `hailctl describe` fails on requester-pays GCS data | Describe command lacks billing project | Use `hailctl describe -u GCP_PROJECT gs://BUCKET/path`. |
| Hail Query reads fail, not Batch localization | Wrong sub-skill | Route to setup/backends and data workflow references for `hl.init` or query-specific requester-pays settings. |

## CLI Configuration Problems

| Symptom | Likely cause | Response |
| --- | --- | --- |
| `hailctl` not found | Entry-point directory is not on `PATH` | Try `python -m hailtop.hailctl --help` from the active Python environment or fix the shell `PATH`. |
| `hailctl config set` rejects a value | Variable validation failed | Check allowed forms: `batch/backend` is `local` or `service`; `query/backend` is `local`, `spark`, or `batch`; `batch/remote_tmpdir` must be a cloud storage URI. |
| `hailctl config get` prints nothing | Value is unset or overridden by profile/source behavior | Use `hailctl config list` and `hailctl config config-location` to inspect active/default/profile sources. |
| Wrong profile is active | `profile` config variable points to a different profile | Use `hailctl config profile list` and `hailctl config profile load PROFILE`. |
| User asks for Hail Query backend setting through config | Batch/CLI and setup overlap | Document `query/backend` existence but route backend initialization decisions to setup/backends. |

## Command Misuse and Quoting

- Use `--` before command arguments that look like options in `hailctl batch submit`, `hailctl dataproc submit`, and `hailctl hdinsight submit`.
- For `hailctl batch submit -v SRC:DST`, `DST` must be an absolute path. A trailing slash changes copy semantics.
- Do not pass local paths to service jobs unless they are mounted/localized through CLI options or Batch APIs.
- Prefer deterministic job names and attributes; they make `hailctl batch jobs --name ...` and log lookup useful.
- Use `output=json` or YAML/grid output options when machine-readable status is needed and the command family supports it.

## Dataproc Skip and Failure Conditions

Skip or ask before running Dataproc commands when:

- Google Cloud SDK is missing or not authenticated.
- Project, region, or zone is unknown.
- The command would create, delete, modify, or submit work to a cluster without explicit user approval.
- The workflow requires VEP installation, custom wheels, requester-pays data, or large cloud resources that the user has not authorized.
- The task is ordinary `hailtop.batch` service execution rather than a Spark cluster workflow.

Use `--dry-run` where available for `start`, `stop`, `connect`, `submit`, and `modify` planning.

## HDInsight Skip and Failure Conditions

Skip or ask before running HDInsight commands when:

- Azure CLI is missing or unauthenticated.
- Storage account, resource group, cluster password, or location is unknown.
- The command would create or delete Azure resources.
- The task can be solved with local Batch smoke or Hail Query backend setup instead.

Do not expose generated cluster passwords or storage credentials in logs or examples.

## Native Verification Candidates

Useful native candidates after whole-skill integration:

- Local Batch file/dependency behavior from the local backend tests.
- Hail configuration CLI behavior from config CLI tests.
- CLI help checks for packaged `hailctl` command families.
- Service, Dataproc, HDInsight, and GCP integration tests should be skipped unless explicit credentials, billing authorization, and safe resource limits are available.
