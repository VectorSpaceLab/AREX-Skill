# ASR Workflows

This reference gives self-contained procedures for common NeMo Speech ASR work. Evidence was distilled from `docs/source/asr/inference.rst`, `docs/source/asr/fine_tuning.rst`, `docs/source/asr/datasets.rst`, `docs/source/dataloaders.rst`, `examples/asr/transcribe_speech.py`, `examples/asr/speech_to_text_finetune.py`, `examples/asr/conf/asr_finetune/speech_to_text_finetune.yaml`, `examples/asr/conf/asr_streaming_inference/*.yaml`, `nemo/collections/asr/inference/**`, ASR model classes, and ASR tests.

## Model Selection

- Use CTC models such as Parakeet/FastConformer CTC when fast non-autoregressive transcription, CTC timestamps, CTC LM fusion, or simple decoding is the priority.
- Use RNNT/TDT models when accuracy, streaming-friendliness, transducer timestamps, and batched greedy/beam decoding matter.
- Use Hybrid RNNT-CTC models when the same checkpoint should support RNNT and CTC decoding heads; set the decoder head explicitly when needed.
- Use AED/Canary multitask models when the task needs prompt-conditioned ASR/AST, punctuation/capitalization control, language control, or Canary-style manifest fields.
- Use cache-aware streaming only with models whose encoder supports streaming caches. Use buffered streaming for regular offline models that must be simulated over overlapping chunks.

## Load Checkpoints

Python loading patterns:

```python
import nemo.collections.asr as nemo_asr

model = nemo_asr.models.ASRModel.restore_from("model.nemo")
model = nemo_asr.models.ASRModel.from_pretrained("nvidia/parakeet-tdt-0.6b-v2")
```

Operational notes:

- `restore_from()` loads a local `.nemo` file; `from_pretrained()` may download or read from a model cache.
- For cluster fine-tuning from a pretrained name, only one global rank should download first while others wait; the generic fine-tune script already handles this pattern.
- Training usually needs GPU/CUDA. Inference can run on CPU for small jobs but GPU is recommended; Apple MPS can be enabled with `allow_mps=true` and `PYTORCH_ENABLE_MPS_FALLBACK=1` when supported by PyTorch.

## Offline Transcription

Use either the Python API or the Hydra-backed transcription script.

Python API:

```python
outputs = model.transcribe(audio=["file1.wav", "file2.wav"], batch_size=2)
print(outputs[0].text if hasattr(outputs[0], "text") else outputs[0])
```

Direct arrays/tensors:

```python
import soundfile as sf

audio, sample_rate = sf.read("audio.wav", dtype="float32")
if sample_rate != 16000:
    raise ValueError("NeMo ASR examples expect 16 kHz mono audio")
outputs = model.transcribe([audio], batch_size=1)
```

Transcription config pattern:

```yaml
# Transcription CLI/Hydra field pattern for a caller-owned NeMo transcription wrapper.
pretrained_name: "nvidia/parakeet-tdt-0.6b-v2"
model_path: null
audio_dir: "audio_dir"
dataset_manifest: null
output_filename: "predictions.jsonl"
batch_size: 32
cuda: 0
amp: false
compute_dtype: bfloat16
```

Manifest transcription/evaluation config pattern:

```yaml
# Manifest transcription/evaluation field pattern.
model_path: "model.nemo"
pretrained_name: null
dataset_manifest: "eval.jsonl"
audio_dir: null
output_filename: "decoded.jsonl"
batch_size: 16
calculate_wer: true
clean_groundtruth_text: false
use_cer: false
```

Key `transcribe_speech.py` choices:

- Exactly one of `model_path` or `pretrained_name` should identify the model.
- Use `audio_dir` for ad hoc audio and `dataset_manifest` for reproducible evaluation.
- `presort_manifest=true` improves short-form throughput by reducing padding.
- `channel_selector="average"` averages multi-channel audio; an integer selects one channel.
- `amp=true` is mutually exclusive with a non-float32 `compute_dtype`; prefer `amp=false compute_dtype=bfloat16` on supported GPUs for evaluation.
- `append_pred=true pred_name_postfix=name` adds an additional prediction field to an existing manifest-like output.

## Timestamps and Alignments

Simple timestamp call:

```python
hypotheses = model.transcribe(["audio.wav"], timestamps=True)
for item in hypotheses[0].timestamp["word"]:
    print(item["start"], item["end"], item["word"])
```

Advanced decoding setup:

```python
from omegaconf import open_dict

decoding_cfg = model.cfg.decoding
with open_dict(decoding_cfg):
    decoding_cfg.preserve_alignments = True
    decoding_cfg.compute_timestamps = True
    decoding_cfg.segment_seperators = [".", "?", "!"]
    decoding_cfg.word_seperator = " "
model.change_decoding_strategy(decoding_cfg)
hypotheses = model.transcribe(["audio.wav"], return_hypotheses=True)
```

Operational notes:

- `timestamps=True` implies hypothesis-style output rather than plain strings.
- CTC and RNNT/TDT timestamp support is tested in ASR decoding and transcription tests; timestamps can include `char`, `word`, and `segment` structures depending on model/decoder.
- For transducer beam decoding, use batched strategies such as `malsd_batch`/`maes_batch` when customizing beam search and CUDA graphs.

## Long Audio and Chunked Inference

For long files:

- First try normal `model.transcribe()` with a small `batch_size` and GPU-friendly `compute_dtype`.
- For very long Conformer audio, switch to local attention:

```python
model.change_attention_model(
    self_attention_model="rel_pos_local_attn",
    att_context_size=[128, 128],
)
```

- If subsampling still OOMs, enable subsampling conv chunking:

```python
model.change_subsampling_conv_chunking_factor(1)
```

- For explicit overlap/merge workflows, use NeMo's ASR chunked inference scripts as reference-only patterns. They are not bundled here because they are long-running, model-dependent, GPU-heavy, and tied to example-tree configs.

## Canary and Prompt-Conditioned ASR

Canary/AED models use prompt slots and/or manifest fields for source language, target language, task, punctuation/capitalization, timestamps, ITN, and context.

Python direct parameters:

```python
from nemo.collections.asr.models import EncDecMultiTaskModel

model = EncDecMultiTaskModel.from_pretrained("nvidia/canary-1b-v2")
results = model.transcribe(
    audio=["audio.wav"],
    batch_size=4,
    source_lang="en",
    target_lang="en",
    pnc=True,
)
```

Pin a multilingual model to one transcription language:

```python
results = model.transcribe(audio=["audio.wav"], source_lang="de", target_lang="de")
```

`transcribe_speech.py` prompt override patterns:

```yaml
# Canary transcription field/override pattern.
pretrained_name: "nvidia/canary-1b-v2"
dataset_manifest: "canary_eval.jsonl"
output_filename: "canary_decoded.jsonl"
multitask_decoding:
  beam:
    beam_size: 1
prompt:
  source_lang: en
  target_lang: en
  task: asr
  pnc: yes
```

For Canary single-language fine-tuning, require `source_lang` and `target_lang` in manifests and keep them identical for ASR. If changing tokenizer or decoder shape, exclude incompatible decoder/tokenizer-dependent components during initialization.

## Streaming Inference

NeMo ASR has a streaming-first pipeline API under `nemo.collections.asr.inference` and a local entry script with configs for buffered CTC/RNNT/SALM and cache-aware CTC/RNNT.

Buffered CTC/RNNT command shape:

```yaml
# Buffered streaming config pattern for a caller-owned NeMo streaming wrapper.
pipeline_type: buffered
asr_decoding_type: rnnt
audio_file: "audio_or_manifest"
output_filename: "streaming_output.json"
asr:
  model_name: "nvidia/parakeet-rnnt-1.1b"
  device: cuda
  device_id: 0
  compute_dtype: bfloat16
streaming:
  chunk_size: 4.8
  left_padding_size: 1.6
  right_padding_size: 1.6
```

Cache-aware RNNT command shape:

```yaml
# Cache-aware streaming config pattern for a caller-owned NeMo streaming wrapper.
pipeline_type: cache_aware
asr_decoding_type: rnnt
audio_file: "audio_or_manifest"
output_filename: "cache_aware_output.json"
asr:
  model_name: "streaming_model_or_checkpoint.nemo"
  decoding:
    strategy: greedy_batch
streaming:
  att_context_size: [70, 13]
  use_cache: true
  num_slots: 256
```

Streaming builder constraints:

- `pipeline_type` must be `buffered` or `cache_aware`.
- `asr_decoding_type` must match the model/pipeline: `ctc`, `rnnt`, or buffered-only `salm`.
- Cache-aware RNNT accepts `greedy_batch` or `malsd_batch` only.
- Streaming confidence supports non-blank confidence only: keep `confidence.exclude_blank=true`.
- Enable ITN only when the text-processing dependency stack is installed and `lang`/target language is supplied.
- NMT streaming requires vLLM-compatible model/runtime and a separate supported device; do not enable it for ordinary ASR unless explicitly requested.

Prompt-conditioned cache-aware models can set a fixed prompt once:

```python
model.set_inference_prompt("en-US")
```

or use cache-aware script overrides such as `target_lang=en-US`, `target_lang=auto`, and `strip_lang_tags=true` when using prompt-enabled cache-aware examples.

## Fine-Tuning

Generic fine-tuning field pattern:

```yaml
# Fine-tuning field pattern for a caller-owned NeMo training entry.
init_from_pretrained_model: "nvidia/parakeet-tdt-0.6b-v2"
init_from_nemo_model: null
model:
  train_ds:
    manifest_filepath: "train.jsonl"
  validation_ds:
    manifest_filepath: "val.jsonl"
trainer:
  devices: 1
  max_epochs: 50
```

Alternative local checkpoint initialization pattern:

```yaml
# Local-checkpoint fine-tuning field pattern.
init_from_nemo_model: "base_model.nemo"
init_from_pretrained_model: null
model:
  train_ds:
    manifest_filepath: "train.jsonl"
  validation_ds:
    manifest_filepath: "val.jsonl"
```

Rules:

- Set exactly one of `init_from_pretrained_model` or `init_from_nemo_model`.
- The generic script supports `init_from_nemo_model` and `init_from_pretrained_model`; it intentionally does not support `init_from_ptl_ckpt`.
- Validate manifests with `scripts/check_asr_manifest.py` before starting long jobs.
- Use a low fine-tuning LR such as `1e-4` to `1e-5` for domain adaptation; avoid resetting a warmup scheduler to an unexpectedly high LR.
- Use GPU/CUDA for practical training. Current docs require Python 3.12+, PyTorch 2.7+, and a GPU/CUDA-backed setup for normal training.

Tokenizer/vocabulary changes:

```yaml
# Tokenizer-update fine-tuning field pattern.
init_from_nemo_model: "base_model.nemo"
model:
  tokenizer:
    update_tokenizer: true
    dir: "tokenizer_dir"
    type: bpe
  train_ds:
    manifest_filepath: "train.jsonl"
  validation_ds:
    manifest_filepath: "val.jsonl"
```

- Do not set both `model.tokenizer.update_tokenizer=true` and `model.char_labels.update_labels=true`.
- If tokenizer vocabulary size changes, NeMo reinitializes the decoder; for transducer-style manual initialization, exclude `decoder` and `joint` when loading pretrained weights.
- Do not train tokenizers on validation or test transcripts.

## Lhotse and Dynamic Bucketing

Use Lhotse for efficient ASR training when dynamic batch sizes or dynamic bucketing are needed:

```yaml
# Lhotse fine-tuning field pattern.
init_from_pretrained_model: "nvidia/parakeet-tdt-0.6b-v2"
model:
  train_ds:
    manifest_filepath: "train.jsonl"
    use_lhotse: true
    batch_duration: 1100
    quadratic_duration: 30
    num_buckets: 30
    bucket_buffer_size: 10000
    shuffle_buffer_size: 10000
  validation_ds:
    manifest_filepath: "val.jsonl"
trainer:
  use_distributed_sampler: false
  limit_train_batches: 1000
  val_check_interval: 1000
  max_steps: 300000
```

Important Lhotse rules:

- `batch_duration` controls total audio seconds per batch; `batch_size` can cap examples if both are set.
- `num_buckets` improves padding efficiency but can reduce randomness.
- `quadratic_duration` stabilizes memory for long utterances in transformer-like models.
- `bucket_duration_bins` should have length `num_buckets - 1`; estimate bins once and reuse to skip startup estimation.
- Lhotse handles distributed sampling; set `trainer.use_distributed_sampler=false`.
- Tarred/Shar Lhotse dataloaders are effectively infinite, so use `limit_train_batches`, `val_check_interval`, and `max_steps`.
- HuggingFace dataset loading is not supported with the Lhotse dataloader.
- If using `input_cfg` from a pretrained recipe, override it to `null` when switching to direct manifest fields.

Recommended preflight for dynamic bucketing:

```bash
python scripts/check_asr_manifest.py train.jsonl \
  --min-duration 0.1 \
  --max-duration 30 \
  --style-summary \
  --warn-missing-audio
```

Use the duration/style report to catch mixed transcript conventions and outlier durations before a long job.

## Checkpoint Averaging, OOMptimizer, and Utility Scripts

These source scripts are reference-only, not bundled runtime dependencies:

- `scripts/speech_recognition/estimate_duration_bins.py` and `estimate_duration_bins_2d.py`: useful for Lhotse/static duration bin planning but tied to source-version utility dependencies and real datasets.
- `scripts/speech_recognition/oomptimizer.py`: useful for finding the largest per-bucket batch sizes that fit GPU memory, but intentionally GPU/model/checkpoint-heavy.
- Checkpoint averaging utilities in the repository are checkpoint-mutating and should be run only after the user selects checkpoints and output paths.
- ASR example training/evaluation scripts are not copied because they are long-running, model-download-capable, GPU/training-heavy, and maintained as repo examples.

When using OOMptimizer-derived bucket batch sizes, explicitly null conflicting batch controls before adding per-bucket sizes: `batch_size=null`, `batch_duration=null`, and `quadratic_duration=null`.

## Evaluation

Basic manifest evaluation:

```yaml
# Standalone ASR evaluation field pattern.
model_path: "candidate.nemo"
pretrained_name: null
dataset_manifest: "test.jsonl"
output_filename: "test_decoded.jsonl"
batch_size: 16
calculate_wer: true
clean_groundtruth_text: false
use_cer: false
```

Evaluation guidance:

- Decide whether to ignore punctuation/capitalization before comparing runs; do not mix raw and normalized WER in one headline number.
- Use `use_cer=true` for character error rate, especially for languages/scripts where WER is inappropriate.
- Canary/multitask evaluation may need WER for ASR samples and BLEU for translation samples, with constraints such as `.source_lang==.target_lang` for transcription.
- Report final quality from standalone evaluation, not only training validation logs.
