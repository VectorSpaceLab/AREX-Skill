# InternVideo video MLLM troubleshooting

## Model or processor will not load

- Use `trust_remote_code=True` for InternVideo3 `AutoModelForCausalLM` and `AutoProcessor` loading.
- Keep model and processor from the same release unless the user intentionally split them. A mismatched processor often appears as missing chat-template tokens, wrong visual token counts, or decode errors.
- The repo evidence uses the `transformers` 4.57.x generation. If `AutoProcessor` or Qwen3-VL classes are missing, verify the exact installed version before changing code.
- `qwen-vl-utils` may be imported as `qwen_vl_utils` in Python. Install the package name expected by the environment but debug the import name from the traceback.

## FlashAttention, SDPA, and CUDA failures

- The README inference path uses `attn_implementation="sdpa"`; this is the safer first option.
- Evaluation launchers often use `attn_implementation=flash_attention_2`; SFT launchers set `XTUNER_USE_FA3=1`. These require compatible CUDA, PyTorch, and FlashAttention builds.
- If an error says FlashAttention tensors must be CUDA half/bfloat16, verify the model is on GPU and loaded with a half/bfloat16 dtype.
- If FlashAttention is unavailable, do not silently compare SDPA results against FlashAttention benchmark numbers; record the implementation change.

## Video OOM or slow prefill

- Reduce in this order: `max_num_frames` (when supported), `fps`, `max_pixels`, then `max_new_tokens`.
- Very long videos can still OOM during prefill even with M2LA. M2LA compresses KV cache for decoding but does not make video decoding or visual-token prefill free.
- For quick sanity checks, start with a short local video and `attn_implementation="sdpa"`; move to long-context or thinking evaluation only after the base path works.

## Message schema mismatch

- Hugging Face inference messages use content items `type: "video"` with a `video` key and `type: "image"` with an `image` key.
- InternVideo3 SFT annotations use `type: "video_url"` / `type: "image_url"`, nested `video_url` / `image_url` objects, and text placeholders `<VIDEO_CONTEXT>` / `<IMG_CONTEXT>`.
- For SFT JSONL, placeholder counts must match the number of video/image items. Missing placeholders can discard data or raise token-count assertions.

## SFT config and launcher surprises

- Some comments/defaults mention config files named `internvideo3_sft.py` or `internvideo3_sft_debug.py`; the current inspected snapshot provides `internvideo3_cpt.py`, `internvideo3_sft_short.py`, and `internvideo3_sft_long.py`. Pass an explicit existing config.
- If `META_DATA_PATH` is unset, configs try to find exactly one `.json` file in the config directory. Set `META_DATA_PATH` explicitly in production.
- The README lists `GLOBAL_BATCH_SIZE` as an environment variable, but current configs assign `global_batch_size` as Python constants. Use a derived config for batch changes.
- `TOKENIZER_CACHE_DIR` should point to storage with enough space for token/packing caches. Cache tags include processor/tokenizer and visual-budget settings; regenerate caches after changing frame or pixel parameters.
- The rjob launcher is cluster-specific. Rebuild a portable `torchrun` command for the user's cluster instead of copying the rjob mounts/image/resources.

## SFT data is repeatedly skipped or replaced by fake data

- Validate JSONL with the `datasets` sub-skill. Common causes are malformed messages, missing `image_wh`, unsupported video extension, unresolved media paths, and inconsistent frame metadata.
- If `processed_video_length` is present, `processed_fps` must also be present. If `frames_timestamp` is present, its length must match the processed frame count.
- If no `origin_video_length`/`origin_fps` are present, tokenization falls back to random frame counts up to `rand_video_max_frames` and loses precise timestamps.
- If many records have too many visual tokens, reduce per-dataset pixel/frame overrides or split short and long video data into separate config entries.

## Evaluation cannot find benchmark data

- LMMS-Eval scripts set `HF_DATASETS_OFFLINE=1`; pre-cache datasets or unset only with user approval and a known network/download policy.
- Dedicated Python evaluators may have placeholder or fixed data-root defaults. Parameterize data roots in the user's working copy before running.
- `MODEL_PATH` is required by all shell wrappers; `OUTPUT_DIR` defaults to a local logs directory if not set. Always set it explicitly for reproducible runs.

## Results are incomparable to paper tables

Record all of: model id/checkpoint, processor id, attention implementation, normal versus thinking mode, frame cap, fps, min/max pixels, benchmark data version, package versions, and whether any data-root or evaluator code was patched. Small changes in any of these can invalidate direct paper-number comparisons.
