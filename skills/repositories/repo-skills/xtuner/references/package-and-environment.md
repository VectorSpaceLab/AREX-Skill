# XTuner Package and Environment Reference

Read this before installing, importing, or troubleshooting XTuner in a target environment.

## Package identity

- Distribution/import root: `xtuner`.
- Python support from package metadata: `>=3.10`.
- The skill was generated from XTuner package version `0.2.0`; check [repo provenance](repo-provenance.md) before assuming a checkout matches.
- XTuner V1 uses installed-package Python module entry points such as `python -m xtuner.v1.train.cli.sft` and `python -m xtuner.v1.train.cli.rl`.

## Baseline install patterns

For ordinary installed-package use:

```bash
python -m pip install xtuner
python -m xtuner.v1.train.cli.sft --help
```

For editable development from a trusted local checkout:

```bash
python -m pip install -e .
python -m xtuner.v1.train.cli.sft --help
```

For RL planning, install XTuner's RL extra or equivalent Ray dependencies, then install exactly one rollout backend needed by the task:

```bash
python -m pip install 'xtuner[rl]'
python -m xtuner.v1.train.cli.rl --help
```

The generated RL command builder does not start Ray or install LMDeploy/SGLang/vLLM. Verify those packages separately when the user selects a rollout backend.

## Optional acceleration surfaces

XTuner can benefit from optional packages and hardware-specific stacks. Treat each as a separate gate:

| Surface | Why it matters | Verify before claiming |
|---|---|---|
| CUDA-enabled PyTorch | Core GPU training and many model/backend tests | `torch.cuda.is_available()`, device count, tiny CUDA tensor allocation |
| FlashAttention / FA3 | Faster attention paths; XTuner may warn and fall back to `flex_attention` | import package and run a small supported attention smoke in the target stack |
| bitsandbytes | 4/8-bit quantization and 8-bit optimizers | wheel has a CUDA binary matching local CUDA; quantization path imports cleanly |
| GroupedGEMM / AdaptiveGEMM | MoE and FP8 grouped GEMM acceleration | package import plus tiny kernel/backend smoke on compatible GPU |
| DeepEP / all-to-all dispatchers | MoE expert dispatch | distributed backend and dispatcher import/smoke on target cluster |
| NPU/vendor backends | Ascend/vendor accelerator training | vendor framework/runtime and NPU smoke; CUDA checks do not apply |
| Ray + LMDeploy/SGLang/vLLM | RL rollout workers and inference services | Ray cluster status, selected backend import, model load/resource check |

## Safe smoke script

Run the bundled root helper from this generated skill tree:

```bash
python scripts/check_xtuner_install.py --json
```

Useful flags:

- `--check-sft-help`: also run `python -m xtuner.v1.train.cli.sft --help`.
- `--check-rl-help`: also run `python -m xtuner.v1.train.cli.rl --help`.
- `--no-cuda`: skip CUDA probing when running on a CPU-only host or where GPU access is intentionally hidden.

## Known construction-time warnings

The construction environment proved XTuner package metadata/imports, SFT/RL help, and a CUDA tensor allocation. It also observed optional warnings that are common in XTuner environments:

- FlashAttention was not installed, so XTuner warned that it would use `flex_attention` instead.
- The installed bitsandbytes wheel did not include a CUDA 13.0 binary, so 8-bit optimizer/quantization paths were unavailable in that environment.
- LMDeploy, SGLang, vLLM, DeepSpeed, GroupedGEMM, AdaptiveGEMM, and NPU stacks were not installed for this skill build; do not infer those capabilities in a target environment without fresh checks.

These warnings are not fatal for schema validation, command planning, or many CPU-safe inspections. They are fatal only when the user's requested workflow specifically requires the missing backend.
