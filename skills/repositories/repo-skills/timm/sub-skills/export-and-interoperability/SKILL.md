---
name: export-and-interoperability
description: "Build ONNX export and validation commands, package/load timm
  models via Hugging Face Hub or local directories, use Torch Hub compatibility,
  and safely clean or average checkpoints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Export and Interoperability

Use this sub-skill when a task asks for timm model export, ONNX Runtime validation, pretrained model interchange through Hugging Face Hub or local directories, Torch Hub compatibility, or checkpoint cleanup/averaging before sharing weights.

## Routing Checklist

- Use `references/export-checkpoint-workflows.md` for ONNX export/validation command options, dynamic input caveats, `exportable=True`, reparameterization, checkpoint cleaning, checkpoint averaging, hash naming, and safetensors choices.
- Use `references/hub-and-conversion.md` for `hf-hub:` and `local-dir:` model names, `push_to_hf_hub`, local `config.json` plus weight-file expectations, Torch Hub behavior, and conversion-script caveats.
- Use `references/troubleshooting.md` for missing optional dependencies, unsupported ONNX ops, dynamic-shape failures, checkpoint prefix/EMA mismatches, safe loading failures, local-dir packaging mistakes, Hugging Face auth/cache/network issues, and external conversion requirements.
- Use `scripts/timm_onnx_command_builder.py` to print dry `onnx_export.py` and `onnx_validate.py` commands without importing timm or requiring ONNX dependencies.
- Use `scripts/timm_checkpoint_tools.py` for self-contained checkpoint inspection, dry command construction for cleaning/averaging, and bundled averaging; cleaning remains a generated command for a timm script checkout rather than a write action inside this helper.

## High-Value Defaults

- Start ONNX work with a small, common model and static shape: `--model resnet18 --batch-size 1 --input-size 3 224 224`; add `--dynamic-size` only when deployment needs variable height/width.
- Export through timm's export path, not ad hoc tracing: create models with `exportable=True`, use `--checkpoint` for local weights, and add `--reparam` for models that expose reparameterization before deployment.
- Treat `--check-forward` as optional verification because it requires ONNX/ONNX Runtime support and may expose numerical or operator-coverage differences rather than command-construction mistakes.
- Prefer safetensors for shared cleaned or averaged weights when the dependency is installed; keep `.pth` only for legacy consumers that need PyTorch serialization.
- Keep checkpoint tools non-destructive: never overwrite an existing output, inspect candidate keys first, and decide whether EMA weights should be used before cleaning or averaging.
- For hosted or portable timm models, package both `config.json` and a recognized weight filename; use exact `hf-hub:org/model@revision` or `local-dir:/path/to/model_dir` source prefixes when loading.

## Boundary Routing

- Use `../model-library/` for ordinary `timm.create_model`, model discovery, pretrained config inspection, feature extraction, and generic checkpoint mismatch analysis before export.
- Use `../cli-workflows/` for `train.py`, `validate.py`, and `inference.py` commands that are not ONNX-specific.
- Use `../benchmarking-and-results/` when the task is performance measurement rather than export or validation correctness.
- Treat framework conversion scripts as reference-only starting points; do not promise turnkey conversion unless the external checkpoint format, framework package, and architecture mapping are available.

## Bundled Helpers

```bash
python scripts/timm_onnx_command_builder.py export \
  --output model.onnx --model resnet18 --input-size 3 224 224 --batch-size 1 --check-forward
```

```bash
python scripts/timm_checkpoint_tools.py inspect \
  --checkpoint model_best.pth.tar
```

The helpers are intentionally conservative. The ONNX builder prints commands only. The checkpoint helper can inspect checkpoints, construct clean/average commands, and run bundled checkpoint averaging with overwrite refusal; checkpoint cleaning is emitted as a command for a trusted timm script checkout.
