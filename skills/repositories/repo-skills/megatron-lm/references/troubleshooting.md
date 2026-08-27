# Cross-cutting troubleshooting

## Install/import/backend

- Confirm the distribution (`megatron-core`) and import roots (`megatron.core`, `megatron.training`) with the same Python that will launch the task.
- Run `python -m pip check` and the bundled environment probe before interpreting deeper errors.
- A CPU import or tiny CUDA allocation does not validate NCCL, multi-rank process groups, TransformerEngine, FP8/FP4, CUDA graphs, ModelOpt, or H100/GB200 behavior.
- Missing TransformerEngine/Apex warnings can be fallback-safe for local/Torch paths but are blockers for some fused/FP8/MoE workflows. Classify the requested path first.
- Prefer supported containers for broad CUDA/dev dependencies; use conservative `MAX_JOBS` when source builds OOM.

## Distributed launch

- Recompute `WORLD_SIZE = TP × PP × CP × DP` and verify EP/ETP constraints for MoE.
- For multi-node, validate shared paths, `MASTER_ADDR`, `MASTER_PORT`, `NNODES`, node rank, and GPUs per node.
- Scan all rank logs. The first Python traceback is usually the cause; later NCCL/barrier timeouts are often symptoms.
- Apply `CUDA_DEVICE_MAX_CONNECTIONS` only for the selected hardware/parallelism mode; do not set `1` for FSDP.

## Data/config

- JSONL keys, tokenizer files, vocab size/padding, `.bin/.idx` prefixes, split ratios, cache paths, and object-storage mounts must agree.
- Use `NullTokenizer` and numeric-token tiny fixtures for bounded preprocessing checks; arbitrary natural-language rows require real HF/SentencePiece/TikTokenizer files/dependencies.
- If startup is slow, distinguish rank-0 dataset-index construction from model/NCCL initialization. Prebuild cache and use fast/deferred mmap flags when appropriate.

## Checkpoints

- Confirm checkpoint root/tracker, `--ckpt-format`, model args, and optimizer state format before changing topology or resume semantics.
- Use safe loading and explicit allow-lists for trusted checkpoint classes; do not disable weights-only safety globally.
- GPT-Hybrid conversion requires pattern/source compatibility; conversion to a new target root is safer than overwriting the source.

## Inference/serving

- Validate checkpoint/tokenizer/model topology before debugging generation.
- Prompt length, sampling-parameter shape, coordinator lifecycle, CUDA graph capture, and server port are common independent failure surfaces.
- Bind servers locally for tests; external binding requires explicit intent and network authorization.

## CI/maintenance

- Unit tests commonly require distributed/GPU launch; plain pytest can hang or misrepresent CI.
- Functional golden drift after CUDA/Torch/container changes can be expected; compare magnitude and affected metrics before refreshing goldens.
- Never invoke internal CI force-push tools without a dry run and a private pull-request branch.
- `dev` is default; LTS is opt-in. Keep `pyproject.toml`, `uv.lock`, and dev Dockerfile semantics aligned; do not hand-edit `uv.lock`.

## Evidence limits

The current verified environment covered base import, focused parser/help checks, and Torch CUDA availability on A100. H100/GB200/FP8, TE/Apex/ModelOpt full paths, multi-node scale, external services, credentials, and large training remain optional or unverified unless a later run proves them.
