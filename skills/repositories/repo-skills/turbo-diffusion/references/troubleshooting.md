# Cross-cutting Troubleshooting

## Purpose

Use this for failures that span multiple TurboDiffusion workflows. For route-specific fixes, follow the linked sub-skill troubleshooting file.

| Symptom or error | Likely cause | What to do |
| --- | --- | --- |
| `No module named imaginaire`, `No module named rcm`, `No module named serve`, or `No module named modify_model` | Source-layout imports are expected by several scripts and the installed entry point may not expose all top-level modules | Use a source-layout `PYTHONPATH` for the checkout/package directory you are operating on; then rerun the help/command. Do not hardcode historical checkout paths. |
| `No module named turbo_diffusion_ops` | Local package was installed without building the CUDA extension, or install used a CPU-only/metadata-only path | Reinstall with CUDA-capable PyTorch, initialized CUTLASS submodule, `nvcc`, CUDA dev headers/libraries, and `--no-build-isolation`; then run the root diagnostic. |
| `CUDA_HOME environment variable is not set` during build | PyTorch extension build cannot find CUDA toolkit/dev files | Install an environment-local CUDA toolkit/dev package or use a system CUDA toolkit compatible with the PyTorch build; retry from a clean build directory. |
| `cusparse.h` or CUDA header missing during build | Runtime CUDA libraries are present but development headers are absent | Add CUDA development libraries/headers for the same CUDA generation; runtime-only wheels are not enough for source builds. |
| `SageSparseLinearAttention` asserts or `SAGESLA_ENABLED` is false | SpargeAttn is not installed | Install SpargeAttn for the SageSLA path or switch command flags to `--attention_type sla` or `original`. |
| Full generation command starts downloading or asks for weights | Checkpoints, VAE, or text encoder path is missing and a library attempts network fallback | Stop unless user authorized downloads. Ask for local asset paths, then rerender the command. |
| Command uses a quantized checkpoint but output quality/runtime is wrong | Missing `--quant_linear` or mismatched quantized/unquantized checkpoint | Inspect checkpoint filename/metadata and rerender with matching quantization flag. |
| I2V command loads the wrong model stage | High- and low-noise checkpoint paths are swapped | Verify names contain high/low stage cues; use the video-inference builder's swap detection. |
| Interactive server exits before TUI | Missing mode-specific model path or source-layout import failure | Use `interactive-serving` command builder, add mode-specific required paths, and include source-layout `PYTHONPATH` when needed. |
| Training command would start a long run unexpectedly | User asked for setup/debug but command lacks `--dryrun` or budget confirmation | Use the training dry-run builder first. Start full `torchrun` only after data/checkpoints/GPU/WandB policy are confirmed. |
| TurboT2AV command fails with Hugging Face/Gemma access errors | Gemma checkpoint is gated or token is missing/unauthorized | Ask the user to accept model terms and provide/access a valid local Gemma directory; do not embed tokens in commands or skill files. |

## Route to specific troubleshooting

- One-shot T2V/I2V generation: [video-inference troubleshooting](../sub-skills/video-inference/references/troubleshooting.md)
- Interactive terminal server: [interactive-serving troubleshooting](../sub-skills/interactive-serving/references/troubleshooting.md)
- Training/checkpoint conversion: [training-and-checkpoints troubleshooting](../sub-skills/training-and-checkpoints/references/troubleshooting.md)
- CUDA/SLA/SageSLA/custom-op backend: [acceleration-backends troubleshooting](../sub-skills/acceleration-backends/references/troubleshooting.md)
- TurboT2AV extension: [TurboT2AV troubleshooting](../sub-skills/turbot2av-extension/references/troubleshooting.md)

## Stop conditions

Stop and ask for confirmation before:

- downloading model checkpoints, VAE/text encoder assets, datasets, or gated models;
- installing large optional training or TurboT2AV dependency stacks;
- launching full generation/training/benchmark commands;
- using credentials such as Hugging Face or WandB tokens;
- overwriting checkpoints or output directories that may contain user work.
