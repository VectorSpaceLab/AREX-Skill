# Backend Selection Reference

Use this reference to choose TRL scaling and acceleration options safely. It distills the public TRL docs and bundled examples into decision rules; do not require future agents to open source repo docs or examples at runtime.

## Decision Matrix

| Need | Prefer | Why | Watch for |
| --- | --- | --- | --- |
| Simple single-GPU training | Plain trainer or `accelerate launch` with one process | Lowest complexity | Tune `per_device_train_batch_size`, `gradient_accumulation_steps`, `max_length` first |
| Multi-GPU data parallel training | Accelerate multi-GPU config | TRL trainers are Accelerate-based and each process handles its own batch | Effective batch size is `per_device_train_batch_size × num_devices × gradient_accumulation_steps` |
| Large model does not fit | FSDP2 or DeepSpeed ZeRO | Shards model states across GPUs | Use one sharding family at a time; do not mix FSDP and DeepSpeed configs |
| Long context does not fit | Context parallelism/Ring Attention with FSDP2, or ALST/Ulysses with DeepSpeed | Splits sequence dimension across GPUs | Sequence length divisibility and backend version requirements matter |
| Online RL generation is slow | vLLM | Faster generation for supported online trainers | Separate server GPUs are safest; see [vllm-reference](vllm-reference.md) |
| Memory pressure in fine-tuning | PEFT/LoRA, QLoRA, truncation, packing, padding-free, activation checkpointing/offloading | Reduces trainable states or activations | PEFT and quantization need optional packages and may restrict kernels/loss paths |
| Training throughput/memory kernels | Liger Kernel, Kernels Hub attention implementations, FlashAttention variants | Reduces activation memory and improves speed | Requires compatible hardware, CUDA/PyTorch stack, and model support |
| Rapid hyperparameter comparison | RapidFire AI | Runs many configs in chunked schedules | Treat as optional environment/service integration; avoid if user did not ask for experiment orchestration |

## Accelerate, FSDP, and DeepSpeed

TRL trainers use Accelerate for distributed execution. Recommend `accelerate launch` once the user has a working training script and a config matching the topology.

Distilled config families from TRL examples:

- `single_gpu`: one local process; useful for smoke tests and small models.
- `multi_gpu`: data parallel training across visible GPUs.
- `fsdp1` and `fsdp2`: shard model state with PyTorch FSDP; prefer FSDP2 for newer long-context/context-parallel setups.
- `deepspeed_zero1`, `deepspeed_zero2`, `deepspeed_zero3`: progressively more aggressive ZeRO sharding. ZeRO-3 shards parameters too and is usually the most memory-saving, but has more communication/config complexity.
- `context_parallel_2gpu`: FSDP2 plus context parallelism for long sequences.
- `alst_ulysses_4gpu`: DeepSpeed-backed sequence parallelism for long context on suitable interconnects.

Selection rules:

1. Start with ordinary Accelerate multi-GPU if the model fits on each GPU and the goal is throughput.
2. Move to FSDP or DeepSpeed when model states do not fit or optimizer state dominates memory.
3. Use context/sequence parallelism only when the sequence length is the blocker, not merely because there are multiple GPUs.
4. Keep DeepSpeed and FSDP config paths mutually exclusive in launch commands.
5. For multi-node or tensor-parallel vLLM serving, call out that cluster networking/NCCL/Ray/service setup may be required and should not be attempted without user confirmation.

## Long Context Parallelism

TRL docs distinguish two long-context paths:

- Ring Attention / Context Parallelism: FSDP2 backend, `cp_size`, SDPA attention, suitable for extremely long sequences and less constrained by attention-head count.
- ALST/Ulysses: DeepSpeed backend, `sp_size`, can be faster on high-bandwidth interconnects but requires attention heads to split across ranks.

Important constraints:

- Context-parallel global length is the full sequence length before splitting. Micro sequence length is per-rank after splitting.
- Ring Attention requires sequence divisibility by `cp_size * 2`; data collation can pad to the needed multiple.
- Ulysses requires enough attention heads for `sp_size` and benefits from NVLink/InfiniBand-class interconnects.
- Do not present these as general speed toggles for ordinary short-context fine-tuning.

## Memory Reduction Stack

Use this order when diagnosing OOM unless the user already chose a backend:

1. Reduce `max_length`, `max_completion_length`, or batch size; increase `gradient_accumulation_steps` to preserve effective batch size.
2. Use mixed precision: `bf16=True` on Ampere/newer GPUs, `fp16=True` on older CUDA GPUs when bf16 is not suitable.
3. For SFT, consider packing or padding-free batching when attention implementation supports it. Padding-free should use FlashAttention 2/3 or compatible kernels to avoid batch contamination.
4. Use PEFT/LoRA when adapter training is acceptable. Use QLoRA with bitsandbytes for stronger memory reduction if CUDA/package support exists.
5. Use activation checkpointing/offloading or FSDP/DeepSpeed sharding when activations/model state remain too large.
6. Add Liger or Kernels Hub attention after checking compatibility; do not combine blindly with incompatible loss/trainer paths.

Notes from TRL docs:

- `SFTTrainer` uses chunked cross-entropy by default through `loss_type="chunked_nll"` for memory reduction on large-vocabulary models.
- Chunked NLL is not compatible with `use_liger_kernel=True`, PEFT, or VLM paths.
- Liger can reduce peak memory and improve throughput for SFT, DPO, GRPO, KTO, and GKD when `liger-kernel` is installed.

## PEFT, LoRA, and Quantization

TRL trainers support a `peft_config` argument. CLI workflows may expose `--use_peft` and LoRA flags for standard scripts, but route detailed CLI syntax to `cli-and-configs`.

Recommend PEFT when:

- The user wants to fine-tune a larger model on limited GPU memory.
- Adapter artifacts are acceptable.
- A higher LoRA learning rate than full fine-tuning is expected.

Common package decisions:

- `peft` is required for LoRA/adapter configs.
- `bitsandbytes` is required for common 4-bit/8-bit QLoRA paths.
- Quantized training is hardware and platform sensitive; check CUDA availability and package import status first.

Avoid overpromising: PEFT lowers trainable parameters and optimizer memory, but it does not remove all activation/KV-cache pressure from long sequences or online generation.

## Kernels, Liger, Unsloth, and RapidFire

Use optional accelerators deliberately:

- Kernels Hub: prefer `attn_implementation="kernels-community/flash-attn2"` or related Hub kernels when the user wants optimized attention without manually compiling FlashAttention. Requires `kernels` and compatible hardware/software.
- Liger Kernel: set `use_liger_kernel=True` in supported trainer configs after installing `liger-kernel`; works with FSDP and DeepSpeed in supported environments.
- Unsloth: useful for fast LoRA/QLoRA-style fine-tuning workflows through `FastLanguageModel`; it changes model loading flow and should be recommended only when the user accepts an Unsloth-specific path.
- RapidFire AI: useful for concurrent hyperparameter/config comparisons and dashboards. It has service, Python, CUDA, and GPU constraints; route environment/service integration details outside this sub-skill if needed.

## Command Templates to Adapt Safely

These are templates, not commands to run automatically:

```bash
accelerate launch train.py
accelerate launch --config_file path/to/accelerate_config.yaml train.py
```

```python
from peft import LoraConfig
from trl import SFTConfig, SFTTrainer

training_args = SFTConfig(bf16=True, gradient_checkpointing=True)
peft_config = LoraConfig(r=32, lora_alpha=16, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM")
trainer = SFTTrainer(model="model-id", args=training_args, train_dataset=train_dataset, peft_config=peft_config)
```

```python
from trl import SFTConfig

training_args = SFTConfig(
    max_length=2048,
    packing=True,
    use_liger_kernel=True,
)
```

Before turning templates into runnable commands, verify packages, GPU visibility, model size, expected downloads, and user permission for long-running jobs.
