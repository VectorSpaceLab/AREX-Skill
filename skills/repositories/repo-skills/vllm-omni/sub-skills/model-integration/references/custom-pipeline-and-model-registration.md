# Custom pipeline and model registration

## Purpose

Read this when extending vLLM-Omni rather than merely using an existing model. It summarizes extension surfaces that recur across diffusion pipelines, omni AR/TTS models, deployment metadata, and serving endpoints.

## Custom diffusion pipeline route

Use this route when the user has a Diffusers-like or vLLM-Omni diffusion pipeline and wants to add task-specific behavior such as trajectory outputs, custom preprocessing, alternate scheduler settings, or a model-specific `forward` wrapper.

Key runtime knobs:

| Knob | Purpose | Typical use |
| --- | --- | --- |
| `diffusion_load_format="default"` | Use vLLM-Omni's model registry and native loader. | Supported production models. |
| `diffusion_load_format="dummy"` | Skip the initial model load so custom pipeline args can initialize the worker later. | Custom pipeline experiments that own initialization. |
| `diffusion_load_format="diffusers"` | Load through the Hugging Face Diffusers adapter. | A pipeline already available as a Diffusers class. |
| `custom_pipeline_args={"pipeline_class": "module.Class"}` | Point the worker extension at a custom implementation. | Safe class import path to a user module. |
| `worker_extension_cls=...` | Add worker methods or reinitialization behavior. | Advanced extensions; keep the interface narrow. |

Minimal custom pipeline pattern:

```python
from vllm_omni.diffusion.data import OmniDiffusionConfig
from vllm_omni.diffusion.worker.request_batch import DiffusionRequestBatch

class CustomPipeline(ExistingPipeline):
    def __init__(self, *, od_config: OmniDiffusionConfig, prefix: str = ""):
        super().__init__(od_config=od_config, prefix=prefix)

    def forward(self, req: DiffusionRequestBatch):
        # Normalize request-scoped params before calling the base pipeline.
        if req.sampling_params.num_inference_steps is None:
            req.sampling_params.num_inference_steps = 30
        out = super().forward(req=req)
        # Attach only serializable or documented tensors that downstream output
        # formatting knows how to expose.
        return out
```

Usage sketch:

```python
from vllm_omni.entrypoints.omni import Omni

omni = Omni(
    model="Qwen/Qwen-Image-Edit",
    diffusion_load_format="dummy",
    custom_pipeline_args={"pipeline_class": "my_pkg.custom_pipeline.CustomPipeline"},
)
outputs = omni.generate({"prompt": "make the mascot dance"})
```

Checklist before running a full model:

1. The custom class import path resolves in the target Python environment.
2. The custom class constructor accepts keyword-only `od_config` and optional `prefix` when extending native diffusion pipelines.
3. The `forward` method accepts a `DiffusionRequestBatch` and returns the expected pipeline output object.
4. New output fields are handled by the output formatter or are placed in already supported custom/trajectory fields.
5. The selected `diffusion_load_format` avoids double-loading weights.
6. GPU memory is validated with a small prompt after imports and parser checks pass.

## Adding or changing model registrations

A vLLM-Omni model integration usually spans these concepts:

| Surface | What to define | Common failure if wrong |
| --- | --- | --- |
| model implementation | The model, pipeline, adapter, tokenizer/processor, or stage input processor classes. | Import errors, wrong tensor shapes, unsupported modality payloads. |
| pipeline config | `model_type`, model architecture, stages, endpoint restrictions, default deploy config name. | Model loads but requests route to the wrong stage or endpoint. |
| deploy config | Stage IDs, devices, connectors, default sampling params, platform overrides. | Unknown stage id, connector mismatch, OOM, headless registration failure. |
| serving adapter | OpenAI protocol conversion, TTS/audio/video response packaging, streaming behavior. | Server starts but response schema is invalid or missing media. |
| optional extras | Model-specific tokenizers, guardrails, voice codecs, alignment, kernels. | Import-time optional dependency errors. |
| tests | CPU config/parser/unit tests first; GPU/full-model examples only with model cache and hardware. | Slow failures after broad e2e launch. |

## Integration flow by model family

### Omni AR / multimodal chat

- Identify the Hugging Face architecture or `model_type` signal that should select the integration.
- Define stage topology for thinker/talker/vocoder or similar components.
- Make prompt preprocessing explicit: text, image, audio, video, `additional_information`, and `model_intermediate_buffer` fields.
- Confirm default output modalities and final stage IDs.
- Add endpoint restrictions when the model should not expose every OpenAI-compatible endpoint.

### Diffusion image/video/audio/action

- Decide whether the model is a native registered pipeline, a Diffusers adapter, or a custom pipeline.
- Map request parameters to `OmniDiffusionSamplingParams` fields or `extra_args`.
- Choose attention backend behavior and sequence/CFG/VAE parallel options only when the model supports them.
- Keep LoRA, quantization, offload, cache, and step-execution compatibility matrix close to the model's pipeline code.
- Ensure output formatter returns the expected images, video frames, audio, latents, trajectory fields, or custom payload.

### TTS / audio output

- Verify prompt/reference-audio schema and voice-style/task-type behavior.
- Keep text normalization, forced aligner, token-to-waveform, and streaming chunk behavior explicit.
- Check OpenAI speech/audio response packaging and adapter class behavior.
- Add optional dependency notes for phonemizers, tokenizers, alignment models, codecs, and platform-specific packages.

## Registration review checklist

- The model can be selected by its intended `model_type`, architecture, or explicit pipeline override.
- Default deploy config exists and stage IDs match pipeline config stages.
- Platform overrides are limited to supported CUDA/ROCm/NPU/XPU/MUSA differences.
- CLI flags and kwargs used by examples are recognized by `OmniConfig` or model-specific config.
- A CPU/static test covers registration or config parsing before any full model test.
- A GPU/full-model test is marked as hardware/model-cache dependent rather than run by default.

## When to stop and ask for runtime evidence

Stop before claiming a model integration works if any of these are missing:

- A compatible vLLM/vLLM-Omni version pair.
- Required checkpoint files, license acceptance, or private model cache.
- Required CUDA/ROCm/NPU/XPU/MUSA backend.
- Optional packages named by the model implementation.
- A validated endpoint response shape for the selected modality.
