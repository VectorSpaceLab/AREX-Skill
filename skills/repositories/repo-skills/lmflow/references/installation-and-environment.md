# Installation and Environment

## Purpose

Read this before importing or using the LMFlow package skill. It summarizes the supported install pattern, optional extras, and backend split rules that matter for future agents.

## Baseline Install

LMFlow is a Python package named `lmflow` with version `1.1.0` in the inspected checkout.

From the repository root:

```bash
python -m pip install -e .
```

The repository declares Python `>=3.9`. The inspected environment used Python 3.10 successfully.

## Optional Extras

Install only the extra you need for the selected workflow:

| Extra | Enables | Notes |
| --- | --- | --- |
| `vllm` | vLLM inference and iterative DPO rollout paths | Requires a separate environment from SGLang. |
| `sglang` | SGLang inference and iterative DPO rollout paths | Requires a separate environment from vLLM. |
| `trl` | DPO, DPOv2, and iterative DPO | Needed for post-training alignment workflows. |
| `deepspeed` | DeepSpeed integration and distributed launch paths | Useful for larger training/evaluation runs. |
| `flash_attn` | Flash Attention 2 support | Optional performance path; not required for base imports. |
| `ray` | Ray-backed reward-model inference and related text-regression helpers | Install the full extra, not a partial namespace package. |
| `multimodal` | Image/text data and multimodal model helpers | Pulls in Pillow-based features. |
| `gradio` | Gradio chatbot UI helpers | Optional UI-only dependency. |
| `flask` | Flask service helpers | Optional service-only dependency. |

Examples:

```bash
python -m pip install -e ".[trl]"
python -m pip install -e ".[vllm]"
python -m pip install -e ".[sglang]"
```

## Backend Split Rules

- vLLM and SGLang should not be installed into the same environment because their CUDA/PyTorch stacks conflict.
- Base LMFlow import and dataset utilities can be inspected without the optional engines.
- CUDA-capable torch is required for genuine GPU workflows, but CPU inspection is enough for the offline route map and unit tests.
- Some LMFlow modules guard optional imports, but the safe default is still to install the matching extra before asking future agents to use that workflow.

## Import Smoke

Use a clean shell or isolated Python when verifying the package:

```bash
python -c "import lmflow; print(lmflow.__version__)"
```

If you are debugging optional import issues, run the environment checker script in this skill tree and inspect the troubleshooting reference for next steps.
