# Policy Optimization Troubleshooting

## Prompt Input Assertions

### Symptom
- The trainer raises an assertion about prompt inputs.

### Cause
- The trainer accepts exactly one of `prompts`, `prompts_path`, or `prompt_token_ids`.

### Recovery
- Choose one input style only.
- If you are using raw strings, pass a tokenizer that produces padded token-id tensors.

## Large Defaults

### Symptom
- A supposedly small smoke run takes too long or uses too much memory.

### Cause
- The source trainers are configured for large episode counts, timesteps, and sequence lengths.

### Recovery
- Override the defaults explicitly in the bundled smoke script or in your own tiny call.
- Keep `num_episodes`, `max_timesteps`, `update_timesteps`, `max_seq_len`, and `minibatch_size` small.

## `max_norm` Branch Failures

### Symptom
- A trainer fails when `max_norm` is enabled.

### Cause
- The source code references `self.accelerator` in some gradient clipping branches, while the trainer object stores the accelerator as `self.accelerate`.

### Recovery
- Leave `max_norm=None` for smoke checks.
- Patch the trainer before using that branch in a longer run.

## TPO Replay Buffer Side Effects

### Symptom
- A run leaves a memmap replay-buffer folder behind or writes to an unexpected location.

### Cause
- TPO uses a `ReplayBuffer` folder in the current working directory by default.

### Recovery
- Run TPO in a scratch directory or clean the folder afterward.
- Mention this side effect in any reproducibility notes.

## GRPO Generate Caution

### Symptom
- The GRPO trainer's `generate` helper misbehaves or raises when asked to sample a sequence.

### Cause
- In the inspected source, the GRPO trainer's `generate` path appears to expect more returned values than the actor currently yields.

### Recovery
- Use the smoke script for import and construction checks first.
- Prefer the trainer-selection guidance and avoid trusting a long GRPO generation workflow until the source has been patched or rechecked.

## FlowRL Partition-Function Confusion

### Symptom
- The trainer appears to need an extra model or fails when prompt embeddings are shaped unexpectedly.

### Cause
- FlowRL learns a partition function in addition to the actor and uses prompt embeddings inside that module.

### Recovery
- Keep the prompt tensor shape small and explicit.
- Read the trainer-selection guide before choosing FlowRL over PPO.

## Source Example Is Not A Smoke Test

### Symptom
- `examples.py` fails or takes longer than expected.

### Cause
- The example imports `lion_pytorch` and uses expensive defaults for a real training-style path.

### Recovery
- Use the bundled tiny smoke script instead.
- Treat the source example as reference-only unless you explicitly add the missing dependency and accept the extra cost.
