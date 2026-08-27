---
name: inference-export
description: "Export Composer or PyTorch models for inference with TorchScript
  or ONNX, including checkpoint loading, export callbacks, and HuggingFace
  integration caveats."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Composer Inference Export

Use this sub-skill when a user asks to make a Composer or PyTorch model ready for inference through TorchScript, ONNX, checkpoint-backed export, `ExportForInferenceCallback`, or optional HuggingFace/PEFT integration.

## Route here

- Export a model to TorchScript or ONNX.
- Export from an existing checkpoint with `load_path` and optional `load_object_store`.
- Attach `ExportForInferenceCallback` so export happens at the end of training.
- Use `Trainer.export_for_inference` from an already-constructed Trainer.
- Choose `sample_input`, `dynamic_axes`, `input_names`, and `output_names`.
- Apply `surgery_algs`, `transforms`, or `quantize_dynamic` before export.
- Validate a saved TorchScript or ONNX artifact.
- Handle HuggingFaceModel tokenizer, embedding, PEFT, or checkpoint metadata caveats.

## Reroute

- Training, checkpoint saving, or resume flow details: use `../training/SKILL.md`.
- Logger destinations, object-store upload, and artifact routing beyond export arguments: use `../observability/SKILL.md`.
- Distributed launch, wrapping, FSDP setup, or backend rank topology: use `../distributed/SKILL.md`.
- Speedup method choice before export: use `../methods/SKILL.md`, then return here for artifact generation.

## Read first

- [Export and inference](references/export-and-inference.md): recipes, signatures, arguments, and validation checks.
- [HuggingFace integration](references/huggingface-integration.md): optional `mosaicml[nlp]`, PEFT, tokenizer/config/embedding caveats, and checkpoint metadata.
- [Troubleshooting](references/troubleshooting.md): export-specific failure modes and recovery steps.
- [TorchScript export smoke](scripts/export_torchscript_smoke.py): a safe no-download export/load check.

## Core export choices

1. Choose `save_format="torchscript"` for a self-contained scripted/traced artifact.
2. Choose `save_format="onnx"` when the target runtime expects ONNX and you can provide a representative `sample_input`.
3. Use `load_path` when the model object needs weights from a Composer checkpoint before export.
4. Use `surgery_algs` for pre-load model surgery and `transforms` for post-load export-time transforms.
5. Use `quantize_dynamic` only when the target model layers and runtime support dynamic quantization.
6. Validate the output artifact immediately on the same example input.

## Common API skeleton

```python
from composer.utils import export_for_inference, quantize_dynamic

export_for_inference(
    model=model,
    save_format="torchscript",
    save_path="model.pt",
    sample_input=example_batch,
    transforms=[quantize_dynamic],
)
```

For ONNX, provide `sample_input` and usually explicit names or dynamic axes:

```python
export_for_inference(
    model=model,
    save_format="onnx",
    save_path="model.onnx",
    sample_input=(inputs,),
    input_names=["input"],
    output_names=["logits"],
    dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}},
)
```

## Callback pattern

Use `ExportForInferenceCallback` when export should be part of the training lifecycle:

```python
from composer.callbacks import ExportForInferenceCallback
from composer import Trainer

trainer = Trainer(
    model=model,
    train_dataloader=train_loader,
    max_duration="1ep",
    callbacks=[ExportForInferenceCallback(save_format="torchscript", save_path="model.pt")],
)
trainer.fit()
```

For ONNX callbacks, pass `sample_input` or allow the callback to capture a batch after the dataloader runs.

## Distributed and checkpoint caveats

- Only global rank zero writes the export artifact.
- If the model is wrapped in DDP, export the underlying module rather than the wrapper.
- Do not export an FSDP-wrapped module directly; recreate/load the model without FSDP wrapping first.
- `load_strict=False` is the export utility default; choose strictness intentionally when loading changed heads or adapter-only weights.
- Remote checkpoint paths need matching object-store or logger configuration from the observability route.

## HuggingFace quick checks

- Install the NLP extra before using `HuggingFaceModel`.
- Pass the tokenizer when checkpoint metadata should preserve tokenizer files.
- If tokenizer vocabulary is larger than model embeddings, either resize embeddings before wrapping or set `allow_embedding_resizing=True`.
- PEFT support is optional and Composer's wrapper expects supported PEFT configuration, with LoRA as the intended adapter path.

## Bundled smoke script

Run from this sub-skill directory:

```bash
python scripts/export_torchscript_smoke.py
```

The script exports a tiny CPU model to a temporary TorchScript file, reloads it, and compares outputs.

## Ask or stop before proceeding

- The export target is ONNX but `onnx`/`onnxruntime` are not available and validation is required.
- The model requires downloading remote weights/tokenizers and network approval is unclear.
- The checkpoint is untrusted, private, remote, or requires credentials.
- The model is FSDP-wrapped and the unwrapped construction path is unknown.
- The target runtime requires shapes, names, quantization, or operator sets that the source model may not support.
