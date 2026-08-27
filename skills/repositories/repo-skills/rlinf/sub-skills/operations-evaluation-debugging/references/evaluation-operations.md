# Evaluation operations

This reference distills RLinf's embodied evaluation behavior into a planning and inspection workflow. It is for static review, command construction, and post-run analysis; it is not permission to start a long GPU/robot evaluation.

## What RLinf evaluation does

RLinf has a unified embodied evaluation path built around `EmbodiedEvalRunner`:

1. Hydra resolves an evaluation YAML and any command-line overrides.
2. The validated config sets `runner.task_type: embodied_eval` and `runner.only_eval: True`.
3. A cluster object and hybrid component placement create rollout and environment worker groups.
4. The rollout worker sends actions through RLinf channels; the environment worker executes episodes.
5. The runner aggregates metrics from workers, prefixes them with `eval/`, logs them once at step 0, prints a metric table, and closes metric backends.

Evaluation is usually lighter than training because there is no actor optimization loop, but it still needs the correct model checkpoint, simulator assets, GPU/graphics setup, and placement.

## Launcher and config contract

When a user asks for an evaluation plan, identify these fields before suggesting a launch:

- **Benchmark/config identity:** explicit benchmark plus config name, or a config name whose prefix implies a benchmark (`libero`, `robotwin`, `behavior`, `realworld`, `maniskill`, `metaworld`, `calvin`, `robocasa`, `robocasa365`, `roboverse`, `polaris`).
- **Model source:** `rollout.model.model_path` for base/deploy model directories; some models additionally require `lora_path`, tokenizer paths, config paths, or norm-stat assets.
- **RL checkpoint source:** `runner.ckpt_path` when evaluating a saved `.pt`/converted checkpoint instead of only base model weights.
- **Coverage settings:** `env.eval.total_num_envs`, `rollout_epoch`, `max_episode_steps`, `max_steps_per_rollout_epoch`, `auto_reset`, `ignore_terminations`, `use_fixed_reset_state_ids`, and `use_ordered_reset_state_ids`.
- **Placement:** `cluster.component_placement` should place `env` and `rollout` on the intended accelerators; route low-level cluster/Ray syntax to `setup-and-cluster`.
- **Output:** `runner.logger.log_path` determines the evaluation log directory; videos use `<log_path>/video/eval/` when enabled.

The launcher accepts either an explicit benchmark/config pair or an inferable config name plus Hydra overrides. For planning, use this abstract signature rather than hard-coding local paths:

```text
<RLinf evaluation launcher> <benchmark> <config_name> [hydra_overrides...]
<RLinf evaluation launcher> <config_name> [hydra_overrides...]
```

For ManiSkill OOD batch mode, it accepts a special batch selector and requires environment variables that name the eval run, checkpoint path, env count, and rollout epochs. Treat that as a multi-run batch job, not a quick smoke test.

## Output inspection checklist

Use the bundled [`../scripts/check_run_artifacts.py`](../scripts/check_run_artifacts.py) against a candidate output directory before diagnosing a failed eval by memory:

- Log candidates: `eval_embodiment.log`, `run_ppo.log`, `run_embodiment.log`, `metrics.log`, and per-worker logs when enabled.
- Metric fragments: `eval/success_once`, `eval/return`, `num_trajectories`, and the printed `Metric Table`.
- Video evidence: `<log_path>/video/eval/` when `env.eval.video_cfg.save_video: True`.
- Config capture: TensorBoard logger writes a resolved `config.yaml` under its backend directory; other launchers may print resolved config JSON to the main log.
- Failure fragments: root-cause messages normally appear before final `RuntimeError`, `Gloo timeout`, or Ray task-failure wrappers.

A healthy eval run should have at least one main log, a resolved/printed config, `eval/*` metrics, and either a user-expected absence of videos or a non-empty eval-video directory.

## Benchmark prerequisites and gotchas

| Benchmark family | Key prerequisites | Common evaluation-specific checks |
| --- | --- | --- |
| LIBERO | MuJoCo/robosuite stack; model path; `ROBOT_PLATFORM` convention for LIBERO. | Suites are Spatial/Object/Goal/Long. Full coverage is about 500 trajectories per suite. Ensure `max_steps_per_rollout_epoch` is divisible by `rollout.model.num_action_chunks` and large enough when `auto_reset` is used. |
| RoboTwin | RLinf-compatible RoboTwin assets; `ROBOTWIN_PATH`; `ROBOT_PLATFORM=ALOHA`; `env.eval.assets_path`. | Seed files cover a fixed set of task success seeds. OpenVLA-OFT/OpenPI/LingBotVLA use different embodiments, cameras, domain-randomization expectations, action chunks, and extra tokenizer/config fields. |
| BEHAVIOR | Isaac Sim/OmniGibson installation, large BEHAVIOR assets, license/key material, valid `ISAAC_PATH` and OmniGibson data paths. | Headless operation uses OmniGibson headless flags. Confirm `rollout.model.model_path` and any converted OpenPI/PyTorch checkpoints before launch. |
| ManiSkill OOD | ManiSkill assets, GPU simulator support for `sim_backend: gpu`, base OpenVLA-OFT model, usually `rollout.model.lora_path`. | OOD protocol spans vision, semantic, and execution scenes. Batch mode requires run name, checkpoint path, env count, and rollout epochs. Single-scene overrides use `env.eval.init_params.id` and `obj_set`. |
| RealWorld | Physical robot/control-node readiness, robot IP/topology, deploy model path, `runner.ckpt_path`, calibrated cameras/grippers, operator approval. | Never run from this skill alone. Verify safety gates, operator presence, e-stop, and exact control node role before any live motion. |
| PolaRiS | Dataset root in `POLARIS_DATA_PATH`, local model checkpoint. | Dataset path errors look like missing asset/config failures; confirm dataset root before blaming policy code. |
| Standalone framework evals | Framework-specific environment and model assumptions. | These scripts provide finer-grained per-task metrics but are often slow and single-threaded; use them for deep diagnosis, not as the first smoke check. |

## Config coverage planning

Use [`../scripts/summarize_config_matrix.py`](../scripts/summarize_config_matrix.py) on copied or live YAML directories supplied by the user. It reports counts for task types, env/model types, algorithms, training backends, rollout backends, and likely benchmark families. Use the matrix to answer:

- Which benchmark families have eval YAML coverage?
- Are the user's env/model/backend combinations represented by an existing config?
- Does a requested eval require an RL checkpoint (`runner.ckpt_path`) or only a base model path?
- Which configs are likely hardware-heavy and should not be used as smoke tests?

## Evaluation triage flow

1. **Clarify scope:** evaluation plan, post-run diagnosis, benchmark coverage audit, or real execution.
2. **Classify benchmark and config:** use the config matrix script; verify required model/assets paths are explicit placeholders or user-provided values.
3. **Preflight coverage settings:** ensure `is_eval=True`, `only_eval=True`, sane env count, action-chunk divisibility, and coverage strategy (`auto_reset` vs high parallelism).
4. **Preflight placement:** ensure `env` and `rollout` placement matches available accelerators; route cluster startup details to `setup-and-cluster`.
5. **Inspect output:** run artifact checker, read earliest root-cause log fragments, and compare expected video/log/checkpoint layout.
6. **Escalate carefully:** if failure is assets/credentials/hardware, stop and ask for missing prerequisites; if it is config mismatch, propose minimal Hydra overrides; if it is a model/load failure, check checkpoint format and model-family expectations from [`metrics-checkpoints.md`](metrics-checkpoints.md) and [`data-checkpoint-utilities.md`](data-checkpoint-utilities.md).
