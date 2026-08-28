---
name: inference
description: "Guides FastVideo typed Python and config-first CLI generation, model inputs, outputs, offload, attention backends, quantization, and compilation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Inference

Use for text-to-video, image-to-video, video-to-video, image, and supported
audio generation. Start with a registered model ID and a backend-compatible
configuration.

## Preferred typed path

```python
from fastvideo import VideoGenerator

generator = VideoGenerator.from_pretrained(
    "Wan-AI/Wan2.1-T2V-1.3B-Diffusers", num_gpus=1
)
result = generator.generate({
    "prompt": "A fox running through snow",
    "sampling": {"num_frames": 81, "height": 480, "width": 832, "seed": 42},
    "output": {"output_path": "outputs/", "save_video": True},
})
```

For a reusable file, use `VideoGenerator.from_file()` or the CLI. Read [API
reference](references/api-reference.md), [workflows](references/workflows.md),
and [optimizations](references/optimizations.md) before changing advanced
settings. Run [typed helper](scripts/generate_typed.py) only after choosing a
model and accepting remote-weight execution.

## CLI

```bash
fastvideo generate --config run.yaml
fastvideo generate --config run.yaml --request.sampling.seed 7
```

The config must be nested; flat flags are not the current contract. Input images,
video paths, prompt files, control tensors, refinement inputs, and output modes
belong in `request.inputs`, `request.sampling`, and `request.output`.

## Performance and safety

Fix prompt, seed, dimensions, steps, and model before comparing backends. Warm
up once before measuring `torch.compile`. Use offload or multi-GPU only when the
selected model supports it. Attention and low-bit paths can alter numerics;
validate quality on the target configuration rather than assuming equivalence.

See [inference troubleshooting](references/troubleshooting.md) for shape,
backend, memory, output, and deprecated-API failures. Serving is a separate
route: [serving](../serving/SKILL.md).
