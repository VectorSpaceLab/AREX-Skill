---
name: batch-and-cli
description: "Use hailtop.batch DAGs and packaged hailctl commands for Hail
  Batch, cloud configuration, authentication, cluster helpers, and file
  description workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Batch and CLI

Use this sub-skill when the task mentions Hail Batch, `hailtop.batch`, `Batch`, `LocalBackend`, `ServiceBackend`, `new_job`, resource files, Docker/resource settings, `hailctl batch`, `hailctl config`, `hailctl auth`, `hailctl dataproc`, `hailctl hdinsight`, `hailctl describe`, billing projects, requester-pays, regions, or `remote_tmpdir`.

## Route First

- Read `references/batch-workflows.md` for Python `hailtop.batch` DAG construction, local/service backend choice, dependencies, input/output files, resource groups, Docker images, resource requests, and scatter/gather planning.
- Read `references/cloud-and-cli.md` for packaged `hailctl` command families, Batch service configuration, auth, Dataproc, HDInsight, `describe`, and cloud side-effect boundaries.
- Read `references/troubleshooting.md` for LocalBackend/Docker/tmp failures, ServiceBackend auth/billing/remote tmpdir errors, requester-pays access, command interpolation mistakes, and cloud skip conditions.
- Run `scripts/batch_local_smoke.py --help` first; use `scripts/batch_local_smoke.py --dry-run` for a no-execution template or `scripts/batch_local_smoke.py --run` for a local-only smoke when `hailtop.batch` is importable.

## Boundaries

- For Hail query backend selection, `hl.init`, `hl.init_batch`, Spark/local setup, package import failures, or generated runtime asset issues, route to `../setup-and-backends/SKILL.md` unless the task is specifically about `hailtop.batch` DAG execution.
- For Table or MatrixTable analysis code, route to `../tables-and-expressions/SKILL.md` or `../genomics-analysis/SKILL.md`; use this sub-skill only to package those scripts as Batch jobs.
- For sparse `VariantDataset` or GVCF combiner workflows, route data-processing logic to `../variant-datasets/SKILL.md`; keep this sub-skill focused on orchestration.
- Do not recommend private development, service-maintenance, or deployment commands as public user workflows. Prefer packaged `hailctl` commands visible in installed help.

## Verified Entry Points

- Python API: `hailtop.batch.Batch`, `LocalBackend`, `ServiceBackend`, `Batch.new_job`, `Batch.new_python_job`, `Batch.read_input`, `Batch.read_input_group`, `Batch.write_output`, `Job.depends_on`, `BashJob.command`, `BashJob.declare_resource_group`, `BashJob.image`, `Job.cpu`, `Job.memory`, `Job.storage`, and `Job.regions`.
- Installed signatures include `Batch(name=None, backend=None, attributes=None, requester_pays_project=None, default_image=None, default_memory=None, default_cpu=None, default_storage=None, default_regions=None, default_timeout=None, default_shell=None, default_python_image=None, default_spot=None, project=None, cancel_after_n_failures=None)`.
- Installed signatures include `LocalBackend(tmp_dir='/tmp/', gsa_key_file=None, extra_docker_run_flags=None)` and `ServiceBackend(*args, billing_project=None, bucket=None, remote_tmpdir=None, google_project=None, token=None, regions=None, gcs_requester_pays_configuration=None, gcs_bucket_allow_list=None)`.
- Verified CLI help covers `hailctl --help`, `hailctl auth --help`, `hailctl batch --help`, `hailctl config --help`, `hailctl dataproc --help`, `hailctl describe --help`, `hailctl hdinsight --help`, and `python -m hailtop.hailctl --help`.

## Safety Defaults

- Start with `LocalBackend` for examples, smoke tests, and DAG debugging; it avoids Batch Service credentials and cloud billing.
- Treat `ServiceBackend`, `hailctl batch submit`, `hailctl batch init`, `hailctl dataproc start`, `hailctl dataproc stop`, `hailctl dataproc modify`, `hailctl hdinsight start`, and `hailctl hdinsight stop` as cloud-mutating or billing-impacting.
- Use placeholders for billing projects, buckets, tokens, and remote tmpdirs; do not store credentials in scripts, skills, prompts, or logs.
- Close explicit backend objects after use with `backend.close()` or the async close pattern used by the surrounding application.
