# Post-Training Troubleshooting

Start with the failing stage's inputs, then inspect metrics, then tune hyperparameters. Avoid rerunning the whole pipeline until the immediate failure is explained.

## Quick triage table

| Symptom | Likely cause | What to inspect | Recovery |
|---|---|---|---|
| File-not-found for checkpoint | Upstream stage not run, wrong `*_ckpt`, or output path mismatch | Dry-run command, config JSON, stage matrix | Point the stage at the real upstream checkpoint or run the missing upstream stage. |
| File-not-found for data | Data prep skipped or config points to a different data directory | Stage `data_path`/`pref_path`/`prompt_path`; route to data-preparation validators | Generate/validate the required prepared file; do not fabricate empty JSONL/HDF5. |
| Shape/dimension mismatch loading checkpoint | Config model dims do not match checkpoint dims | `vocab_size`, `context_length`, `n_embed`, `n_head`, `n_blocks` | Use the config saved with the checkpoint or retrain upstream with matching dims. |
| Metrics JSONL missing | Only non-main DDP rank checked, log dir mismatch, or logger did not initialize | `log_dir`, rank-0 stdout, `use_wandb` setting | Inspect rank-0 logs; JSONL is source of truth, wandb is optional. |

## SFT failures

### Loss is unchanged or NaN

Likely causes:

- `loss_mask` is all zeros, not shifted with tokens, or marks prompt tokens instead of assistant tokens.
- Token IDs exceed vocabulary or HDF5 arrays have mismatched shapes.
- LR is too high for the current model size.

Recovery:

1. Route to `../data-preparation/SKILL.md` and validate the SFT HDF5 before training.
2. Confirm `loss_mask.sum() > 0` and there are masked tokens after the shift (`loss_mask[:, 1:]`).
3. Run a tiny `max_steps` smoke with low LR before full epochs.
4. If only dev loss rises, reduce epochs/LR or check train/dev split mismatch.

### Model learns to parrot prompts

Likely causes:

- Prompt/user/system tokens were included in `loss_mask`.
- Chat examples lack the assistant boundary expected by the repo's chat template.

Recovery:

- Validate mask alignment at example level.
- Rebuild packed SFT rows; do not try to fix this by tuning LR.

## Reward-model failures

### Preference accuracy stays near chance

Likely causes:

- Chosen/rejected rows are identical or labels are reversed.
- `max_len` truncates away the response difference.
- Dataset is too noisy or too small for a visible held-out gain.

Recovery:

1. Validate `prompt/chosen/rejected` rows and reject degenerate pairs.
2. Increase `max_len` if truncation removes answer content, while watching memory.
3. Inspect `margin`; a positive but small margin may still be plausible on noisy human preference data.
4. Avoid using the reward model for PPO if it does not beat chance on held-out pairs.

### DDP complains about unused parameters

Reason:

- The reward model uses `forward_hidden` and a reward head; the LM head may not receive gradients. This is expected for reward training.

Recovery:

- Use the repo trainer's reward-model DDP path, which enables unused-parameter handling.
- Do not force LM-head gradients for the reward objective.

## DPO / ORPO / KTO failures

### Wrong `loss_type`

Use:

- `dpo` for paired chosen/rejected preference optimization with a frozen SFT reference.
- `orpo` for reference-free training that combines chosen-response NLL with an odds-ratio preference term.
- `kto` for desirable/undesirable framing; this repo maps paired chosen/rejected rows into those labels.

Recovery:

- Rebuild the command with `scripts/build_stage_command.py dpo --loss-type ...`.
- If switching variants, use a fresh output checkpoint path so metrics are not mixed.

### Implicit rewards explode or downstream behavior degrades

Likely causes:

- LR too high, beta too high, too many epochs, or noisy preferences.
- Preference JSONL includes very long/truncated responses.

Recovery:

1. Reduce `lr`, `beta`, or epochs.
2. Inspect `r_chosen`, `r_rejected`, and margin; prefer gradual separation.
3. Compare downstream eval/chat before accepting the checkpoint.
4. For ORPO, lower `orpo_lambda` if the odds-ratio term dominates instruction retention.

## PPO failures

### KL blows up

Likely causes:

- LR too high, too many PPO epochs, low `kl_coef`, high temperature, or reward scale too strong.

Recovery:

1. Lower `lr`, `ppo_epochs`, or `clip`.
2. Raise `kl_coef` moderately.
3. Shorten `rollout_len` while debugging.
4. Confirm log-probs are recomputed in fp32 and that the reference model is frozen SFT.

### `clipfrac` is high for many iterations

Interpretation:

- Most response tokens hit the PPO clip; updates are too large for the collected rollouts.

Recovery:

- Reduce LR, `ppo_epochs`, or advantage scale.
- Increase minibatch size only if memory allows.
- Check that advantages are whitened only over response tokens.

### `value_loss` is large or exploding

Likely causes:

- Reward scale/placement is wrong, returns are noisy, or the value head is learning too fast relative to the policy.

Recovery:

1. Verify scalar task reward is added only at the final response token and KL penalty is per response token.
2. Check reward source: `rm` requires a valid reward checkpoint; `verifier` requires numeric gold answers.
3. Lower LR or `vf_coef`; inspect response lengths for cap-hitting.
4. Use a short smoke to ensure reward improves before scaling iterations.

## GRPO / RLVR failures

### `informative_groups` is zero or reward is flat

Likely causes:

- Every sampled answer in each group gets the same reward, often all wrong.
- Group size too small, temperature too low, curriculum too short, or verifier cannot parse answers.

Recovery:

1. Increase `group_size` or sampling temperature.
2. Extend arithmetic curriculum with easier prompts.
3. Inspect raw responses for `<answer>...</answer>` format and parseable numbers.
4. Reduce prompt difficulty or rollout length while debugging.
5. If all completions are correct, reduce reward saturation or move beyond warm-up.

### KL or clip fraction is unstable

Recovery:

- Lower LR, lower `grpo_epochs`, increase `kl_coef`, or reduce rollout length.
- Confirm old-policy log-probs are collected from the sampling policy and reference log-probs from frozen SFT.

## Reward hacking and answer format

Risks:

- The model learns to emit empty answer tags, repeated tags, or short strings that exploit a format bonus.
- The verifier falls back to the last number in free text, so rambling outputs may accidentally score.

Recovery:

1. Keep correctness reward dominant and format bonus bounded.
2. Inspect sampled responses, not only scalar reward.
3. Route final answer-format and GSM8K evaluation behavior to `../evaluation-chat/SKILL.md`.
4. If format collapses, refresh SFT data/mask quality before stronger RL.

## Context-cap and rollout issues

Symptoms:

- Generation fails with no room under `context_length`.
- Responses are truncated or `resp_len` always hits the cap.
- Long preference examples lose the chosen/rejected distinction.

Recovery:

- Keep `prompt_len + rollout_len <= context_length`.
- Lower `rollout_len` or truncate/clean prompts at data-prep time.
- For preference stages, set `max_len` high enough for the response signal but below memory limits.

## Log-prob recomputation precision

Invariant:

- DPO/PPO/GRPO compare differences between policy, reference, and old-policy log-probs. These must be computed with `logits.float()` even when forward passes use bf16 autocast.

Do not:

- Replace fp32 log-softmax with bf16 log-softmax for speed.
- Compare sampled top-k/top-p truncated probabilities against full-distribution recomputed probabilities.

Recovery:

- If ratios/KL are nonsensical, inspect temperature consistency and fp32 log-prob paths first.

## DDP and rank logging

Facts:

- Only rank 0 should write human-readable JSONL metrics and final checkpoints.
- Periodic eval may run on all ranks and reduce scalars; final rank-0 eval should avoid collectives after other ranks enter cleanup.
- Non-main rank logs may look quiet by design.

Recovery:

- Inspect rank-0 stdout/logs first.
- Use single-process `nproc=1` dry-runs for parser/config issues.
- Use torchrun only after paths/configs are correct.

## Wandb optional failure

Facts:

- JSONL logging is always the durable metrics path.
- If wandb import/login/network fails, training should continue with JSONL only.

Recovery:

- Set `use_wandb=false` or omit it for reproducibility.
- Use `scripts/inspect_metrics_jsonl.py` on local JSONL metrics.
- Do not treat wandb failure as a model-training failure unless the trainer itself exits.
