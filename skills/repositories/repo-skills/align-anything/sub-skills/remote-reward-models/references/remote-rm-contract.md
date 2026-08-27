# Remote reward-model contract

This reference captures the operating contract for the Align-Anything remote reward-model path.
It covers the Flask server, the Python client, the math verifier reward function, and the PPO remote-RM launch pattern.

## 1) End-to-end flow

1. Start the reward server with `python -m align_anything.models.remote_rm.run_reward_server`.
2. The server registers a reward function and, when a dataset is provided, builds a prompt → gold-answer lookup table.
3. A client sends `prompts` and `responses` to POST `/get_reward`.
4. The server returns `{"rewards": [...]}`.
5. PPO training uses `RemoteRewardModel.score(...)` to fetch those rewards and inject them into the rollout batch.

## 2) Server startup contract

| Item | Contract |
|---|---|
| Entry point | `python -m align_anything.models.remote_rm.run_reward_server` |
| Host flag | `--host`, default `0.0.0.0` |
| Port flag | `--port`, default `6000` |
| Reward type flag | `--reward-type`, choices: `example_math`, `example_coding`, `example_safety`, `math_verifier` |
| Dataset flag | `--dataset`, optional for generic rewards; effectively required for dataset-backed math verification |
| Startup log | The server prints a human-readable start message and Flask prints `Running on ...` |

### Practical start order

- Use `scripts/start_remote_rm_template.sh` for a smoke-tested launch.
- If you are following the repo’s PPO scripts, the reward server must be running before the DeepSpeed job starts.
- The bundled template treats `math_verifier` as the default smoke path and can bootstrap a one-row dataset when no dataset path is supplied.

## 3) HTTP API contract

### Route
- Method: `POST`
- Path: `/get_reward`

### Request body

| Field | Type | Required | Notes |
|---|---|---|---|
| `prompts` | list[str] | Yes | Must have the same length as `responses`. |
| `responses` | list[str] | Yes | Sent to the configured reward function. |
| `golden_responses` | list[str] | No | Current server code does not read this field; it is optional in the public contract but ignored by the current implementation. |

### Response body

| Field | Type | Notes |
|---|---|---|
| `rewards` | list[float] | Returned on success. The list length should match `prompts`. |
| `error` | string | Returned on 4xx/5xx failures. |

### Status codes

| Status | Meaning |
|---|---|
| `200` | Rewards computed successfully. |
| `400` | Payload shape failure, such as missing `prompts`/`responses` or mismatched lengths. |
| `500` | Server-side exception, such as a missing dataset lookup or reward-function failure. |

### Example payload

```json
{
  "prompts": ["How many vertical asymptotes does the graph of y=2/(x^2+x-6) have?"],
  "responses": ["<think>Factor the denominator.</think><answer>2</answer>"],
  "golden_responses": ["2"]
}
```

### Example success response

```json
{
  "rewards": [1.5]
}
```

## 4) Reward function contract

### Registration signature

The server expects a callable shaped like:

```python
Callable[[List[str], List[str], Optional[List[str]]], List[float]]
```

### Meaning of the arguments

| Argument | Meaning |
|---|---|
| `prompts` | Input prompts as strings. |
| `responses` | Model outputs as strings. |
| `golden_responses` | Optional gold answers supplied by the server after dataset lookup. |

### Return contract

- Return one float per prompt-response pair.
- Keep the returned list length equal to `len(prompts)`.
- Do not return tensors, dicts, or nested structures.

### Built-in reward types

| Reward type | Behavior |
|---|---|
| `example_math` | Lightweight math-shaped heuristic. |
| `example_coding` | Lightweight code-shape heuristic. |
| `example_safety` | Lightweight safety heuristic. |
| `math_verifier` | Format + answer verification using `math_verify` and `latex2sympy2_extended`. |

## 5) Math verifier contract

The math verifier path is designed for deterministic reasoning rewards.

### Required response format

- Exactly one `<think>...</think>` block.
- Exactly one `<answer>...</answer>` block.
- No extra text outside the tags.

### Scoring behavior

| Component | Behavior |
|---|---|
| Format reward | `verify_format(response)` returns `1.0` only when the tag structure is exact. |
| Accuracy reward | `verify_acc(response, golden_response)` checks the extracted answer against the parsed gold answer. |
| Final reward | `0.5 * format_reward + acc_reward` |

### Important edge cases

- A correct answer without the exact tag format is not rewarded.
- If the gold answer cannot be parsed, the verifier may skip the example with a neutral reward path.
- The default lookup uses Levenshtein similarity against the loaded dataset, so exact prompt matching is safer than semantic paraphrase.

## 6) Dataset contract for math verification

| Item | Contract |
|---|---|
| Supported formats | JSON, JSONL, or a Hugging Face dataset name/path |
| Required keys | `question` and `answer` |
| Answer normalization | If the answer does not start with `$`, the server wraps it as `$...$` |
| Lookup method | Prompt text is matched to the nearest stored question with Levenshtein ratio |

### Implications

- If you use `math_verifier`, pass a dataset that contains the same style of questions the trainer will send.
- A missing or unrelated dataset can lead to 500 errors when the server cannot find a valid gold answer.
- Empty answers are risky because the loader expects to inspect the first character.

## 7) RemoteRewardModel client contract

| Behavior | Notes |
|---|---|
| HTTP call | `requests.post(endpoint, json={"prompts": ..., "responses": ...})` |
| SSL verification | Disabled in the client (`verify=False`). |
| Timeouts | Controlled by `timeout`. |
| Retries | Controlled by `retry_times`. |
| Return value | Converts `{"rewards": [...]}` into a `torch.Tensor`. |

### Client failure patterns

- Non-200 responses trigger retries.
- Connection failures, timeouts, and JSON parsing failures also trigger retries.
- After the retry budget is exhausted, the client raises a runtime error.

## 8) PPO remote-RM integration contract

### Config keys to set

| Key | Meaning |
|---|---|
| `model_cfgs.remote_rm_url` | Remote reward endpoint, usually `http://127.0.0.1:6000/get_reward`. |
| `model_cfgs.remote_rm_timeout` | Client timeout in seconds. |
| `model_cfgs.remote_rm_retry_times` | Number of client retries. |
| `model_cfgs.reward_critic_model_name_or_path` | Reward critic checkpoint. |
| `model_cfgs.actor_model_name_or_path` | Actor checkpoint. |

### Trainer behavior

- If `remote_rm_url` is set, the trainer uses the remote reward client and does not rely on a local reward model.
- The reward critic checkpoint is forced to align with the actor checkpoint when the remote-RM branch is active.
- The trainer raises an error if `remote_rm_url` is missing in the remote-RM path.
- The trainer decodes prompts and responses from generated text before calling the client.

### Launch order used by the repo scripts

1. Start the reward server.
2. Export `REMOTE_RM_URL`.
3. Run `deepspeed --module align_anything.trainers.text_to_text.ppo_remote_rm ...`.

### Script patterns to mirror

| Script | Pattern to reuse |
|---|---|
| `scripts/start_remote_rm.sh` | Start server in the background, wait for readiness, then inspect the log. |
| `scripts/qwen2_5_vl/qwen2_5_vl_ppo_remote_rm.sh` | Set `REMOTE_RM_URL`, pass actor/critic paths, and launch the PPO module with DeepSpeed. |
| `scripts/llama/llama_ppo_remote_rm.sh` | Same remote-RM launch order, with PTX settings layered on top. |

## 9) Minimal working checklist

- [ ] Pick a reward type.
- [ ] Ensure the dataset matches the reward type.
- [ ] Start the server and confirm `Running on ...` appears in the log.
- [ ] Probe `/get_reward` with a prompt/response pair.
- [ ] Set `REMOTE_RM_URL` in the PPO launch environment.
- [ ] Confirm the PPO trainer can decode the prompt/response format before blaming the server.

## 10) Unsupported or optional assumptions

- There is no documented GET health endpoint in the current server.
- The incoming `golden_responses` field is optional in the public shape but not consumed by the current server implementation.
- The client disables certificate verification, so do not treat it as production-grade transport security.
- The module entry point can still fail before Flask starts if the broader package import path is missing an optional dependency; treat that as an environment issue, not a remote-RM API issue.
