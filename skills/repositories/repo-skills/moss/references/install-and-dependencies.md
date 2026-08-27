# MOSS install and dependency guidance

## Purpose

Read this before preparing an environment for MOSS runtime work. MOSS is a
source-code and Hugging Face remote-code model release, not a conventional
installable Python package with `pyproject.toml` or `setup.py` metadata.

## Baseline dependencies

The public requirement set used for this skill includes:

- Python 3.8 class of runtime for the original scripts.
- `torch==1.13.1` with CUDA-capable wheels when GPU execution is required.
- `transformers==4.25.1` for `AutoTokenizer`, `AutoConfig`, and
  `AutoModelForCausalLM` remote-code loading.
- `sentencepiece`, `datasets`, `accelerate`, `matplotlib`, and
  `huggingface_hub`.
- `triton` for documented GPTQ quantized inference.
- `streamlit`, `gradio`, and `mdtex2html` for UI demos.
- FastAPI/Uvicorn when exposing the API service.
- TensorBoard/TQDM/PyYAML/DeepSpeed-related packages when planning full SFT.

Install only what the selected workflow needs. Do not install Jittor,
DeepSpeed, UI packages, or GPU-specific packages merely to run a prompt-format
or JSON-schema helper.

## Source-root import model

For a local checkout, MOSS runtime modules are imported from the checkout source
root, for example `models.configuration_moss`, `models.modeling_moss`, and
`models.tokenization_moss`. For Hugging Face checkpoint usage, use
`trust_remote_code=True` so the checkpoint's custom model/tokenizer code can be
loaded.

Safe source-root import checks:

```bash
python scripts/check_moss_env.py --repo-root /path/to/MOSS --json
python sub-skills/model-runtime/scripts/check_model_runtime.py --repo-root /path/to/MOSS --json
```

These checks do not download checkpoints.

## Backend selection

| Workflow | Minimum useful backend | Notes |
| --- | --- | --- |
| Prompt formatting, command planning, request templates, SFT schema validation | CPU / stdlib | No model imports are required for most bundled helpers. |
| Class import and tiny config/model inspection | CPU with PyTorch + Transformers | Does not prove full generation. |
| Real FP16 chat generation | CUDA strongly expected | Memory depends on prompt/context; model parallelism can use FP16 checkpoint. |
| INT4/INT8 generation | CUDA + Triton-compatible Linux/WSL | Quantized checkpoints are single-GPU only. |
| FastAPI/Gradio/Streamlit serving | Same as generation plus service/UI deps | Startup loads a checkpoint. |
| Full SFT fine-tuning | Multi-GPU CUDA + Accelerate/DeepSpeed + storage | Training-scale; not a smoke test. |
| Jittor runtime | Separately installed Jittor | Optional; not part of baseline requirements. |

## Verification evidence captured during creation

The private inspection environment used for this generated skill verified:

- Python 3.8.20.
- `pip check` with no broken requirements.
- `torch 1.13.1+cu117`, `transformers 4.25.1`, `accelerate 1.0.1`,
  `huggingface_hub 0.36.2`, and `datasets 3.1.0`.
- CUDA availability with eight A100-class devices and a tiny CUDA tensor.
- Safe imports of MOSS configuration, tokenizer, model class, inference wrapper,
  and SFT dataset loader from source evidence.

Do not copy local environment paths from that private setup into user-facing
commands. Use the generic commands in this skill instead.

## Common install choices

- For pure planning: install nothing beyond Python; most bundled helpers are
  stdlib-only.
- For runtime import checks: install PyTorch, Transformers, Accelerate, and
  Hugging Face Hub, then provide a MOSS source root or use Hugging Face remote
  code.
- For UI work: add Gradio/Streamlit/mdtex2html only when the UI route is needed.
- For API work: add FastAPI and Uvicorn only when serving is needed.
- For training: add DeepSpeed intentionally and match its version to the host
  CUDA/PyTorch stack.

## Do not do this

- Do not treat `pip install -e .` as guaranteed; the repository has no package
  metadata for that workflow.
- Do not call a CPU import check a successful CUDA inference proof.
- Do not install all optional backends when only prompt or data validation is
  needed.
- Do not run full checkpoint generation, service launch, or SFT training just
  to confirm dependency installation.
