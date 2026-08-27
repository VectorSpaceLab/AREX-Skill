# Installation and Environment Notes

Read this before importing `otter_ai`, choosing dependency pins, or deciding whether a failure is an install issue versus a workflow issue.

## Package identity

- Distribution name: `otter-ai`
- Import name: `otter_ai`
- Public root exports: `OtterForConditionalGeneration` and `FlamingoForConditionalGeneration`
- Package version in the inspected source metadata: `0.0.0-alpha-7`
- Source layout: installable package code is under the Python package tree; many training, benchmark, serving, MIMIC-IT, and demo scripts are checkout workflows rather than installable console scripts.

## Public setup patterns

For a target checkout:

```bash
python -m pip install -e .
python -c "import otter_ai; from otter_ai import OtterForConditionalGeneration; print('ok')"
```

The repository also documents a Conda environment with Python 3.9 and `pip` installing `requirements.txt`.

```bash
conda env create -f environment.yml
```

Use that only when the user wants a broad Otter development/training environment. For lightweight tasks, prefer a minimal environment plus the bundled validators/builders in this skill.

## Compatibility pins that matter

Repository metadata pins `transformers==4.35.1` and `tokenizers==0.14.1` while allowing broad versions of `accelerate`, `peft`, and `huggingface_hub`. Live inspection found that the latest resolver choices can break `otter_ai` imports because newer Accelerate/PEFT expect newer Hugging Face Hub APIs while `tokenizers==0.14.1` constrains the hub package.

Known compatible repair set from inspection:

```bash
python -m pip install "transformers==4.35.1" "tokenizers==0.14.1" \
  "huggingface_hub==0.17.3" "accelerate==0.23.0" "peft==0.4.0"
```

Use this as troubleshooting evidence, not as a universal lockfile. If the user intentionally upgrades Transformers, re-check the whole stack.

## Minimal import probe

Run the bundled root script from the skill directory:

```bash
python scripts/check_otter_environment.py --json
```

It checks importability and key dependency versions without starting model downloads, training, servers, or API calls.

## CUDA and hardware notes

- The repository docs discuss CUDA/PyTorch matching and historical success with CUDA 11.1/torch 1.10.1 and CUDA 11.7/torch 2.0.0.
- Real Otter/OpenFlamingo 9B inference commonly needs multiple high-memory GPUs. The Hugging Face model wrapper docs mention at least 33 GB GPU memory for OpenFlamingo-9B and multi-GPU sharding for commodity 24 GB GPUs.
- OtterHD/Fuyu training can require Flash-Attention 2 and fused operators. Treat those as optional performance dependencies; do not source-build them unless the user has approved build time, compiler/toolkit needs, and GPU target.

## Optional and workflow-specific dependencies

| Surface | Dependency notes |
|---|---|
| Package model import | `torch`, `transformers`, `accelerate`, `peft`, `einops`, `open_clip_torch`, and related requirements. |
| MIMIC-IT data validation | `pyyaml`, `orjson`, `pandas`, optional `pyarrow` for parquet checks. |
| Syphus | `openai` plus `litellm` imported by the current Syphus helper; API credentials or local OpenAI-compatible server are needed for actual generation. |
| Serving | `fastapi`, `uvicorn`, `gradio`, `requests`, model dependencies, and a patch for the missing `pipeline.constants` module in affected checkouts. |
| Benchmarks | Dataset/model-specific dependencies and optional GPT API keys for GPT-judged datasets. |

## Install triage order

1. Verify `python -m pip check` in the target environment.
2. Verify `import otter_ai` and the public model classes.
3. If imports fail inside Transformers/Accelerate/PEFT/Hugging Face Hub, apply the compatibility pin set or move the whole stack to a newer consistent Transformers version.
4. If serving modules fail before argparse with `pipeline.constants`, route to the serving sub-skill; this is a checkout code issue, not a generic pip install issue.
5. If Syphus fails on `litellm`, install/configure that optional dependency only when the user intends to run Syphus.
