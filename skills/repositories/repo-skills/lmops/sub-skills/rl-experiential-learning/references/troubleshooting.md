# RL experiential-learning troubleshooting

For shared LMOps install, credential, hardware, and checkout boundaries, also consult the root troubleshooting reference if it is bundled in the same generated skill tree: `../../../references/troubleshooting.md`. This file covers OEL, OPCD, LLM-as-a-Coach, GAD, and OPO-specific failure modes.

## First response: classify the failure

| Symptom | Most likely class | First safe action |
| --- | --- | --- |
| Planner output has placeholders | Missing user decision | Ask for the model, experiment name, checkpoint, data root, or credential intent; do not invent local paths. |
| Command would start Docker/Ray/vLLM/training | Heavy backend | Stop at a command plan and ask the user to run it in an approved target environment. |
| `WANDB_API_KEY`, `HF_TOKEN`, or `OPENAI_API_KEY` missing | Credential | Explain which stage needs which credential; never request or print secret values in skill files. |
| Checkpoint cannot be found or merged | Checkpoint layout | Confirm experiment name, `global_step_<STEP>`, actor/critic directory, and whether `use_bsl=true` should skip merging. |
| System-prompt or experience-list file rejected | Input shape | Run `scripts/check_experience_inputs.py` and repair the prompt/list/data root before planning training. |
| Ray worker hangs or nonzero ranks sleep forever | Cluster launch | Verify Ray setup, rank variables, network reachability, node count, and launch method outside this skill. |
| vLLM out-of-memory | Runtime budget | Reduce prompt length, response length, rollout count, tensor parallel assumptions, or GPU memory utilization; use larger GPUs if needed. |

## Heavy backend boundaries

This sub-skill must not execute these actions:

- Docker or container setup,
- Ray cluster startup or teardown,
- vLLM server/rollout execution,
- VeRL trainer runs,
- checkpoint merging,
- Hugging Face dataset/model downloads,
- W&B login or logging,
- OpenAI-compatible scoring calls,
- IF-Eval or unsafe code-evaluation runs.

Return staged command plans and validation results only. If the user asks you to run the downstream workflow in Creator mode, report the mode mismatch and ask them to switch to Researcher mode.

## Credential surfaces

- **W&B**: OEL/OPCD consolidation, Coach training, and GAD training use W&B project/API-key environment variables. Keep secrets in the target shell or secret manager, not in command text.
- **Hugging Face**: gated models and datasets may require `HF_TOKEN`; cache placement may require `HF_HOME`.
- **OpenAI-compatible APIs**: Coach GPT-4o feedback/scoring and optional GAD scoring require `OPENAI_API_KEY`; `OPENAI_BASE_URL` and `OPENAI_MODEL` are optional endpoint/model controls.
- **Credential diagnosis**: authentication, permission, quota, rate limit, and timeout failures should be reported as target-environment blockers, not as skill-generation failures.

## OEL issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Round two or later cannot resume | `resume_policy_name` is present but checkpoint step is missing or wrong. | Ask for both previous experiment name and checkpoint step, or a direct model path. |
| Experience list contains wrong files | Mixed environment, no-think flag, prompt version, validation sample count, or round. | Rebuild the experience list for the same OEL round and validate it before consolidation. |
| Consolidation fails to find deploy data | Deploy/trajectory collection was skipped or produced output under a different experiment name. | Re-run the deploy planning stage and pass the matching deploy-data directory. |
| Prompt budget exceeds vLLM limits | Experience max length plus game-step prompt budget is too large. | Lower experience length, response length, or max game steps; verify token budget before launch. |
| FrozenLake/Sokoban quality is inconsistent | Thinking/no-thinking flag or environment variant is mismatched. | Align `textgame_no_think`, environment name, and model family across extraction, deploy, consolidation, and eval. |

## OPCD issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Math data files missing | DAPO preparation was not staged or data root differs from the training plan. | Validate with `--profile opcd-math`; stage train/validation/test parquets before launch. |
| Off-policy training cannot find logits/trajectories | Generate-off-policy stage output directory is missing or from another experiment. | Plan generate-off-policy first and pass its exact save directory to the train-off-policy stage. |
| Teacher/student mismatch breaks consolidation | `ref_model_path` model family/tokenizer is incompatible with the student model. | Confirm tokenizer compatibility and model family before using a larger teacher. |
| System-prompt results are unstable | Wrong prompt type, prompt file, KL top-k settings, or checkpoint selection. | Validate the prompt, keep `system_prompt_type` aligned, and average or inspect multiple checkpoints if the user follows the paper recipe. |
| Safety prompt plan omits top-k renormalization | Safety examples may use an extra renormalization flag. | Preserve the safety-specific KL settings when reproducing that variant. |

## LLM-as-a-Coach issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| User provides a short alias to the scorer | Scoring utilities expect the long experiment/checkpoint-directory name. | Map the alias to the long experiment name before planning score commands. |
| `eval_fuzzy` produced responses but no final score | Fuzzy generation and GPT-4o fuzzy scoring are separate stages. | Plan `eval_fuzzy` first, then `eval_gpt4o_fuzzy` with OpenAI-compatible credentials. |
| `eval_endtask` is requested casually | IF-Eval uses unsafe code-evaluation allowance and a heavy vLLM path. | Require explicit sandbox approval and leave execution to the target environment. |
| Multi-dataset EL run fails | Dataset ratios, reward-prompt list, or fixed-teacher flags do not match dataset count. | For `qwen-el-self-iter`, keep WildChat/Tulu dataset fields aligned by position. |
| Checkpoint merge fails during eval | Actor shards are missing or already merged path is empty. | Confirm `EL_CHECKPOINT_ROOT`, long experiment name, and checkpoint step; use `use_bsl=true` only for base-model evaluation. |

## GAD issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Correct script gives unexpected behavior | Wrong VeRL implementation branch. | Check out `seqkd`, `warmup`, `gad`, or `eval` before the matching stage. |
| Adversarial stage cannot start | Warmup checkpoint was not copied/staged into the adversarial experiment namespace. | Stage the warmup checkpoint and provide an explicit resume step. |
| Actor or critic merge fails | Sharded checkpoint files are missing or the actor/critic directory is wrong. | Verify actor and critic checkpoint directories before planning adversarial training. |
| Teacher-data export fails | Dataset access, network, or local parquet destination is unavailable. | Stage teacher-response train/test parquets in an approved data root and validate them. |
| ROUGE-L improves but final quality is poor | ROUGE-L is only a local diagnostic. | Use the intended automatic or human evaluation plan; do not select checkpoints only by ROUGE-L. |

## OPO issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Exact on-policy recipe still has KL regularization | One of the KL/entropy coefficients was not zeroed. | Check every OPO key in `references/opo-config-reference.md`. |
| PPO mini-batch differs from train batch | Run is not exact on-policy. | Set `actor_rollout_ref.actor.ppo_mini_batch_size` equal to `data.train_batch_size`. |
| Baseline is not active | Target checkout lacks the OPO advantage-computation modification. | Confirm the OPO-modified VeRL core algorithms module and selected estimator before launch. |
| User wants OPO inside OEL/OPCD/Coach/GAD | Algorithm recipes conflict. | Treat this as a porting task and make every changed KL, batch, rollout, and advantage setting explicit. |

## Input validation quick commands

```bash
python scripts/check_experience_inputs.py --experience-list <EXPERIENCE_LIST> --min-lines 1 --warn-absolute-lines
python scripts/check_experience_inputs.py --system-prompt-file <SYSTEM_PROMPT_FILE> --prompt-type safety --strict
python scripts/check_experience_inputs.py --data-root <EL_DATA_ROOT> --profile coach
python scripts/check_experience_inputs.py --data-root <DATA_ROOT> --profile opcd-math
python scripts/check_experience_inputs.py --data-root <GAD_DATA_ROOT> --profile gad
```

These commands validate files and shapes only. They do not import LMOps code, load models, start services, or call APIs.
