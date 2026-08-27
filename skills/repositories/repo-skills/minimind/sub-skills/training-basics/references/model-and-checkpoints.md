# MiniMind model knobs and checkpoints

This reference summarizes the MiniMind configuration and checkpoint behavior needed for tokenizer, pretraining, SFT, and LoRA work.

## `MiniMindConfig` training knobs

| Knob | Default | Training meaning |
|---|---:|---|
| `hidden_size` | `768` | Main model width. Weight file names include this value. Keep divisible by `num_attention_heads` unless `head_dim` is explicitly set. |
| `num_hidden_layers` | `8` | Transformer block count. Smaller values are useful for tiny smokes; the main branch default is shallow and wide for small-model efficiency. |
| `use_moe` | `false` | Switches block MLPs from dense feed-forward to MoE feed-forward. Adds router auxiliary loss during training. Weight names gain `_moe`. |
| `dropout` | `0.0` | Applied in attention residuals and embeddings. |
| `vocab_size` | `6400` | Must match the tokenizer for real training weights. Tiny smokes may use smaller random vocabularies only when not loading real weights. |
| `bos_token_id` / `eos_token_id` | `1` / `2` | Match `<|im_start|>` and `<|im_end|>`. |
| `flash_attn` | `true` | Uses PyTorch scaled-dot-product attention when available and masks allow it; otherwise falls back to manual attention. |
| `num_attention_heads` | `8` | Query head count. |
| `num_key_value_heads` | `4` | Key/value head count for grouped-query attention. `num_attention_heads` must be divisible by this. |
| `head_dim` | `hidden_size / num_attention_heads` | Per-head dimension. RoPE buffers are built with this size. |
| `hidden_act` | `silu` | MLP activation from Transformers activation registry. |
| `intermediate_size` | `ceil(hidden_size*pi/64)*64` | Dense MLP width. |
| `max_position_embeddings` | `32768` | Size of precomputed RoPE buffers; separate from training `max_seq_len`. |
| `rope_theta` | `1e6` | Base frequency for RoPE. |
| `tie_word_embeddings` | `true` | Shares embedding and LM head weights. |
| `inference_rope_scaling` | `false` | If true, builds a YaRN `rope_scaling` config. Normally an inference/serving decision, not a training fix. |

MoE-specific knobs used only when `use_moe=true`:

| Knob | Default | Meaning |
|---|---:|---|
| `num_experts` | `4` | Routed expert count. |
| `num_experts_per_tok` | `1` | Top-k active experts per token. |
| `moe_intermediate_size` | same as `intermediate_size` | Per-expert MLP width. |
| `norm_topk_prob` | `true` | Normalizes selected expert probabilities. |
| `router_aux_loss_coef` | `5e-4` | Router load-balancing auxiliary loss coefficient. |

MoE is useful for exploring active-parameter trade-offs, but training is slower than dense at similar active size because tokens are bucketed by expert in native PyTorch. Treat MoE speed claims as hardware- and implementation-dependent.

## RoPE and YaRN context

Training scripts control truncation with `--max_seq_len`; this is the actual token length fed to the model. `max_position_embeddings` only sets how far RoPE buffers are available.

When `inference_rope_scaling=true`, MiniMind creates a YaRN-style scaling record:

```json
{
  "type": "yarn",
  "factor": 16,
  "original_max_position_embeddings": 2048,
  "beta_fast": 32,
  "beta_slow": 1,
  "attention_factor": 1.0
}
```

Use YaRN as an inference/long-context extrapolation option. If a training task needs longer supervised contexts, prefer preparing longer SFT samples and setting an appropriate `--max_seq_len`; do not assume inference extrapolation replaces training coverage.

## `MiniMindForCausalLM` training behavior

- The model is a Transformers `PreTrainedModel` plus `GenerationMixin` wrapper around the native MiniMind backbone.
- Forward pass returns causal LM loss, MoE auxiliary loss, logits, past key values, and hidden states.
- Label loss is shifted internally and uses `ignore_index=-100`; dataset classes are responsible for setting `-100` on pads and non-assistant tokens.
- Training scripts add `res.loss + res.aux_loss`, then divide by `--accumulation_steps` before backward.
- The custom `generate` method supports cache, temperature, top-p, top-k, repetition penalty, and deterministic generation with `do_sample=false`.

## Weight and checkpoint names

Main output weights are saved under the configured output directory, defaulting to `../out` from the training entrypoint directory:

| Stage | Dense output | MoE output |
|---|---|---|
| Pretraining | `pretrain_{hidden_size}.pth` | `pretrain_{hidden_size}_moe.pth` |
| Full SFT | `full_sft_{hidden_size}.pth` | `full_sft_{hidden_size}_moe.pth` |
| LoRA | `{lora_name}_{hidden_size}.pth` | `{lora_name}_{hidden_size}_moe.pth` |

Complete resume checkpoints are saved under the checkpoint directory, defaulting to `../checkpoints` from the training entrypoint directory:

```text
{weight_or_lora_name}_{hidden_size}{_moe}_resume.pth
```

Resume checkpoint content includes:

- model state dict saved in half precision on CPU;
- optimizer state;
- epoch and step;
- saved world size;
- logging run id when available;
- scaler state for mixed precision training when supplied.

The checkpoint helper also writes a non-resume model-only checkpoint beside the resume file. Training scripts separately write the stage output weight into the output directory.

## Loading and resume rules

`init_model` constructs `MiniMindForCausalLM`, loads the tokenizer from the local tokenizer directory, and optionally loads weights from the output directory.

- `--from_weight none`: start from random model weights.
- `--from_weight pretrain`: load `pretrain_{hidden_size}{_moe}.pth` before SFT.
- `--from_weight full_sft`: load `full_sft_{hidden_size}{_moe}.pth` before LoRA.
- Any custom `--from_weight <prefix>` expects `<prefix>_{hidden_size}{_moe}.pth` in the output directory.

`--from_resume 1` checks the checkpoint directory for the resume file keyed by the current stage prefix, `hidden_size`, and `use_moe` value. To resume reliably, keep these values aligned with the interrupted run:

- pretrain/full SFT: `--save_weight`, `--hidden_size`, `--use_moe`;
- LoRA: `--lora_name`, `--hidden_size`, `--use_moe`.

If the saved world size differs from the current DDP world size, MiniMind scales the saved step as:

```text
new_step = saved_step * saved_world_size // current_world_size
```

This preserves approximate sample progress, but it can still change exact batch ordering. For high-stakes runs, record the old and new GPU counts in the experiment log.

## DDP initialization

The training utilities enable DDP only when `RANK` is present in the environment. `torchrun` sets `RANK`, `LOCAL_RANK`, and world-size variables. DDP uses the `nccl` backend and sets the CUDA device to `LOCAL_RANK`.

Single-process runs do not initialize distributed training and keep the user-selected `--device`.

## LoRA implementation details

MiniMind's LoRA implementation is hand-written and does not rely on a PEFT wrapper.

Behavior:

- `apply_lora(model, rank=16)` attaches a `LoRA(A, B)` branch only to square `nn.Linear` modules where `in_features == out_features`.
- Matrix `A` is initialized from a normal distribution with standard deviation `0.02`; matrix `B` starts at zero, so initial behavior matches the base model.
- The implementation monkey-patches each selected module's `forward` to return `original(x) + lora(x)`.
- LoRA training freezes every parameter whose name does not contain `lora` and optimizes only LoRA parameters.
- `save_lora` stores only LoRA tensors in half precision on CPU.
- `load_lora` strips a leading `module.` prefix when loading DDP-saved weights.
- `merge_lora` loads LoRA weights, adds `B @ A` into each adapted base linear weight, excludes `.lora.` tensors, and saves a full merged state dict.

Compile note: LoRA monkey-patching is incompatible with `torch.compile` in the native training route. The LoRA trainer turns `--use_compile 1` back off and logs a warning. Keep `--use_compile 0` for LoRA unless the implementation changes.

Merged LoRA export, serving, API use, and local chat are outside this sub-skill; hand those tasks to `inference-serving`.
