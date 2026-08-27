# Reward Modeling Troubleshooting

## Prompt Mask And Length Conflicts

### Symptom
- Assertion error because both `prompt_mask` and `prompt_lengths` were supplied.

### Cause
- The reward model expects one prompt-description style at a time.

### Recovery
- Use `prompt_mask` when you already know token positions.
- Use `prompt_lengths` when you only know prefix lengths.
- Do not pass both.

## Scalar Versus Binned Output Confusion

### Symptom
- The model returns sampled class ids when you expected logits.
- Cross-entropy labels were passed to a scalar reward model or vice versa.

### Cause
- `num_binned_output > 1` changes the output family.
- `sample_from_bins` defaults to inference sampling for binned rewards.

### Recovery
- Use `num_binned_output=0` for scalar rewards.
- Use `sample_from_bins=False` if you need logits from a binned model.
- Match label dtype and shape to the chosen output family.

## Shape And Pooling Errors

### Symptom
- Unexpected batch or sequence shape from the reward head.
- Pooling appears to ignore the wrong tokens.

### Cause
- `mask` controls the pooled sequence reduction.
- `prompt_mask`/`prompt_lengths` only inform the extra prompt vs response embeddings.

### Recovery
- Pass `mask` explicitly when padding or special tokens should be excluded.
- Verify that `seq.shape == (batch, seq_len)` and that labels are shaped `(batch,)`.

## ImplicitPRM Length Surprises

### Symptom
- The returned dense reward tensor is one token shorter than the input.

### Cause
- The implicit process reward compares source tokens to target tokens and therefore shifts the sequence by one.

### Recovery
- Expect `(batch, seq_len - 1)` at inference.
- If you need alignment with original tokens, shift or pad in your downstream code intentionally.

## Load Path Problems

### Symptom
- `load(path)` raises because the path does not exist.

### Cause
- `RewardModel.load` and `ImplicitPRM`-related loads use `torch.load` on an existing file.

### Recovery
- Save checkpoints with `torch.save(model.state_dict(), path)` first.
- Recreate the same backbone and LoRA scope before loading.

## When To Stop

Stop and ask for clarification if the user needs a pretrained reward checkpoint, a large human-feedback dataset, or a reward calibration workflow that is not present in the package evidence.
