# Training and Decoding CLI Reference

Use module execution (`python -m wenet.bin.<tool>`) where practical so commands
work in installed/editable environments without depending on source-checkout
paths.

## Training: `wenet.bin.train`

Core arguments:

| Argument | Meaning |
|---|---|
| `--train_engine {torch_ddp,torch_fsdp,deepspeed}` | Distributed training engine. |
| `--device {cpu,npu,cuda}` | Accelerator for training. Code defaults to `cuda`. |
| `--config CONFIG` | YAML training config. Required. |
| `--model_dir MODEL_DIR` | Output directory for checkpoints and generated `train.yaml`. Required. |
| `--checkpoint CHECKPOINT` | Resume/init checkpoint. |
| `--tensorboard_dir DIR` | TensorBoard output root. |
| `--override_config KEY=VALUE` | Repeatable config override. |
| `--data_type {raw,shard}` | Dataset input layout. |
| `--train_data FILE [FILE ...]` | Training data list(s). Required. |
| `--cv_data FILE` | Cross-validation data list. Required. |
| `--num_workers N`, `--prefetch N`, `--pin_memory` | DataLoader controls. |
| `--ddp.dist_backend {nccl,gloo,hccl}` | Distributed backend. Use `nccl` for CUDA when healthy, `hccl` for NPU, `gloo` for CPU/fallback debugging. |
| `--use_amp`, `--dtype {fp32,fp16,bf16}` | Mixed precision controls. |
| `--use_lora`, `--lora_*` | LoRA fine-tuning controls. |

DeepSpeed adds its own `--deepspeed` and `--deepspeed_config`-style arguments
through the DeepSpeed parser. Keep the DeepSpeed JSON consistent with WeNet's
training config for batch size, accumulation, clipping, and logging.

## Recognition: `wenet.bin.recognize`

Core arguments:

| Argument | Meaning |
|---|---|
| `--config CONFIG` | `train.yaml` used to initialize model/tokenizer/features. Required. |
| `--test_data FILE` | Evaluation `data.list`. Required. |
| `--data_type {raw,shard}` | Test data layout. |
| `--checkpoint FILE` | Model checkpoint. Required. |
| `--result_dir DIR` | Output directory. Required. |
| `--modes MODE [MODE ...]` | One or more decoding modes. |
| `--device {cpu,npu,cuda}` / `--gpu ID` | Device selection. `--gpu` sets CUDA compatibility behavior. |
| `--dtype {fp16,fp32,bf16}` | Compute dtype. |
| `--beam_size`, `--length_penalty`, `--blank_penalty` | Search controls. |
| `--ctc_weight`, `--reverse_weight`, `--attn_weight`, `--transducer_weight` | Rescoring weights. |
| `--decoding_chunk_size`, `--num_decoding_left_chunks`, `--simulate_streaming` | Streaming/non-streaming controls. |
| `--word`, `--hlg`, `--lm_scale`, `--decoder_scale`, `--r_decoder_scale` | HLG/k2 decoding inputs and scales. |
| `--context_bias_mode`, `--context_list_path`, `--context_graph_score` | Context biasing. |
| `--use_lora`, `--lora_ckpt_path` | LoRA checkpoint use. |

Recognition writes one `text` file per mode under `result_dir/<mode>/text`.

## Checkpoint averaging: `wenet.bin.average_model`

Typical command:

```bash
python -m wenet.bin.average_model \
  --dst_model exp/model/avg_30.pt \
  --src_path exp/model --num 30 --val_best
```

Use after enough checkpoints exist and before recognition/export.

## Alignment: `wenet.bin.alignment`

Use forced alignment only when you have matching audio, transcript labels,
model config, and checkpoint. If the task is a single audio package-level
alignment request, first check whether the package CLI `wenet --align --label`
is enough; otherwise use the experiment-level alignment entry point with the
same config/checkpoint discipline as recognition.

## Scoring helper

The bundled `score_text.py` is for small reference/hypothesis text files. It is
not a replacement for a recipe's full normalization, but it is useful for
assertion-backed checks and quick debugging.
