# Local Serving Troubleshooting

## Symptoms and recovery

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No model found for ...` | The selected repository cache is missing, stale, or does not contain the requested tag. | Switch to `model-repositories` to inspect `openllm repo update` and `openllm model list`. Confirm the exact `MODEL:VERSION` string. |
| `The machine(...) does not appear to have sufficient resources` | The model Bento needs more GPU memory or a different platform than the local machine provides. | Use a smaller model, choose a cloud deployment, or confirm the resource expectation in `environment-maintenance`. |
| Server waits forever at readiness | `bentoml serve` has not finished loading the model, or a required env var/credential is missing. | Check the output for missing env messages, verify `HF_TOKEN` for gated models, and use `scripts/check_local_server.py` to probe `/readyz`. |
| `http://localhost:3000/chat` does not open | Browser port conflict or server startup failure. | Confirm the selected port, look for binding errors, and retry with a different port. |
| `KeyboardInterrupt` during `run` | User stopped the terminal chat loop. | This is normal. Restart with the same command if you want another chat session. |

## When to stop

Do not keep retrying if the issue is clearly credentials, model download access, or unavailable GPU memory. At that point, move to the owning sub-skill or ask the user for the missing prerequisite.

## Next checks

- Use [scripts/build_serve_command.py](../scripts/build_serve_command.py) to confirm the intended command without starting a model.
- Use [scripts/check_local_server.py](../scripts/check_local_server.py) against a running local server to distinguish readiness from network/port failures.
