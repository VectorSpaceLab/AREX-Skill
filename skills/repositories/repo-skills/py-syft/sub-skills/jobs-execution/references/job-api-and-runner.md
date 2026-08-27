# Job API and runner

| API | Verified shape | Use |
| --- | --- | --- |
| `submit_python_job` | `submit_python_job(user, code_path, job_name='', dependencies=None, entrypoint=None, force_submission=False, ignore_peer_version=False)` | DS submits Python file/folder. |
| `submit_bash_job` | `submit_bash_job(user, script, job_name='', force_submission=False, ignore_peer_version=False)` | DS submits bash script. |
| `process_approved_jobs` | `process_approved_jobs(stream_output=True, timeout=None, force_execution=False, share_outputs_with_submitter=False, share_logs_with_submitter=False, ignore_peer_version=False)` | DO runs approved jobs. |

Runner help:

```bash
python -m syft_job.runner_main --help
```

Known entry-point issue: `syft-job` may fail with `ImportError: cannot import name 'main' from 'syft_job'` in this version.
