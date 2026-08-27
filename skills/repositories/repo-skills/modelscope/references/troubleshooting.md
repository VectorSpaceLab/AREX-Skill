# ModelScope Cross-Cutting Troubleshooting

## Purpose

Use this reference when the failure spans installation, package import, CLI dispatch, optional dependencies, backend selection, Hub/cache policy, or trust boundaries. Then route to the nearest sub-skill for workflow-specific recovery.

## Install or import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'modelscope'` | Package is not installed in the active Python. | Install `modelscope` in the environment that will run the workflow; then run `python scripts/check_modelscope_environment.py --summary`. |
| `No module named 'modelscope_hub'` when using CLI or Hub shims | Base Hub dependency is absent or broken. | Install/repair `modelscope-hub>=0.2.0` or reinstall `modelscope`; verify `modelscope --help`. |
| Import of `modelscope.pipelines` fails on `torch`, `transformers`, `PIL`, `cv2`, `datasets`, etc. | Optional dependency or extra is missing for the selected surface. | Install the smallest extra that owns the workflow (`framework`, `datasets`, `server`, domain extra) rather than `all`. |
| `pip check` reports version conflicts after broad extras | Optional groups pulled conflicting compiled/domain packages. | Create a fresh private environment and reinstall only required extras. Do not mutate a user-owned environment without approval. |

## CLI dispatch failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `modelscope: command not found` but Python import works | Console scripts are not on `PATH` for the active environment. | Use the environment's script path or `python -m modelscope.cli.cli --help` when supported; repair the environment if packaging is broken. |
| Top-level command list differs from this skill | CLI commands are registered by installed `modelscope_hub` and plugins. | Run `modelscope --help` and `modelscope <command> --help` in the target environment before execution. |
| Upload/login commands fail with auth errors | Missing, expired, or wrong-scope token; endpoint mismatch. | Use the Hub/CLI sub-skill. Prefer env vars or Python `token=` over literal shell tokens. Verify endpoint and repo type. |

## Hub, cache, and offline failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Model appears downloaded but pipeline cannot find it | CLI/Python/server use different cache roots or `local_dir` vs `cache_dir` was confused. | Pick one cache root (`MODELSCOPE_CACHE` or explicit `cache_dir`) or pass a concrete local model directory to `pipeline`. |
| `local_files_only=True` fails | Cache does not contain the requested repo/revision/file. | First populate the exact repo/revision online, or pass a known local directory. |
| Include/exclude filters seem ignored | Explicit file paths may override pattern filtering, or shell expanded globs before CLI saw them. | Quote globs and avoid mixing explicit files with patterns unless help documents the behavior. |
| Legacy cache not reused after upgrade | Current `modelscope_hub` may use a new cache layout; legacy reuse may depend on compatibility probes. | Use the Hub/CLI troubleshooting reference to inspect cache roots and avoid re-downloading large models unnecessarily. |

## Pipeline and backend failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Pipeline tries to use GPU on a CPU-only host | `pipeline(...)` defaults `device` to GPU when omitted. | Pass `device='cpu'` for CPU workflows. |
| `RuntimeError` mentions plugins, `allow_remote`, or `trust_remote_code` | Model repo declares remote code/plugins. | Review trust boundary; pass `trust_remote_code=True` only when the source is trusted. |
| Registry `KeyError` for pipeline/model/preprocessor type | Custom module not imported, wrong task group, config `type` mismatch, or missing optional package prevented lazy import. | Use the pipeline and customization sub-skills. Verify task, registry group, module name, import side effects, and optional extras. |
| CUDA unavailable or `torch.cuda.is_available()` is false | CPU torch build, driver/runtime mismatch, no GPU passthrough, or missing backend package. | Install a matching backend variant only when the workflow requires it; otherwise run CPU. Do not claim GPU verification from CPU import. |

## Dataset and config failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Unsupported format` from file IO | File extension is not JSON/YAML/YML for `modelscope.fileio`. | Convert recipe/config to supported format or use normal Python file handling. |
| `.py` config refused | Python config executes code and needs explicit trust. | Prefer JSON/YAML; pass `trust_remote_code=True` only for reviewed sources. |
| Dataset recipe fails before training | Missing local paths, remote URI used in offline context, bad split/column mapping, or wrong `target`. | Run `sub-skills/datasets-config/scripts/validate_dataset_recipe.py` on the recipe. |

## Training, serving, export, and destructive tools

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Training or evaluation launches unexpectedly during a check | `trainer.train()`, `trainer.evaluate()`, or `modelscope.tools.train/eval` are real jobs. | Use `training-and-evaluation/scripts/build_training_args_preview.py` for safe planning first. |
| Server starts but hangs/downloading/uses GPU | `modelscope server` loads the target model and may download/cache it. | Pre-download or provide local model directory, choose port/host, verify extras and backend resources. |
| Export fails on missing ONNX/TF/Torch libraries | Exporter is task/model/back-end specific. | Install only required export extra and verify with a tiny/local model when possible. |
| Checkpoint conversion overwrote files | Repository utility is intentionally destructive. | Always run `serving-export-and-tools/scripts/checkpoint_conversion_plan.py` first and operate on a backed-up copy. |

## When to stop and ask

Ask the user before:

- Saving tokens, logging in, uploading/deleting remote Hub content, or clearing caches.
- Installing broad extras or mutating an existing user-owned environment.
- Enabling `trust_remote_code=True` for unreviewed repositories.
- Running real model downloads, training, server launches, export, benchmark, or destructive checkpoint utilities.
- Claiming GPU/vLLM/domain execution without actual target-environment verification.
