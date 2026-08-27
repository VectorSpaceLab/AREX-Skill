# LLM Retrievers and Rankers

Tevatron's LLM retriever examples use large autoregressive or embedding models as first-stage retrievers. The important routing decisions are model family, driver, LoRA handling, pooling, normalization, prefixes, EOS behavior, padding, and whether vLLM can safely replace standard Transformers encoding.

## Driver Choice

| Request | Preferred Tevatron route | Cross-link |
| --- | --- | --- |
| RepLLaMA or LLaMA/Mistral first-stage retrieval | `tevatron.retriever.driver.encode`, or `tevatron.retriever.driver.vllm_encode` when vLLM is available | Search/evaluation belongs to `../encoding-retrieval/`. |
| Qwen3-Embedding retrieval or fine-tuning | text `encode`/`train` with Qwen-specific prefix and padding settings | Generic training details belong to `../training/`. |
| RankLLaMA cross-encoder reranking | `tevatron.reranker.driver.rerank` or `tevatron.reranker.driver.train` | Execution belongs to `../reranking/`; preserve LLM LoRA assumptions here. |
| Qwen2.5-VL / Omni multimodal retriever | `train_mm`, `encode_mm`, and optionally image-only `vllm_encode_mm` | See `multimodal-workflows.md`. |

Use package drivers for new Tevatron plans. Older example-local RepLLaMA scripts use legacy flag names such as `--p_max_len`, `--q_max_len`, and `--encoded_save_path`; translate those to package-level `--passage_max_len`, `--query_max_len`, and `--encode_output_path` when planning current workflows.

## LoRA and Adapter Rules

- Training with `--lora` creates a PEFT adapter unless `--lora_name_or_path` is also supplied for continued adapter training.
- Encoding with a trained adapter normally uses `--lora_name_or_path <adapter>` and, for standard Transformers encoding examples, also includes `--lora` to keep the plan explicit.
- Standard `EncoderModel.load` merges a supplied LoRA adapter into the base model before wrapping it for encoding; verify memory and disk expectations before assuming this is cheap for 7B+ models.
- vLLM encoding enables LoRA when `--lora_name_or_path` is present and uses `--lora_r` as `max_lora_rank`; set it to the adapter rank, such as `32` for RepLLaMA-style adapters.
- `lora_target_modules` defaults to `q_proj,k_proj,v_proj,o_proj,down_proj,up_proj,gate_proj`, matching common LLaMA, Mistral, and Qwen examples.
- Merging an adapter into model weights can reduce vLLM overhead, but only propose it as an offline preparation step when the user controls disk, licensing, and reproducibility.

## Pooling, Normalization, Prefixes, and EOS

| Model pattern | Pooling | Normalize | Prefixes | EOS / padding notes |
| --- | --- | --- | --- | --- |
| RepLLaMA | `last` in package-level plans; older examples use custom model code | yes | `query: ` and `passage: ` for RepLLaMA-style prompts | Use `--append_eos_token`; standard text `encode` honors `--padding_side`, vLLM text encoding sets tokenizer padding side to right internally. |
| Mistral/LLaMA Tevatron 101 | `eos` | yes | `Query: ` and `Passage: ` | Use `--append_eos_token`; match train and encode choices exactly. |
| Qwen3-Embedding | `last` | yes | task instruction in `--query_prefix`, usually empty `--passage_prefix` | Use `--padding_side left`; example inference omits EOS, fine-tuning keeps the same pooling and padding. |
| Qwen2.5-VL / Omni retrievers | `eos` in training examples, `last` in several evaluation examples | yes | `Query: ` and often empty passage prefix | `train_mm` and `encode_mm` set processor tokenizer padding side to left internally and often use `--append_eos_token`. |
| RankLLaMA reranker | cross-encoder score, not vector pooling | n/a | `query: ` and `document: ` in reranking examples | Route max length and scoring details to `../reranking/`. |

Keep query and corpus encoding compatible. A mismatch in prefix, pooling, normalization, EOS, tokenizer, model checkpoint, LoRA adapter, or max length can silently produce embeddings that search but do not represent the intended retriever.

## Standard RepLLaMA Encoding Shape

```bash
python -m tevatron.retriever.driver.encode \
  --output_dir temp \
  --model_name_or_path meta-llama/Llama-2-7b-hf \
  --lora_name_or_path castorini/repllama-v1-7b-lora-passage \
  --lora \
  --bf16 \
  --per_device_eval_batch_size 16 \
  --normalize \
  --pooling last \
  --passage_prefix "passage: " \
  --append_eos_token \
  --passage_max_len 512 \
  --dataset_name Tevatron/beir-corpus \
  --dataset_config scifact \
  --dataset_split train \
  --encode_output_path <corpus-shard.pkl> \
  --dataset_number_of_shards <n> \
  --dataset_shard_index <i>
```

For queries, switch to `--query_prefix "query: "`, `--query_max_len 512`, query dataset/config/split, `--encode_output_path <queries.pkl>`, and add `--encode_is_query`.

## vLLM Text Encoding Shape

Use vLLM when the environment has a compatible `vllm` installation and the user wants faster LLM embedding inference. vLLM avoids the standard model forward path and returns embeddings through `LLM.embed`.

```bash
python -m tevatron.retriever.driver.vllm_encode \
  --output_dir temp \
  --model_name_or_path meta-llama/Llama-2-7b-hf \
  --lora_name_or_path castorini/repllama-v1-7b-lora-passage \
  --lora_r 32 \
  --bf16 \
  --per_device_eval_batch_size 16 \
  --normalize \
  --pooling last \
  --passage_prefix "passage: " \
  --append_eos_token \
  --passage_max_len 512 \
  --dataset_name Tevatron/beir-corpus \
  --dataset_config scifact \
  --dataset_split train \
  --encode_output_path <corpus-shard.pkl> \
  --dataset_number_of_shards <n> \
  --dataset_shard_index <i>
```

vLLM caveats:

- `vllm` is optional and may require a specific CUDA/PyTorch stack.
- The packaged vLLM drivers reject multi-GPU encoding in one process; shard the dataset and launch separate processes if needed.
- `vllm_encode` sets tokenizer padding side to right internally; do not assume `--padding_side left` affects that path.
- `vllm_encode_mm` is image-oriented; do not route audio/video encoding to it unless the implementation has been updated.
- Large LoRA rank, context length, and batch size interact with GPU memory; reduce `per_device_eval_batch_size`, shard more finely, or merge LoRA offline.

## Qwen3-Embedding Pattern

For Qwen3-Embedding text retrieval, the example uses a task-specific instruction prefix, left padding, `--pooling last`, `--normalize`, and Qwen embedding model IDs such as `Qwen/Qwen3-Embedding-4B`.

Query encoding shape:

```bash
python -m tevatron.retriever.driver.encode \
  --output_dir temp \
  --model_name_or_path Qwen/Qwen3-Embedding-4B \
  --bf16 \
  --per_device_eval_batch_size 16 \
  --normalize \
  --pooling last \
  --padding_side left \
  --query_prefix "Instruct: <task instruction>\nQuery:" \
  --query_max_len 512 \
  --dataset_name Tevatron/beir \
  --dataset_config scifact \
  --dataset_split test \
  --encode_output_path <queries.pkl> \
  --encode_is_query
```

Corpus encoding should use the same model, pooling, normalization, and padding, usually with empty `--passage_prefix` and `--passage_max_len 512`.

Fine-tuning Qwen3-Embedding uses the generic retriever training driver, not `train_mm`, unless the task also includes media fields. Preserve the same instruction prefix, `--pooling last`, `--padding_side left`, and normalization between training and encoding.

## RankLLaMA Cross-Link

RankLLaMA is a cross-encoder reranker, not a first-stage vector retriever. Use this sub-skill only to keep LLM-specific context straight:

- RankLLaMA examples use LoRA on large decoder models and query/document prefixes such as `query: ` and `document: `.
- Training and inference are handled by `tevatron.reranker.driver.train` and `tevatron.reranker.driver.rerank`.
- Pairwise rerank JSONL preparation, score interpretation, and reranker troubleshooting belong to `../reranking/`.
- First-stage RepLLaMA outputs can feed RankLLaMA, but retrieval run preparation belongs to `../encoding-retrieval/` and `../data-preparation/`.

## Planning Checklist

- Decide first-stage retriever versus cross-encoder ranker before selecting a driver.
- Keep query/corpus embedding runs compatible across model, LoRA, tokenizer, pooling, normalization, prefixes, EOS, padding, and max lengths.
- State optional dependencies and hardware assumptions instead of trying to run large model commands by default.
- Use small, local schema/dependency checks before suggesting any model download, GPU launch, or vLLM run.
- Send FAISS search, ranking conversion, and metric evaluation to `../encoding-retrieval/` after embeddings exist.
