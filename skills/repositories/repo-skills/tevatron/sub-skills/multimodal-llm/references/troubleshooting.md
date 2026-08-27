# Troubleshooting Multimodal and LLM Workflows

Use this guide before changing model families, processor names, dependency stacks, or shard sizes. Most failures in these workflows come from optional dependencies, media asset resolution, processor/model mismatch, LoRA/vLLM compatibility, or GPU memory pressure rather than Tevatron core installation.

## Dependency Import Failures

Run:

```bash
python scripts/check_multimodal_dependencies.py --json
```

Use `--workflow text-llm`, `--workflow multimodal`, `--workflow qwen-vl`, `--workflow qwen-omni`, `--workflow vllm-text`, `--workflow vllm-mm`, or `--workflow colpali` to highlight route-specific missing packages.

Interpretation:

- `transformers` and `datasets` are core package requirements, but Qwen, ColPali, DSE, and LLM families may need newer versions than the package minimum.
- `torch` is required for package training/encoding drivers and all GPU execution.
- `PIL`/`Pillow` is required for image handling and multimodal dataset imports.
- `qwen_omni_utils` is required because Tevatron's packaged multimodal collators import `process_mm_info` at module import time.
- `qwen_vl_utils` is required by several Qwen-VL, DSE-Qwen, and ColPali example-local evaluators/collators, even though package-level `train_mm`/`encode_mm` use `qwen_omni_utils`.
- `peft` is required for `--lora` and `--lora_name_or_path` workflows.
- `vllm` is required only for `vllm_encode` and `vllm_encode_mm`.
- `flash_attn` is optional but relevant because `ModelArguments.attn_implementation` defaults to `flash_attention_2`.
- `deepspeed` is optional but common in large LoRA training examples.

If `flash_attn` is missing or incompatible, consider `--attn_implementation sdpa` or `--attn_implementation eager` before changing the model or dataset.

## Missing Image, Audio, or Video Assets

Symptoms:

- Dataset loads but processor receives empty media.
- Encoding logs warnings for missing video or audio files.
- Training fails while joining a relative media path with a null asset root.
- Image-only examples work but video/audio examples do not.

Checks and fixes:

- Confirm query-side fields are named `query_image`, `query_audio`, and `query_video`.
- Confirm corpus-side fields are named `image`, `audio`, and `video`; README-style `document_image` and `document_text` must be transformed for package datasets.
- Confirm string audio paths end in `.mp3`; otherwise the dataset code asserts.
- For encoding, set `--assets_path <asset-root>` when corpus `video` or string `.mp3` fields are relative paths.
- For multi-dataset training, use `train_yaml` object entries with corpus `assets_path` values.
- Use `--no_encode_image`, `--no_encode_audio`, or `--no_encode_video` only when intentionally dropping that modality; the defaults encode all modalities.

## Qwen Processor and Tokenizer Mismatch

Symptoms:

- `AutoProcessor.from_pretrained` fails.
- Tokenizer lacks a pad token.
- Chat template or media preprocessing fails.
- Qwen-Omni thinker model loads but the processor is wrong.
- Qwen-VL examples work in source form but package `train_mm` fails on missing Omni utilities.

Checks and fixes:

- For Qwen-Omni thinker workflows, provide both `--model_name_or_path <thinker-model>` and matching `--tokenizer_name <processor-tokenizer-id>` when they differ.
- Keep `trust_remote_code=True` in mind: Tevatron's multimodal drivers set it for processors/models, but the user environment and model policy must permit it.
- `train_mm` and `encode_mm` set processor tokenizer padding side to left internally; text `encode` honors `--padding_side`, while `vllm_encode` sets padding side to right internally.
- If the processor cannot handle audio/video, route to the correct Qwen-Omni stack rather than forcing a Qwen-VL model.
- Distinguish package-level Qwen multimodal drivers from example-local DSE/ColPali scripts; the latter may use different utility imports and model classes.

## vLLM and LoRA Problems

Symptoms:

- `ModuleNotFoundError: vllm`.
- `max_lora_rank` or adapter-rank errors.
- vLLM returns shape/type errors for multimodal inputs.
- Audio/video records silently do not appear in vLLM input planning.

Checks and fixes:

- Use `vllm_encode` only when `vllm` is installed and the selected model supports `task="embed"`.
- Pass `--lora_r` matching the adapter rank when using `--lora_name_or_path`; RepLLaMA-style examples often use rank 32.
- Reduce `--per_device_eval_batch_size` before changing model logic.
- Shard corpora with `--dataset_number_of_shards`; the packaged drivers reject multi-GPU encoding in one process.
- Use standard `encode_mm` for audio/video. Packaged `vllm_encode_mm` currently passes prompt plus image only.
- Consider an offline merged-adapter checkpoint when vLLM LoRA overhead or compatibility blocks inference.

## Memory Pressure and Shard Sizing

Symptoms:

- CUDA out-of-memory during encode or train.
- ColPali-like embeddings produce huge index files.
- Search fails when loading all passage shards.
- Encoder raises `NotImplementedError` for multi-GPU encoding.

Checks and fixes:

- Lower `--per_device_eval_batch_size` for encoding and rerun only the failed shard.
- Increase `--dataset_number_of_shards` and encode fewer records per process.
- Keep one encoding process per GPU; package encoders reject multi-GPU encoding in a single process.
- For training, combine LoRA, gradient checkpointing, smaller `train_group_size`, smaller per-device batch size, and DeepSpeed before changing data semantics.
- For ColPali-style late interaction, plan many shards and family-specific scoring; do not load a very large late-interaction index as if it were a small dense FAISS matrix.

## Prefix, Pooling, and EOS Mismatches

Symptoms:

- Search runs successfully but quality is poor.
- Query and corpus embeddings have expected shapes but represent different prompt formats.
- vLLM output differs from Transformers output more than expected.

Checks and fixes:

- RepLLaMA-style retrieval normally uses `--pooling last`, `--normalize`, `--append_eos_token`, `--query_prefix "query: "`, and `--passage_prefix "passage: "` in package-level plans.
- Mistral/LLaMA Tevatron 101 examples use `--pooling eos`, `--normalize`, `--append_eos_token`, `--query_prefix "Query: "`, and `--passage_prefix "Passage: "`.
- Qwen3-Embedding normally uses `--pooling last`, `--normalize`, `--padding_side left`, a task instruction query prefix, and an empty passage prefix.
- Qwen multimodal examples often train with `--pooling eos` and evaluate with `--pooling last`; document the checkpoint's expected pooling choice and keep query/corpus encoding consistent.
- Do not mix embeddings created with different LoRA adapters, tokenizer/processor identifiers, pooling, normalization, prefixes, EOS, or max lengths.

## RankLLaMA Routing Mistakes

Symptoms:

- A RankLLaMA request is planned as FAISS vector search.
- Pairwise rerank input is missing first-stage retrieval candidates.
- User asks to compare RepLLaMA and RankLLaMA but the plan merges their drivers.

Checks and fixes:

- RepLLaMA is a first-stage retriever; RankLLaMA is a cross-encoder reranker.
- Route RankLLaMA train/rerank commands to `../reranking/`.
- Use this sub-skill only to preserve LLM-specific LoRA, tokenizer, prefix, model-access, and memory notes.
