# Agents and Workflows Troubleshooting

## Symptoms and Recovery

| Symptom | Likely cause | Recovery |
|---|---|---|
| Agent keeps calling the wrong tool | Prompt formatting mismatch, tool list missing, or the model is not following the schema. | Inspect the prompt builder and parser reference; verify the tool is registered. |
| Parser raises an exception on output | The model output is not JSON-like or lacks the expected tool fields. | Use the output-parsing reference and a smaller prompt/result sample. |
| Task queue appears empty | Redis not reachable, wrong queue name, or tasks were not seeded. | Check the Redis URL and the task queue prefix. |
| Workflow does not advance | Permission step not resolved, wait step still pending, or next-step links are missing. | Inspect the workflow seed and the execution loop reference. |
| Scheduled agents never run | Celery beat or scheduler is not running, or database state is missing. | Verify the worker/scheduler layer in `superagi.worker`. |
| Token counts or history look wrong | Prompt builder and token counter truncated the context. | Reduce prompt size or inspect the token-limit settings. |

## Safe Recovery Steps

- Use the payload validator script before debugging an API or template payload.
- Check Redis/database connectivity before assuming workflow logic is broken.
- Prefer static inspection of the workflow seed and prompt templates before
  starting a live worker.
