# Environment and Installation

This repo skill is based on a scripts-first project rather than an installable Python package. Use the repository's public requirements as the starting point, then add only the optional packages needed for the selected workflow.

## Public Base Requirements

The repository pins:

```text
torch==1.13.1
git+https://github.com/huggingface/peft.git@13e53fc
transformers==4.30.0
sentencepiece==0.1.97
```

For safe inspection and parser checks, the generated skill's root environment probe can confirm the following optional packages when present:

- `datasets`
- `pandas`
- `numpy`
- `scikit-learn`
- `fastapi`
- `uvicorn`
- `shortuuid`
- `pydantic`
- `gradio`
- `langchain`
- `faiss` backend used by LangChain examples

## Suggested Environment Approach

- Prefer an isolated Conda or micromamba prefix when compiling or using torch-based stacks.
- Use Python 3.10 or 3.11 for older ML dependencies; this repo was verified against Python 3.10 for the inspection environment.
- Do not mutate the Python interpreter running the agent.
- Install optional extras only when the chosen sub-skill needs them.

## Safe Probe

```bash
python scripts/check_environment.py --include-optional
```

This check only imports packages and reports CUDA availability. It is safe to run before deciding whether a larger workflow is feasible.

## Workflow-Specific Additions

| Workflow | Extra packages / notes |
| --- | --- |
| Reconstruction | `huggingface_hub`, enough disk/RAM for model merging, and original LLaMA-compatible assets. |
| Inference / serving | `gradio` for UI, `fastapi`/`uvicorn`/`shortuuid`/`pydantic` for the API server, optional `langchain` and vectorstore packages for QA/summarization demos. |
| Training | `datasets`, `scikit-learn`, optional `deepspeed`, and a GPU-backed torch install appropriate for the user's model size. |
| C-Eval | `pandas`, `numpy`, `tqdm`, and a compatible model path plus C-Eval CSV data. |

If a user only wants help with command construction or parser inspection, the safe probe plus `--help` checks are usually enough. Do not start real model downloads or long jobs until the user confirms the final plan.
