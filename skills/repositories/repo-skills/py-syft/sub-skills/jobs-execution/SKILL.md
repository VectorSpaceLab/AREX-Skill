---
name: jobs-execution
description: "Operate PySyft job submission, review, execution, outputs, runner,
  and job packaging workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# jobs-execution

Use this sub-skill for `submit_python_job`, `submit_bash_job`, `process_approved_jobs`, job review, approval/rejection, outputs/logs, `entrypoint`, dependencies, generated `run.sh`, `config.yaml`, pre-submit scanning, and `syft-job` runner behavior.

## Workflow

1. Confirm DS and DO are accepted peers and synced.
2. DS submits a Python file/folder or bash script. For folders, pass `entrypoint` unless `main.py` is unambiguous.
3. DO reviews code, approves or rejects, and runs approved jobs.
4. DO intentionally shares outputs and optionally logs; DS syncs and reads results.
5. For runner CLI checks use `python -m syft_job.runner_main --help` because the `syft-job` console entry point may be broken in this version.

Read [references/job-workflows.md](references/job-workflows.md), [references/job-api-and-runner.md](references/job-api-and-runner.md), [references/submission-format.md](references/submission-format.md), and [references/troubleshooting.md](references/troubleshooting.md).

Helpers: [scripts/create_python_job_template.py](scripts/create_python_job_template.py) creates safe job code; [scripts/inspect_job_submission.py](scripts/inspect_job_submission.py) checks packaged job shape without executing it.
