# Reward Modeling API Reference

This reference covers the reward-model and implicit process reward APIs that future agents need most often.

## Public Imports

```python
from palm_rlhf_pytorch import RewardModel, ImplicitPRM
```

## RewardModel

Verified constructor shape:

```python
RewardModel(
    palm,
    dropout=0.1,
    num_binned_output=0.0,
    use_lora=True,
    lora_r=8,
    reward_lora_scope='reward',
    sample_from_bins=None,
    sample_temperature=1.0,
)
```

### Constructor Notes

| Argument | Meaning |
| --- | --- |
| `palm` | Backbone `PaLM` model. The reward model deep-copies it internally. |
| `dropout` | Dropout probability applied to the copied backbone. |
| `num_binned_output` | If greater than 1, the model predicts class bins instead of a scalar. |
| `use_lora` | Adds a named reward LoRA scope to the copied backbone when true. |
| `lora_r` | LoRA rank used for the reward scope. |
| `reward_lora_scope` | Name of the reward adapter scope. |
| `sample_from_bins` | If `None`, inference samples class ids when binned output is enabled. |
| `sample_temperature` | Gumbel sampling temperature for binned inference. |

### Forward Signature

```python
RewardModel.forward(
    x,
    mask=None,
    prompt_mask=None,
    prompt_lengths=None,
    labels=None,
    disable_lora=False,
)
```

### Forward Semantics

- `x` is a token-id tensor shaped `(batch, seq_len)`.
- Pass **either** `prompt_mask` **or** `prompt_lengths`, not both.
- `prompt_mask` injects different prompt and response embeddings before the copied backbone.
- `mask` controls pooled averaging over the sequence.
- If `labels` is omitted, the method returns predictions.
- If `labels` is supplied and `num_binned_output <= 1`, the method returns scalar MSE loss.
- If `labels` is supplied and `num_binned_output > 1`, the method returns cross-entropy loss over bins.
- When `num_binned_output > 1` and `sample_from_bins` is truthy, inference returns sampled class ids, not raw logits.

### Typical Shapes

- Scalar inference: `(batch,)`
- Binned logits before sampling: `(batch, num_binned_output)`
- Binned sampled ids at inference: `(batch,)`

### Load and Finetune

```python
reward_model.load(path)
params = reward_model.finetune_parameters()
```

`finetune_parameters()` returns the trainable reward head plus the copied backbone's active LoRA parameters when a reward scope exists.

## ImplicitPRM

Verified constructor shape:

```python
ImplicitPRM(model, ref_model=None, beta=0.1)
```

### Forward Signature

```python
ImplicitPRM.forward(seq, labels=None)
```

### Forward Semantics

- `seq` is a token-id tensor shaped `(batch, seq_len)`.
- The module compares a trainable model against a frozen reference model.
- It computes token-level implicit rewards from the difference between log-probabilities under the model and reference model.
- Inference returns a dense tensor shaped `(batch, seq_len - 1)` because the target sequence is shifted by one token.
- If `labels` is supplied, the module uses the binary classification loss described in the source comments.

## Shape And Mask Examples

Scalar reward training with prompt lengths:

```python
reward_model = RewardModel(palm, num_binned_output=0)
loss = reward_model(tokens, prompt_lengths=torch.tensor([4, 5]), labels=torch.tensor([0.5, 1.0]))
```

Binned inference with raw logits preserved:

```python
reward_model = RewardModel(palm, num_binned_output=5, sample_from_bins=False)
logits = reward_model(tokens, prompt_mask=prompt_mask)
```

Implicit process reward inference:

```python
prm = ImplicitPRM(palm)
rewards = prm(tokens)
# rewards.shape == (batch, seq_len - 1)
```

## Tiny Smoke Expectations

The bundled scripts check:

- reward-model importability;
- scalar loss/backward;
- binned loss/backward;
- prompt-mask or prompt-length handling;
- optional logits-mode inference;
- implicit process reward loss/backward;
- implicit process reward dense output shape.
