# Checkpoint Flow For Inference, Evaluation, And Quantization

Use this reference when a trained output directory exists and the agent must decide which files and checkpointer settings belong in generation, Eleuther evaluation, or quantization configs.

## Training Output Shapes

A LoRA-family torchtune training run can produce several kinds of files:

| Output | Meaning | Use in this sub-skill |
| --- | --- | --- |
| `adapter_model.safetensors` | Trained adapter weights for PEFT-style adapter loading | Not enough by itself for `generate` or `eleuther_eval` recipe configs that expect full model weights |
| `adapter_model.pt` | Duplicate adapter weights for resuming torchtune training | Not an inference/eval target by itself |
| `adapter_config.json` | PEFT adapter placement metadata | Useful for external PEFT loading, not direct torchtune generation/eval |
| `model-00001-of-000NN.safetensors` and siblings | Merged full model weights, present when LoRA training saved merged weights | Preferred for torchtune generation/eval after LoRA |
| `model.safetensors.index.json` | HF index for sharded merged weights | Keep alongside merged weights for HF-style loading |
| `original/` tokenizer and metadata files | Copied lightweight tokenizer/config files from the source checkpoint | Point tokenizer paths here after training |
| `recipe_state/recipe_state.pt` | Training recipe state | Resume/training concern, not generation/eval input |

Files copied from the original checkpoint exclude large weight files over the training copy threshold, so the epoch directory may contain tokenizer/config files plus either adapter-only weights or merged full-model shards depending on training settings.

## Merged Weights Versus Adapter-Only Outputs

For torchtune `generate` and `eleuther_eval`, prefer merged full model weights:

1. Inspect the chosen epoch directory for `model-*.safetensors`, `.bin`, `.pth`, or `.ckpt` full-model files.
2. If merged files exist, set `checkpointer.checkpoint_dir` to that epoch directory and `checkpointer.checkpoint_files` to those full-model file names.
3. Set `tokenizer.path` to the copied tokenizer under the epoch directory, usually `original/tokenizer.model` for Llama-style tokenizers.
4. Keep `model._component_` as the base model builder; do not add a LoRA model builder just because training used LoRA.
5. Keep `quantizer: null` unless evaluating/generating an already quantized torchtune checkpoint.

If only adapter files exist:

- Do not pretend `adapter_model.safetensors` is a full checkpoint for `generate` or `eleuther_eval`.
- Ask whether the training run can be repeated or exported with merged weights, for example by using a training config that saves merged full-model weights instead of adapter-only outputs.
- If the user wants external PEFT/Hugging Face loading, route outside this sub-skill or create a separate serving/export plan; torchtune recipe configs here are full-checkpoint oriented.
- If the user wants additional training/resume behavior, route back to `../post-training-recipes/SKILL.md` or `../training-utilities-and-rlhf/SKILL.md`.

## Dense Checkpoint To Generation/Eval

For a normal dense checkpoint:

```yaml
checkpointer:
  _component_: torchtune.training.FullModelHFCheckpointer
  checkpoint_dir: <checkpoint-dir>
  checkpoint_files: [<weight-file-1>, <weight-file-2>]
  output_dir: ${output_dir}
  model_type: <MODEL_TYPE>

tokenizer:
  _component_: <matching-tokenizer-component>
  path: <checkpoint-or-epoch-dir>/original/tokenizer.model
  prompt_template: null

quantizer: null
```

Use the checkpointer matching the checkpoint format. HF-style sharded safetensors commonly use `FullModelHFCheckpointer`; torchtune-saved `.ckpt` files commonly use `FullModelTorchTuneCheckpointer`.

## Dense Or QAT Checkpoint To Quantized Checkpoint

The `quantize` recipe loads a full model checkpoint, quantizes it, and writes a `.ckpt` into `output_dir`.

For post-training quantization:

```yaml
quantizer:
  _component_: torchtune.training.quantization.Int8DynActInt4WeightQuantizer
  groupsize: 256
```

For QAT conversion:

```yaml
quantizer:
  _component_: torchtune.training.quantization.Int8DynActInt4WeightQATQuantizer
  groupsize: 256
```

Use a QAT quantizer only in the quantization conversion step for QAT checkpoints. For later generation or evaluation of the produced quantized checkpoint, switch back to the non-QAT `Int8DynActInt4WeightQuantizer` because the runtime quantization type is the same and recipe guards reject QAT quantizers during eval/generation.

## Quantized Checkpoint To Generation/Eval

For a quantized torchtune checkpoint, both `generate` and `eleuther_eval` require:

```yaml
checkpointer:
  _component_: torchtune.training.FullModelTorchTuneCheckpointer
  checkpoint_dir: <quantized-output-dir>
  checkpoint_files: [<quantized-model-file>.ckpt]
  output_dir: ${output_dir}
  model_type: <MODEL_TYPE>

quantizer:
  _component_: torchtune.training.quantization.Int8DynActInt4WeightQuantizer
  groupsize: 256
```

Do not use `FullModelHFCheckpointer` with `quantizer` for quantized eval/generation. The recipes explicitly reject quantized loading unless the checkpointer is `FullModelTorchTuneCheckpointer`, because quantized checkpoints are saved in torchtune format and loaded with `weights_only=False`.

## Output Directory Rules

- `generate`: `output_dir` is part of config/log/checkpointer context; make it writable even if the recipe primarily logs generated text.
- `eleuther_eval`: `output_dir` is usually not central to metrics but still must be valid for checkpointer/config components that require it.
- `quantize`: `output_dir` is where the quantized checkpoint is written; choose a durable location and record the final `.ckpt` name.
- Avoid `/tmp` for user-important artifacts unless the user explicitly wants scratch output.

## Difficult Case: LoRA Epoch Directory

Given a LoRA run output:

- `epoch_0/adapter_model.safetensors`
- `epoch_0/adapter_config.json`
- `epoch_0/original/tokenizer.model`
- no `epoch_0/model-*.safetensors`

The correct inference/eval answer is: adapter-only output is insufficient for the torchtune `generate` and `eleuther_eval` full-checkpoint configs. Ask for a merged full-model export or a run with merged weights. Do not build a command that lists `adapter_model.safetensors` under `checkpointer.checkpoint_files` for these recipes.

Given a LoRA run output:

- `epoch_0/model-00001-of-00002.safetensors`
- `epoch_0/model-00002-of-00002.safetensors`
- `epoch_0/original/tokenizer.model`
- adapter files also present

The correct inference/eval answer is: use the `model-*` merged full weights, base model builder, tokenizer under `original/`, and `quantizer: null`. Adapter files are not listed in the torchtune generation/eval config.

## Difficult Case: Quantize Then Eval Then Generate

A safe plan should produce three command shapes and mark all model execution unsafe until confirmed:

1. `tune run quantize --config ./custom_quantization_config.yaml` with a source dense/QAT checkpoint and `output_dir` for the generated `.ckpt`.
2. `tune run eleuther_eval --config ./custom_eval_quantized.yaml` using `FullModelTorchTuneCheckpointer`, the produced `.ckpt`, and `Int8DynActInt4WeightQuantizer`.
3. `tune run generate --config ./custom_generation_quantized.yaml` with the same quantized checkpointer/quantizer pair and a prompt override.

The plan should explicitly confirm torchao availability, GPU memory, tokenizer path, eval harness install/version, task scope, and output directory before any run.
