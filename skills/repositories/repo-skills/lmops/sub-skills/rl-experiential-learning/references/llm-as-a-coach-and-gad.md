# LLM-as-a-Coach and GAD workflows

This reference covers two experiential-learning families that share VeRL, Ray, vLLM, large checkpoint, and credential constraints:

- **LLM-as-a-Coach** for non-verifiable tasks, with EL and RL training presets, held-out WildChat evaluation, fuzzy benchmark generation, IF-Eval, and GPT-4o/OpenAI-compatible scoring.
- **GAD** for black-box on-policy distillation, including SeqKD baseline, warmup, adversarial training, generation/evaluation, branch switching, teacher-data preparation, and checkpoint conversion.

Use the bundled planner first:

```bash
python scripts/verl_experiment_planner.py --family coach --stage train --alias qwen-el-self --model <MODEL_OR_ID> --exp-name wildchat-el-q3-8b-r8b --nodes 4 --gpus-per-node 8 --credentials wandb,hf
python scripts/verl_experiment_planner.py --family gad --stage warmup --model <MODEL_OR_ID> --reward-model <REWARD_MODEL_OR_ID> --exp-name <WARMUP_EXP> --nodes 1 --gpus-per-node 8 --credentials wandb,hf
```

The planner emits command skeletons only. It does not run Docker, Ray, vLLM, training, evaluation, scoring, branch checkout, or checkpoint merging.

## LLM-as-a-Coach operating model

LLM-as-a-Coach turns a judge into a coach: feedback is converted into textual experiential knowledge, a teacher conditions on that knowledge, and the policy internalizes it via on-policy context distillation. The source dispatcher concept supports `list`, `train`, `eval`, `eval_fuzzy`, and `eval_endtask`; GPT-4o scoring is performed by separate evaluator scripts after generation.

### Credential and root surfaces

Resolve these before planning:

- `WANDB_PROJECT` and `WANDB_API_KEY` for training logs.
- `HF_TOKEN` and `HF_HOME` when model or dataset access is gated or cache placement matters.
- `OPENAI_API_KEY` for GPT-4o coach, reward, or scoring calls.
- `OPENAI_BASE_URL` for an OpenAI-compatible endpoint when not using the default endpoint.
- `OPENAI_MODEL`, which defaults to `gpt-4o` in the scoring utilities if the user does not override it.
- `EL_DATA_ROOT`, `EL_CHECKPOINT_ROOT`, and `EL_RESULT_ROOT` for local data, checkpoints, and results. Ask the user to provide safe target roots instead of relying on machine-local defaults.

Expected Coach data layout under `EL_DATA_ROOT`:

```text
wildchat-if_rubric-4o_train.parquet
wildchat-if_rubric-4o_val.parquet
tulu-3-sft-mixture-filtered.parquet
alpacaeval2/alpaca_eval_gpt4_baseline.json
wildbench/v2.json
arena_hard_v2/prompts.json
creativewritingv3/creative_writing_prompts_v3.json
```

Validate staged data with:

```bash
python scripts/check_experience_inputs.py --data-root <EL_DATA_ROOT> --profile coach
```

### Preset aliases

The source usage dispatcher maps short aliases to long experiment/checkpoint-directory names. Use the short alias for dispatcher-style train/eval planning and the long name for scoring and result-root checks.

| Short alias | Mode | Feedback/reward source | Long experiment name |
| --- | --- | --- | --- |
| `qwen-el-self` | EL | policy-family model | `wildchat-el-q3-8b-r8b` |
| `qwen-el-self-iter` | EL | policy-family model with iterative teacher and WildChat/Tulu mixture | `wildchat-el-q3-8b-r8b-itert30-mopd025-fixt` |
| `qwen-el-gpt4o` | EL | GPT-4o/OpenAI-compatible coach | `wildchat-el-q3-8b-rgpt4o` |
| `olmo-el-self` | EL | policy-family model | `wildchat-el-om3-7b-r7b` |
| `olmo-el-gpt4o` | EL | GPT-4o/OpenAI-compatible coach | `wildchat-el-om3-7b-rgpt4o` |
| `qwen-rl-self` | RL | policy-family reward model | `wildchat-rl-q3-8b-r8b` |
| `qwen-rl-gpt4o` | RL | GPT-4o/OpenAI-compatible reward model | `wildchat-rl-q3-8b-rgpt4o` |
| `olmo-rl-self` | RL | policy-family reward model | `wildchat-rl-om3-7b-r7b` |
| `olmo-rl-gpt4o` | RL | GPT-4o/OpenAI-compatible reward model | `wildchat-rl-om3-7b-rgpt4o` |

`qwen` aliases expect a Qwen3-8B policy; `olmo` aliases expect an OLMo-3-7B-Instruct policy. Keep model identifiers user-supplied.

### Train stage

EL aliases route to an EL trainer with these important knobs:

- `trainer.stage=consolidate`, `trainer.use_exp_model=true`, KL loss enabled,
- `rm_prompt_version` (source presets use a v2 rubric prompt for training),
- rollout count, batch size, actor learning rate, prompt/response lengths, GPU memory utilization,
- optional iterative teacher steps for `qwen-el-self-iter`,
- optional multi-dataset fields: dataset list, dataset ratios, per-dataset reward prompts, and fixed-teacher flags,
- optional log-prob/TIS controls,
- checkpoint save contents and automatic resume mode.

RL aliases route to an RL trainer with these important differences:

- `trainer.stage=rl`, KL loss disabled, no-think enabled,
- reward/feedback model through the experiential model path,
- optional log-prob/TIS controls,
- automatic resume defaults to enabled in the source script.

Skeletons:

```bash
bash usage_example.sh train qwen-el-self
bash usage_example.sh train qwen-rl-gpt4o
```

Use the planner to expand these into a checklist with explicit `EL_DATA_ROOT`, `EL_CHECKPOINT_ROOT`, model roles, node count, rollout count, and credentials.

### Eval, fuzzy eval, end-task eval, and score

- `eval`: held-out WildChat generation for one alias and checkpoint step. The lower-level evaluator can use `wildchat_4o`, `wildchat`, or a train-as-validation suffix for debugging. It merges actor checkpoints unless `use_bsl=true`.
- `eval_fuzzy`: generation for `alpacaeval2`, `wildbench`, `arena_hard_v2`, and `creativewritingv3`. This stage writes model responses but does not score them.
- `eval_endtask`: IF-Eval through lm-evaluation-harness. It uses an unsafe-code-evaluation allowance and must only be run in an approved sandbox.
- `score`: GPT-4o/OpenAI-compatible scoring after `eval` and `eval_fuzzy`. Use the long experiment name, not the short alias.

Scoring argument surfaces from static inspection:

- Held-out GPT-4o scorer: `exp_name`, `start_ckpt`, `end_ckpt`, `step`, `max_workers`, `resume`, `reval`, `eval_suffix`, and `base_dir`.
- Fuzzy GPT-4o scorer: `benchmark`, `exp_name`, `start_ckpt`, `end_ckpt`, `step`, `max_workers`, `no_shorten`/`shorten`, `reval`, and `base_dir`.
- Fuzzy generation helper: `benchmark`, `model`, `output_dir`, `temperature`, `top_p`, `max_tokens`, and GPU memory utilization.

Skeleton:

```bash
bash usage_example.sh eval qwen-el-self <CKPT_STEP>
bash usage_example.sh eval_fuzzy qwen-el-self <CKPT_STEP>
bash usage_example.sh eval_endtask qwen-el-self <CKPT_STEP>
source-script-label:eval_gpt4o.py --exp_name wildchat-el-q3-8b-r8b --start_ckpt <CKPT_STEP> --end_ckpt <CKPT_STEP>
source-script-label:eval_gpt4o_fuzzy.py --benchmark alpacaeval2,wildbench,arena_hard_v2,creativewritingv3 --exp_name wildchat-el-q3-8b-r8b --start_ckpt <CKPT_STEP> --end_ckpt <CKPT_STEP>
```

Before scoring, verify that generated response files exist under `EL_RESULT_ROOT` for the long experiment name and checkpoint step, and confirm OpenAI-compatible credentials without embedding their values.

## GAD operating model

GAD uses a VeRL-based implementation with stage-specific branches. Branch discipline is mandatory: the correct script on the wrong branch is still a wrong run.

### Data preparation

Teacher data comes from a GPT-5-Chat response dataset and is exported to train/test parquet files before training. The exporter requires dataset access and writes local parquet files used by all training stages. Treat this as a user-approved data-acquisition step, not as a planner action.

Validate staged files with either explicit expected file names or the GAD profile:

```bash
python scripts/check_experience_inputs.py --data-root <GAD_DATA_ROOT> --profile gad
```

### Stage and branch map

| Stage | Required branch | Command concept | Key checks |
| --- | --- | --- | --- |
| SeqKD baseline | `seqkd` | SeqKD training | Student model path, teacher-response train/test parquets, W&B credentials, 8-GPU/node assumption, save/eval cadence. |
| Warmup | `warmup` | Warmup training | Student model path, reward/discriminator model path, KL enabled, warmup checkpoint step for later adversarial training. |
| Adversarial GAD | `gad` | Adversarial training | Warmup checkpoint copied into the adversarial experiment namespace, explicit `resume_step`, actor and critic Hugging Face directories prepared from shards. |
| Generation/eval | `eval` | Parallel generation | Checkpoint range, validation data names, GPU partitioning, merged actor checkpoints, optional external scoring plan. |

### SeqKD baseline

SeqKD is supervised fine-tuning on teacher responses through the VeRL-aligned implementation. Static script evidence shows GRPO entrypoint usage with KL disabled, entropy and KL coefficients set to zero, actor learning rate `5e-6`, tensor parallel size `2`, rollout count `8`, and ROUGE-L logging as a diagnostic.

Skeleton:

```bash
cd <GAD_VERL_IMPL>
git checkout seqkd
cd <GAD_WORKFLOW_DIR>
source-script-label:train/gpt5-chat-filtered-7b-seqkd-lr5e-6.sh --model <STUDENT_MODEL> --exp_name <SEQKD_EXP> --nnodes <NODES>
```

### Warmup stage

Warmup initializes the actor and discriminator/reward model before adversarial training. Static script evidence shows KL enabled with low-variance KL, actor and critic learning rates `1e-6`, tensor parallel size `2`, rollout count `8`, and two total epochs.

Skeleton:

```bash
cd <GAD_VERL_IMPL>
git checkout warmup
cd <GAD_WORKFLOW_DIR>
source-script-label:train/gpt5-chat-filtered-7b-warmup-lr1e-6.sh --model <STUDENT_MODEL> --reward_model <REWARD_MODEL> --exp_name <WARMUP_EXP> --nnodes <NODES>
```

### Adversarial stage

Adversarial GAD starts from a warmup checkpoint. The source script prepares actor and critic Hugging Face directories from checkpoint shards, then launches GRPO-style training with KL enabled, critic model path set to the merged reward/discriminator checkpoint, actor/critic learning rates `1e-6`, and save/test frequency around checkpoint intervals.

Skeleton:

```bash
cd <GAD_VERL_IMPL>
git checkout gad
cd <GAD_WORKFLOW_DIR>
# Copy or stage the warmup checkpoint into the adversarial experiment namespace first.
source-script-label:train/gpt5-chat-filtered-7b-adversarial-lr1e-6.sh --exp_name <ADVERSARIAL_EXP> --resume_step <WARMUP_STEP> --nnodes <NODES>
```

### Generation and evaluation

Generation requires the `eval` branch. The parallel generation concept evaluates validation data names `lmsys`, `dolly`, `self-inst`, and `Vicuna` over checkpoint ranges, partitioning visible GPUs across intervals. Static script evidence shows generation-only validation with KL disabled, vLLM rollout, configurable checkpoint start/end/step, node count, GPU count, and override behavior.

Skeleton:

```bash
cd <GAD_VERL_IMPL>
git checkout eval
cd <GAD_WORKFLOW_DIR>
source-script-label:generate/generate.sh --model <BASE_MODEL> --exp_name <ADVERSARIAL_EXP> --val_data lmsys --ckpt_start <START> --ckpt_end <END> --ckpt_step <STEP> --nnodes <NODES> --ngpus <GPUS> --override false
```

GAD evaluation can use GPT-4o or open-source models for reference answer generation and scoring. Confirm OpenAI-compatible credentials only when the user selects an OpenAI scorer.

### GAD metric caution

ROUGE-L is logged as a training diagnostic to check optimization behavior. It is local and n-gram oriented; do not treat it as the final quality criterion for GAD.

## Coach/GAD handoff checklist

Before finalizing a command plan, confirm:

1. Family and stage: Coach train/eval/eval_fuzzy/eval_endtask/score, or GAD SeqKD/warmup/adversarial/generation.
2. Model path, reference/reward model path, experiential/coach model, and experiment name are distinct and intentional.
3. Checkpoint step or range is explicit for every eval, score, resume, or adversarial stage.
4. Data root, checkpoint root, and result root are user-provided placeholders or environment variables.
5. W&B, Hugging Face, and OpenAI-compatible credential needs are listed without secret values.
6. GPU count and node count match the script assumptions; many source trainer snippets assume 8 GPUs per node.
7. For GAD, branch switching happens before each stage and is not skipped.

## Verification boundary

No Coach or GAD training, data download, GPT-4o scoring, IF-Eval run, checkpoint merge, Docker setup, Ray startup, branch checkout, or vLLM generation was executed during skill creation. This reference is a static planning guide for a target environment prepared by the user.
