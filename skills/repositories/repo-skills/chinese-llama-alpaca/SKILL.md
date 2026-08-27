---
name: chinese-llama-alpaca
description: "Route Chinese-LLaMA-Alpaca model reconstruction,
  inference/deployment, training/fine-tuning, and evaluation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Chinese-LLaMA-Alpaca Repo Skill

Use this repo skill when a task involves the original Chinese-LLaMA-Alpaca project: Chinese LLaMA/Alpaca LoRA adapters, tokenizer expansion, LoRA reconstruction, local Transformers inference, Gradio or OpenAI-compatible serving, LangChain demos, PEFT pretraining/SFT, C-Eval, or the repo's example benchmark tables. The command examples below assume the current working directory is this generated skill root.

This skill is self-contained for workflow guidance and bundled helper scripts, but it does **not** provide original LLaMA weights, Chinese LoRA downloads, C-Eval data, API keys, or permission to use restricted assets commercially. Always confirm asset/license, hardware, network, service, and budget constraints before running heavyweight commands.

## Start Here

1. Read [`references/repo-provenance.md`](references/repo-provenance.md) when checking freshness against a repository checkout.
2. Read [`references/model-family-overview.md`](references/model-family-overview.md) to choose Chinese LLaMA versus Chinese Alpaca, size, Plus/Pro, and tokenizer family.
3. Read [`references/environment-and-installation.md`](references/environment-and-installation.md) before creating an environment or installing optional dependencies.
4. Run [`scripts/check_environment.py`](scripts/check_environment.py) for a safe dependency/backend probe.
5. Use [`scripts/verify_sha256.py`](scripts/verify_sha256.py) with the checksum reference when checking downloaded model/tokenizer assets.
6. Use [`references/troubleshooting.md`](references/troubleshooting.md) for cross-cutting install/import/asset/backend failures.
7. Use [`references/compliance-and-limitations.md`](references/compliance-and-limitations.md) before publishing outputs or advising on commercial/safety-sensitive use.

## Route Map

| User request | Use |
| --- | --- |
| "Merge Chinese Alpaca LoRA with LLaMA", "convert to HF/PTH", "tokenizer mismatch", "verify adapter checksum" | [`sub-skills/model-reconstruction/`](sub-skills/model-reconstruction/) |
| "Run inference", "batch predictions", "interactive single-turn", "Gradio demo", "OpenAI API server", "LangChain QA" | [`sub-skills/inference-deployment/`](sub-skills/inference-deployment/) |
| "Prepare SFT data", "validate instruction JSON", "pretrain Chinese LLaMA", "fine-tune Alpaca LoRA", "DeepSpeed/PEFT args" | [`sub-skills/training-finetuning/`](sub-skills/training-finetuning/) |
| "Run C-Eval", "validate C-Eval data", "interpret examples scores", "compare q4/q8/Plus/Pro" | [`sub-skills/evaluation-benchmarks/`](sub-skills/evaluation-benchmarks/) |

## Minimal Public Environment Check

The original `requirements.txt` pins:

```text
torch==1.13.1
transformers==4.30.0
sentencepiece==0.1.97
PEFT from the repository's pinned Hugging Face commit
```

Additional workflows need optional packages such as `datasets`, `pandas`, `scikit-learn`, `fastapi`, `uvicorn`, `shortuuid`, `gradio`, `langchain`, FAISS, or DeepSpeed. Install only the optional group required by the selected workflow.

Safe check from the generated skill root:

```bash
python scripts/check_environment.py --include-optional
```

Use `python scripts/verify_sha256.py /path/to/file --expected name=hex` from the same skill root when validating downloaded model, tokenizer, or data files. These helpers only import packages, check CUDA visibility, or hash files; they do not download models, launch servers, run training, or read credentials.

## Common Boundaries

- If a user only has LoRA files and wants generation, reconstruct or load the LoRA with a compatible base model first.
- If a user wants chat/instruction following, prefer Chinese Alpaca and use the Alpaca prompt template. Chinese LLaMA is base/continuation-oriented.
- If a user wants training, validate data before allocating GPUs. Real training is long-running.
- If a user wants benchmark claims, record model path, dataset, decoding flags, hardware, and skipped/failed cases; do not infer global quality from example tables.
