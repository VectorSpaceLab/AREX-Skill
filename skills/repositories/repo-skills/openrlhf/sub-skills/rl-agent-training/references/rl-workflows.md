# RL Workflows

OpenRLHF RL training is centered on `python -m openrlhf.cli.train_ppo_ray`. The command orchestrates Ray actors for actor, reference, critic, reward, and vLLM engines, then uses an agent execution pipeline for rollout generation.

## Execution modes

| Mode | Core flags | Use when | Caution |
| --- | --- | --- | --- |
| Synchronous RL | no async flag | debugging, reproducibility, sensitive algorithms | lower throughput |
| Hybrid engine | `--train.colocate_all`, usually `--vllm.enable_sleep`, `--ds.enable_sleep` | maximizing GPU use with on-policy rollout/train phases | avoid pairing `--vllm.enable_sleep` with async |
| Async training | `--train.async_enable`, `--train.async_queue_size N` | throughput after recipe quality is known | larger queues increase off-policyness |
| Async partial rollout | `--train.async_enable`, `--train.partial_rollout_enable` | aggressive overlap of rollout and training | in-flight samples may mix old/new weights; consider IS correction |
| Single-turn custom reward | `--reward.remote_url <reward_func.py-or-http-url>` | rule, math, code, judge, or external reward | set the dataset label key when labels are required |
| Multi-turn agent | `--train.agent_func_path <agent_func.py>` | tool/environment/game/browser/coding feedback loops | script must export `AgentExecutor` |
| VLM multi-turn | `--train.agent_func_path <vlm_agent.py>`, `--data.max_images_per_prompt > 0` | image prompts and image feedback | no critic model and no packing samples |

## Baseline command skeleton

The exact resource sizes are hardware-specific. Keep this structure and adjust counts, model names, datasets, and output paths:

```bash
ray job submit --address="http://127.0.0.1:8265" \
  --runtime-env-json='{"working_dir":"."}' \
  -- python -m openrlhf.cli.train_ppo_ray \
  --actor.model_name_or_path <actor-or-sft-model> \
  --reward.model_name_or_path <reward-model-or-unused-with-remote-reward> \
  --data.prompt_dataset <dataset> \
  --data.input_key <prompt-key> \
  --ckpt.output_dir <output-dir> \
  --ckpt.path <checkpoint-dir> \
  --ref.num_nodes 1 --ref.num_gpus_per_node <gpus> \
  --actor.num_nodes 1 --actor.num_gpus_per_node <gpus> \
  --critic.num_nodes 1 --critic.num_gpus_per_node <gpus> \
  --reward.num_nodes 1 --reward.num_gpus_per_node <gpus> \
  --vllm.num_engines <engines> \
  --vllm.tensor_parallel_size <tp> \
  --vllm.sync_backend nccl \
  --rollout.batch_size <rollout-batch> \
  --train.batch_size <train-batch> \
  --train.micro_batch_size <micro-batch> \
  --rollout.micro_batch_size <rollout-micro-batch> \
  --data.max_len <prompt-plus-response-tokens> \
  --rollout.max_new_tokens <response-tokens> \
  --ds.zero_stage 3 \
  --ds.param_dtype bf16
```

Use operations-and-utilities for Ray startup, Slurm submission, container setup, NCCL environment, and service readiness checks.

## PPO and PPO-like algorithms

- Default PPO uses `--algo.advantage.estimator gae`, a critic, and `--algo.kl.init_coef` for KL penalty.
- Use `--actor.eps_clip`, `--actor.eps_clip_low_high`, `--actor.dual_clip`, and `--critic.value_clip` for PPO clipping behavior.
- `--actor.policy_loss_type gspo` selects the GSPO actor loss variant when appropriate.
- `--algo.kl.init_coef 0` disables the reference-model KL penalty path; only do this intentionally.

## REINFORCE++, RLOO, GRPO, and Dr.GRPO

Set `--algo.advantage.estimator` explicitly:

| Estimator | Meaning | Required shape |
| --- | --- | --- |
| `reinforce` | REINFORCE++ style returns without critic | can run with one sample per prompt |
| `reinforce_baseline` | REINFORCE++-baseline, strong default for RLVR/math reasoning | requires `--rollout.n_samples_per_prompt > 1` |
| `rloo` | leave-one-out group baseline | requires `--rollout.n_samples_per_prompt > 1` |
| `group_norm` | GRPO group normalization | requires `--rollout.n_samples_per_prompt > 1` |
| `dr_grpo` | Dr.GRPO-style group mean without local std division | requires `--rollout.n_samples_per_prompt > 1` |

For GRPO-style KL-as-loss behavior, use `--algo.kl.use_loss` and prefer `--algo.kl.estimator k2` or `k3`. Without KL loss, prefer `--algo.kl.estimator k1`.

## DAPO and ProRL-style options

DAPO-like runs combine multi-sample rollout, reward scores, dynamic filtering, and sometimes overlong penalties:

```bash
--algo.advantage.estimator group_norm \
--rollout.n_samples_per_prompt 8 \
--algo.dynamic_filtering_enable \
--algo.dynamic_filtering_range 0 1 \
--reward.remote_url <reward_func.py-or-http-url> \
--reward.overlong_buffer_len <tokens> \
--reward.overlong_penalty_factor <factor>
```

Important constraints:

- Dynamic filtering requires `--rollout.n_samples_per_prompt > 1`.
- Dynamic filtering also requires either `--reward.remote_url` or `--train.agent_func_path`.
- Overlong penalty uses response length relative to `--rollout.max_new_tokens` / `--data.max_len` budget.
- ProRL-style stop-properly penalty is controlled by `--reward.stop_properly_penalty_coef` and depends on vLLM finish reason.

## Async and off-policy controls

Async training can increase throughput by overlapping rollout and optimization:

```bash
--train.async_enable \
--train.async_queue_size 1
```

Partial rollout overlaps even more aggressively:

```bash
--train.async_enable \
--train.partial_rollout_enable \
--algo.advantage.is_correction_enable \
--algo.advantage.is_correction_type tis \
--algo.advantage.is_correction_threshold 0.5 5.0
```

Use `--rollout.vllm_generate_batch_size > --rollout.batch_size` only with async enabled. This oversamples generation and buffers extra samples; it is intentionally more off-policy.

## Single-turn custom reward

Use a Python file path or HTTP URL in `--reward.remote_url`:

```bash
--reward.remote_url reward_func.py \
--data.label_key answer
```

For a local Python file, OpenRLHF imports `reward_func(queries, prompts, labels, **kwargs)` and expects a dict containing `rewards`; `scores` is used by dynamic filtering; `extra_logs` is logged when present. For HTTP reward URLs, the request JSON uses `query`, `prompts`, and `labels` arrays.

## Multi-turn agent

Use a Python script with an exported `AgentExecutor`:

```bash
--train.agent_func_path agent_func.py \
--train.async_enable
```

When `--train.agent_func_path` is set, OpenRLHF internally treats the reward source as agent-based. The script is imported by vLLM Ray engines, so keep dependencies installed on every Ray worker.

## OpenAI-compatible agent server executor

Use this pattern when a custom agent framework expects an OpenAI chat-completions API. The executor starts a local FastAPI/uvicorn server inside the Ray actor, wraps vLLM at `/v1/chat/completions`, records token IDs/logprobs, and stitches the trace into OpenRLHF rollout fields.

Customize by subclassing or editing `run_agent(prompt, label, session_id)` in an executor file. Every OpenAI call should pass a stable `session_id` through request body extras so token traces can be joined.

## VLM RL and VLM multi-turn

VLM runs add image data routing:

```bash
--data.image_key images \
--data.max_images_per_prompt 1 \
--actor.freeze_visual_encoder \
--algo.advantage.estimator reinforce_baseline \
--rollout.n_samples_per_prompt 4 \
--train.agent_func_path vlm_agent.py
```

Constraints enforced by `train_ppo_ray`:

- If `--data.max_images_per_prompt > 0`, do not use a critic; choose an estimator other than `gae`.
- Do not enable `--ds.packing_samples` for VLM because packing breaks image/token alignment.
- Initial prompts and environment feedback must contain the model-specific image placeholder tokens that match the returned image list.
