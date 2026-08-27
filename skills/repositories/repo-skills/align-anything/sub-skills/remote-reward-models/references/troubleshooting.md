# Remote reward-model troubleshooting

Use this guide when the remote reward server starts, but payload validation or PPO training fails.
It is organized from the earliest failure point to the latest.

## 1) Startup and port problems

| Symptom | Likely cause | What to do |
|---|---|---|
| No `Running on ...` line in the log | Flask server never reached readiness | Open the log, look for import errors or dataset errors, then restart after fixing the root cause. |
| Port already in use | Another reward server or stale process still owns the port | Stop the old PID, or choose a different `REWARD_PORT`. The bundled launcher checks for a live listener before starting. |
| The server exits immediately | Bad reward type, missing dependency, or broken dataset path | Re-run with the same command while capturing the full log; the log usually shows the exception before exit. |
| `ModuleNotFoundError` before Flask starts | A broader Align-Anything import dependency is missing, not the remote-RM code itself | Install the missing dependency or use an environment that satisfies the package initializer before retrying the server launch. |

### Fast checks

1. Confirm the command uses `python -m align_anything.models.remote_rm.run_reward_server`.
2. Confirm the log contains `Reward server started at http://...` or Flask `Running on ...`.
3. Confirm the port in `REMOTE_RM_URL` matches the server port.

## 2) HTTP payload problems

| Symptom | Likely cause | What to do |
|---|---|---|
| `400` with `Request must contain 'prompts' and 'responses'` | Payload missing one of the required keys | Send both lists. Use `scripts/probe_remote_rm_payload.py` to generate a valid request. |
| `400` with length mismatch | `prompts` and `responses` are different lengths | Ensure the lists align one-to-one. |
| Response is not JSON | Endpoint is wrong or the server crashed before handling the request | Check the server log, then confirm the URL path ends with `/get_reward`. |
| The client retries until failure | The server is unreachable, too slow, or returning non-200 status codes | Fix the server first; the client only retries, it does not correct the payload. |

### Validation rule

The current server expects JSON shaped like:

```json
{
  "prompts": ["..."],
  "responses": ["..."]
}
```

Extra fields are tolerated by Flask, but the current server code only relies on `prompts` and `responses`.

## 3) Dataset and math-verifier problems

| Symptom | Likely cause | What to do |
|---|---|---|
| HTTP `500` after a math-verifier request | No dataset was loaded, so the server cannot map the prompt to a gold answer | Pass `--dataset` or use the smoke dataset created by `scripts/start_remote_rm_template.sh`. |
| `500` with a lookup-related exception | The prompt did not match any stored question well enough | Use an exact or near-exact dataset question, or swap to a custom reward function that does not depend on prompt lookup. |
| Unexpected reward of `0.0` on a correct answer | The model output does not satisfy the exact `<think>...</think><answer>...</answer>` format | Reformat the response to match the required tag structure exactly. |
| The reward seems too low despite a correct answer | `math_verifier` only rewards exact formatting plus parsed correctness | Check both the tags and the LaTeX parseability of the answer. |
| Dataset load error | The dataset file does not expose the expected `question` and `answer` fields | Normalize the dataset rows before launching the server. |

### Evidence-grounded notes

- The loader inspects `item['question']` and `item['answer']`.
- It wraps answers in `$...$` when they do not already start with `$`.
- It uses Levenshtein similarity to pick the nearest stored question.
- For `math_verifier`, this means a mismatched dataset can still start but fail at request time.

## 4) Reward-function registration problems

| Symptom | Likely cause | What to do |
|---|---|---|
| `Using default reward function for debug` appears unexpectedly | The requested reward type did not resolve to a registered callable | Pick one of the known reward types or extend the registry before launch. |
| `reward_function is None`-style failure | The server could not register a usable reward function | Confirm the reward type exists in the registry and imports cleanly. |
| Custom reward returns the wrong shape | The callable returned a scalar, tensor, or mismatched list | Return a plain `list[float]` with one value per prompt. |

### Required callable shape

```python
Callable[[List[str], List[str], Optional[List[str]]], List[float]]
```

### Registration rule

The reward function must be set before `app.run(...)` starts serving requests.

## 5) PPO integration problems

| Symptom | Likely cause | What to do |
|---|---|---|
| Trainer raises that the remote reward endpoint is not provided | `remote_rm_url` is unset or empty | Export `REMOTE_RM_URL` or pass `--remote_rm_url ...` in the launch command. |
| Trainer fails before calling the server | The prompt/response text could not be decoded from the generated batch | Check the `user`/`assistant` markers and the output format expected by the trainer. |
| Tokenizer mismatch error for the reward critic | Actor and critic checkpoints do not share a compatible tokenizer | Set `reward_critic_model_name_or_path` to the actor-compatible checkpoint. |
| The trainer uses a local reward model unexpectedly | `remote_rm_url` was left null | Set the URL explicitly so the remote-RM branch is selected. |

### PPO launch sanity checklist

- `REMOTE_RM_URL` points to the live Flask endpoint.
- The reward server is already running.
- The reward critic checkpoint matches the actor tokenizer.
- The training script uses `align_anything.trainers.text_to_text.ppo_remote_rm`.

## 6) Address and port failures

| Symptom | Likely cause | What to do |
|---|---|---|
| Connection refused | Wrong host/port or server not running | Recheck `REWARD_PORT`, `REMOTE_RM_URL`, and the server log. |
| Requests hang until timeout | Server is overloaded or stuck in reward computation | Increase the client timeout only after confirming the server is healthy. |
| Works on `localhost` but not on another machine | The server is bound to a local interface or blocked by networking | Bind to the correct host and confirm firewall or container networking rules. |

### Launcher pattern to remember

- Start the server with `0.0.0.0` when you need external reachability.
- Point the PPO job at `http://127.0.0.1:6000/get_reward` only when the job and server share the same machine.

## 7) Unsupported or optional assumptions

- There is no documented health-check route beyond `/get_reward` in the current implementation.
- The client disables TLS certificate verification; do not use it as a security control.
- The incoming `golden_responses` field is not consumed by the current server, so fixing a request by adding that field will not help unless the server implementation is changed.
- In this repo snapshot, the package import path can fail before the reward server starts if a broader optional dependency is missing; that failure is environmental, not a remote-RM contract bug.

## 8) When to stop debugging and change the setup

Consider switching to a different reward type or a custom reward function when:

- the prompt lookup keeps missing because the dataset does not match your training prompts,
- the math verifier rejects valid answers because the response format is not the project’s tag format,
- or the PPO trainer’s output template cannot be made to match the server’s reward logic.
