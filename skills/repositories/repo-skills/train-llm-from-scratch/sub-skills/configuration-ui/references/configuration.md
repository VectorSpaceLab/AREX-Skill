# Configuration reference

This repository uses JSON configs for the modern pretraining and post-training
stages. The legacy teaching pretraining path has its own Python constants and is
owned by [../model-pretraining/SKILL.md](../../model-pretraining/SKILL.md); do
not conflate the two systems.

## Merge order and paths

The modern loader resolves a stage config in this order, lowest to highest
precedence:

1. stage dataclass defaults from the typed config classes,
2. shared `base.json`,
3. the selected stage JSON,
4. CLI `--field` overrides.

For a normal stage file such as `configs/sft.json`, the shared base is
`configs/base.json`. For a stage JSON inside a subdirectory that contains its own
`base.json`, the sibling base wins automatically. For example,
`configs/smoke/sft.json` uses `configs/smoke/base.json`, not the full CUDA base.

JSON `null` becomes Python `None`. This is the intended way to disable nullable
fields such as `amp_dtype`. Unknown JSON keys are not fatal: the loader prints an
`ignoring unknown key` warning and drops them before constructing the dataclass.

## Full defaults versus smoke defaults

The default dataclass/base combination targets a meaningful CUDA run:

| Field group | Full CUDA default behavior |
|---|---|
| Model size | `vocab_size=50304`, `context_length=1024`, `n_embed=1024`, `n_head=16`, `n_blocks=24` |
| Runtime | `device="cuda"`, `amp_dtype="bf16"`, `seed=1337`, `compile=false` |
| Outputs | checkpoints under `/ephemeral/ckpts`, metrics under `/ephemeral/logs` |
| Optional logging | `use_wandb=false`, project `train-llm-from-scratch-posttrain` |

The smoke directory is deliberately much smaller and CPU-oriented. Its sibling
base sets `context_length=256`, `n_embed=128`, `n_head=4`, `n_blocks=2`,
`device="cpu"`, and `amp_dtype=null`. Smoke stage JSONs then reduce steps,
evaluation cadence, sequence length, or rollout counts. Smoke files are useful
for parser/config validation and short local runs, but they are not proof of the
full CUDA/bf16/DDP training path.

## Stage config fields

All modern stage dataclasses share the base/runtime fields:

| Shared field | Meaning |
|---|---|
| `vocab_size`, `context_length`, `n_embed`, `n_head`, `n_blocks` | Model architecture; checkpoints must match these dimensions. |
| `device` | Usually `cuda` for full runs; `cpu` in smoke configs. |
| `amp_dtype` | `bf16` for CUDA/H100-style full runs; `null`/`None` for CPU smoke. |
| `seed`, `compile` | Reproducibility and optional `torch.compile`. |
| `ckpt_dir`, `log_dir` | Default output roots for checkpoints and JSONL metrics. |
| `use_wandb`, `wandb_project` | Optional W&B mirror; JSONL logging is always local. |

Stage-specific fields are:

| Stage JSON | Main fields |
|---|---|
| `pretrain.json` | `train_path`, `dev_path`, `batch_size`, `grad_accum`, `train_steps`, `eval_steps`, `eval_iters`, `warmup_steps`, `lr`, `min_lr`, `weight_decay`, `grad_clip`, `out_ckpt`, `save_every` |
| `sft.json` | `pretrained_ckpt`, `data_path`, `out_ckpt`, `batch_size`, `grad_accum`, `epochs`, `max_steps`, `eval_steps`, `warmup_steps`, `lr`, `min_lr`, `weight_decay`, `grad_clip`, `save_every` |
| `reward.json` | `sft_ckpt`, `pref_path`, `out_ckpt`, `batch_size`, `epochs`, `eval_steps`, `warmup_steps`, `lr`, `weight_decay`, `grad_clip`, `max_len`, `save_every` |
| `dpo.json` | `sft_ckpt`, `pref_path`, `out_ckpt`, `loss_type`, `beta`, `orpo_lambda`, `batch_size`, `epochs`, `eval_steps`, `warmup_steps`, `lr`, `weight_decay`, `grad_clip`, `max_len`, `save_every` |
| `ppo.json` | `sft_ckpt`, `reward_ckpt`, `prompt_path`, `eval_prompt_path`, `out_ckpt`, `reward_source`, `iterations`, `prompts_per_iter`, `rollout_len`, `temperature`, `top_p`, `ppo_epochs`, `minibatch_size`, `clip`, `vf_clip`, `vf_coef`, `ent_coef`, `gamma`, `gae_lambda`, `kl_coef`, `lr`, `grad_clip`, `eval_every`, `save_every` |
| `grpo.json` | `sft_ckpt`, `prompt_path`, `eval_prompt_path`, `curriculum_path`, `curriculum_iters`, `out_ckpt`, `iterations`, `prompts_per_iter`, `group_size`, `rollout_len`, `temperature`, `top_p`, `grpo_epochs`, `clip`, `kl_coef`, `lr`, `grad_clip`, `eval_every`, `save_every` |

## CLI config interface

Every modern trainer accepts:

- `--config PATH`: choose a stage JSON. Defaults are the stage's normal JSON,
  e.g. `configs/sft.json`.
- `--print-config`: print the fully resolved config as JSON and exit. Use this
  before expensive runs.
- `--field VALUE` for every dataclass field. These overrides have the highest
  precedence and are best for one-off changes.

Examples:

```bash
python scripts/pretrain_base.py --config configs/smoke/pretrain.json --print-config
python scripts/train_sft.py --config configs/sft.json --lr 2e-5 --batch_size 8 --print-config
python scripts/train_dpo.py --config configs/dpo.json --loss_type orpo --print-config
python scripts/train_ppo.py --config configs/smoke/ppo.json --reward_source verifier --print-config
```

Boolean CLI parsing is string based. `--use_wandb true`, `--use_wandb yes`, and
`--use_wandb 1` parse as true; any other provided string parses as false. Do not
use shell-style bare `--use_wandb` because the parser expects a value.

## Stage command construction

Single-process command shape:

```bash
python scripts/train_sft.py --config configs/sft.json
```

Multi-GPU command shape:

```bash
torchrun --standalone --nproc_per_node=2 scripts/train_sft.py --config configs/sft.json
```

The Streamlit UI constructs the same shapes. When `multi_gpu` is true and the
chosen GPU count is greater than one, it uses `torchrun --standalone`; otherwise
it uses the current Python executable. Smoke mode forces one process and the
smoke config path.

Stage-to-script map used by the UI:

| Stage | Script | Full config | Smoke config | Metrics prefix |
|---|---|---|---|---|
| Pretrain | `scripts/pretrain_base.py` | `configs/pretrain.json` | `configs/smoke/pretrain.json` | `pretrain` |
| SFT | `scripts/train_sft.py` | `configs/sft.json` | `configs/smoke/sft.json` | `sft` |
| Reward | `scripts/train_reward.py` | `configs/reward.json` | `configs/smoke/reward.json` | `reward` |
| DPO/ORPO/KTO | `scripts/train_dpo.py` | `configs/dpo.json` | `configs/smoke/dpo.json` | `dpo` for normal UI lookup; trainer logs `dpo_<loss_type>` |
| PPO | `scripts/train_ppo.py` | `configs/ppo.json` | `configs/smoke/ppo.json` | `ppo` |
| GRPO | `scripts/train_grpo.py` | `configs/grpo.json` | `configs/smoke/grpo.json` | `grpo` |

For data format checks before launch, route to
[../data-preparation/SKILL.md](../../data-preparation/SKILL.md). For memory,
checkpoint, algorithm, and training interpretation, route to
[../model-pretraining/SKILL.md](../../model-pretraining/SKILL.md) or
[../post-training-rlhf/SKILL.md](../../post-training-rlhf/SKILL.md).

## Safe config summary helper

Use the bundled helper when you need a checkout-independent summary of explicit
JSON keys or want to see how a stage JSON differs from a base JSON:

```bash
python sub-skills/configuration-ui/scripts/print_config_summary.py configs/sft.json --base configs/base.json
python sub-skills/configuration-ui/scripts/print_config_summary.py configs/smoke/base.json configs/smoke/sft.json
python sub-skills/configuration-ui/scripts/print_config_summary.py --demo
```

The helper intentionally does not import the repo and does not know the typed
dataclass schema. It catches syntax errors, duplicate path input mistakes, and
explicit overrides versus a supplied base JSON, but it cannot prove that all keys
are valid dataclass fields. To validate against the actual schema, use the
trainer's `--print-config` in a real checkout.
