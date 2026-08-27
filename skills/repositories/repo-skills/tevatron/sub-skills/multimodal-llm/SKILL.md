---
name: multimodal-llm
description: "Plan Tevatron multimodal and LLM retriever/ranker workflows,
  including Qwen, ColPali, DSE, RepLLaMA, RankLLaMA, vLLM, and asset-aware
  datasets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Multimodal and LLM Workflows

Use this sub-skill when a Tevatron task names multimodal retrievers, large LLM retrievers, Qwen-family embedding or vision/audio models, ColPali, DSE, RepLLaMA, RankLLaMA, vLLM encoding, LoRA adapters, or dataset assets for image/audio/video records.

Do not use this sub-skill for ordinary text JSONL schema work, generic dense training, FAISS search mechanics, or generic cross-encoder reranking. Route those to `../data-preparation/`, `../training/`, `../encoding-retrieval/`, or `../reranking/` and use this sub-skill only for multimodal/LLM-specific choices.

## Start Here

1. Read `references/multimodal-workflows.md` to choose Qwen2.5-VL, Qwen-Omni, DSE, ColPali, `train_mm`, `encode_mm`, `vllm_encode_mm`, asset fields, and modality toggles.
2. Read `references/llm-retrievers.md` for RepLLaMA, Qwen3-Embedding, RankLLaMA routing, LoRA, pooling, prefixes, padding, EOS, and text `vllm_encode` trade-offs.
3. Run `python scripts/check_multimodal_dependencies.py --workflow <profile> --json` before recommending a multimodal or LLM command in a minimal environment.
4. Read `references/troubleshooting.md` before changing asset paths, processor/tokenizer names, vLLM flags, FlashAttention settings, shard counts, or batch sizes.

## Route by Workflow

- **Qwen2.5-VL and Qwen-Omni retrievers**: use packaged `tevatron.retriever.driver.train_mm` and `tevatron.retriever.driver.encode_mm`; keep `query_image`, `query_audio`, `query_video`, corpus `image`, `audio`, and `video` fields asset-aware.
- **Document screenshot retrieval**: use Qwen/DSE or ColPali planning from `references/multimodal-workflows.md`; DSE and ColPali example scripts are reference patterns unless their code is separately bundled into a project workflow.
- **RepLLaMA and Qwen3-Embedding**: use text `tevatron.retriever.driver.encode`, `tevatron.retriever.driver.train`, or `tevatron.retriever.driver.vllm_encode` with matching prefixes, `--pooling last` or family-specific pooling, normalization, EOS, and padding choices from `references/llm-retrievers.md`.
- **RankLLaMA**: route cross-encoder scoring and training to `../reranking/`, but use this sub-skill to preserve LLM LoRA, tokenizer, prefix, and memory assumptions when the request compares RankLLaMA with RepLLaMA.
- **vLLM encoding**: prefer it only when `vllm` is installed and the model/adapter supports vLLM embedding; note that packaged `vllm_encode_mm` currently passes prompt plus image, not audio/video.

## Required Checks

Before handing off a plan, confirm:

- Optional packages are explicit: `torch`, `PIL`/`Pillow`, `qwen_omni_utils`, `qwen_vl_utils`, `vllm`, `peft`, suitable `transformers`, FlashAttention, DeepSpeed, and model-specific remote code are not guaranteed by core Tevatron.
- The driver matches the model family: `train_mm`/`encode_mm` for current Qwen-Omni/VL multimodal support, text `train`/`encode`/`vllm_encode` for LLM embedding models, and `../reranking/` for RankLLaMA cross-encoders.
- Dataset asset fields and `--assets_path` or `train_yaml` corpus `assets_path` are consistent before any GPU/model launch.
- Query and corpus encoding use compatible model, adapter, tokenizer/processor, pooling, normalization, prefix, EOS, padding, and shard settings.
- Downstream retrieval matches embedding type: dense pickle outputs go to `../encoding-retrieval/`, while ColPali-style late-interaction outputs need family-specific scoring.
