# ASR Troubleshooting

Use this reference to diagnose NeMo Speech ASR install/import, hardware/backend, manifest/config, transcription, streaming, fine-tuning, Lhotse, decoding, customization, and evaluation failures. Evidence was distilled from ASR docs, source checks, streaming builders/wrappers, examples, and tests.

## Install and Import Failures

Symptoms:

- `ModuleNotFoundError: No module named 'nemo'`
- `ImportError` for `lightning`, `lhotse`, `soundfile`, `kenlm`, `nemo_text_processing`, `pynini`, `vllm`, CUDA libraries, or compiled RNNT/CTC components
- Package imports work but ASR optional workflows fail

Actions:

1. Verify the active environment is the one where NeMo Speech is installed.
2. Check Python/PyTorch compatibility. Current docs target Python 3.12+ and PyTorch 2.7+ for NeMo Speech, while package metadata allows Python `>=3.10`.
3. Install optional extras only for the workflow that needs them: Lhotse for dynamic dataloading, text-processing for ITN, LM/boosting packages for language model customization, compiled/CUDA packages for accelerated loss/decoding, docs/dev packages for docs/tests.
4. If only using the bundled manifest checker, do not install NeMo; `scripts/check_asr_manifest.py` uses only the Python standard library.
5. If source checkout and installed package differ, prefer the user's intended runtime and avoid mixing source-version scripts from one commit with a different installed package.

## CUDA, GPU, MPS, and Compiled Backend Mismatches

Symptoms:

- CUDA is unavailable despite `cuda=0` or `asr.device=cuda`.
- Training starts on CPU unexpectedly.
- AMP/bfloat16/float16 errors.
- CUDA graph decoder failures or graph capture shape errors.
- RNNT/CTC compiled extension errors.
- Apple MPS operation fallback errors.

Actions:

- For inference on CPU, set `cuda=-1` in `transcribe_speech.py` or streaming `asr.device=cpu`, reduce `batch_size`, and expect slower throughput.
- For GPU inference, confirm PyTorch sees CUDA before tuning NeMo configs.
- Do not set `amp=true` together with `compute_dtype=bfloat16`/`float16` in `transcribe_speech.py`; use one precision path.
- Use `compute_dtype=bfloat16` on Ampere+ GPUs when supported; use `float16` on older GPUs only if stable; fall back to `float32` for correctness debugging.
- Disable CUDA graphs for debugging with `model.disable_cuda_graphs()` or config flags such as `rnnt_decoding.greedy.use_cuda_graph_decoder=false` / `rnnt_decoding.beam.allow_cuda_graphs=false`.
- For MPS, set `allow_mps=true` and `PYTORCH_ENABLE_MPS_FALLBACK=1`, but expect unsupported operations to fall back or fail.
- For training, use a CUDA-capable GPU setup; CPU training is generally impractical.

## Manifest and Data Problems

Symptoms:

- `KeyError: audio_filepath`, `text`, `duration`, `source_lang`, `target_lang`, `task`, or `pnc`.
- Samples silently disappear after filtering.
- Lhotse emits duration/bucketing warnings.
- WER is much worse than expected due to transcript style mismatch.
- Canary produces wrong language, translation instead of ASR, or punctuation behavior mismatch.

Actions:

1. Run the bundled checker:

```bash
python scripts/check_asr_manifest.py data.jsonl \
  --canary \
  --min-duration 0.1 \
  --max-duration 30 \
  --style-summary \
  --warn-missing-audio
```

2. Fix malformed JSONL before training; each line must be one JSON object.
3. Ensure `duration` is numeric and positive; verify `min_duration`/`max_duration` do not filter all examples.
4. Align transcript style across train/validation/test: casing, punctuation, numerals, ITN, special symbols, and language tags.
5. For Canary ASR, set `source_lang` and `target_lang` to the same language. For Canary v1 manifests, include `task=asr` and `pnc=yes/no`.
6. For multilingual Lhotse configs, ensure tag fields (`source_lang`, `target_lang`, `task`, `lang`, `pnc`) match tokenizer and metric constraints.
7. If relative `audio_filepath` values fail, resolve them relative to the manifest location or the working directory expected by the script.

## Hydra and CLI Misuse

Symptoms:

- Hydra says a key is not in struct.
- Shell expands lists/braces unexpectedly.
- Overrides appear ignored.
- Script complains both model options or both data options are missing.

Actions:

- Use `+`/`++` for newly added Hydra keys.
- Quote list overrides in shells that expand brackets: `'streaming.att_context_size=[70,13]'`.
- Use `_OP_` and `_CL_` in brace-expandable tar paths when shell/SLURM expansion is a risk.
- For transcription, set exactly one of `model_path` or `pretrained_name` and at least one of `audio_dir` or `dataset_manifest`.
- For fine-tuning, set exactly one of `init_from_nemo_model` or `init_from_pretrained_model`.
- Print/log the Hydra config at startup and inspect the resolved values rather than assuming an override applied.

## Offline Transcription Failures

Symptoms:

- `ValueError: Both cfg.model_path and cfg.pretrained_name cannot be None!`
- `ValueError: Both cfg.audio_dir and cfg.dataset_manifest cannot be None!`
- Decoder type errors for CTC/RNNT/hybrid models.
- OOM during inference.
- Output order differs from input order after presorting.

Actions:

- Provide one model source and one data source.
- Match `decoder_type` to the loaded model: pure CTC=`ctc`, pure RNNT=`rnnt`, hybrid=`ctc` or `rnnt`.
- Disable `compute_langs` for CTC; it is not supported in the transcription script.
- Reduce `batch_size`, use `compute_dtype=bfloat16`/`float16` where stable, or run CPU for tiny jobs.
- Use `presort_manifest=true` for throughput; NeMo restores output order in the transcription utility, but custom wrappers must preserve order explicitly.
- For timestamp output, set `timestamps=true` or `return_hypotheses=true` and inspect `Hypothesis.timestamp`, not plain text strings.

## Long Audio and Memory Failures

Symptoms:

- Conformer attention OOM on long files.
- Subsampling module OOM before encoder attention.
- Very slow transcription on hour-long audio.

Actions:

- Switch Fast Conformer-style models to local attention with `change_attention_model(self_attention_model="rel_pos_local_attn", att_context_size=[128,128])` when appropriate.
- Use `change_subsampling_conv_chunking_factor(1)` when subsampling is the memory bottleneck.
- Use chunked/buffered inference patterns for hour-scale audio and tune overlap/chunk sizes.
- Lower `batch_size` to 1 for long files, then scale up only after a successful run.

## Streaming Failures

Symptoms:

- `Invalid asr decoding type` or wrong `pipeline_type` errors.
- `Encoder of this model does not support streaming!`
- Cache-aware RNNT rejects the decoding strategy.
- Streaming confidence raises `exclude_blank` errors.
- ITN/NMT import or runtime failures.
- `num_slots`/batch handling errors.

Actions:

- Use `pipeline_type=buffered` with CTC/RNNT/SALM or `pipeline_type=cache_aware` with CTC/RNNT only.
- Use cache-aware streaming only with a streaming-capable encoder/checkpoint.
- For cache-aware RNNT, set `asr.decoding.strategy=greedy_batch` or `asr.decoding.strategy=malsd_batch`.
- Keep streaming `confidence.exclude_blank=true`; non-blank confidence is the supported streaming path.
- Set `streaming.num_slots >= streaming.batch_size` for cache-aware configs.
- Disable `enable_itn` unless text-processing dependencies are installed and `lang` is provided.
- Disable `enable_nmt` unless a vLLM-compatible translation model, device, and memory budget are intentionally configured.
- For prompt-enabled streaming, use fixed `target_lang=<code>` or manifest-driven `target_lang=auto`; set `strip_lang_tags=true` if decoded tags must be removed.

## Fine-Tuning Failures

Symptoms:

- Generic fine-tune script rejects `init_from_ptl_ckpt`.
- Fine-tuning destroys pretrained quality quickly.
- Tokenizer/vocabulary changes crash or reinitialize unexpected layers.
- Validation never runs or training never exits with Lhotse/tarred data.
- DDP sampler conflicts with Lhotse.

Actions:

- Use `.nemo` or pretrained-name initialization with the generic fine-tune script. Use architecture-specific scripts only when changing architecture.
- Start with a lower LR for domain adaptation, commonly `1e-4` to `1e-5`, and avoid an unintended high warmup schedule.
- When changing tokenizers, set `model.tokenizer.update_tokenizer=true` and provide `dir`/`type`; do not also set char labels update.
- For transducer/hybrid tokenizer changes, expect decoder/joint incompatibility and intentionally exclude/reinitialize those components.
- Do not train tokenizers from validation/test text.
- With Lhotse/tarred/Shar, set `trainer.use_distributed_sampler=false`, `trainer.limit_train_batches`, `trainer.val_check_interval`, and `trainer.max_steps`.
- Validate manifests and transcript style before launching multi-hour jobs.

## Lhotse and Dynamic Bucketing Failures

Symptoms:

- Conflicting batch settings produce unexpected batch sizes.
- Bucket bin estimation is slow.
- Dynamic bucketing emits buffer-size warnings.
- Some datasets vanish in multi-dataset configs.
- HuggingFace dataset + Lhotse mismatch.

Actions:

- Choose either static `batch_size`, duration-based `batch_duration`, or OOMptimizer/per-bucket settings. Do not leave stale conflicting fields.
- When applying OOMptimizer bucket results, explicitly set `batch_size=null`, `batch_duration=null`, and `quadratic_duration=null` before adding per-bucket sizes.
- Provide `bucket_duration_bins` of length `num_buckets - 1` to avoid repeated startup estimation.
- Increase `bucket_buffer_size` if Lhotse cannot fill buckets effectively.
- Set `input_cfg=null` when replacing an inherited multi-source config with direct manifests.
- Do not use HuggingFace dataset loading with Lhotse; use non-Lhotse HF flow or convert data to manifests/CutSets.

## Decoding, LM, Word Boosting, and Confidence Failures

Symptoms:

- CUDA graph decoder fails with custom decoding settings.
- Beam decoding is extremely slow.
- LM/boosting artifact path errors.
- Confidence arrays are absent or all zeros.
- Timestamps disappear after changing decoding strategy.

Actions:

- Disable CUDA graphs while debugging decoding customization.
- Prefer batched transducer strategies (`greedy_batch`, `malsd_batch`, `maes_batch`) when supported.
- Use NGPU-LM/boosting only when the optional GPU LM stack and artifacts are installed/provided.
- Treat KenLM/legacy CPU fusion as slower and dependency-heavy.
- Set confidence preservation flags before decoding; for streaming RNNT, use `preserve_frame_confidence=true` and top-level `confidence` with `exclude_blank=true`.
- Preserve timestamp settings (`compute_timestamps=true`, `preserve_alignments=true` when needed) after every `change_decoding_strategy()` call.

## Evaluation and Reporting Problems

Symptoms:

- WER changes dramatically between training logs and standalone eval.
- Raw/cased WER conflicts with normalized WER.
- Multitask BLEU/WER applies to the wrong samples.
- RTFx numbers are noisy.

Actions:

- Report standalone evaluation on a fixed manifest and checkpoint.
- State whether punctuation/capitalization are ignored and whether text was cleaned.
- Use `use_cer=true` for CER; otherwise WER is used.
- For Canary/AST mixes, use constrained multitask metrics so ASR samples get WER and translation samples get BLEU.
- Use warmup steps before reporting RTFx; `warmup_steps=0` can produce noisy throughput.
- Compare averaged checkpoints against the best individual checkpoint and keep the averaged model only if it improves standalone metrics.

## Safe Recovery Checklist

Before a long ASR job, confirm:

- Environment imports `nemo` and PyTorch sees the intended device.
- Manifest checker passes with expected duration/style summaries.
- Model source is explicit (`.nemo` path or pretrained name).
- Dataset paths are accessible from the job working directory.
- Batch controls are non-conflicting.
- Decoder type matches model family.
- Evaluation normalization policy is written down.
- Output/checkpoint paths are user-approved and not overwriting needed artifacts.
