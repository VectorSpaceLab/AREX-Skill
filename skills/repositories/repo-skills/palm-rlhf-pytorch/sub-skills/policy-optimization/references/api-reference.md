# Policy Optimization API Reference

This reference covers the package's PPO-family trainer surface and the import paths future agents need most often.

## Public Imports

Root PPO path:

```python
from palm_rlhf_pytorch import RLHFTrainer, ActorCritic
```

Alternative trainer modules:

```python
from palm_rlhf_pytorch import grpo, tpo, flowrl
```

## PPO ActorCritic

Verified constructor shape:

```python
ActorCritic(
    palm,
    critic=None,
    pooled_values=False,
    actor_lora=True,
    critic_lora=True,
    actor_lora_r=8,
    critic_lora_r=8,
    actor_lora_scope='actor',
    critic_lora_scope='critic',
    actor_dropout=0.0,
    critic_dropout=0.0,
    critic_dim_out=6,
)
```

### Notes

- `actor_palm` is the policy model.
- If `critic` is omitted, a deep copy of `palm` is used for the critic.
- `pooled_values=True` changes how critic embeddings are reduced before value prediction.
- If `critic` is an `ImplicitPRM`, the critic path becomes process-reward-like and `critic_lora` is disabled internally.

### Key Methods

```python
actor_critic.actor_parameters()
actor_critic.critic_parameters()
actor_critic.forward(x, mask=None, return_values=True)
actor_critic.generate(state, max_seq_len, eos_token=None, return_values=False, **kwargs)
```

`generate` returns a named structure containing actions, the concatenated sequence, masks, logits, and values.

## PPO RLHFTrainer

Verified constructor shape:

```python
RLHFTrainer(
    *,
    prompts=None,
    prompts_path=None,
    prompt_token_ids=None,
    tokenizer=None,
    palm,
    reward_model,
    critic=None,
    actor_critic=None,
    actor_lr=1e-4,
    critic_lr=1e-4,
    actor_wd=0.0,
    critic_wd=0.0,
    actor_lora=True,
    critic_lora=True,
    actor_lora_r=8,
    critic_lora_r=8,
    critic_pooled_values=True,
    actor_dropout=0.0,
    critic_dropout=0.0,
    betas=(0.9, 0.999),
    max_norm=None,
    eps_clip=0.2,
    value_clip=0.4,
    beta_s=0.01,
    pad_value=0.0,
    minibatch_size=16,
    epochs=1,
    kl_div_loss_weight=0.1,
    accelerate_kwargs=dict(),
    critic_num_pred_bins=6,
    hl_gauss_loss_kwargs=dict(...),
)
```

### Important Behaviors

- Exactly one of `prompts`, `prompts_path`, or `prompt_token_ids` must be supplied.
- Raw string prompts require `tokenizer`.
- The trainer uses `Accelerator` internally and prepares the actor-critic, reward model, and optimizers.
- `generate(max_seq_len, prompt, num_samples=4, ...)` repeats a 1D prompt and returns the highest-reward sequence.
- `train(...)` uses large defaults; tiny smoke checks should override them explicitly.
- `learn(memories)` consumes accumulated PPO memories and performs the policy/value updates.

### Key Methods

```python
trainer.print(msg)
trainer.save(filepath='./checkpoint.pt')
trainer.load(filepath='./checkpoint.pt')
trainer.generate(max_seq_len, prompt, num_samples=4, **kwargs)
trainer.learn(memories)
trainer.train(num_episodes=50000, max_timesteps=500, update_timesteps=5000, max_batch_size=16, max_seq_len=2048, eos_token=None, temperature=1.0)
```

## GRPO Trainer

Verified constructor shape:

```python
grpo.RLHFTrainer(
    *,
    prompts=None,
    prompts_path=None,
    prompt_token_ids=None,
    tokenizer=None,
    palm,
    reward_model,
    grpo_num_times_sample_rewards=10,
    actor_lr=1e-4,
    actor_wd=0.0,
    actor_lora=True,
    actor_lora_r=8,
    actor_dropout=0.0,
    betas=(0.9, 0.999),
    max_norm=None,
    eps_clip=0.2,
    beta_s=0.01,
    pad_value=0.0,
    minibatch_size=16,
    epochs=1,
    kl_div_loss_weight=0.1,
    use_simple_policy_optimization=False,
    use_dr_grpo=False,
    dr_grpo_constant=None,
    use_max_rl=False,
    add_entropy_to_advantage=False,
    entropy_to_advantage_kappa=2.0,
    entropy_to_advantage_scale=0.4,
    accelerate_kwargs=dict(),
)
```

### Notes

- GRPO removes the critic and samples multiple rewards per prompt.
- The actor is the main trainable component.
- It supports SPO, Dr. GRPO, MaxRL, and optional entropy shaping.

## TPO Trainer

Verified constructor shape:

```python
tpo.RLHFTrainer(
    *,
    prompts=None,
    prompts_path=None,
    prompt_token_ids=None,
    tokenizer=None,
    palm,
    reward_model,
    num_times_sample_rewards=10,
    actor_lr=1e-4,
    actor_wd=0.0,
    actor_lora=True,
    actor_lora_r=8,
    actor_dropout=0.0,
    betas=(0.9, 0.999),
    max_norm=None,
    beta_s=0.01,
    pad_value=0.0,
    minibatch_size=16,
    epochs=1,
    tpo_eta=1.0,
    accelerate_kwargs=dict(),
)
```

### Notes

- TPO uses a `ReplayBuffer` backed by a memmap folder in the current working directory by default.
- It computes target `q` distributions from rewards and old policy scores.
- It exposes `get_log_probs(sequences, action_masks)` for internal scoring.

## FlowRL Trainer

Verified constructor shape:

```python
flowrl.FlowRLTrainer(
    *,
    prompts=None,
    prompts_path=None,
    prompt_token_ids=None,
    tokenizer=None,
    palm,
    reward_model,
    flowrl_num_times_sample=8,
    beta=15.0,
    actor_lr=1e-4,
    actor_wd=0.0,
    actor_lora=True,
    actor_lora_r=8,
    actor_dropout=0.0,
    betas=(0.9, 0.999),
    max_norm=None,
    eps_clip=0.2,
    beta_s=0.01,
    pad_value=0.0,
    minibatch_size=16,
    epochs=1,
    kl_div_loss_weight=0.1,
    partition_function_hidden_dim=768,
    partition_function_lr=1e-4,
    accelerate_kwargs=dict(),
)
```

### Notes

- FlowRL introduces a `PartitionFunction` MLP in addition to the actor.
- It uses reward-distribution matching / trajectory-balance style training.
- The partition function is trained alongside the actor.

## Tiny Smoke Expectations

The bundled `scripts/tiny_rlhf_smoke.py` checks:

- root PPO importability;
- tiny `PaLM` + `RewardModel` construction;
- prompt-token-id trainer setup;
- optional one-step PPO training;
- generation from a 1D prompt;
- bounded smoke defaults instead of the large source defaults.
