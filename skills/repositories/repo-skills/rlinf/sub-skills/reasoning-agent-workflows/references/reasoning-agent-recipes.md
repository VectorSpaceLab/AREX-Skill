# Reasoning and agentic workflow recipes

This reference is a self-contained operating guide for constructing RLinf reasoning and agentic runs. It intentionally describes recipe concepts and config shapes rather than instructing agents to run source-tree example scripts.

## Shared mental model

A reasoning/agentic RL run composes these groups:

| Group | Present when | Role | Key config blocks |
| --- | --- | --- | --- |
| `rollout` | all RL/eval workflows | Runs SGLang or vLLM generation and receives synced actor weights during training. | `rollout.*`, `algorithm.sampling_params`, `rollout.model.*` |
| `actor` | all RL/SFT workflows | Trains the policy with Megatron or FSDP/FSDP2. | `actor.training_backend`, `actor.model.*`, `actor.optim`, `actor.megatron` or `actor.fsdp_config` |
| `reward` | rule/reward-model RL workflows | Fills rewards for generated sequences; absent in some agent loops that compute reward internally. | `reward.reward_type`, `reward.reward_scale`, `reward.tokenizer`, `reward.use_reward_model` |
| `critic` | PPO with critic | Trains value model for GAE advantages. | `critic.use_critic_model`, `critic.*`, `cluster.component_placement` |
| `inference` / `actor_inference` | disaggregated logprob recomputation | Recomputes old/reference logprobs after rollout. Collocated mode reuses actor workers. | `algorithm.recompute_logprobs`, `inference.*`, placement |
| `agentloop` | multi-turn agentic RL/eval | Orchestrates tool calls, turn limits, parsing, and multi-agent workflow. | `agentloop.*`, `tools.*` |
| tool workers | SearchR1, rStar2, WideSeek-R1 | Serve search/access/code-execution functions to the agent loop. | `tools.*`, parser-specific service fields |
| online serving workers | coding online RL | Expose completion and feedback ingestion services while training. | `rollout_server.*`, `runner.task_type: coding_online_rl` |

RLinf’s core training cadence for reasoning RL is:

```text
batch prompts -> sync actor weights to rollout -> rollout generations -> compute rewards
-> optional actor/critic inference for logprobs/values -> optional critic update -> actor update
-> checkpoint/validation decisions
```

For multi-turn agentic RL, the rollout stage is replaced by:

```text
batch questions -> agent loop -> generation calls -> tool calls -> tool responses
-> final trajectories/rewards -> optional logprob recomputation -> actor update
```

## Common launch construction checklist

Before preparing any launch command:

1. Confirm the workflow class and `runner.task_type`.
2. Ask for local model/tokenizer checkpoints, output directory, data path(s), and whether the user has already started Ray.
3. Route cluster, Ray, node-rank, and placement fundamentals to `setup-and-cluster`.
4. Run the bundled static inspector against the candidate config:

   ```bash
   python /path/to/skill/sub-skills/reasoning-agent-workflows/scripts/inspect_agentic_config.py CONFIG.yaml
   ```

5. Resolve every placeholder path, credential, service address, and length-budget warning before expensive execution.
6. Choose the user’s actual Hydra/application launcher. This skill does not prescribe source-tree launch scripts; it distills the fields such launchers need.

## Recipe catalog

### Math reasoning GRPO

Use for prompt-level relative scoring with multiple samples per prompt and no critic.

Config anchors:

```yaml
runner:
  task_type: reasoning
  seq_length: 12288        # or larger for long chain-of-thought tasks
algorithm:
  adv_type: grpo
  loss_type: actor
  group_size: 8            # must be >= 2 for useful GRPO
  n_minibatches: 2-4
  recompute_logprobs: true
  normalize_advantages: true
  ratio_clip_eps: 0.2
  sampling_params:
    do_sample: true
    temperature: 0.7-1.0
    max_new_tokens: ${subtract:${runner.seq_length}, ${data.max_prompt_length}}
data:
  type: math
  prompt_key: prompt
  answer_key: solutions
  max_prompt_length: 512-4096
reward:
  use_reward_model: false
  reward_type: math
```

Operational notes:

- `group_size` controls completions per prompt; global generated sequences are `data.rollout_batch_size * group_size`.
- Rule reward expects final answers that the math verifier can extract, commonly boxed or numeric answers.
- `runner.seq_length` must exceed `data.max_prompt_length`; the difference is the generation budget.
- `algorithm.recompute_logprobs: true` is the stable default when rollout logprobs are not trusted or when the backend should not return logprobs.

### Math reasoning PPO with critic

Use when actor-critic GAE is required instead of group-relative rewards.

Config deltas from GRPO:

```yaml
cluster:
  component_placement:
    actor,critic,rollout,reward: all
algorithm:
  adv_type: gae
  group_size: 1
  gamma: 1
  gae_lambda: 1
  loss_type: actor
  value_cliprange: 0.5
critic:
  use_critic_model: true
  group_name: CriticGroup
```

Operational notes:

- PPO reasoning uses a separate critic model; do not assume an actor value head.
- If placement is disaggregated and `recompute_logprobs` is true, an inference group is also required.
- `critic_warmup_steps` is present in configs but source runner marks warmup unimplemented; avoid setting it above zero unless the code has changed.

### VQA / VLM reasoning GRPO

Use for visual reasoning such as geometry QA and robot-scene VQA.

Config anchors:

```yaml
runner:
  task_type: reasoning
data:
  type: vlm
  dataset_name: robo2vlm        # or a VLM dataset registered in the package
  prompt_key: problem           # or question/prompt, depending on dataset
  answer_key: answer
  image_keys: [images]
  use_chat_template: true
  max_prompt_length: 1024-4096
rollout:
  model:
    model_type: qwen2.5_vl      # or qwen3_vl family
actor:
  training_backend: fsdp        # FSDP/FSDP2 is common for VLM examples
  fsdp_config:
    strategy: fsdp2             # for Qwen3-VL style configs
algorithm:
  adv_type: grpo
  importance_sampling_fix: true # useful for selected VLM configs
```

Operational notes:

- The VLM loader can read JSON, JSONL, parquet, directories, image bytes, PIL images, paths, and `<image>` placeholders. If prompts omit placeholders, images are prepended before text.
- Qwen3-VL-style workflows require matching modern Torch, SGLang, and Transformers versions; verify package versions before launch.
- `recompute_logprobs` plus `return_logprobs` enables rollout-vs-training KL diagnostics, but costs more memory and time.

### Coding online RL service

Use when a code editor or client sends completion requests and feedback to RLinf while training.

Config anchors:

```yaml
runner:
  task_type: coding_online_rl
algorithm:
  adv_type: raw
  loss_type: actor
  group_size: 1
  recompute_logprobs: true      # asserted by the runner
rollout:
  rollout_backend: sglang       # online coding path is SGLang-oriented
  detokenize: true
rollout_server:
  online_router:
    host: 0.0.0.0
    port: 8081                  # OpenAI-compatible completion endpoint
  tracking_rollout:
    host: 0.0.0.0
    port: 8082                  # feedback ingestion endpoint
data:
  max_prompt_length: 1024       # reserved for validation and generation budget
```

Prerequisites and pitfalls:

- This workflow expects disaggregated placement for rollout, inference, and actor. Route placement construction to `setup-and-cluster`.
- The external client should point completions to the online router endpoint and feedback to the tracking endpoint.
- Feedback events must include enough prompt/completion/context fields for the server rollout worker to build training samples.
- Weight sync pauses request routing around actor-to-rollout updates. If requests hang at sync boundaries, inspect router logs before changing model code.

### Offline code validation with LLM-as-judge

Use when simulating code-completion feedback from a fixed dataset and a judge model rather than live user feedback.

Config anchors:

```yaml
runner:
  task_type: reasoning
data:
  type: math                  # code FIM data is adapted into prompt/solution records
  prompt_key: prompt
  answer_key: solutions
reward:
  reward_type: code_offline
  use_prompt: true
algorithm:
  adv_type: grpo
  group_size: 8
```

Required environment variables for the judge service:

```text
LLMASJUDGE_API_URL
LLMASJUDGE_API_KEY
LLMASJUDGE_MODEL
```

The judge prompt and model must fit the completion task. Treat missing or placeholder judge values as a hard preflight failure.

### AgentLightning multi-turn agent RL

Use for AgentLightning triplet-store based multi-turn trajectories, such as calculator-backed math agents.

Config and runtime concepts:

- Rollout backend is an SGLang HTTP-serving worker (`serving_mode: worker_http` in SGLang configs).
- The runner obtains server addresses, passes them to an AgentLightning rollout worker, and stores trajectories through a LightningStore endpoint.
- The adapter converts traces into training triplets; reward missing values can be filled with `algorithm.reward_fillna_value`.
- Training still uses actor sync, optional recomputed logprobs, and actor update like reasoning RL.

Prerequisites:

- AgentLightning and the agent framework dependencies must be installed in the environment.
- The store endpoint must be HTTP-addressable from Ray workers; in-process store objects are not serializable across Ray boundaries.
- Eval mode may force CUDA launch blocking and should validate rollout weights on first sync.

### SearchR1-style search-tool RL

Use for multi-turn QA where the model emits search tags/tool calls and receives local retrieval snippets.

Config anchors:

```yaml
runner:
  task_type: reasoning
algorithm:
  adv_type: grpo_dynamic
  advantage_mode: trajectory
  loss_scales: [group_level, agent_level, turn_level]
  recompute_logprobs: true
agentloop:
  toolcall_parser: searchr1-qwen
  max_turns: 2
  max_tool_response_length: 500
  is_dynamic_rollout_batch: true
tools:
  search:
    server_addr: HOST:8000
    topk: 3
rollout:
  detokenize: true              # needed when stop strings are used and output is re-tokenized
reward:
  reward_type: searchr1
```

Prerequisites:

- A local retrieval server exposing the expected search API must be running and reachable from tool workers.
- The wiki corpus, embedding model, and vector index are large assets; confirm they already exist before planning a run.
- `agentloop` worker count must match rollout data-parallel size in the source launch pattern.

### rStar2-style code-tool reasoning

Use when the agent invokes a code-execution judge and receives tool responses during math reasoning.

Config anchors:

```yaml
runner:
  task_type: reasoning
  seq_length: 10240
algorithm:
  adv_type: grpo
  group_size: 16-32
  recompute_logprobs: false     # selected rStar2 configs rely on rollout logprobs
  down_sampling:
    do_down_sampling: true
agentloop:
  toolcall_parser: rstar2-qwen
  max_assistant_turns: 5
  continue_at_tool_failure: true
  max_tool_response_length: 256
tools:
  codejudge:
    host_addr: 127.0.0.1
    host_port: 8000
    concurrency_limit: 128
reward:
  reward_type: rstar2
```

Prerequisites:

- A code judge server and workers must be running; they normally require Redis plus a Python execution worker pool.
- Math verification dependencies are required for final-answer reward computation.
- Generated code execution is an external service boundary; keep it isolated and do not point it at sensitive workspaces.

### WideSeek-R1 hybrid multi-agent search

Use for long-context information-seeking with planner/worker roles, search/access tools, optional online web APIs, and optional judge LLM.

Config anchors:

```yaml
runner:
  task_type: reasoning          # train; reasoning_eval for eval
  seq_length: 32000
algorithm:
  adv_type: grpo_dynamic
  advantage_mode: trajectory
  loss_scales: [group_level, agent_level, turn_level]
  group_size: 4-8
agentloop:
  workflow: mas                 # or sa
  toolcall_parser: wideseek_r1-qwen
  max_planner_turns: 10
  max_worker_turns: 20
  max_sa_turns: 50
  llm_ip: JUDGE_HOST
  llm_port: JUDGE_PORT
  use_local_judge: false
tools:
  online: false                 # false = local retrieval; true = web search
  search:
    server_addr: HOST:8000
  use_jina: true
rollout:
  rollout_backend: sglang
  detokenize: true
  use_fixed_worker: false
```

Prerequisites and choices:

- Offline training typically uses a local Qdrant retrieval service and corpus; online evaluation may need Serper and Jina API keys.
- If `agentloop.use_local_judge: true`, plan an additional fixed rollout/judge model group with its own model path and placement.
- `actor.enable_dp_load_balance: true` and `actor.pack_traj: true` are important in multi-agent configs to handle variable turn lengths.
- `data.is_hybrid` distinguishes hybrid WideSearch/QA training data from single-source datasets; `data.is_markdown` changes how answers are packaged for reward/eval.

## Backend and training-backend selection

| Need | Prefer | Why |
| --- | --- | --- |
| Large text-only Megatron post-training | Megatron actor + SGLang rollout | Efficient tensor/pipeline parallel actor training and mature weight sync. |
| Smaller or HuggingFace-centric text/VLM workflows | FSDP/FSDP2 actor + SGLang/vLLM rollout | Simpler model loading; FSDP2 helps large VLMs. |
| Rollout logprobs are not reliable or backend cannot return them cheaply | `algorithm.recompute_logprobs: true` | Actor/inference recomputes old/ref logprobs. |
| Need rollout-vs-train KL diagnostics or TIS | `return_logprobs: true` plus recomputation | Provides both rollout and recomputed logprob tensors. |
| Agentic tag/string stop sequences | SGLang and `detokenize: true` | Agent loops often re-parse text and stop strings. |
| High-throughput prefix-heavy generation | vLLM with chunked prefill/prefix caching | Useful when supported by the model and logprob needs. |

## Minimal preflight prompts for users

Ask only for missing concrete values:

- Which workflow: math GRPO/PPO, VQA, coding online, offline code judge, AgentLightning, SearchR1, rStar2, WideSeek-R1, or SFT?
- Local model/tokenizer path and model type?
- Training/eval data path, format, prompt key, answer key, image keys if any?
- Available GPUs/nodes and whether Ray is already started?
- External services: retrieval server, code judge, LLM judge, online search keys, code editor feedback endpoint?
- Maximum sequence length/prompt length budget and desired rollout backend?

When these are unknown, stop before launch and return a config checklist rather than guessing.
