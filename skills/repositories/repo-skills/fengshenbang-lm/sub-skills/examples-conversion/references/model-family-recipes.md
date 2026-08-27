# Model-family example recipe map

This reference converts Fengshenbang-LM example families into planning guidance. It is intentionally high level: common pipeline mechanics live in `../pipelines-cli/SKILL.md`, model class/config/tokenizer internals live in `../model-zoo/SKILL.md`, and dataloaders/Trainer/checkpoint flags live in `../data-training/SKILL.md`.

## Family map

| Family | Main demand/task | Typical model IDs or package surface | Example-family actions | Safe handling here |
|---|---|---|---|---|
| Ziya | General large language model: translation, coding, text classification, information extraction, summarization, copy generation, QA, math | `IDEA-CCNL/Ziya-LLaMA-13B-*`, Fengshen LLaMA modules | HF inference, bitsandbytes quantized inference, llama.cpp quantized inference, full-parameter fine-tune, HF/Fengshen/tensor-parallel conversion | Use [ziya-llama.md](ziya-llama.md) and `../scripts/plan_ziya_conversion.py`; do not run conversion or fine-tune without explicit mutation/resource approval. |
| Erlangshen | NLU: classification, matching, NLI, CLUE/FewCLUE/ZeroCLUE | Megatron-BERT/Roberta/DeBERTa/UniMC/Ubert variants | Downstream classification, CLUE leaderboard conversion, UniMC for classification-style tasks, Ubert for extractive QA | Use [clue-and-task-recipes.md](clue-and-task-recipes.md); route CLI/data schema details to `../pipelines-cli/SKILL.md`. |
| Randeng | NLT/NLG: summarization, question generation, generative QA, translation, causal reasoning | T5, BART, PEGASUS, DeltaLM, Transformer-XL | LCSTS summary, ChineseSQuAD question generation, CMRC/ChineseSQuAD generative QA, DeltaLM translation, deduction/abduction generation | Use [nlg-nlt-recipes.md](nlg-nlt-recipes.md); treat full training as GPU/Deepspeed optional. |
| Wenzhong / Yuyuan | Domain NLG and medical close-book QA | GPT2-style large models, medical QA variants | Prompted close-book QA fine-tune/inference, FastDemo-style UI demo | Use [nlg-nlt-recipes.md](nlg-nlt-recipes.md) and [troubleshooting.md](troubleshooting.md); do not start Streamlit/FastAPI services as verification. |
| Taiyi | Multimodal: Chinese/Bilingual text-to-image, CLIP, diffusion fine-tune, DreamBooth | `IDEA-CCNL/Taiyi-Stable-Diffusion-1B-Chinese-v0.1`, `IDEA-CCNL/Taiyi-Stable-Diffusion-1B-Chinese-EN-v0.1`, Taiyi CLIP | Diffusers inference, FP16 CUDA inference, full fine-tune, DreamBooth, Diffusers-to-original checkpoint conversion | Use [taiyi-diffusion.md](taiyi-diffusion.md); use `../scripts/check_recipe_requirements.py` before proposing any execution. |
| Unified NLU pipelines | Prompt/unified classification/extraction | UniMC, UniEX, Ubert, TCBert | Prompt schemas, extraction schemas, pipeline prediction/training | This sub-skill only references them for CLUE/task recipes; operational details belong to `../pipelines-cli/SKILL.md`. |
| Pretraining examples | Large-scale BERT/T5/BART/DeBERTa/Hubert/CLIP pretraining | Megatron/Lightning/Deepspeed scripts | Corpus pretraining, tokenizer preparation, distributed runs | Reference-only. Use `../data-training/SKILL.md` for data/training planning; do not run. |

## Recipe selection checklist

Before writing a command or suggesting a model family, identify:

1. **Task family**: classification/CLUE, summarization, QA, question generation, translation, text-to-image, LLaMA chat/instruction, conversion, or demo/API.
2. **Model source**: model ID, local model cache, local checkpoint directory, delta weights, or tensor-parallel shards.
3. **Allowed side effects**: downloads, checkpoint writes, training writes, service startup, and network calls must be explicitly allowed before any execution.
4. **Backend**: CPU, CUDA, number of GPUs, per-GPU VRAM, RAM, and desired precision.
5. **Data format**: JSONL fields, image/text sidecars, prompt/answer fields, source/target translation files, or CLUE public layout.
6. **Routing**: if the request is about CLI mechanics, model internals, or training arguments, route to the sibling sub-skill rather than duplicating details here.

Use the static requirement checker for a quick first pass:

```bash
python ../scripts/check_recipe_requirements.py --recipe ziya-finetune --device cuda --gpus 8 --vram-gb 80
python ../scripts/check_recipe_requirements.py --recipe taiyi-inference --device cpu --precision fp32
python ../scripts/check_recipe_requirements.py --recipe nlg-summary --device cuda --gpus 1 --vram-gb 24
```

## Safety classification of example families

| Family | Safe to run as verification? | Why |
|---|---:|---|
| Requirement/planner helpers in this skill | Yes | Static only; no imports that download models; no writes except stdout. |
| Pipeline help/parser inspection | Yes, but belongs to `../pipelines-cli/SKILL.md` | Help parsing does not load a pretrained model. |
| CLUE preprocessing/submission adapters | Usually not bundled here | They mutate local output files and assume downloaded benchmark data; document the schema instead. |
| Summary/QA/translation fine-tune scripts | No by default | They require datasets, model downloads, Lightning/Deepspeed, and checkpoint outputs. |
| Taiyi/Ziya inference | No by default | `from_pretrained` may download large models and memory requirements are high. |
| Taiyi/Ziya fine-tune | No | Heavy CUDA/Deepspeed, large checkpoints, and long runtimes. |
| Checkpoint conversion utilities | No | They intentionally write model outputs and may delete or overwrite target paths. |
| FastDemo/API demos | No | They start services or call backends and may contain placeholder network endpoints. |

## Model source and citation notes

- Public model identifiers used by the examples are in the `IDEA-CCNL` model namespace. Treat a model ID as a possible network download unless the user confirms it is already cached or gives a local path.
- Cite the Fengshenbang project as: Fengshenbang 1.0, arXiv:2209.02970. For UniMC-specific work, cite the UniMC paper arXiv:2210.08590 when relevant.
- For Taiyi Stable Diffusion outputs or fine-tuning, also acknowledge the Stable Diffusion lineage and any downstream model/dataset license constraints.
- For Ziya delta-weight workflows, verify that the user has rights to the base LLaMA-compatible checkpoint and the delta checkpoint before constructing a full target model.

## Common planning patterns

### Classification or CLUE

1. Decide whether the request is generic classification or CLUE leaderboard reproduction.
2. For generic classification, route command/data details to `../pipelines-cli/SKILL.md`.
3. For CLUE, use [clue-and-task-recipes.md](clue-and-task-recipes.md) to distinguish UniMC classification-style tasks from Ubert CMRC2018 extractive QA.
4. Keep official benchmark download/submission steps as user-managed external steps.

### NLG/NLT

1. Identify the transformation: text-to-summary, context+answer-to-question, context+question-to-answer, source-to-target translation, or causal reasoning.
2. Choose model family: Randeng T5/BART/Pegasus/DeltaLM/Transformer-XL, or Yuyuan/Wenzhong GPT2 for close-book medical QA.
3. Use [nlg-nlt-recipes.md](nlg-nlt-recipes.md) for prompt/data shape and resource gates.

### Taiyi diffusion

1. If the user asks for inference only, choose CPU/full precision only for small tests or offline planning; choose FP16 CUDA only when CUDA and compatible `torch`/`diffusers` are available.
2. If the user asks for fine-tuning/DreamBooth, require image/text data, output path, VRAM/RAM, precision, and checkpoint backup plan.
3. Use [taiyi-diffusion.md](taiyi-diffusion.md).

### Ziya LLaMA

1. Determine source format: delta, HF full checkpoint, Fengshen single-shard, Fengshen tensor-parallel shards, or llama.cpp artifact.
2. Determine target: inference, quantized inference, full fine-tune, generate from fine-tuned Fengshen checkpoint, or export back to HF.
3. Run the dry-run planner, then follow [ziya-llama.md](ziya-llama.md).
