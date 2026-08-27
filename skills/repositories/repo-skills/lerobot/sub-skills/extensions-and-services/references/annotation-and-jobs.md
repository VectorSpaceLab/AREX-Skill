# Annotation pipeline and Hugging Face Jobs

## Annotation shape

`lerobot-annotate` is backed by `AnnotationPipelineConfig`. The local input may be a dataset `root`, a Hub `repo_id`, or both. `new_repo_id` is an optional separate push destination. `staging_dir` defaults to a hidden staging directory under the local root when a root is used. `seed`, `only_episodes`, `video_backend`, `skip_validation`, and push flags control the pass.

The top-level nested configs are `plan`, `interjections`, `vqa`, `vlm`, `executor`, and `job`. Useful local fields include:

- `plan.enabled`, `frames_per_second`, `max_frames_per_prompt`, `plan_max_steps`, `emit_plan`, `emit_memory`, and task derivation settings;
- `interjections.enabled`, `max_interjections_per_episode`, and `interjection_min_t`;
- `vqa.enabled`, `vqa_emission_hz`, `K`, `question_types`, and `restrict_to_default_camera`;
- `vlm.backend` (`openai` or test `stub`), `model_id`, `api_base`, `api_key`, `auto_serve`, `serve_port`, `serve_command`, `parallel_servers`, `num_gpus`, `client_concurrency`, `serve_ready_timeout_s`, generation limits, `camera_key`, and optional chat-template/reasoning fields;
- `executor.episode_parallelism`;
- `job.target`, `image`, `timeout`, `lerobot_ref`, `detach`, and `tags`.

The VLM config is an endpoint/credential boundary. `openai` uses an OpenAI-compatible API (local vLLM is auto-served only during an explicit annotation run); `stub` is intended for tests. `api_key=EMPTY` is suitable only for an intentionally local unauthenticated server. A local schema pass does not prove that the model is downloaded, the endpoint exists, a server is ready, or the key is accepted.

## Staging and validator invariants

The pipeline has three phases: read episode frames/metadata, run plan/interjection/VQA modules into per-episode JSONL staging, then validate and rewrite language columns. The validator is `StagingValidator` and returns `ValidationReport(errors, warnings, episodes_checked)`; `.ok` is true only when `errors` is empty.

The source language routing contract is:

| style/atom | destination | producer |
| --- | --- | --- |
| `subtask`, `plan`, `memory`, `task_aug` | `language_persistent` | plan |
| `interjection`, speech with `style=null` and a `say` tool call | `language_events` | interjections |
| paired `vqa` user/assistant rows | `language_events` | vqa |

Before parquet rewriting, validation checks:

- every event timestamp equals a source frame timestamp by default (`timestamp_atol=0.0`);
- view-dependent rows have a valid camera field, and optionally that camera is one of the dataset video keys;
- every interjection has a same-time assistant speech atom and a plan refresh;
- persistent plan/memory/subtask relationships are coherent (some memory conditions are warnings);
- VQA assistant `content` parses as JSON and matches one known shape: `bbox` requires `detections`; `keypoint` requires `label`, `point_format`, `point`; `count` requires `label`, `count`; `attribute` requires `label`, `attribute`, `value`; `spatial` requires `subject`, `relation`, `object`;
- no duplicate VQA role at the same timestamp/camera;
- the producer module emits styles into its expected column.

`--skip_validation=true` is a debugging escape hatch, not a publication recommendation. An error should stop the writer and leave the staging evidence available for inspection. Do not repair timestamps by recomputing floating-point time; copy the source timestamp.

## Safe local annotation checks

Use `annotation_config_check.py` with a local JSON/YAML fragment or flags. It validates known keys, scalar ranges, module enablement, VLM endpoint syntax, job target shape, and optional synthetic rows against the same style/camera/timestamp/VQA invariants. It does not read video, rewrite parquet, call OpenAI/vLLM, load a model, access the Hub, or submit a job.

A synthetic pass should include source timestamps such as `[0.0, 0.5]`, paired `interjection` plus speech and plan rows, and a valid VQA pair. A deliberately failing pass should include an off-frame timestamp, orphan interjection, or invalid VQA JSON. Report the exact invariant and stop.

## HF Jobs boundary

For local annotation, `job.target` omitted or `local` keeps work on the current machine. Any other flavor submits to HF Jobs. Remote annotation requires:

1. a Hub `repo_id` accessible to the pod; a local-only `root` is not enough;
2. a valid HF login/token; the submitter sends `HF_TOKEN` as a job secret;
3. CLI flags rather than host-only nested config files; the pod cannot read local config paths;
4. an image/runtime with the pinned LeRobot-compatible dependencies and video decoding support;
5. `push_to_hub=true` plus a destination (`new_repo_id` or source `repo_id`) if output must survive pod teardown.

The submitter ensures the source dataset is reachable, removes client-only job/root/config flags, re-adds the Hub repo id, and forces the pod's job target to local so it does not recursively resubmit. `Ctrl-C` detaches from log following; it does not cancel the remote job. Use the platform's explicit job logs/cancel commands only when the user asks for remote job management.

Training HF Jobs has a similar boundary: it resolves HF credentials, may stage a sanitized train config/model repo, forwards `HF_TOKEN` and optional W&B credentials, ensures the dataset is Hub-reachable, and submits a cloud run. It may push checkpoints. This sub-skill diagnoses config/credential gates only; the training skill owns the actual submission decision.

## Credential stop conditions

If the local dataset is not on the Hub, remote annotation must first arrange a private Hub upload or the user must choose local execution. If `push_to_hub` is false, a remote result is normally discarded when the pod exits (a smoke test may intentionally accept that). If W&B is enabled for remote training and no `WANDB_API_KEY` environment value or netrc credential is available, stop with that requirement; never search for or print secrets. Do not treat `api_key`, `HF_TOKEN`, or W&B keys as ordinary config values to echo in a report.
