# Data, reward, and workflow troubleshooting

## Dataset schema problems

| Symptom | Likely cause | Fix |
|---|---|---|
| Built-in loader rejects dataset | `path`/`type` does not match built-in routing and path is not a saved Hugging Face dataset | Use a supported dataset path/type, save a dataset to disk, or implement a custom loader before trainer launch. |
| RLVR workflow sees no prompt | Row lacks `messages` or custom extraction function | Add `messages=[{"role":"user","content":"..."}]` or pass a custom `get_input_ids_fn`. |
| SFT training fails on missing masks | SFT dataset not tokenized into `input_ids` and `loss_mask` | Pre-tokenize prompt+answer and mask only completion tokens. |
| VLM processor errors | Image field is missing, path inaccessible, or processor/tokenizer mismatch | Validate a tiny sample JSON with `--expect-vlm` and pass matching processor/tokenizer. |
| Dataset loading is slow or network-bound | Loader downloads public data at runtime | Pre-stage data or use a saved local dataset in production; do not make validation depend on downloads. |

## Reward function failures

| Symptom | Likely cause | Fix |
|---|---|---|
| Reward import fails on worker | Function is nested, lambda, or not module-level | Move it to an importable module-level symbol and pass its import string. |
| Reward returns coroutine | Async function used where sync reward is expected | Wrap with `AsyncRewardWrapper` only where AReaL expects async reward handling, or make the function synchronous. |
| Reward has wrong parameters | Signature does not accept `prompt`, `completions`, `prompt_ids`, `completion_ids`, and dataset fields | Add `**kwargs` or the specific dataset fields used by the workflow. |
| Reward returns list/string/dict unexpectedly | Workflow expects scalar reward for a sample | Return `float`/numeric scalar unless using an agent workflow return dict keyed by interaction id. |
| Math answer extraction is brittle | Model output format differs from expected boxed/final-answer pattern | Add robust extraction and format reward separately from accuracy reward. |

## Rollout workflow failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `arun_episode` blocks event loop | Sync I/O, blocking client, or CPU-heavy work inside async rollout | Use async clients, `await`, batching, or subprocess mode for blocking agents. |
| Returned tensors have mismatched shape | `input_ids`, `attention_mask`, `loss_mask`, `logprobs`, `rewards`, or `versions` shapes differ | Follow tensor dictionary contract; batch dimension must align. |
| Loss trains on prompts/tools | `loss_mask` marks prompt or tool/context tokens as trainable | Mask only assistant/model-generated tokens intended for policy loss. |
| Grouped rollout drops all samples | Workflow returns `None` for every group member | Inspect rejection criteria and reward/filter logic; consider dynamic batch settings. |
| Trajectory dump decode fails | Missing tokenizer/processor or multimodal serialization issue | Set rollout tokenizer/processor fields and validate image/message format. |

## Agent workflow failures

| Symptom | Likely cause | Fix |
|---|---|---|
| AReaL does not detect agent workflow | Class lacks `async def run(self, data, **extra_kwargs)` or import path is wrong | Validate import path and method signature with the bundled checker. |
| Inline mode hangs | Sync SDK/network/file calls inside `run()` | Use async SDKs with injected `http_client`, or switch to `mode: subproc`. |
| Subprocess mode fails to pickle | Agent instance holds unpicklable clients/sessions/file handles | Create clients inside `run()`; keep constructor state simple. |
| Rewards not assigned to the right interaction | Dict keys do not match response IDs or latest reward semantics misunderstood | Return a float for the latest response, or use exact captured response IDs. |
| Tool calls not parsed | Wrong `tool_call_parser`, model family, or response format | Set parser matching model output; record unsupported parser/backend combinations. |
| Provider credentials leak risk | Agent reads environment/provider keys without approval | Use approved runtime env vars; never paste secrets into config examples. |

## Safe diagnosis sequence

1. Run `scripts/check_workflow_contract.py` against import paths and a tiny sample JSON.
2. Check only importability/signatures/schema first; do not start trainers or services.
3. If the issue is backend/service runtime, route to the appropriate sibling sub-skill.
4. When reporting, separate validated contracts from unverified live model/provider behavior.
