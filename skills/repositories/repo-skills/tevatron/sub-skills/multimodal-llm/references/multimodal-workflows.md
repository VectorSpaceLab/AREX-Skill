# Multimodal Workflows

Tevatron's package-level multimodal path is centered on `tevatron.retriever.driver.train_mm` and `tevatron.retriever.driver.encode_mm`. These drivers use `AutoProcessor` with `trust_remote_code=True`, build `MultiModalDenseModel`, and format each example as a chat-template message containing text plus optional image, audio, or video parts.

Most example scripts in ColPali, DSE, Qwen2.5-VL, and Qwen-Omni are reference-only because they require model downloads, GPUs, large datasets, or example-local code. Use them to choose flags and failure modes; do not make a runtime plan depend on the original checkout.

## Modality and Data Fields

Use the sibling data-preparation sub-skill for full JSONL validation, but preserve these multimodal facts when routing execution:

| Purpose | Query fields | Corpus fields | Notes |
| --- | --- | --- | --- |
| Training query | `query_id`, `query_text`, optional `query_image`, `query_audio`, `query_video` | linked by `positive_document_ids` and `negative_document_ids` | New-format training rows resolve documents from `corpus_name`/`corpus_path`. |
| Encoding query | `query_id`, `query_text` or `query`, optional `query_image`, `query_audio`, `query_video` | none | Use `--encode_is_query`. |
| Encoding corpus | none | `docid`, optional `title`, `text`, `image`, `audio`, `video` | Omit `--encode_is_query`. README examples may say `document_text` and `document_image`, but package datasets read `text` and `image`. |
| Asset-backed media | path values in media fields | path values in media fields | Corpus `video` and string `.mp3` audio are joined with `--assets_path`; in multi-dataset training, each corpus entry carries `assets_path`. |

`DataArguments` defaults keep `encode_text`, `encode_image`, `encode_audio`, and `encode_video` enabled. Disable a modality only when intentionally comparing ablations or avoiding missing media. Image values are passed through to the processor and are not joined with `assets_path` by Tevatron's dataset code; provide image objects or paths in the form expected by the selected dataset/processor. Video paths and string audio paths are checked or joined with the configured asset root. Audio may also be a dataset object with an `array` key.

## Qwen2.5-VL Retrieval Pattern

Use Qwen2.5-VL when the request is image/text document retrieval or a unified text/image retriever. The examples use `Qwen/Qwen2.5-VL-3B-Instruct` with LoRA, `--pooling eos` for training, `--pooling last` for several evaluation paths, `--normalize`, `--append_eos_token`, and empty passage prefix for public datasets.

Training shape:

```bash
python -m tevatron.retriever.driver.train_mm \
  --output_dir <retriever-output> \
  --model_name_or_path Qwen/Qwen2.5-VL-3B-Instruct \
  --lora \
  --lora_target_modules q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj \
  --train_yaml <dataset-config.yaml> \
  --query_prefix "Query: " \
  --passage_prefix "" \
  --bf16 \
  --pooling eos \
  --append_eos_token \
  --normalize \
  --query_max_len 512 \
  --passage_max_len 512 \
  --train_group_size 4 \
  --gradient_checkpointing \
  --overwrite_output_dir
```

Encoding shape:

```bash
python -m tevatron.retriever.driver.encode_mm \
  --output_dir temp \
  --model_name_or_path Qwen/Qwen2.5-VL-3B-Instruct \
  --lora_name_or_path <adapter-or-output> \
  --lora \
  --bf16 \
  --per_device_eval_batch_size 16 \
  --normalize \
  --pooling last \
  --query_prefix "Query: " \
  --passage_prefix "" \
  --append_eos_token \
  --query_max_len 512 \
  --passage_max_len 512 \
  --dataset_name <query-or-corpus-dataset> \
  --dataset_config <optional-config> \
  --dataset_split <split> \
  --encode_output_path <embeddings.pkl> \
  --encode_is_query
```

For corpus encoding, remove `--encode_is_query`, set `--passage_max_len`, and add `--dataset_number_of_shards` plus `--dataset_shard_index` for large corpora. Route resulting dense pickle files to `../encoding-retrieval/` for search and evaluation.

## Qwen-Omni Retrieval Pattern

Use Qwen-Omni when audio/video may be present or the request explicitly names Omni. The current package model class imports `Qwen2_5OmniThinkerForConditionalGeneration` and freezes visual and audio towers inside `MultiModalDenseModel`. The examples use `Tevatron/Qwen2.5-Omni-7B-Thinker` as the model and `Qwen/Qwen2.5-Omni-7B` as the tokenizer/processor name.

Key differences from Qwen2.5-VL:

- Include `--tokenizer_name Qwen/Qwen2.5-Omni-7B` when the thinker model and processor/tokenizer live under different identifiers.
- Ensure `qwen_omni_utils` is installed because Tevatron's multimodal collators import `process_mm_info` at module import time.
- Keep `assets_path` explicit for video corpora and string `.mp3` audio corpora.
- Treat audio/video execution as GPU/model/download-heavy; validate schema and dependencies first.

A multi-dataset `train_yaml` for current `MultiTrainDataset` should use object entries with `name` and corpus `assets_path`, for example:

```yaml
train:
  - name: Tevatron/msrvtt
  - name: Tevatron/audiocaps
  - name: Tevatron/wiki-ss-nq-new
corpus:
  - name: Tevatron/msrvtt-corpus
    assets_path: ./msrvtt-corpus/video
  - name: Tevatron/audiocaps-corpus
    assets_path: null
  - name: Tevatron/wiki-ss-corpus-new
    assets_path: null
```

Some older configs use a short string-list form, but the current `MultiTrainDataset` implementation reads `entry['name']` and corpus `entry['assets_path']`; prefer the object form above when generating new configs.

## DSE and ColPali Patterns

DSE and ColPali are document screenshot retrieval families in the examples. They are valuable evidence for workflow planning but differ in packaging status:

| Family | Typical model | Packaged path status | Planning notes |
| --- | --- | --- | --- |
| DSE Phi/Qwen | `Tevatron/Phi-3-vision-128k-instruct-clone`, `MrLight/dse-qwen2-2b-mrl-v1` | examples use local `train.py`, `encode.py`, and model classes | Route new package-level Qwen multimodal work to `train_mm`/`encode_mm` when possible; otherwise label old scripts reference-only. |
| ColPali | `vidore/colpali-v1.2-hf` | examples use local `encode.py`/`search.py` and `ColPaliProcessor.score_retrieval` | Plan GPU shard sizing and late-interaction scoring carefully; do not promise packaged `tevatron.retriever.driver.search` will score ColPali token embeddings. |
| Wiki-SS / VIDORE evaluation | public screenshot datasets | examples use local evaluation helpers | Treat evaluation helpers as reference-only unless copied/adapted into a project-specific workflow outside this runtime skill. |

ColPali embeddings can be very large because they retain token/image patch representations and are scored with a processor-specific retrieval scorer. Use many corpus shards, small batch sizes, and explicit GPU memory notes. For regular dense vector pickle files from `encode_mm`, use `../encoding-retrieval/` for FAISS search.

## vLLM Multimodal Encoding

`tevatron.retriever.driver.vllm_encode_mm` uses `AutoProcessor`, `PoolerConfig`, `vllm.LLM(task="embed")`, and optional `LoRARequest`. It currently builds vLLM inputs with:

- `prompt`: chat-templated text.
- `multi_modal_data`: `{'image': image}` when an image is present.

The vLLM multimodal collator reads image fields but does not pass audio or video to vLLM. Use standard `encode_mm` for audio/video plans unless the user explicitly accepts an image-only vLLM route.

## Multimodal Command Checklist

- Confirm `python scripts/check_multimodal_dependencies.py --workflow multimodal --json` reports the optional packages required by the selected route.
- Confirm the chosen model has a compatible `AutoProcessor` and remote-code trust policy.
- Confirm the tokenizer/processor identifier if it differs from the model identifier.
- Confirm media fields are present on the expected side: query-side `query_image`/`query_audio`/`query_video`, corpus-side `image`/`audio`/`video`.
- Confirm `--assets_path` or train-yaml corpus `assets_path` covers relative video and `.mp3` audio values.
- Confirm `--dataset_number_of_shards` and `--dataset_shard_index` are used for large corpora; package encoders reject multi-GPU encoding in one process.
- Confirm downstream search matches embedding type: FAISS for dense vector outputs, family-specific scoring for ColPali-style late interaction outputs.
