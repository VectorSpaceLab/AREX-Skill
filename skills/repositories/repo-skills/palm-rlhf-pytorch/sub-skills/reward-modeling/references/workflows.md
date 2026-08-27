# Reward Modeling Workflows

## 1. Scalar Reward Model Workflow

Use this when you want one reward score per sequence.

1. Build a tiny or pretrained `PaLM` backbone.
2. Wrap it in `RewardModel(..., num_binned_output=0)` for scalar MSE training.
3. Provide token ids shaped `(batch, seq_len)`.
4. Choose exactly one prompt indicator style:
   - `prompt_mask` when you already know the token positions;
   - `prompt_lengths` when you only know the prompt prefix length per row.
5. Provide `mask` if you need to exclude padded tokens from pooling.
6. Supply float labels shaped `(batch,)`.
7. Run a backward pass and save the reward head with `reward_model.load(...)` / `state_dict` as needed.

Tiny example:

```python
import torch
from palm_rlhf_pytorch import PaLM, RewardModel

palm = PaLM(num_tokens=32, dim=16, depth=1, heads=2, dim_head=8)
reward = RewardModel(palm, num_binned_output=0)
seq = torch.randint(0, 32, (2, 8))
prompt_lengths = torch.tensor([3, 4])
labels = torch.tensor([0.5, 1.0])
loss = reward(seq, prompt_lengths=prompt_lengths, labels=labels)
loss.backward()
```

## 2. Binned Reward Workflow

Use this when the output should be a discrete rating class.

1. Set `num_binned_output` to the number of bins.
2. Leave `sample_from_bins` at its default if you want sampled class ids at inference.
3. Set `sample_from_bins=False` if you need raw logits for debugging or downstream calibration.
4. Pass integer labels shaped `(batch,)`.
5. Use the same prompt-mask rules as scalar reward training.

## 3. Implicit Process Reward Workflow

Use this when you want dense process rewards instead of a single final score.

1. Build a trainable `PaLM` model and a separate reference model.
2. Wrap the trainable model in `ImplicitPRM(model, ref_model=...)`.
3. Provide token sequences shaped `(batch, seq_len)`.
4. Train with binary labels if you have supervision.
5. Use inference output as token-level dense reward signals for later analysis or ranking.
6. Remember that the returned tensor is shifted by one token and therefore has shape `(batch, seq_len - 1)`.

## 4. Tiny Smoke Scripts

Run the bundled helper scripts for quick verification instead of rebuilding the workflow from scratch:

- `scripts/tiny_reward_smoke.py` for scalar and binned reward checks.
- `scripts/tiny_implicit_prm_smoke.py` for dense process reward checks.

These scripts are intentionally CPU-safe and use very small tensors so future agents can verify the API without running a full RLHF pipeline.
