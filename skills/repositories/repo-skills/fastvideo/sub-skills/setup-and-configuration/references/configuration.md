# Configuration reference

## Typed object layout

`GeneratorConfig` contains `model_path`, optional `revision` and
`trust_remote_code`, `engine`, and `pipeline`. `EngineConfig` contains
`num_gpus`, `execution_backend` (`mp` or `ray`), parallelism, offload, compile,
stage verification, FSDP, autocast, and optional quantization. `PipelineSelection`
contains workload type, preset, component paths, VAE tiling, preset overrides,
and experimental options.

`GenerationRequest` contains `prompt`, `negative_prompt`, `inputs`, `sampling`,
`runtime`, `output`, `stage_overrides`, optional continuation `state`, optional
`plan`, and `extensions`. Keep initialization options in `GeneratorConfig` and
per-call options in the request.

## CLI file shape

`fastvideo generate --config RUN_CONFIG` requires a nested JSON/YAML file with a
`generator` mapping and either `request.prompt` or
`request.inputs.prompt_path`, but not both. Generation files can use:

```yaml
generator:
  model_path: Wan-AI/Wan2.1-T2V-1.3B-Diffusers
  engine:
    num_gpus: 1
request:
  prompt: A fox running through snow
  sampling:
    num_frames: 81
    height: 480
    width: 832
    num_inference_steps: 30
    seed: 42
  output:
    output_path: outputs/
    save_video: true
    return_frames: false
```

Override only with dotted paths such as
`--request.sampling.seed 7` or `--generator.engine.num_gpus 2`. Unknown
fields and invalid nested types should be fixed at their reported path.

## Backend selection

- NVIDIA x86: CUDA 12.6 or 13.0, a compatible PyTorch wheel, and a suitable
  GPU/driver. `flashvideo-kernel` and attention extensions may need their own
  compatibility check.
- Apple Silicon: MPS on macOS 14+; omit Linux-only packages.
- ROCm: use a ROCm-compatible torch environment and the `rocm` extra only when
  the AMD workflow is selected.
- CPU: suitable for config/API inspection and some utilities, but not a
  substitute for model execution or custom attention kernels.

Use the canonical package metadata, not a guessed distribution name, when
checking installation. The installed package's public version in this bundle's
baseline is 0.2.0.
