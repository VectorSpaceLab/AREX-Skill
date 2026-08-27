# DeepSpeed Configuration

Baichuan2 fine-tuning uses Hugging Face `TrainingArguments` together with a DeepSpeed JSON config. The documented setup is ZeRO stage 3 with automatic batch-size values and bf16 controlled by the trainer flag.

## Default config

Use the bundled trainer to write this config:

```bash
python scripts/train_supervised.py \
  --dry_run True \
  --write_deepspeed_config /work/baichuan2_sft/ds_config.json \
  --data_path /data/baichuan2_sft.json \
  --model_name_or_path baichuan-inc/Baichuan2-7B-Base \
  --output_dir /work/baichuan2_sft/output
```

Equivalent JSON:

```json
{
  "train_batch_size": "auto",
  "train_micro_batch_size_per_gpu": "auto",
  "gradient_accumulation_steps": "auto",
  "gradient_clipping": 1.0,
  "bf16": {
    "enabled": "auto"
  },
  "zero_optimization": {
    "stage": 3,
    "overlap_comm": true,
    "stage3_gather_16bit_weights_on_model_save": true
  },
  "flops_profiler": {
    "enabled": false,
    "profile_step": 1,
    "module_depth": -1,
    "top_modules": 1,
    "detailed": true,
    "output_file": null
  }
}
```

## Field interpretation

| Field | Meaning | Practical effect |
| --- | --- | --- |
| `train_batch_size: auto` | Delegate global batch size to Hugging Face arguments. | Uses `world_size * per_device_train_batch_size * gradient_accumulation_steps`. |
| `train_micro_batch_size_per_gpu: auto` | Delegate per-GPU micro-batch to `per_device_train_batch_size`. | Change the CLI flag rather than hard-coding here. |
| `gradient_accumulation_steps: auto` | Delegate accumulation to the trainer flag. | Increase this when reducing per-device batch size for VRAM. |
| `gradient_clipping: 1.0` | Clip gradient norm. | Matches the documented `--max_grad_norm 1.0` setting. |
| `bf16.enabled: auto` | Follow `--bf16 True/False`. | Requires hardware and torch support for bf16. A100-class GPUs support it. |
| `zero_optimization.stage: 3` | Partition optimizer states, gradients, and parameters. | Enables fitting a 7B model across multiple GPUs but increases communication and save complexity. |
| `overlap_comm: true` | Overlap communication with computation. | Usually improves throughput; can expose networking issues on multi-node jobs. |
| `stage3_gather_16bit_weights_on_model_save: true` | Gather full 16-bit weights during save. | Makes saved full fine-tuned checkpoints easier to load after ZeRO-3. |
| `flops_profiler.enabled: false` | Disable DeepSpeed FLOPs profiler. | Avoids profiler overhead during normal fine-tuning. |

## Batch-size arithmetic

Effective global batch size:

```text
effective_batch = num_nodes * gpus_per_node * per_device_train_batch_size * gradient_accumulation_steps
```

The documented example uses `per_device_train_batch_size=16` and `gradient_accumulation_steps=1`. This is aggressive for full-parameter 7B training unless enough GPU memory is available. If out-of-memory occurs:

1. lower `per_device_train_batch_size`;
2. increase `gradient_accumulation_steps` to retain a similar effective batch;
3. keep `model_max_length` at 512 until you have memory headroom;
4. use LoRA if full-parameter tuning remains too expensive.

## Hostfile relationship

The DeepSpeed config does not list machines. Multi-machine placement comes from the DeepSpeed hostfile passed to the launcher:

```text
node-a slots=8
node-b slots=8
```

The launcher combines hostfile slots with the JSON config and trainer arguments. Keep every node on a compatible Python environment, package set, model cache policy, and filesystem or data access strategy.

## Saving and loading notes

- With ZeRO-3 full fine-tuning, keep `stage3_gather_16bit_weights_on_model_save=true` if you expect `AutoModelForCausalLM.from_pretrained(output_dir, trust_remote_code=True)` to work directly.
- With LoRA, the output directory stores adapter-related files; load with PEFT's `AutoPeftModelForCausalLM`.
- Checkpoint directories can be large. Ensure the output filesystem has enough free space before a multi-epoch run.

## When to modify this config

Modify only with a clear reason:

- Set `bf16.enabled` explicitly only when trainer auto-detection behaves incorrectly.
- Disable `overlap_comm` if multi-node networking or NCCL instability points to communication overlap as the cause.
- Consider ZeRO-2 only when you have sufficient memory and want simpler saves; do not silently change stage if reproducing the documented workflow.
- Add offload settings only after measuring local CPU/NVMe bandwidth; offload can make runs much slower.
