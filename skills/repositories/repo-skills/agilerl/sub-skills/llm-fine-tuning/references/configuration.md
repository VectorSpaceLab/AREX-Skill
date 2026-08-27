# LLM Configuration

## Optional Dependencies

Install LLM extras only when needed:

```bash
pip install "agilerl[llm]"
```

This can pull large GPU-sensitive packages. Check Python version, platform, CUDA driver, and available VRAM first.

## Accelerate And DeepSpeed

- Keep Accelerate YAML paths explicit and environment-specific.
- DeepSpeed can require compiler/CUDA compatibility and may build extensions.
- Validate a single-process or CPU dry-run before distributed launch.

## vLLM And Rollouts

vLLM workflows need compatible GPU, CUDA, Python, model architecture, and memory. Colocated rollout/training setups may use vLLM sleep/wake behavior to hand GPU memory between trainer and generator. Validate backend support before relying on this mode.

## Quantization

Quantization can involve bitsandbytes, PEFT, Transformers, vLLM constraints, and GPU architecture support. Check that the quantized loading path and rollout backend both support the selected quantization.

## Checkpoints

- Decide save directory and checkpoint cadence before training.
- Verify save/load on a tiny model or dry-run config when possible.
- Keep model artifacts out of package install directories.

## Dataset And Reward Config

- Validate prompt/response/preference columns.
- Validate chat template output before training.
- Run reward functions on tiny examples.
- For multiturn envs, validate reset, step, done, and reward behavior independently.
