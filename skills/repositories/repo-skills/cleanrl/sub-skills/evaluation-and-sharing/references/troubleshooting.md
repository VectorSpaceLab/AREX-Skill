# Troubleshooting Evaluation And Sharing

Use this guide when CleanRL model evaluation, artifact inspection, or Hugging Face sharing fails. Start with local-only checks before attempting downloads or uploads.

## Missing Saved Model

Symptoms:

- `runs/<run_name>/<exp_name>.cleanrl_model` does not exist.
- The run directory contains TensorBoard event files but no model file.
- An upload or eval command cannot find `<exp_name>.cleanrl_model`.

Checks and fixes:

1. Run `python sub-skills/evaluation-and-sharing/scripts/check_cleanrl_artifact.py --runs-dir runs --exp-name <exp-name> --env-id <env-id> --seed <seed>`.
2. Confirm the training command included `--save-model`; without it, CleanRL logs to `runs/<run_name>` but does not save the model artifact.
3. Check whether the run name follows `<env_id>__<exp_name>__<seed>__<timestamp>` and whether the requested seed/env match the actual directory.
4. Re-run training with `--save-model` if the artifact was never created. Add `--upload-model` only when the user explicitly wants Hugging Face sharing.

## Wrong Hugging Face Repository

Symptoms:

- `RepositoryNotFoundError`, 404, or a private-repo permission error while using `cleanrl_utils.enjoy`.
- `enjoy` downloads from `cleanrl/<env_id>-<exp_name>-seed<seed>` but the model was uploaded under another owner.
- A repo exists but does not contain `<exp_name>.cleanrl_model`.

Checks and fixes:

1. Derive the default repository as `<hf_entity>/<env_id>-<exp_name>-seed<seed>`.
2. If the uploaded model belongs to another owner or uses a custom repo name, pass `--hf-repository <owner>/<repo>`.
3. Confirm the file name in the repository is exactly `<exp_name>.cleanrl_model` for `enjoy`.
4. Treat private-repo access as a credential issue; ask before login, token configuration, or retrying network access.

## Network Or Authentication Failure

Symptoms:

- Hugging Face download/upload fails due to missing token, offline runtime, TLS/proxy issues, rate limits, or insufficient permissions.
- `--upload-model` starts creating or updating remote repository contents unexpectedly.

Checks and fixes:

1. Stop and confirm the user wants network access.
2. For local artifacts, bypass `enjoy` and call the matching eval function directly with a local `model_path`.
3. For sharing, explain that `push_to_hub` creates or reuses a repository, deletes prior remote event/video files, writes a model card, and uploads run artifacts.
4. Do not request, print, store, or embed API tokens in skill content or generated commands.

## Env, Script, Or Eval Function Mismatch

Symptoms:

- `KeyError` for `MODELS[exp_name]`.
- Model load errors such as missing keys, unexpected keys, shape mismatches, or Flax deserialization failures.
- Environment construction fails even though the model file exists.

Checks and fixes:

1. Read `references/evaluation-api.md` and choose the eval function that matches `exp_name` and serialization format.
2. Use direct eval modules for DDPG, TD3, PPO continuous-control, or other algorithms not routed through `cleanrl_utils.evals.MODELS`.
3. Confirm `env_id` matches training; CleanRL model classes often infer observation and action dimensions from the constructed environment.
4. Verify optional dependencies for that environment family before assuming the model file is corrupt.
5. If `cleanrl_utils.enjoy` fails with a missing `capture_video` attribute in the source snapshot, call the eval function directly and pass `capture_video=False`.

## Video Capture Failures

Symptoms:

- Errors mention render modes, `RecordVideo`, `moviepy`, `cv2`, ffmpeg, missing display, or empty video folders.
- Evaluation works until video capture starts.

Checks and fixes:

1. Retry evaluation with `capture_video=False` to isolate model correctness from video tooling.
2. For normal Gym/Gymnasium wrappers, expect videos under `videos/<run_name>`.
3. For upload/evaluation flows, expect eval videos under `videos/<run_name>-eval` when capture was enabled.
4. Install only the targeted video/backend dependency required by the selected algorithm and environment; do not install every CleanRL extra by default.

## Optional Dependency Gaps

Symptoms:

- Imports fail for JAX, Flax, EnvPool, MuJoCo, Atari/ALE, Procgen, PettingZoo, OpenCV, or MoviePy.
- Base CleanRL import/help checks pass, but a specific evaluation script fails.

Checks and fixes:

1. Identify the algorithm family from `exp_name` before installing extras.
2. JAX variants require JAX/Flax-compatible runtime packages.
3. Atari variants require Atari environment dependencies and ROM handling appropriate to the user's setup.
4. Continuous-control examples such as HalfCheetah/Hopper require MuJoCo-compatible Gymnasium environments.
5. EnvPool variants require EnvPool and may require OpenCV/MoviePy for video capture.
6. Keep dependency changes scoped to the user's approved environment.
