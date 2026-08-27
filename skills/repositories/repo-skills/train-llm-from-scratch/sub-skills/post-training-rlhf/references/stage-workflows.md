# Post-Training Stage Workflows

This guide assumes data preparation and base pretraining are already complete. It focuses on post-training launch order, dependencies, config fields, outputs, metrics, and safe recovery. Use the bundled command builders to print commands before running training.

## Dependency graph

```text
base_pretrained.pt
  -> SFT -> sft.pt
      -> Reward Model -> reward.pt -> PPO with reward_source=rm (optional)
      -> DPO / ORPO / KTO -> dpo.pt or variant checkpoint
      -> PPO with reward_source=verifier -> ppo.pt
      -> GRPO / RLVR -> grpo.pt
```

Recommended learning/debug sequence:

1. Run SFT first and confirm masked dev loss moves.
2. Train reward model if PPO will use `reward_source=rm`; verifier-only PPO can skip reward model but the full pipeline usually keeps it.
3. Run DPO with `loss_type=dpo` first; try ORPO or KTO only when the task calls for their behavior.
4. Run PPO with conservative LR/KL settings and inspect `KL_ref`, `clipfrac`, and `value_loss`.
5. Run GRPO with curriculum/group settings that keep `informative_groups` non-zero.
6. Route final GSM8K table evaluation and chat to `../evaluation-chat/SKILL.md`.

## Command helpers

Print a single stage command:

```bash
python scripts/build_stage_command.py sft --nproc 2 --config configs/sft.json \
  --pretrained-ckpt "$CKPT_DIR/base_pretrained.pt" \
  --data-path "$DATA_DIR/sft_packed.h5" \
  --out-ckpt "$CKPT_DIR/sft.pt"
```

Print a full dry-run sequence:

```bash
python scripts/plan_posttraining_pipeline.py --nproc 2 \
  --ckpt-dir "$CKPT_DIR" --data-dir "$DATA_DIR" --log-dir "$LOG_DIR"
```

Add arbitrary config overrides with repeated `--extra=...` tokens:

```bash
python scripts/build_stage_command.py ppo --nproc 1 --reward-source verifier \
  --extra=--iterations --extra=20 --extra=--rollout_len --extra=96
```

The helpers only print commands. Review paths, GPU count, and config overrides before copying output into a shell.

## Stage matrix

| Stage | Trainer entry point | Required inputs | Output | Key config fields | Main metrics | Recovery focus |
|---|---|---|---|---|---|---|
| SFT | `scripts/train_sft.py` | Base checkpoint; packed SFT HDF5 with `tokens` and `loss_mask`; optional dev HDF5 | SFT policy checkpoint | `pretrained_ckpt`, `data_path`, `out_ckpt`, `batch_size`, `grad_accum`, `epochs`, `max_steps`, `lr`, `min_lr`, `grad_clip`, `eval_steps`, `save_every` | `train_loss`, `ppl`, `dev_loss`, `dev_ppl` | Verify non-empty/shift-aligned `loss_mask`, checkpoint dims, and dev path. Lower LR or reduce epochs if dev loss rises. |
| Reward | `scripts/train_reward.py` | SFT checkpoint; preference JSONL with `prompt/chosen/rejected` | Reward-model checkpoint | `sft_ckpt`, `pref_path`, `out_ckpt`, `batch_size`, `epochs`, `lr`, `max_len`, `grad_clip`, `eval_steps` | `loss`, `train_acc`, `test_acc`, `margin` | Validate preference pairs; check chosen/rejected not identical; increase data quality before tuning if accuracy stays at chance. |
| DPO/ORPO/KTO | `scripts/train_dpo.py` | SFT checkpoint; preference JSONL | Preference-aligned policy checkpoint | `sft_ckpt`, `pref_path`, `out_ckpt`, `loss_type`, `beta`, `orpo_lambda`, `batch_size`, `epochs`, `lr`, `max_len` | `loss`, `acc`, `r_chosen`, `r_rejected`, `test_acc`, `margin` | Use `dpo` for paired reference-anchored preference optimization, `orpo` for reference-free SFT+alignment, `kto` for desirable/undesirable framing. Keep LR gentle. |
| PPO | `scripts/train_ppo.py` | SFT checkpoint; RL prompt JSONL; eval prompt JSONL; reward checkpoint only when `reward_source=rm` | PPO policy checkpoint | `sft_ckpt`, `reward_ckpt`, `prompt_path`, `eval_prompt_path`, `out_ckpt`, `reward_source`, `iterations`, `prompts_per_iter`, `rollout_len`, `temperature`, `top_p`, `ppo_epochs`, `minibatch_size`, `clip`, `vf_clip`, `vf_coef`, `gamma`, `gae_lambda`, `kl_coef`, `lr` | `reward`, `KL_ref`, `policy_loss`, `value_loss`, `clipfrac`, `resp_len`, periodic GSM8K accuracy | If KL or clipfrac blows up, lower LR/epochs or raise `kl_coef`. If value loss explodes, inspect reward scale and returns. |
| GRPO/RLVR | `scripts/train_grpo.py` | SFT checkpoint; RL prompt JSONL; eval prompt JSONL; arithmetic curriculum JSONL if curriculum enabled | GRPO policy checkpoint | `sft_ckpt`, `prompt_path`, `eval_prompt_path`, `curriculum_path`, `curriculum_iters`, `out_ckpt`, `iterations`, `prompts_per_iter`, `group_size`, `rollout_len`, `temperature`, `top_p`, `grpo_epochs`, `clip`, `kl_coef`, `lr` | `reward`, `informative_groups`, `loss`, `KL`, `clipfrac`, `resp_len`, periodic GSM8K accuracy | If informative groups are zero, increase temperature/group size, extend curriculum, inspect verifier format, or reduce prompt difficulty. |

## Stage-specific command recipes

### SFT

```bash
python scripts/build_stage_command.py sft --nproc 2 \
  --pretrained-ckpt "$CKPT_DIR/base_pretrained.pt" \
  --data-path "$DATA_DIR/sft_packed.h5" \
  --out-ckpt "$CKPT_DIR/sft.pt" \
  --extra=--lr --extra=1e-5
```

Before launch:

- Data-preparation should confirm `tokens.shape == loss_mask.shape` and `loss_mask.sum() > 0`.
- Check base checkpoint architecture matches config fields.
- Use `max_steps` for a tiny smoke; use full `epochs` for production.

Expected output:

- Checkpoint saved at `out_ckpt` with stage metadata.
- JSONL metrics file under `log_dir` with masked train/dev losses.

### Reward model

```bash
python scripts/build_stage_command.py reward --nproc 2 \
  --sft-ckpt "$CKPT_DIR/sft.pt" \
  --pref-path "$DATA_DIR/preferences.jsonl" \
  --out-ckpt "$CKPT_DIR/reward.pt"
```

Before launch:

- Validate each row has prompt/chosen/rejected strings.
- Check `max_len` is not silently truncating away the answer signal.
- In DDP, the reward model intentionally has unused LM-head parameters; this is expected.

Expected output:

- Reward checkpoint with reward-head weights.
- Metrics containing preference accuracy and reward margin.

### DPO / ORPO / KTO

```bash
python scripts/build_stage_command.py dpo --nproc 2 --loss-type dpo \
  --sft-ckpt "$CKPT_DIR/sft.pt" \
  --pref-path "$DATA_DIR/preferences.jsonl" \
  --out-ckpt "$CKPT_DIR/dpo.pt"
```

Variant examples:

```bash
python scripts/build_stage_command.py dpo --loss-type orpo --orpo-lambda 1.0
python scripts/build_stage_command.py dpo --loss-type kto --beta 0.1
```

Before launch:

- Use `dpo` when paired chosen/rejected preferences and a frozen SFT reference are desired.
- Use `orpo` only when reference-free behavior is intentional.
- Use `kto` for desirable/undesirable framing; in this repo, paired rows are split into those labels.

Expected output:

- Policy checkpoint from the selected preference objective.
- Implicit reward accuracy/margin metrics.

### PPO

```bash
python scripts/build_stage_command.py ppo --nproc 2 --reward-source verifier \
  --sft-ckpt "$CKPT_DIR/sft.pt" \
  --prompt-path "$DATA_DIR/rl_prompts_train.jsonl" \
  --eval-prompt-path "$DATA_DIR/rl_prompts_test.jsonl" \
  --out-ckpt "$CKPT_DIR/ppo.pt"
```

Reward-model PPO:

```bash
python scripts/build_stage_command.py ppo --reward-source rm \
  --sft-ckpt "$CKPT_DIR/sft.pt" \
  --reward-ckpt "$CKPT_DIR/reward.pt"
```

Before launch:

- For `reward_source=rm`, confirm `reward_ckpt` exists and is a reward-model checkpoint, not a bare policy checkpoint.
- For verifier reward, confirm prompts include numeric gold answers and the SFT policy emits the expected answer tags often enough to receive signal.
- Keep first runs short (`iterations`, `prompts_per_iter`, `rollout_len`) and inspect metrics before scaling.

Expected output:

- PPO policy checkpoint, not a value-head checkpoint for evaluation; the saved policy should be loadable as a backbone.
- Metrics with reward, `KL_ref`, policy/value loss, clip fraction, and response length.

### GRPO / RLVR

```bash
python scripts/build_stage_command.py grpo --nproc 2 --group-size 8 \
  --sft-ckpt "$CKPT_DIR/sft.pt" \
  --prompt-path "$DATA_DIR/rl_prompts_train.jsonl" \
  --eval-prompt-path "$DATA_DIR/rl_prompts_test.jsonl" \
  --out-ckpt "$CKPT_DIR/grpo.pt"
```

Before launch:

- Confirm `prompts_per_iter * group_size` fits memory and rollout time.
- Use an arithmetic curriculum until the model gets non-zero reward variance.
- Keep `informative_groups` above zero; zero-variance groups provide no gradient.

Expected output:

- GRPO policy checkpoint.
- Metrics with reward, informative group fraction, KL, clip fraction, and response length.

## Metrics inspection

Use the read-only JSONL inspector on any stage metrics file:

```bash
python scripts/inspect_metrics_jsonl.py "$LOG_DIR/sft_metrics.jsonl"
python scripts/inspect_metrics_jsonl.py --demo
```

Interpretation shortcuts:

- SFT: `dev_loss` should be stable or falling; `train_loss` alone is not enough.
- Reward: `test_acc` above chance and positive `margin` matter more than train accuracy.
- DPO: `acc`/margin should rise gently; large implicit reward magnitudes can indicate drift.
- PPO: `reward` should rise while `KL_ref` and `clipfrac` stay bounded.
- GRPO: reward only matters when `informative_groups` is non-zero.

## Recovery sequencing

1. Do not jump directly to larger models or longer training when a stage fails.
2. Rebuild the dry-run command and compare it with the intended config fields.
3. Inspect metrics and the upstream checkpoint/data dependency.
4. Route to data-preparation for schema/mask/JSONL failures.
5. Route to model-pretraining for architecture/checkpoint-dimension mismatch.
6. Route to evaluation-chat for answer parsing, GSM8K table, and chat behavior.
