# Troubleshooting

This is the cross-cutting failure guide for `lmms-eval`. Use the nearest subskill reference for workflow-specific detail.

## Install and import problems

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `pip check` fails | Conflicting or missing dependencies | Re-run the targeted install, not a broad reinstall |
| `import lmms_eval.mcp.server` fails with `mcp.server.fastmcp` missing | Incompatible MCP package version | Reinstall the MCP extra with a FastMCP-capable `mcp` release |
| `torch.cuda.is_available() == False` on a GPU host | CPU-only wheel, driver/runtime mismatch, or device passthrough issue | Use a CUDA wheel compatible with the host and re-check device visibility |
| `sentencepiece`, `protobuf`, `httpx`, or `pycocoevalcap` errors | Stale or incompatible dependency versions | Check the install matrix and the task/model that actually needs the package |

## CLI / eval problems

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Unknown task/model name | Registry entry missing or typo | Run `lmms-eval tasks list` / `lmms-eval models --aliases` |
| `--max_tokens` vs `max_new_tokens` confusion | Legacy flag naming | Prefer the task/model docs and the current CLI help |
| Stale outputs or surprising reruns | Cache key changed, cache disabled, or request is non-deterministic | Inspect `--use_cache`, `--cache_requests`, `temperature`, and `do_sample` |
| `<think>` tokens leak into scoring | Reasoning stripping disabled or overridden | Check `--reasoning_tags` and task-level `reasoning_tags` |
| `Unknown keys in config file` | YAML typo or stale config field | Compare the YAML with the current task guide |

## Model backend problems

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `is_simple` validation error | Backend registered under the wrong model type | Fix the registry entry and the class flag together |
| Media extraction fails | `doc_to_messages` / `doc_to_visual` returns the wrong shape | Compare to the task/model reference and the tuple-shape smoke |
| Optional backend import failure | Missing `vllm`, `sglang`, `decord`, `torchcodec`, `qwen-vl-utils`, etc. | Install only the backend the selected workflow truly needs |
| Video decode backend mismatch | Wrong `LMMS_VIDEO_DECODE_BACKEND` or missing video runtime | Use the video decode helper script and the backend docs |

## Task authoring problems

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| YAML parse error | `include`, `!function`, or indentation issue | Validate the YAML and the include chain |
| Wrong request tuple shape | Model and task contract disagree | Inspect the current request-shape table in `task-authoring.md` |
| Metric key mismatch | `process_results` and `metric_list` disagree | Align the names before changing anything else |
| Prompt drift | YAML or formatter changed unexpectedly | Compare against the prompt-stability tests |
| Audio/video/image dataset failure | Missing media cache or external loader setting | Check the dataset kwargs and media resolution settings |

## Service problems

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Server will not start | Port conflict or missing server dependency | Try another port and verify the service extras |
| Queued jobs never finish | Child process hung or log capture issue | Inspect the scheduler and use the job-scheduler smoke helper |
| MCP command fails | Package version mismatch or missing dependency | Reinstall the MCP extra and re-check the import |
| UI build fails | Missing Node.js 18+ or frontend dependencies | Install the frontend toolchain and rebuild |

## A few repo-specific reminders

- `lmms-eval serve` and `lmms-eval mcp` are trusted-environment tools; do not treat them as safe internet-facing services.
- Some benchmark or API workflows are intentionally excluded from smoke checks because they need credentials, model downloads, or large GPU runs.
- If a failure looks like a stale environment rather than a code bug, fix the environment first and rerun the smallest smoke.
- If a required backend cannot be prepared, the skill should stay honest about that gap rather than silently falling back to CPU.
