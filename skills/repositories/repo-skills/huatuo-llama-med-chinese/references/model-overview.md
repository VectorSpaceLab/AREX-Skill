# Model and Workflow Overview

Read this when choosing a Huatuo/BenTsao model family, LoRA adapter, prompt template, or resource plan.

## Repository purpose

Huatuo-Llama-Med-Chinese / BenTsao provides Chinese medical instruction-tuning workflows and released LoRA adapters for several base-model families. The repository combines medical knowledge-graph QA data, medical literature dialogue data, LoRA fine-tuning scripts, inference scripts, prompt templates, and benchmark assets.

## Base-model families and prompt templates

| Family or workflow | Typical role | Prompt template |
| --- | --- | --- |
| LLaMA / Chinese Alpaca medical QA | Medical-knowledge QA with Huatuo/BenTsao LoRA adapters. | `med_template` |
| LLaMA literature adapter | Liver-cancer literature single-/multi-turn dialogue. | `literature_template` |
| Bloom / Huozi medical QA | Bloom-family or Huozi-family Chinese QA adapters. | `bloom_deploy` |
| Baseline LLaMA or Alpaca comparisons | Compare base/Alpaca/medical adapter behavior. | Template must match the baseline runner and available template assets. |

The prompt helper resolves `templates/<name>.json` relative to the process current working directory in the original implementation. The bundled prompt/data sub-skill documents this behavior and provides a stdlib validator.

## LoRA adapter assets

Released LoRA adapters are expected to look like PEFT adapter directories:

```text
adapter_config.json
adapter_model.bin
```

The repository documentation names adapters for Huozi, Bloom, Chinese Alpaca, LLaMA medical-knowledge tuning, and LLaMA literature tuning. The skill does not bundle those weights; users must provide local paths or runtime-resolved model ids.

## Data assets

- Medical QA inference examples use JSON Lines records with `instruction`, `input`, and `output`.
- Training data uses the same JSONL shape.
- Literature data is a JSON list of dialogue records where `instruction` may contain `<user>:` and `<bot>:` turns.
- CMCOQA benchmark assets contain questions and ICD-10 categories, not a complete automatic evaluation harness.

Route data-format questions to [../sub-skills/prompt-data-formats/SKILL.md](../sub-skills/prompt-data-formats/SKILL.md).

## Resource expectations

- Full LoRA fine-tuning is a GPU workflow. The README describes an A100-SXM-80GB example with batch size 128 and about 2h17m for 10 epochs; 24GB GPUs may require smaller micro-batches, shorter cutoff lengths, or other memory reductions.
- Batch/literature inference in the observed scripts is effectively CUDA-required because the script-level `device` variable is only defined when CUDA is available.
- Gradio-style serving can expose a medical model; bind locally and avoid public share links unless explicitly approved.
- Export/merge can run on CPU in principle, but 7B-scale model loading still requires enough RAM and disk space.

## Medical-use limitation

The repository itself warns that generated content is affected by model computation, randomness, data quality, and quantization/precision. Treat all outputs as research artifacts. Do not present model responses as diagnosis, treatment instructions, or clinical advice without domain review.
