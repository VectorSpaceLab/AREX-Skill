# XTuner Cross-Cutting Troubleshooting

Use this for install/import/backend failures before routing to workflow-specific troubleshooting.

## Package import or CLI help fails

Symptoms:

- `ModuleNotFoundError` while importing `xtuner.v1.train.cli.sft` or `xtuner.v1.train.cli.rl`.
- `python -m xtuner.v1.train.cli.sft --help` fails before printing Cyclopts help.
- `python -m xtuner.v1.train.cli.rl --help` fails because Ray is missing.

Actions:

1. Run the bundled environment check:

   ```bash
   python scripts/check_xtuner_install.py --check-sft-help --json
   ```

2. Install the package and missing extras in the target environment. For RL, include Ray and the chosen rollout backend.
3. If a missing dependency is not declared by the package metadata but is imported by XTuner at runtime, install that package explicitly and rerun the help check.
4. If only optional acceleration warnings remain and the user's task is not about that acceleration, continue with the relevant sub-skill.

## FlashAttention warning

Symptom:

```text
flash-attn is not installed, using flex_attention instead
```

Meaning: XTuner imported successfully but an optimized attention backend is unavailable. This is acceptable for command planning, JSONL validation, and many CPU/import checks. It is not acceptable if the user requested FA2/FA3 performance validation.

Actions:

- For ordinary planning: record the fallback and continue.
- For performance-sensitive training: install the FlashAttention variant compatible with the target torch/CUDA/Python stack, then run a small backend smoke before launching training.

## bitsandbytes CUDA binary mismatch

Symptoms:

- `Could not find the bitsandbytes CUDA binary ...`
- `installed version of bitsandbytes was compiled without GPU support`

Meaning: 8-bit optimizers, 8-bit matrix multiplication, and GPU quantization are unavailable for the current CUDA/runtime combination.

Actions:

- If the task is not quantized/8-bit training, record the limitation and continue.
- If quantization is required, install a bitsandbytes build matching the target CUDA/PyTorch combination or switch to a supported CUDA runtime.
- Do not claim QLoRA/8-bit optimizer readiness from a plain `import bitsandbytes` when this warning appears.

## CUDA is visible but XTuner backend is still unverified

A successful `torch.cuda.is_available()` proves only framework/device visibility. It does not prove that XTuner training, FP8, grouped GEMM, DeepEP, MLLM, or RL rollout works.

Actions:

1. Use `model-backends/scripts/check_xtuner_backend.py` for import/probe diagnostics.
2. For actual accelerator workflows, run a small native case appropriate to the selected backend and model family.
3. Treat missing flash-attn, grouped GEMM, AdaptiveGEMM, DeepEP, NPU vendor packages, or rollout engines as explicit optional capability gaps.

## Legacy `xtuner` command missing

The current package metadata may not expose a top-level `xtuner` console script. Do not force legacy workflows when the user really needs V1.

Actions:

- V1 SFT/pretraining/MLLM: route to `training` and use `python -m xtuner.v1.train.cli.sft`.
- V1 RL/GRPO: route to `reinforcement-learning` and use `python -m xtuner.v1.train.cli.rl`.
- Legacy config search/copy: route to `cli-and-tools` and use its bundled `find_legacy_configs.py` with an explicit config-root supplied by the user.
- Legacy chat/eval/conversion: require an environment exposing the legacy router plus model/data assets; do not rely on source-tree script paths from this generated skill.

## Model/data path confusion

Common XTuner failures come from passing cache roots instead of actual HF model snapshots, or passing JSONL directories/files that do not match the selected tokenization path.

Actions:

- A model path should point to a directory with `config.json` and model files, not just a cache root with `blobs/`, `refs/`, and `snapshots/`.
- Validate SFT/MLLM/RL records with `data-preparation/scripts/validate_xtuner_jsonl.py` before launching.
- Use a Python config file when the workflow needs custom tokenizer functions, MLLM `media_root`, preset packing, advanced FSDP, or RL resource/trainer topology.

## Side-effect guardrails

Stop and ask before:

- Starting training, Ray, model conversion, benchmark evaluation, or downloads.
- Writing to user work directories, checkpoint directories, or model output directories.
- Installing broad accelerator stacks or mutating a user-owned environment.
- Running cluster, multi-node, NPU, or service-backed cases.
