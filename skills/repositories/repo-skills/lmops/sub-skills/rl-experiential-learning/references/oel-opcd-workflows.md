# OEL and OPCD workflows

This reference covers safe planning for Online Experiential Learning (OEL) and On-Policy Context Distillation (OPCD). Both families are VeRL/Ray/vLLM workflows: they are not cheap smoke tests, and this skill only builds staged command plans.

Use the bundled planner before presenting commands. Source-script labels name upstream LMOps scripts for orientation only; do not run those labels directly from this generated skill. Materialize checkout-specific commands through `scripts/verl_experiment_planner.py` after the user provides an execution checkout and environment.


```bash
python scripts/verl_experiment_planner.py --family oel --track textgame --stage round --model <MODEL_OR_ID> --exp-name <EXP_NAME> --round 1 --textgame-name Sokoban-v0 --nodes 1 --gpus-per-node 8 --credentials wandb,hf
python scripts/verl_experiment_planner.py --family opcd --track math --stage on-policy --model <MODEL_OR_ID> --exp-name <EXP_NAME> --experience-path <BEST_EXP_PATH> --nodes 2 --gpus-per-node 8 --credentials wandb,hf
```

The planner prints command skeletons only. It does not start Docker, Ray, vLLM, training, evaluation, model merging, external API calls, or data downloads.

## Shared environment assumptions

- Prepare the target checkout with the correct OEL or OPCD environment before execution. The B200 setup path differs from the A100/H100/H200 setup path.
- Ray must be running before trainer commands. Source scripts are rank-aware: rank zero launches the trainer while nonzero ranks idle.
- vLLM rollout is the default rollout engine. Plan prompt length, response length, rollout count, tensor parallel size, GPU memory utilization, and node/GPU counts together.
- W&B is expected for consolidation/training logs. Hugging Face credentials may be needed for gated models or datasets.
- Treat all data files, checkpoint roots, deployment output roots, and result roots as user-provided placeholders. Do not assume a machine-local default root.
- Validate user-provided experience lists and prompt/data files with `scripts/check_experience_inputs.py` before launch.

## OEL round loop

OEL repeats a four-stage text-game round loop. The common environments are `Sokoban-v0` and `FrozenLake-v0-raw`; use `textgame_no_think=true` for non-thinking instruction checkpoints and `false` for thinking checkpoints.

### 1. Experiential-knowledge extraction

Conceptual command labels: `textgame_extract_inturn` for a checkpoint range and `textgame_extract` for one checkpoint/seed.

The in-turn extraction record uses these comma-separated fields:

1. extraction experiment name,
2. checkpoint start,
3. checkpoint end,
4. checkpoint step,
5. resume policy name or initial model,
6. resume policy checkpoint,
7. prompt version,
8. validation sample limit,
9. whether prior experience is available in context,
10. experiential-knowledge max response length,
11. text-game environment name,
12. text-game response length,
13. text-game max steps,
14. no-think flag,
15. OEL round number,
16. optional experiential extractor model.

Extraction computes a prompt budget from game steps and experiential-knowledge length. If prior experience is used in context, the budget must include both the current game prompt and previous experience.

Skeleton:

```bash
source-script-label:textgame_extract_inturn.sh "<EXTRACT_EXP>,<CKPT_START>,<CKPT_END>,<CKPT_STEP>,<MODEL_OR_PREV_EXP>,<PREV_CKPT>,v4,<VAL_LIMIT>,true,<EXP_MAX_LEN>,Sokoban-v0,<TEXTGAME_RESPONSE_LEN>,5,true,<ROUND>,<EXP_MODEL>"
```

### 2. Experience-list construction

Conceptual command label: `make_exp_list`. It consumes six comma-separated fields: extraction experiment name, checkpoint start, checkpoint end, checkpoint step, validation sample limit, and selected validation sample count. The resulting `experience_list.txt` lists one selected experience file per checkpoint.

Validate before consolidation:

```bash
python scripts/check_experience_inputs.py --experience-list <EXPERIENCE_LIST> --min-lines 1 --warn-absolute-lines
```

### 3. Deploy / trajectory collection

Conceptual command label: `textgame_generate_deploy`. Use this after extraction to collect deploy data for partial rollouts. Key fields are model or resume policy checkpoint, deploy experiment name, node count, OEL round, experience max length, text-game name, response length, game steps, no-think flag, and total training steps. This stage is inference/collection, but it still requires the Ray/vLLM GPU environment.

Skeleton:

```bash
source-script-label:textgame_generate_deploy.sh --model <MODEL_OR_ID> --exp_name <DEPLOY_EXP> --nnodes <NODES> --oel_round <ROUND> --experience_max_length <EXP_MAX_LEN> --textgame_name Sokoban-v0 --max_response_length <RESP_LEN> --textgame_max_steps 5 --textgame_no_think true --total_training_steps <STEPS>
```

For round two or later, plan `resume_policy_name` plus `resume_policy_ckpt`; without a checkpoint step the resume target is ambiguous unless the user supplies a direct model path.

### 4. Consolidation and checkpoint evaluation

Conceptual command labels: `textgame_consolidate`, `textgame_eval_inturn`, and `textgame_eval`.

Consolidation trains the policy from the OEL experience list plus deploy data. Required checks:

- model or resume policy checkpoint,
- consolidation experiment name,
- OEL round,
- deploy-data directory from the same round,
- experience-list path from the matching environment/prompt/no-think setting,
- KL type (`full` in source examples), KL top-k (commonly `256`), optional top-k renormalization, actor learning rate, save frequency, and total steps.

Skeleton:

```bash
source-script-label:textgame_consolidate.sh --model <MODEL_OR_ID> --exp_name <CONSOLIDATE_EXP> --nnodes <NODES> --oel_round <ROUND> --kl_loss_type full --kl_topk 256 --actor_lr <LR> --experience_max_length <EXP_MAX_LEN> --textgame_name Sokoban-v0 --max_response_length <RESP_LEN> --textgame_max_steps 5 --textgame_no_think true --deploy_save_dir <DEPLOY_DATA_DIR> --exp_path <EXPERIENCE_LIST> --total_training_steps <STEPS> --save_freq <SAVE_FREQ>
```

Evaluation reads a checkpoint step or range. `use_bsl=true` means evaluate the supplied model directly rather than merging an actor checkpoint.

## OPCD data preparation

OPCD source evidence includes a data-preparation helper that obtains DAPO math data and system-prompt datasets, then writes parquet files for these logical names:

- `dapo_train.parquet`, `dapo_validation.parquet`, `dapo_test.parquet`,
- `sys_medmcqa_train.parquet`, `sys_medmcqa_test.parquet`,
- `sys_safety_train.parquet`, `sys_safety_test.parquet`.

Treat this as network/data acquisition and do not run it during planning. After a user stages the data, validate with:

```bash
python scripts/check_experience_inputs.py --data-root <DATA_ROOT> --profile opcd-math
python scripts/check_experience_inputs.py --data-root <DATA_ROOT> --profile opcd-sys-safety
```

## OPCD math track

The math track performs experiential knowledge extraction over DAPO math data, then uses the best validation experience for on-policy consolidation or an off-policy baseline.

### On-policy

1. Extract with `math_extract_inturn` or `math_extract`.
2. Pick the best experience path by validation accuracy.
3. Consolidate with `math_consolidate`.
4. Evaluate with `math_eval_inturn` or `math_eval`.

Important knobs: student/current model, optional `ref_model_path` for larger-teacher-to-smaller-student distillation, experience path, nodes, rollout count, KL loss type/top-k, actor learning rate, and response length. Source examples use `kl_loss_type=full`, `kl_topk=256`, and a long math response budget.

Skeleton:

```bash
source-script-label:math_consolidate.sh --model <STUDENT_MODEL> --ref_model_path <TEACHER_OR_REF_MODEL> --exp_name <MATH_EXP> --nnodes <NODES> --rollout_n 1 --kl_loss_type full --kl_topk 256 --actor_lr 5e-6 --max_response_length <MATH_RESPONSE_LEN> --exp_path <BEST_EXP_PATH>
```

### Off-policy baseline

The off-policy baseline has two stages:

1. `math_generate_offp`: teacher with experience in context generates trajectories/logits.
2. `math_train_offp`: student consumes the off-policy save directory.

Skeleton:

```bash
source-script-label:math_generate_offp.sh --model <TEACHER_MODEL> --exp_name <OFFP_DATA_EXP> --nnodes <NODES> --rollout_n 1 --kl_loss_type full --kl_topk 256 --max_response_length <MATH_RESPONSE_LEN> --exp_path <BEST_EXP_PATH>
source-script-label:math_train_offp.sh --model <STUDENT_MODEL> --ref_model_path <TEACHER_OR_REF_MODEL> --exp_name <OFFP_TRAIN_EXP> --nnodes <NODES> --rollout_n 1 --kl_loss_type full --kl_topk 256 --actor_lr 5e-6 --off_policy_save_dir <OFF_POLICY_DATA_DIR> --max_response_length <MATH_RESPONSE_LEN> --exp_path <BEST_EXP_PATH>
```

## OPCD text-game track

Text-game OPCD mirrors the math track but adds text-game fields. It does not include the OEL deploy-data round stage.

- Extract with `textgame_extract_inturn` or `textgame_extract`.
- Consolidate on-policy with `textgame_consolidate`.
- Generate and train off-policy with `textgame_generate_offp` then `textgame_train_offp`.
- Evaluate with `textgame_eval_inturn` or `textgame_eval`.

Key fields: `textgame_name`, `textgame_max_steps`, `textgame_no_think`, `experience_max_length`, max response length, KL settings, actor learning rate, and experience path. Keep the experience list/environment/no-think setting matched; do not reuse Sokoban experiences for FrozenLake or thinking-model experiences for no-think runs.

## OPCD system-prompt track

System-prompt distillation handles medical and safety prompt types. Source prompt types are `medmcqa` and `safety`; custom prompts must declare the intended type and be reviewed by the user.

### On-policy

Conceptual command label: `sys_consolidate`. Important fields:

- model and optional reference model,
- experiment name,
- prompt file as the experience path,
- system prompt type,
- experience max length,
- rollout count,
- KL loss type/top-k settings,
- actor learning rate,
- max response length,
- total training steps and save frequency.

Safety examples may enable top-k renormalization; preserve that flag when reproducing a safety-plan variant.

Skeleton:

```bash
source-script-label:sys_consolidate.sh --model <MODEL_OR_ID> --ref_model_path <REF_MODEL_OR_ID> --exp_name <SYS_EXP> --nnodes 1 --rollout_n 1 --kl_loss_type full --kl_topk 256 --actor_lr 5e-6 --max_response_length 512 --experience_max_length 4096 --system_prompt_type safety --exp_path <SYSTEM_PROMPT_FILE> --total_training_steps 50 --save_freq 2
```

### Off-policy baseline

Generate off-policy data from the prompt, then train from that saved data:

```bash
source-script-label:sys_generate_offp.sh --model <TEACHER_MODEL> --ref_model_path <REF_MODEL_OR_ID> --exp_name <SYS_OFFP_DATA_EXP> --nnodes 1 --rollout_n 1 --kl_loss_type full --kl_topk 256 --actor_lr 5e-6 --max_response_length 512 --experience_max_length 4096 --system_prompt_type safety --exp_path <SYSTEM_PROMPT_FILE>
source-script-label:sys_train_offp.sh --model <STUDENT_MODEL> --ref_model_path <REF_MODEL_OR_ID> --exp_name <SYS_OFFP_TRAIN_EXP> --nnodes 1 --rollout_n 1 --kl_loss_type full --kl_topk 256 --actor_lr 5e-6 --max_response_length 512 --experience_max_length 4096 --system_prompt_type safety --exp_path <SYSTEM_PROMPT_FILE> --off_policy_save_dir <OFF_POLICY_DATA_DIR> --total_training_steps 50 --save_freq 2
```

Before using a system prompt:

```bash
python scripts/check_experience_inputs.py --system-prompt-file <SYSTEM_PROMPT_FILE> --prompt-type safety --strict
```

## IF-Eval follow-up

OEL and OPCD READMEs include IF-Eval as an out-of-distribution evaluation. It requires lm-evaluation-harness, vLLM model serving/inference support, Hugging Face access for the model if gated, and an explicit unsafe-code-evaluation allowance. Only plan IF-Eval in an approved sandbox, and never run it as part of this sub-skill.

## Handoff checks

- Confirm family (`oel` or `opcd`), track, stage, model roles, and checkpoint range.
- Confirm W&B/HF credential intent without embedding secret values.
- Confirm node/GPU shape and correct B200 versus A100/H100/H200 environment setup.
- Validate experience lists, prompt files, and data-root expected files with the bundled checker.
- State that Docker/Ray/vLLM/training/eval execution remains unverified until the user runs the planned commands on the target host.
