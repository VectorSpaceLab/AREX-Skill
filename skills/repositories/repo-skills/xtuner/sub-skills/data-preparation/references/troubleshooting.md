# Data-preparation troubleshooting

Use this table when validators, dataset build, tokenization, or packing fail before training starts.

| Symptom | Likely cause | Fix |
|---|---|---|
| `invalid JSON` or validator reports a line/column | JSONL line is truncated, has trailing commas, single quotes, unescaped newlines, or mixed comments | Re-write as one valid JSON value per line. Use `python ./scripts/validate_xtuner_jsonl.py DATA --mode sft` before training. |
| Missing `messages`, `dialogs`, or `prompt` | Wrong mode or wrong schema for the selected tokenizer | SFT/MLLM uses `messages`/`dialogs` or bare message-list lines; RL uses `prompt`. Pick the correct `--mode` and tokenizer config. |
| Missing role/content | Message uses legacy fields or malformed content | Normalize `from` -> `role`, `value` -> `content`; map `human` -> `user` and `gpt` -> `assistant`. The validator accepts common variants but strict OpenAI tokenization is safest with `role`/`content`. |
| Unknown role | Dataset contains roles outside the selected template | For OpenAI tokenization, use `system`, `developer`, `user`, `assistant`, `tool`, or `pretrain`. FTDP supports additional configured sub-roles but they must be covered by the chosen role config. |
| `thinking` on a non-assistant message | Reasoning metadata attached to the wrong role | Keep `thinking` only on assistant messages. For GPT-OSS, remember only the last assistant thinking field is retained by default. |
| MLLM validator reports missing media path | `media_root` is wrong, URLs are relative to a different root, or files were not copied | Run `python ./scripts/validate_xtuner_jsonl.py DATA --mode mllm --media-root MEDIA_ROOT`. Use the same root in `DatasetConfig(media_root=...)`. |
| MLLM silently returns fake data during dataset iteration | `VLMJsonlDataset` caught an exception while loading/tokenizing media | Validate paths and content item shape first. Check that image/video dependencies and model-specific processors are installed in the training environment. |
| Image/video width-height error | `image_wh` is not `[width, height]` or does not match media count | Use two numeric values per media item. If one item supplies `image_wh`, supply it consistently for all media items of that type in the record. |
| Max-length truncation warning | Tokenized input exceeds `max_length` and XTuner truncates | Reduce record length, raise `max_length`, or choose a model/template with a larger context. The bundled validator only approximates; confirm with the real tokenizer. |
| Samples disappear after cache building | Tokenizer returned `num_tokens=0` for damaged or overlength samples and filtering removed them | Inspect validator output and tokenizer max length. Avoid `disable_filter=True` unless debugging or required by preset packing. |
| Cache is stale after editing data or tokenizer code | Cache keys are JSONL hash, tokenize function hash, and tokenizer hash; a fixed `cache_tag` can override expected invalidation | Bump `cache_tag` or delete the cache directory. Include template/tokenizer/max-length version in tag names. |
| Cache rebuilds every run | No `cache_dir`, tokenize function is not cacheable, tokenizer hash changes, or JSONL bytes change | Set `cache_dir`; use cacheable tokenization configs; keep tokenizer path stable; avoid rewriting JSONL with non-semantic byte changes. |
| `pack_level='preset' requires both 'pack_config_path' and 'sampler_config_path'` | Preset packing was enabled without both schedule assets | Provide both paths and set `sampler_type='preset'`, or switch to `soft`, `hard`, `mllm_hybrid`, or `none`. |
| `group_by_length must be False when pack_level is none` | Dataloader config conflict | Set `DataloaderConfig(pack_level="none", group_by_length=False)`. This is common for RL. |
| RL validator reports missing `reward_model.ground_truth` | GSM8K reward record lacks the answer used by the rule reward | Re-convert with `convert_gsm8k_jsonl.py` or add `{"reward_model":{"style":"rule","ground_truth":"..."}}`. |
| RL runtime asserts `data_source is required` | RL record lacks `data_source` | Add a string such as `openai/gsm8k` and ensure judger mapping expects it. |
| Tool-agent GSM8K reward mismatch | Tool metadata ground truth differs from `reward_model.ground_truth` | Keep `extra_info.tools_kwargs.calc_gsm8k_reward.create_kwargs.ground_truth` identical to `reward_model.ground_truth`. |

## Recovery commands

Validate a text SFT file:

```bash
python ./scripts/validate_xtuner_jsonl.py data/openai_sft.jsonl --mode sft --max-length 4096
```

Validate mixed text+image MLLM data and fail on missing local media:

```bash
python ./scripts/validate_xtuner_jsonl.py data/mllm.jsonl --mode mllm --media-root media
```

Convert local GSM8K-style records and validate reward fields:

```bash
python ./scripts/convert_gsm8k_jsonl.py --input-dir raw_gsm8k --out-dir xtuner_gsm8k
python ./scripts/validate_xtuner_jsonl.py xtuner_gsm8k/train.jsonl --mode rl
```

If a problem belongs to launch configuration, model/backend selection, or RL rollout/trainer services, stop data debugging and route to the corresponding sibling sub-skill.
