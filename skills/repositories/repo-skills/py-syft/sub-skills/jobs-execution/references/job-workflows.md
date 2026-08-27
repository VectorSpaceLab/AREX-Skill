# Job workflows

DS submits a job:

```python
ds.submit_python_job(user="owner@example.com", code_path="analysis.py", job_name="analysis")
ds.sync()
```

DO reviews and runs:

```python
do.sync()
job = do.jobs[0]
print(job.code)
job.approve()
do.process_approved_jobs(share_outputs_with_submitter=True, share_logs_with_submitter=False)
do.sync()
```

Use `dependencies=[...]` for extra packages. Use `entrypoint="main.py"` for folder jobs unless there is exactly one root `.py` file or a root `main.py`.
