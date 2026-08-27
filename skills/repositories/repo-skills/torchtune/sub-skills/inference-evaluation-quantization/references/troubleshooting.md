# Troubleshooting Inference, Evaluation, And Quantization

Use this reference when a torchtune generation, Eleuther evaluation, or quantization command fails or looks unsafe to run.

## Fast Triage

1. Confirm the command was built as `tune run <recipe> --config <config> [key=value ...]` and not by importing `recipes`.
2. Confirm the config names real checkpoint and tokenizer files.
3. Confirm the checkpointer class matches the checkpoint format.
4. Confirm optional packages (`lm-eval`, torchao-backed quantizers) are installed only when needed.
5. Confirm `device`, `dtype`, `batch_size`, `max_seq_length`, `max_new_tokens`, and KV cache settings fit available hardware.
6. Confirm `output_dir` is writable and durable enough for the workflow.

## Symptom Matrix

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError` or harness version error for `lm_eval` / `lm-eval` | EleutherAI Eval Harness optional dependency missing or unsupported | Install a compatible `lm-eval` version for the environment before running `eleuther_eval`; the recipe guards for the supported range and asks for the compatible package. |
| `Quantization is only supported for models quantized and saved with the FullModelTorchTuneCheckpointer` | Evaluating/generating with `quantizer` while using an HF/Meta checkpointer | For quantized eval/generation, use `torchtune.training.FullModelTorchTuneCheckpointer` and the torchtune-produced `.ckpt`; for dense checkpoints, set `quantizer: null`. |
| `QAT quantizers should only be used during quantization aware training` | QAT quantizer used in `generate` or `eleuther_eval` | Use `Int8DynActInt4WeightQATQuantizer` only in QAT training/quantize conversion. Use `Int8DynActInt4WeightQuantizer` for later quantized eval/generation. |
| Missing checkpoint file or key mismatch | `checkpoint_dir`, `checkpoint_files`, `model_type`, or model builder do not match files | Inspect the epoch/checkpoint directory, list full-model files exactly, and ensure `model._component_` and `checkpointer.model_type` match the checkpoint family. |
| Adapter file listed as checkpoint | LoRA output is adapter-only, not merged full weights | Do not use `adapter_model.safetensors` as `checkpointer.checkpoint_files` for these recipes. Export or rerun with merged full weights, or use a separate PEFT serving path. |
| Missing tokenizer file | Training output copied weights but tokenizer path points to the source download or wrong epoch | Point tokenizer to the copied tokenizer under the checkpoint/epoch directory when present, commonly `original/tokenizer.model`. |
| Gated model download or auth error | Checkpoint/tokenizer files were not downloaded or credentials are missing | Ask the user to provide local checkpoint/tokenizer paths or approve credentialed `tune download`; never embed tokens in configs or commands. |
| Out of memory during eval/generation | Batch size, sequence length, KV cache, dtype, or model size exceeds hardware | Reduce `batch_size`, `max_seq_length`, or `max_new_tokens`; use supported lower precision; confirm GPU memory; consider CPU only for tiny smoke checks. |
| Quantized generation compiles slowly | Quantized generation uses `torch.compile` warmup for speed measurement | Treat first run latency as expected; warn users before benchmarking and ensure compile cache/hardware are suitable. |
| Generated text ignores chat formatting | Prompt template is null or prompt fields mismatch tokenizer expectations | Confirm `tokenizer.prompt_template` and `prompt.system`/`prompt.user`; set a template only when the tokenizer supports it and the model expects chat format. |
| Eleuther chat-template error | `chat_template`/`apply_chat_template` enabled but tokenizer lacks prompt-template/render support | Disable chat templating or use a tokenizer component that exposes a prompt template or Hugging Face template rendering. |
| Output not saved where expected | `output_dir` is `./`, `/tmp`, or reused across workflows | Set a deliberate writable output path; remember `quantize` writes the important `.ckpt` there. |

## Checkpointer And Quantizer Compatibility

Dense generation/eval:

```yaml
checkpointer:
  _component_: torchtune.training.FullModelHFCheckpointer
  checkpoint_files: [model-00001-of-00002.safetensors, model-00002-of-00002.safetensors]
quantizer: null
```

Quantized generation/eval:

```yaml
checkpointer:
  _component_: torchtune.training.FullModelTorchTuneCheckpointer
  checkpoint_files: [model-00001-of-00002-8da4w.ckpt]
quantizer:
  _component_: torchtune.training.quantization.Int8DynActInt4WeightQuantizer
  groupsize: 256
```

QAT conversion:

```yaml
quantizer:
  _component_: torchtune.training.quantization.Int8DynActInt4WeightQATQuantizer
  groupsize: 256
```

Do not mix the QAT quantizer into eval/generation. Do not mix `FullModelHFCheckpointer` with quantized torchtune `.ckpt` loading.

## Prompt Formatting For Generation

The generation recipe creates torchtune messages from config:

```yaml
prompt:
  system: null
  user: "Tell me a joke."
```

It then adds an empty assistant message to kick-start generation and tokenizes with `inference=True`. If generated text is malformed:

- Verify the tokenizer component matches the model family.
- Verify `tokenizer.path` points to the tokenizer for the checkpoint.
- Set `tokenizer.prompt_template` deliberately. `null` means no custom prompt template.
- Use user/system prompt fields rather than arbitrary unsupported prompt keys.
- Keep prompt overrides shell-quoted when they contain spaces or punctuation.

## GPU, Memory, And Dtype

- `generate` is single-GPU in the stable recipe and does not support speculative decoding.
- `eleuther_eval` is single-GPU in the recipe; reduce `batch_size` for memory pressure.
- KV caches accelerate decoding but increase memory. Disable only when acceptable for the model/task; multimodal eval may force KV cache on.
- `bf16` requires hardware support; use `fp32` for CPU or minimal smoke checks.
- Quantization can still require substantial memory while loading the dense model before conversion.

## Safe Recovery Steps

When a command is failing:

1. Rebuild it with `scripts/build_inference_eval_command.py --print-notes` to inspect recipe, config, and overrides.
2. Use `tune cat <registry-config>` or read the local YAML to confirm field names.
3. Use `tune validate <local-yaml>` only after optional dependencies for referenced components are installed.
4. For missing files, list the checkpoint directory and update `checkpoint_files` exactly.
5. For adapter-only outputs, stop and request merged full weights rather than forcing adapter files into full-checkpoint fields.
6. For quantized outputs, verify the `.ckpt` exists under the quantization `output_dir` and switch eval/generation to `FullModelTorchTuneCheckpointer`.
7. For Eleuther failures, rerun with `limit=1` and a single task before full evaluation.
8. For generation failures, run with a short prompt and small `max_new_tokens` before long prompts.
