---
name: x-turing
description: "Route xTuring dataset preparation, model loading and inference,
  fine-tuning and DPO alignment, CLI/API/UI serving, and evaluation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# xTuring

Use this skill for the public xTuring package (`xturing`) when you need to prepare data, choose or load models, fine-tune or align a causal model, serve the model through CLI/API/UI, or run the built-in evaluation scaffold.

## Install and smoke-check

Install from the repository root:

```bash
pip install -e .
```

If you need the full training, quantization, or provider stack, make sure the environment can satisfy the package dependencies in `pyproject.toml` and the backend notes in the troubleshooting guide.

Quick import smoke:

```bash
python -I -c "import importlib.metadata as md; import xturing; from xturing.models import BaseModel; from xturing.datasets import TextDataset, InstructionDataset, PreferenceDataset; from xturing.evaluation import LMEvalAdapter; print(md.version('xturing'))"
```

For a broader readiness check, run `scripts/check_xturing_environment.py`.

## Route to the right sub-skill

| Task family | Start here | Notes |
| --- | --- | --- |
| Dataset construction, validation, Alpaca conversion, or self-instruct generation | `sub-skills/data-prep-and-generation/SKILL.md` | Use for `TextDataset`, `InstructionDataset`, `PreferenceDataset`, JSONL, and API-backed data generation. |
| Model choice, load/save, generation, hub paths, or registry lookup | `sub-skills/models-and-inference/SKILL.md` | Use for `BaseModel.create`, `BaseModel.load`, `generate`, and model catalog questions. |
| SFT fine-tuning, LoRA, quantized variants, or DPO alignment | `sub-skills/training-and-alignment/SKILL.md` | Use for `model.finetune(...)`, `model.dpo_finetune(...)`, and trainer config issues. |
| `xturing chat`, `xturing api`, `xturing ui`, or FastAPI/Gradio behavior | `sub-skills/cli-api-ui/SKILL.md` | Use for terminal chat, the API server, and the playground UI. |
| Perplexity scoring or adapter-based evaluation artifacts | `sub-skills/evaluation/SKILL.md` | Use for `model.evaluate(...)`, `run_eval_adapter(...)`, and JSON result persistence. |

## Shared notes

- The package name is `xturing`; the public repo skill id is `x-turing`.
- `references/repo-provenance.md` records the source commit and package snapshot used to generate this skill.
- `references/troubleshooting.md` collects cross-cutting install, import, optional dependency, and backend issues.
- `references/source-script-inventory.md` lists the source examples and maintenance helpers that were distilled into bundled skill helpers or references.
- `references/repo-routing-metadata.json` is consumed by the repo-skill router during later import or refresh flows.

## When you are unsure

- If the request mentions a dataset schema, start with the data-prep skill.
- If it mentions a model key, checkpoint, or `generate(...)`, start with the model skill.
- If it mentions LoRA, CPU int8, k-bit, or DPO, start with the training skill.
- If it mentions a command-line or HTTP route, start with the CLI/API/UI skill.
- If it mentions perplexity or `EvalRunResult`, start with the evaluation skill.

Do not depend on the original repository checkout for any runtime guidance; use the bundled references and scripts inside this skill tree instead.
