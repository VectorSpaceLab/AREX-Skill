# Installation and Extras

## Core Install

For normal OpenCompass usage, install the base package first:

```bash
pip install -U opencompass
python -c "import opencompass; print(opencompass.__version__)"
opencompass --help
```

For source development or newest features, use an editable install from a checkout:

```bash
pip install -e .
```

The base runtime dependency set is broad because OpenCompass covers many benchmark families, metrics, model adapters, and data formats. If a task only needs config inspection or CLI help, do not treat successful help output as proof that model downloads, accelerator execution, API calls, or judge evaluation will work.

## Optional Extras

| Extra | Use when | Notes |
| --- | --- | --- |
| `opencompass[api]` | API-provider models or judge services need provider SDKs | Still requires runtime credentials and service endpoints. |
| `opencompass[lmdeploy]` | LMDeploy local/service acceleration is selected | Keep in a separate environment from vLLM when dependencies conflict. |
| `opencompass[vllm]` | vLLM acceleration is selected | Verify CUDA, driver, vLLM, PyTorch, and model architecture compatibility. |
| `opencompass[full]` | Dataset families need optional code-eval/science/math/data dependencies | Python 3.10 is safer for `pyext`-backed code-execution datasets; Python >=3.11 skips `pyext`. |

Avoid installing every extra by default. Choose the smallest environment that covers the selected model, dataset, backend, and evaluator.

## Backend Runtime Checks

- HuggingFace model execution needs compatible `torch`, `transformers`, tokenizers, model weights access, and enough CPU/GPU memory.
- API model execution needs provider SDKs, API keys, base URLs when non-default, rate-limit settings, and no secret leakage in configs.
- LMDeploy/vLLM execution needs matching optional packages and compatible CUDA/driver/model support.
- LLM-as-judge evaluation needs a judge model config or `OC_JUDGE_MODEL`, `OC_JUDGE_API_KEY`, and `OC_JUDGE_API_BASE` when using environment-variable configuration.

## Minimal Smoke Commands

```bash
python scripts/opencompass_environment_check.py
opencompass --help
opencompass path/to/config.py --dry-run -w outputs/plan
```

`--dry-run` checks config/task planning. It does not prove inference quality, model downloads, API reachability, or accelerator health.
