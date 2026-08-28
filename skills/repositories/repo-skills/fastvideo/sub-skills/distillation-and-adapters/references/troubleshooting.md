# Distillation and adapter troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| Missing checkpoint keys | Wrong model family/revision or incomplete conversion | Compare against the target native state dict; fix explicit mapping and rerun coverage checks. |
| Shape mismatch in QKV/MLP | Fused/split ordering or tensor-parallel layout differs | Inspect target config and reshape/split deliberately; do not rename keys inside the model class. |
| Adapter merge changes output unexpectedly | Base revision, dtype, rank, target modules, or scaling differs | Reuse exact base and config, compare fixed seeds, and validate parameter deltas before merge. |
| Distillation diverges | Wrong CFG parameterization, timestep schedule, teacher/student mode, or data latent schema | Verify the guidance conversion, timesteps, precision, and preprocessed record fields against the selected recipe. |
| Kernel compile/import fails | Torch/CUDA/architecture/extension mismatch | Check ABI and architecture; use a supported backend/fallback or rebuild after fixing torch. |
| OOM or stalled multi-GPU job | Model/data/optimizer too large or launcher topology wrong | Dry-run one process, reduce batch/frames, use sharding/accumulation, and validate ranks/ports. |
| Converted model loads but quality is wrong | Silent skipped keys, wrong normalization, or incorrect component mapping | Require key coverage and a fixed-input parity check; retain the original source and conversion manifest. |
| Hub upload/auth failure | Credential or network operation unavailable | Keep output local, configure credentials explicitly, and retry as a separate authorized step. |
