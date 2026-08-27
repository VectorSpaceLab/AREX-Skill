# Policy Optimization Workflows

## 1. Tiny PPO RLHF Workflow

Use this when you want the standard RLHF path around a small PaLM backbone.

1. Build a tiny causal `PaLM`.
2. Build a scalar `RewardModel` around the same scale of backbone.
3. Prepare `prompt_token_ids` as a padded integer tensor.
4. Instantiate the root `RLHFTrainer` with explicit tiny hyperparameters.
5. Run one tiny training update or a construct-only smoke.
6. Optionally call `generate` on a 1D prompt to confirm the best-sequence path.

Example skeleton:

```python
import torch
from palm_rlhf_pytorch import PaLM, RewardModel, RLHFTrainer

palm = PaLM(num_tokens=32, dim=16, depth=1, heads=2, dim_head=8)
reward = RewardModel(palm, num_binned_output=0)
prompts = torch.randint(0, 32, (2, 4))
trainer = RLHFTrainer(palm=palm, reward_model=reward, prompt_token_ids=prompts)
```

## 2. GRPO Workflow

Use this when you want repeated prompt sampling and critic-free group-relative reward normalization.

1. Build `PaLM` and `RewardModel`.
2. Import `palm_rlhf_pytorch.grpo` and instantiate `grpo.RLHFTrainer`.
3. Set `grpo_num_times_sample_rewards` to a tiny value for smoke checks.
4. Use the trainer for actor-only training and compare with PPO if needed.

## 3. TPO Workflow

Use this when you want target-distribution matching with a replay buffer.

1. Build `PaLM` and `RewardModel`.
2. Import `palm_rlhf_pytorch.tpo` and instantiate `tpo.RLHFTrainer`.
3. Keep `num_times_sample_rewards`, `max_seq_len`, and `minibatch_size` tiny.
4. Run in a scratch directory if you want to avoid leaving the replay-buffer folder in a shared location.

## 4. FlowRL Workflow

Use this when you want flow-balance / reward-distribution matching.

1. Build `PaLM` and `RewardModel`.
2. Import `palm_rlhf_pytorch.flowrl` and instantiate `flowrl.FlowRLTrainer`.
3. Be aware that the partition function is a separate learned module.
4. Keep the sampled reward count and hidden size tiny for smoke checks.

## 5. Bundled Smoke Script

Run the bundled helper for ordinary verification:

```bash
python sub-skills/policy-optimization/scripts/tiny_rlhf_smoke.py --device auto --train-smoke
```

Use `--construct-only` if you only want to verify imports and object wiring.
