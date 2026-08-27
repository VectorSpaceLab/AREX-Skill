# Tokenization, caching, and packing

This reference covers the data-facing configuration choices. It does not launch training.

## Choosing a tokenizer function

| Config | Input shape | Main fields | When to use |
|---|---|---|---|
| `OpenaiTokenizeFunctionConfig` | OpenAI-style messages: bare list, `messages`, or `dialogs` | `chat_template`, `max_length`, `hash` | Default SFT flow for chat/instruction data. |
| `FTDPTokenizeFnConfig` | FTDP/dialog records and role-config-driven templates | `chat_template`, `max_length`, `hash` | Use when data already follows XTuner FTDP role formatting or needs sub-role masking behavior. |
| Model-specific MLLM tokenize configs | `messages` with image/video content items | model template fields plus `max_length` | Use with `DatasetConfig(class_name="VLMJsonlDataset", media_root=...)`. |
| `RLTextTokenizeFnConfig` | RL records with `prompt` and `reward_model` | `max_length`, `tools_schema` | Use for text RL/GRPO-style datasets. |

`TrainingArguments` direct dataset mode chooses `OpenaiTokenizeFunctionConfig` when `--tokenize-fn openai` and `FTDPTokenizeFnConfig` when `--tokenize-fn ftdp`. Configuration-file mode can provide explicit `dataset_config_list` entries with different tokenization configs per dataset.

## Chat-template labels

Verified template labels include:

- Text/chat: `internlm2`, `qwen3`, `gpt-oss`, `deepseek-v3`, `glm5.2`.
- MLLM/VL flows also use labels such as `intern-s1`, `internvl-3.5`, `qwen3-vl`, `qwen3-vl-rl`, and `qwen3.5-vl` when paired with the matching model-specific tokenizer.

Template behavior matters:

- `system`, `developer`, `user`, and `tool` content is normally masked.
- `assistant` content is normally supervised unless `loss: false` is set or the template masks earlier rounds.
- GPT-OSS has a `developer` role and keeps only the last assistant thinking field by default; it also computes loss only on the last assistant message unless the template is changed.
- Qwen VL and Intern VL templates differ in their image/video marker tokens; do not reuse a data/template pair across model families without a tokenizer smoke check.

## DatasetConfig fields

| Field | Meaning | Notes |
|---|---|---|
| `anno_path` | JSONL file or directory | Required. Direct-argument training expands files/directories/globs to `.jsonl`. |
| `name` | Dataset alias | Useful in logs and mixed datasets. |
| `class_name` | Dataset class selector | `JsonlDataset` for text/RL; `VLMJsonlDataset` for MLLM media records. |
| `media_root` | Root joined with local image/video references | Set for `VLMJsonlDataset`; validate with the bundled script before training. |
| `sample_ratio` | Fraction or repeat factor | `0.5` samples half; `2.0` repeats twice. Preset packing forces `1.0`. |
| `enable_sequential_sampler` | Deterministic extra samples when `sample_ratio` is non-integer | Preset packing forces `True`. |
| `enable_mmap_shared` | Shared memory/mmap cache metadata across local ranks | Useful for large cached datasets. |
| `disable_filter` | Disable filtering damaged or overlength samples | Preset packing forces `True`; otherwise keep default unless debugging. |
| `cache_dir` | Directory for offsets and tokenization metadata | Enables reusable preprocessing cache. |
| `cache_tag` | Manual cache version tag | Reuses tagged cache even while debugging, so change it when data/tokenization semantics change. |

## Cache behavior

XTuner cache hits depend on three hashes unless `cache_tag` forces a tag hit:

1. The JSONL file content hash.
2. The tokenization function source/config hash.
3. The tokenizer hash.

Cache layout includes offsets and tokenization metadata. If any of the three hashes changes, preprocessing runs again. If `cache_tag` is fixed, XTuner can reuse the tagged cache even if source changes; use this only when you intentionally accept the old preprocessing semantics.

Recommended practice:

- Include dataset name, template, tokenizer family, and max length in the `cache_tag` value, for example `sft-qwen3-4096-v1`.
- Bump `cache_tag` after editing JSONL, changing chat template, changing tokenizer/model, changing max length, or modifying a custom tokenize function.
- Delete the cache directory only when tags and hashes cannot explain stale behavior.

## DataloaderConfig and packing

Core fields:

| Field | Default surface | Meaning |
|---|---|---|
| `collator` | `sft_llm_collator` | Choose text or VL collator appropriate to the tokenizer/model. |
| `pack_to_max_length` | `True` | Pad/pack batches to `pack_max_length`. |
| `pack_level` | `soft` in config class; direct quickstart may set smaller `pack_max_length` | Packing strategy. |
| `pack_max_length` | context length budget | Keep consistent with model and tokenizer. |
| `pack_chunk_size` / `pack_workers` | preprocessing parallelism | Increase only when CPU and memory allow. |
| `global_pack` | `True` | Pack across dataset shards/ranks. |
| `sampler_type` | `none` | Use `preset` only with preset sampler assets. |
| `group_by_length` | inferred | Must be `False` when `pack_level="none"`. |
| `pad_token_id` | `None` | Defaults to `0` in the collator if unset. |
| `tokenizer_hash` | `None` | Override only when reproducing cache identity intentionally. |
| `round_up` | `True` | Controls sampler rounding behavior. |

`pack_level` choices:

| `pack_level` | Use case | Constraints |
|---|---|---|
| `none` | RL datasets, debugging exact samples, or no packing | `group_by_length` must be `False`. |
| `soft` | General SFT/pretraining packing | Uses expandable soft packing and length grouping. |
| `hard` | Fixed hard packing | Less flexible; requires reliable token counts. |
| `mllm_hybrid` | Multimodal pretraining/SFT packing | Use with MLLM tokenizers and collators. |
| `preset` | Reuse precomputed pack/sampler schedule | Requires both `pack_config_path` and `sampler_config_path`; forces `sample_ratio=1.0`, `enable_sequential_sampler=True`, and `disable_filter=True`. |
| `__legacy` | Debug/compatibility only | Do not choose for new production configs. |

Preset packing fails early unless both of these are set:

```python
DataloaderConfig(
    pack_level="preset",
    sampler_type="preset",
    pack_config_path="pack_schedule_dir",
    sampler_config_path="sampler_order.npy",
)
```

## Safe handoff checklist

Before routing to training or reinforcement-learning:

1. `validate_xtuner_jsonl.py` passes in the correct mode.
2. MLLM local media references pass with the exact `media_root` intended for `DatasetConfig`.
3. The tokenizer function and `chat_template` match the model family.
4. `max_length` is set deliberately, and long-record warnings are either fixed or accepted.
5. `cache_dir`/`cache_tag` changes are documented.
6. `pack_level`, `collator`, and `group_by_length` are compatible.
7. RL records contain non-empty `reward_model.ground_truth`.
