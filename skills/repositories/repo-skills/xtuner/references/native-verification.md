# Native Verification Guidance

Read this before deciding whether an XTuner workflow was actually verified in a target environment.

## Verification levels

| Level | What it proves | What it does not prove |
|---|---|---|
| Static syntax/import | Files and Python imports are loadable | Training, CUDA kernels, Ray rollout, data/model correctness |
| CLI help | Parser and import-time dependencies are present | The command can train or serve a model |
| Schema/helper tests | Data records or generated command snippets are structurally sound | Tokenizer-specific length/label behavior or model training success |
| Torch CUDA smoke | PyTorch can see and allocate on CUDA | XTuner FP8, flash-attn, grouped GEMM, DeepEP, training throughput, or RL backend success |
| Native tiny training/RL case | A selected workflow runs on actual backend/resources | Large-scale throughput, all model families, or unrelated backends |

## Safe native candidates

Use safe checks first:

```bash
python scripts/check_xtuner_install.py --check-sft-help --check-rl-help --json
python sub-skills/data-preparation/scripts/validate_xtuner_jsonl.py sample.jsonl --mode sft
python sub-skills/training/scripts/build_sft_command.py --help
python sub-skills/reinforcement-learning/scripts/build_rl_command.py --help
```

When package dependencies are available, useful native checks include:

- SFT CLI help: `python -m xtuner.v1.train.cli.sft --help`.
- RL CLI help: `python -m xtuner.v1.train.cli.rl --help`.
- A tiny CUDA torch allocation if the task needs GPU visibility.
- CPU-safe unit-test subsets only when they are short, deterministic, and do not need model downloads, private paths, Ray clusters, or long training.

## Accelerator cases

XTuner's documented quick-start training and RL examples are accelerator workflows. Treat them as optional unless the user specifically asks for backend proof.

Before running a GPU/NPU/native case, confirm:

- Model checkpoint or config is local and small enough for the target device.
- Dataset or fixture is local and validated.
- The chosen optional packages are installed: FlashAttention, bitsandbytes CUDA binary, GroupedGEMM, AdaptiveGEMM, DeepEP, LMDeploy/SGLang/vLLM, or NPU vendor stack as applicable.
- The command is short, bounded, writes only to approved output directories, and will not download or mutate external state unexpectedly.

Do not convert these into passes:

- A skipped GPU training command.
- A CPU import standing in for FP8/grouped-GEMM/NPU/RL backend execution.
- A synthetic JSONL validator case standing in for tokenizer/model training behavior.
- A Ray command builder output standing in for a running Ray cluster.

## Result labels

When recording verification, use these meanings:

- `PASS`: the selected check ran and matched the expected signal.
- `SKILL_GAP`: the generated skill guidance or helper was wrong or too thin and was revised.
- `NATIVE_FAIL`: the original package/native workflow failed for reasons not caused by the skill.
- `BLOCKED_REQUIRED_BACKEND`: a required hardware/backend/package/service was unavailable. This is not a skip.
- `SKIP_UNSAFE`: command would download, require credentials, run long training, consume excessive resources, or write destructively.
- `SKIP_NOT_SELECTED`: capability is outside the user-approved verification scope.

For this generated skill, import was explicitly disabled by the construction request. A future import decision still needs a fresh verification/readiness review in the target environment.
