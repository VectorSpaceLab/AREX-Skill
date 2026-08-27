# EBFT Feature-Matching Rewards

Energy-Based Fine-Tuning (EBFT) is Axolotl's feature-matching RL method. Instead of writing external reward code, the trainer compares hidden-state features from generated completions against ground-truth completions and uses the similarity as the reward signal.

Use EBFT when you have reference completions but not an external verifier or preference pairs. Route DPO/KTO/ORPO/SimPO preference data away from this sub-skill.

## Mode Selection

| Mode | Use When | vLLM | Dataset Output |
| --- | --- | --- | --- |
| Structured | Prompt/completion instruction, QA, code, or chat data with reference answers | Usually yes | `prompt`, `ground_truth` |
| Structured async | Same as structured, but generation should overlap with training | Yes | `prompt`, `ground_truth` |
| Strided | Raw or structured documents where training should place rollout anchors inside token sequences | No | `input_ids`, `attention_mask`, `labels`, `prompt_length` |

Structured EBFT extends the GRPO-style rollout path and uses feature-matching rewards instead of user reward functions. Strided EBFT runs block-parallel short rollouts inside the trainer and does not require an external vLLM server.

## Structured EBFT Skeleton

```yaml
rl: ebft

adapter: lora
lora_target_linear: true

ebft:
  mode: structured
  feature_layers: [0.25, 0.5, 0.75]
  embed_method: last_token
  use_whitening: true
  alignment_coef: 1.0
  diversity_coef: 1.0
  ce_coef: 0.0

trl:
  use_vllm: true
  use_data_producer: true
  vllm_lora_sync: true
  num_generations: 4
  max_completion_length: 256
  temperature: 0.7
  scale_rewards: true
  loss_type: grpo

vllm:
  gpu_memory_utilization: 0.5
  max_model_len: 1024

datasets:
  - path: your-dataset
    type: your_ebft_transform.transform
```

Start vLLM before training:

```bash
axolotl vllm-serve ebft_config.yaml
axolotl train ebft_config.yaml
```

Structured transforms must emit:

```python
{
    "prompt": [{"role": "user", "content": "..."}],
    "ground_truth": "reference completion",
}
```

For multi-turn EBFT, preserve turn boundaries in the transformed output so the trainer can reconstruct ground truth with chat-template role markers rather than raw string concatenation.

## Strided EBFT Skeleton

```yaml
rl: ebft

ebft:
  mode: strided
  stride: 8
  context_length: 8
  generate_max_len: 8
  n_samples_per_prompt: 4
  temperature: 0.6
  feature_layers: [0.25, 0.5, 0.75]
  embed_method: last_token
  use_whitening: true
  alignment_coef: 1.0
  diversity_coef: 1.0
  rl_coef: 1.0
  ce_coef: 0.03
  advantage_estimator: rloo
  min_completion_prefix: 8

attn_implementation: flex_attention
gradient_checkpointing: true
gradient_checkpointing_kwargs:
  use_reentrant: true

datasets:
  - path: your-dataset
    type: ebft_strided_structured.transform
```

Run strided mode with a single training command; no `axolotl vllm-serve` process is needed.

## Feature Settings

- `feature_layers` are fractions of model depth, such as `[0.25, 0.5, 0.75]`; Axolotl resolves them to hidden-state layer indices.
- `embed_method` controls pooling. `last_token` is the common default; `mean_pooling`, `completion_mean`, and `concat` are mode-dependent alternatives.
- `use_whitening: true` decorrelates feature dimensions before reward calculation and is usually recommended.
- `alignment_coef` rewards similarity to ground truth; `diversity_coef` penalizes same-prompt generations that collapse to each other.
- `ce_coef` mixes cross-entropy on ground-truth tokens into strided or structured training when drift control is needed.

## Strided Constraints

For strided mode, check these before training:

- Prefer `attn_implementation: flex_attention`; dense masks can consume much more memory.
- Use `gradient_checkpointing_kwargs.use_reentrant: true` with flex-attention block masks.
- Avoid unrelated graph compilation settings when they conflict with flex attention in the installed stack.
- `n_samples_per_prompt >= 2` is required for RLOO or group-normalized advantage estimators; if it is `1`, the trainer falls back to a reinforce-style estimator and disables diversity that needs multiple samples.
- `micro_batch_size` and generation counts must be chosen so each prompt group is complete.

## Monitoring

Watch these EBFT signals:

- `ebft/alignment` should trend upward as generated features approach ground truth.
- `ebft/diversity` should not explode; very high values indicate mode collapse or poor whitening/temperature settings.
- `ebft/cfm_loss` should trend downward.
- `ebft/reward` or `ebft/mean_reward` should improve over time.
- `grad_norm` and `entropy` should remain in reasonable ranges for the model and optimizer.

## Common Mode Mistakes

- Do not require vLLM for strided EBFT; it is intentionally trainer-local.
- Do not omit vLLM planning for structured EBFT unless using a deliberately small no-vLLM experiment.
- Do not feed raw string metadata columns into strided DataLoader outputs; transforms should remove original string columns after producing token tensors.
- Do not confuse external reward functions with EBFT rewards; EBFT uses feature matching from model hidden states.
