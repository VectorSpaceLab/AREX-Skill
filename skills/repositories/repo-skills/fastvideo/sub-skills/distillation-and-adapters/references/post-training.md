# Post-training workflows

FastVideo's sparse-distill combines DMD with sparse attention. Public recipes
include Wan 2.1 T2V and Wan 2.2 TI2V variants, commonly using preprocessed
synthetic latent datasets, multi-GPU launchers, and a small number of student
denoising steps. Treat published node counts and timings as recipe evidence,
not universal requirements.

DMD teacher guidance uses the parameterization `x_cond + w * (x_cond -
x_uncond)`. If translating from standard CFG `x_uncond + s * delta`, use
`w = s - 1` for equivalent guidance strength. This is a frequent source of
quality drift.

Self-Forcing requires a causal workflow and matching continuation/trajectory
semantics. Validate a short segment and state handoff before scaling out.

Attn-QAT has two distinct concerns: fake quantization during training and the
inference backend/quantized linear configuration. Do not enable
`ATTN_QAT_INFER` without checking architecture gates; on unsupported GPUs the
runtime may fall back to Flash Attention or fail depending on the selected
kernel policy. Keep FSDP away from pointer-sensitive FP4 paths.

Safe preparation checklist:

1. Verify model revisions and data schema.
2. Run a config parse/dry-run with one process.
3. Confirm GPU architecture, torch/CUDA ABI, kernels, and output disk space.
4. Preserve checkpoints and resume metadata.
5. Evaluate baseline and distilled outputs with identical prompt/seed/shape.
