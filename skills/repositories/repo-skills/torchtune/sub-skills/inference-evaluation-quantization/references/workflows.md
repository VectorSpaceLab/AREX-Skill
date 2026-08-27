# Inference, Evaluation, And Quantization Workflows

This reference covers torchtune workflows after checkpoints already exist. Prefer local copied configs over editing registry configs in place, and keep recipe execution behind explicit user approval.

## Recipe Entry Points

| Workflow | Registry recipe | Typical config | Main purpose | Runs model work? |
| --- | --- | --- | --- | --- |
| Generate text | `generate` | `generation` or copied YAML | Single-device prompt generation from a checkpoint | Yes |
| Eleuther evaluation | `eleuther_eval` | `eleuther_evaluation` or copied YAML | Run EleutherAI Eval Harness tasks | Yes |
| Quantize checkpoint | `quantize` | `quantization` or copied YAML | Convert a supported full model checkpoint to torchao quantized state | Yes |

Use `tune cp generation ./custom_generation_config.yaml`, `tune cp eleuther_evaluation ./custom_eval_config.yaml`, or `tune cp quantization ./custom_quantization_config.yaml` before tailoring fields for a real run. Use `tune cat <config>` for inspection and `tune validate <local-yaml>` when optional dependencies for referenced components are installed.

## Safe Command Builder

Use the bundled helper to print commands without executing them:

```bash
python sub-skills/inference-evaluation-quantization/scripts/build_inference_eval_command.py eval \
  ./custom_eval_config.yaml \
  --override tasks=[truthfulqa_mc2,hellaswag] \
  --override limit=50 \
  --override checkpointer.checkpoint_dir=./runs/model/epoch_0 \
  --print-notes
```

Supported modes are `generate`, `eval`, and `quantize`. The helper maps them to `tune run generate`, `tune run eleuther_eval`, and `tune run quantize`, validates override syntax, warns about optional dependencies and quantization compatibility, and never reads configs or launches work.

## Generation Config Checklist

When adapting `generation`, set:

- `output_dir`: directory for recipe output/log context; choose a writable path, not a transient shared path unless intended.
- `model._component_`: model builder matching the checkpoint family and parameter size.
- `checkpointer._component_`: checkpoint format loader. Use full-model HF/Meta checkpointers for dense checkpoints, and `torchtune.training.FullModelTorchTuneCheckpointer` for torchtune-saved quantized checkpoints.
- `checkpointer.checkpoint_dir`: directory containing checkpoint files.
- `checkpointer.checkpoint_files`: exact weight file names or paths expected by the checkpointer.
- `checkpointer.output_dir`: usually `${output_dir}` for conversion/output context.
- `checkpointer.model_type`: model family constant expected by the checkpointer.
- `tokenizer._component_` and `tokenizer.path`: tokenizer constructor and tokenizer asset copied or downloaded with the checkpoint.
- `tokenizer.prompt_template`: `null` when the tokenizer/config should not apply a chat template.
- `device` and `dtype`: e.g. `cuda` with `bf16` on supported GPUs, or `cpu` with `fp32` for small smoke checks.
- `prompt.system` and `prompt.user`: the generation prompt fields converted into torchtune `Message` objects.
- `max_new_tokens`, `temperature`, and `top_k`: sampling controls passed to `torchtune.generation.generate`.
- `enable_kv_cache`: usually `True` for speed; confirm memory headroom.
- `quantizer`: `null` for dense checkpoints, or a compatible post-training quantizer for already quantized torchtune checkpoints.

Run shape-only command construction before execution:

```bash
python sub-skills/inference-evaluation-quantization/scripts/build_inference_eval_command.py generate \
  ./custom_generation_config.yaml \
  --override prompt.user='Tell me a joke.' \
  --override max_new_tokens=128 \
  --override temperature=0.6 \
  --override top_k=300
```

## Eleuther Evaluation Checklist

When adapting `eleuther_evaluation`, set:

- `tasks`: list of EleutherAI task names, e.g. `[truthfulqa_mc2]` or `[truthfulqa_mc2,hellaswag]`.
- `limit`: small integer for smoke/economic checks, `null` for full evaluation.
- `max_seq_length`: model/eval context length; leave enough room for generation tasks.
- `batch_size`: tune to GPU memory.
- `enable_kv_cache`: normally `True`; multimodal evaluation enforces KV cache for timely generation.
- `apply_chat_template`: config file uses this field name, but the recipe reads `chat_template`; verify current config/recipe alignment before relying on chat templating.
- `include_path`: optional custom Eleuther task path when evaluating non-registry tasks.
- `device`, `dtype`, `seed`: match model and hardware; the default seed mirrors EleutherAI defaults.
- `checkpointer`, `model`, and `tokenizer`: same checkpoint compatibility rules as generation.
- `quantizer`: `null` for dense checkpoints; use a post-training quantizer only for quantized torchtune checkpoints.

Eleuther evaluation imports `lm_eval` and checks the installed harness version. If it is missing or outside the supported range, install the compatible optional package in the working environment before running.

Example non-executing command:

```bash
python sub-skills/inference-evaluation-quantization/scripts/build_inference_eval_command.py eval \
  ./custom_eval_config.yaml \
  --override tasks=[truthfulqa_mc2] \
  --override limit=10 \
  --override batch_size=4 \
  --print-notes
```

## Quantization Checklist

When adapting `quantization`, set:

- `output_dir`: writable directory where the quantized checkpoint is saved.
- `model._component_`: same model architecture as the source checkpoint.
- `checkpointer._component_`: source full-model checkpointer; dense input checkpoints can use HF/Meta/TorchTune full-model checkpointers as appropriate.
- `checkpointer.checkpoint_dir` and `checkpointer.checkpoint_files`: source checkpoint location.
- `checkpointer.output_dir`: `${output_dir}` so the quantized output lands where expected.
- `device` and `dtype`: quantization is model-sized work; check GPU memory before running.
- `quantizer._component_`: supported quantizer component.
- `quantizer.groupsize`: int4 group size such as `256`; smaller values can improve accuracy at higher memory overhead.

Supported recipe modes documented in code are:

- `torchtune.training.quantization.Int8DynActInt4WeightQuantizer`: post-training int8 dynamic activation plus int4 grouped weight quantization.
- `torchtune.training.quantization.Int8DynActInt4WeightQATQuantizer`: conversion for QAT checkpoints; use during `quantize`, not during later `generate` or `eleuther_eval`.

`quantize` saves a `.ckpt` file under `output_dir`, naming it from the first checkpoint file stem plus the quantization mode. Later generation/eval of that file must use `FullModelTorchTuneCheckpointer`, `checkpoint_files: [<quantized-file>.ckpt]`, and the corresponding post-training non-QAT quantizer.

## Quantize Then Evaluate/Generate Sequence

1. Copy `quantization` to a local YAML and point it at the dense or QAT source checkpoint.
2. Build, inspect, and after approval run `tune run quantize --config ./custom_quantization_config.yaml`.
3. Record the produced `.ckpt` file in a durable output directory.
4. Copy `eleuther_evaluation` and/or `generation` to local YAML.
5. Switch `checkpointer._component_` to `torchtune.training.FullModelTorchTuneCheckpointer`.
6. Set `checkpointer.checkpoint_dir` and `checkpointer.checkpoint_files` to the quantized checkpoint.
7. Set `quantizer._component_` to `torchtune.training.quantization.Int8DynActInt4WeightQuantizer` with the same `groupsize`.
8. Build the eval/generation command with the helper and mark actual execution unsafe until dependencies, checkpoints, GPU, and task scope are confirmed.

## Generation API Notes

The public lower-level generation helpers are useful when writing custom inference code around a loaded torchtune model:

- `generate(model, prompt, max_generated_tokens, pad_id=0, temperature=1.0, top_k=None, stop_tokens=None, rng=None, compiled_generate_next_token=None)` returns generated token IDs and logits.
- `sample(logits, temperature=1.0, top_k=None, q=None)` applies temperature/top-k sampling and returns sampled token IDs.
- `generate_next_token(model, input_pos, x, q=None, mask=None, temperature=1.0, top_k=None)` returns next token IDs and logits for decoder-only generation.

The recipe wraps these APIs by converting `prompt.system` and `prompt.user` into torchtune messages, tokenizing with `inference=True`, optionally setting KV caches, and passing tokenizer pad/stop IDs into `generate`.
