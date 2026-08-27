---
name: export-and-deployment
description: "Export trained YOLOX checkpoints to ONNX or TorchScript and reason
  about optional deployment runtimes with backend caveats."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# YOLOX Export And Deployment

Use this sub-skill when a task starts from an existing YOLOX checkpoint and asks how to export it to ONNX or TorchScript, dry-run export settings, debug export failures, or choose among optional deployment runtimes such as ONNXRuntime, TensorRT, OpenVINO, ncnn, MegEngine, or nebullvm.

Do not use this sub-skill to produce a training checkpoint; route checkpoint production to `../training-and-data/SKILL.md`. Do not use it for ordinary PyTorch `.pth` inference; route that to `../inference-and-api/SKILL.md`.

## Start here

1. Identify checkpoint path, model name or custom `Exp`, output format, input/test size, decode setting, and target runtime.
2. Read [references/export-workflows.md](references/export-workflows.md) for ONNX/TorchScript flags, checkpoint-loading rules, decode guidance, and dry-run patterns.
3. Run [scripts/export_yolox_template.py](scripts/export_yolox_template.py) for a safe dry-run or real ONNX/TorchScript export; real export requires an explicit checkpoint path.
4. Read [references/deployment-backends.md](references/deployment-backends.md) before choosing ONNXRuntime, TensorRT, OpenVINO, ncnn, MegEngine, or nebullvm.
5. Read [references/troubleshooting.md](references/troubleshooting.md) when export, checkpoint loading, dynamic axes, decode settings, or optional backend dependencies fail.

## Minimal operating pattern

Dry-run first:

```bash
python scripts/export_yolox_template.py --format onnx --name yolox-s --dry-run
```

Then export with an explicit checkpoint:

```bash
python scripts/export_yolox_template.py --format onnx --name yolox-s --checkpoint yolox_s.pth --output yolox_s.onnx
python scripts/export_yolox_template.py --format torchscript --name yolox-s --checkpoint yolox_s.pth --output yolox_s.torchscript.pt
```

Keep `model.head.decode_in_inference` consistent with the downstream runtime. YOLOX deployment examples commonly expect raw head outputs and decode/postprocess outside the graph; custom runtimes may prefer decoded outputs in the graph.
