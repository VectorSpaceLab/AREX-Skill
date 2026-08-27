---
name: integrations-hub-tracking
description: "Plan and debug RL Baselines3 Zoo Hugging Face Hub, Weights &
  Biases, and video-recording workflows without hidden side effects."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# integrations-hub-tracking

Use this sub-skill when the task involves RL Baselines3 Zoo integrations around Hugging Face Hub model download/upload/model cards, Weights & Biases tracking flags, or video recording of trained agents/training checkpoints.

## Start here

1. Decide whether the requested action is only planning/debugging or an approved live side effect:
   - Hub download/upload and W&B tracking use external services and may require credentials.
   - The bundled helper performs no network calls, reads no credentials, loads no model weights, and does not train.
2. For Hub and W&B command semantics, read [references/hub-and-tracking.md](references/hub-and-tracking.md).
3. For `record_video` and `record_training`, read [references/video-recording.md](references/video-recording.md).
4. For common failures, read [references/troubleshooting.md](references/troubleshooting.md).
5. Before planning a Hub transfer, run [scripts/hub_model_layout_checker.py](scripts/hub_model_layout_checker.py) to inspect local layout and destination collisions without contacting the Hub.

## Operating checklist

- Prefer installed-package commands such as `python -m rl_zoo3.load_from_hub`, `python -m rl_zoo3.push_to_hub`, `python -m rl_zoo3.record_video`, `python -m rl_zoo3.record_training`, and `python -m rl_zoo3.train`.
- Use the `rl_zoo3 ...` console form only when the runtime environment imports the console router successfully; if optional plotting imports break the console, switch to module commands or use `../../references/install-and-environment.md`.
- Treat `--organization` / `-orga`, `--repo-name` / `-name`, `--force`, and model selectors as explicit user-facing decisions; do not invent destinations for destructive overwrites.
- For upload planning, inspect the local log folder for the selected model zip plus saved config/argument files.
- For download planning, compute the intended local destination and check whether it already exists before suggesting `--force`.
- For W&B, include `--track` only when the caller accepts service logging and has arranged `wandb` installation/authentication.
- For video, check display/rendering and `ffmpeg`/video dependency boundaries before using `record_training` or GIF conversion.

## Boundaries and routes

- Local no-render evaluation/enjoy, model selection, and artifact inspection: route to `../evaluation-and-artifacts/SKILL.md`.
- Producing trained models or checkpoints before upload/video: route to `../training-cli/SKILL.md`.
- Plot files, benchmark tables, and curve interpretation: route to `../plotting-benchmarking/SKILL.md`.
- Config grammar, wrappers, callbacks, or custom env import strings: route to `../config-hyperparams/SKILL.md` and `../custom-components/SKILL.md` as needed.
- Do not use batch migration helpers for normal operation; repeated Hub uploads require explicit external-service approval and credentials.

## Minimal no-side-effect preflight

```bash
python scripts/hub_model_layout_checker.py \
  --mode push --folder logs --algo ppo --env CartPole-v1 --exp-id 0 \
  --organization sb3 --repo-name ppo-CartPole-v1
```

If this reports missing local model/config artifacts, create or locate those artifacts through `../training-cli/SKILL.md` or inspect them through `../evaluation-and-artifacts/SKILL.md`; do not compensate by launching a live Hub command blindly.
