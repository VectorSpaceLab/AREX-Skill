# ModelOpt post-training workflows

## Surface map

ModelOpt examples cover operations such as:

- quantization and calibration
- pruning
- distillation and Eagle-style heads
- export
- generation and offline feature extraction
- MMLU/validation evaluation
- generation server wrappers

Treat each operation as a pipeline with explicit input/output checkpoints:

```text
Megatron checkpoint -> optional calibration/data step -> ModelOpt transform -> validated checkpoint/export -> generation/evaluation
```

## Preflight

- Install `nvidia-modelopt[torch]` through a supported dev/container path.
- Confirm Torch/CUDA/TransformerEngine ABI compatibility.
- Verify the model family and checkpoint format are supported by the selected ModelOpt operation.
- Decide whether the output must stay in Megatron format, become Hugging Face/TensorRT-LLM format, or serve from a transformed checkpoint.
- Use a small checkpoint or `--help` first; quantization/pruning may mutate or write large artifacts.

## Common failure categories

- missing `modelopt` import
- checkpoint/model args mismatch
- unsupported quantization recipe or precision on GPU
- calibration data/tokenizer mismatch
- output path not writable or format not accepted by the next tool
- memory exhaustion during calibration/export

Route model format questions to checkpointing-and-conversion and GPU/extra installation questions to install-and-environment.
