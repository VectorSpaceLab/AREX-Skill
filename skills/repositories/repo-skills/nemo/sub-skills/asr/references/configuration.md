# ASR Configuration Reference

This reference distills NeMo ASR manifest, Hydra, fine-tuning, Lhotse, streaming, decoding, customization, and evaluation configuration patterns from the ASR docs, configs, example scripts, source, and tests.

## Hydra Override Rules

NeMo examples use Hydra/OmegaConf. Typical override rules:

- Override existing fields as `section.key=value`.
- Add a new key with `+new.key=value` or `++new.key=value` depending on whether the key may already exist.
- Quote paths and strings that contain shell-sensitive characters.
- Use `null`, `true`, and `false` as YAML values, not Python `None`, `True`, or `False`.
- Use list syntax such as `streaming.att_context_size=[70,13]` and quote it if the shell expands brackets.
- Keep `--config-path` relative to the script location or use an absolute/project-local path chosen by the user.

Common mistakes:

- Passing both `model_path` and `pretrained_name` to transcription.
- Passing neither `audio_dir` nor `dataset_manifest` to transcription.
- Setting `amp=true` together with `compute_dtype=bfloat16`/`float16` in `transcribe_speech.py`.
- Using `compute_langs=true` with CTC decoding.
- Using `decoder_type=ctc` for a pure RNNT model or `decoder_type=rnnt` for a pure CTC model.

## ASR Manifest Format

Base NeMo ASR JSONL format:

```json
{"audio_filepath": "audio.wav", "text": "the transcription", "duration": 3.5}
```

Required fields:

| Field | Type | Notes |
| --- | --- | --- |
| `audio_filepath` | string | Absolute or relative path. WAV is the common assumption. |
| `text` | string | Reference transcript for training/evaluation; may be empty only for specific inference-only workflows. |
| `duration` | positive number | Seconds; used for filtering, batching, bucketing, and throughput estimates. |

Recommended checks:

```bash
python scripts/check_asr_manifest.py train.jsonl \
  --min-duration 0.1 \
  --max-duration 30 \
  --style-summary \
  --warn-missing-audio
```

Transcript style rules:

- Choose one convention for casing, punctuation, numerals, symbols, abbreviations, and inverse-text-normalization before training.
- Do not mix raw cased/punctuated transcripts with normalized lowercase/no-punctuation transcripts unless the model/task is explicitly trained for it.
- Keep validation/test style aligned with the metric configuration; raw WER and normalized WER answer different questions.

## Canary Manifest Format

Canary v1-style ASR/AST entries:

```json
{"audio_filepath":"audio.wav","text":"hello world","duration":3.5,"source_lang":"en","target_lang":"en","task":"asr","pnc":"yes"}
```

Canary Flash/v2-style entries:

```json
{"audio_filepath":"audio.wav","text":"hello world","duration":3.5,"source_lang":"en","target_lang":"en","pnc":"yes","timestamp":"no","itn":"no"}
```

Canary field meanings:

| Field | v1 | Flash/v2 | Notes |
| --- | --- | --- | --- |
| `source_lang` | required | required | Input audio language code. |
| `target_lang` | required | required | Same as source for ASR; different for translation. |
| `task` | required | removed/inferred | v1 commonly uses `asr` or `ast`; newer models infer from language pair. |
| `pnc` | required | optional | Use `yes`/`no` strings in manifests. |
| `itn` | optional | optional | Inverse text normalization; commonly `yes`/`no`. |
| `timestamp` | optional | optional | Word timestamp control; commonly `yes`/`no`. |
| `diarize` | optional | optional | This ASR sub-skill routes diarization work elsewhere. |
| `decodercontext` | optional | optional | Previous transcript/context for biasing. |
| `emotion` | optional | optional | Hint such as `neutral`, `angry`, `happy`, `sad`, or `undefined`. |

For single-language Canary ASR fine-tuning, set `source_lang` and `target_lang` to the same code for every sample and make the inference call do the same.

## Fine-Tuning Config

Base config shape from `speech_to_text_finetune.yaml`:

```yaml
init_from_nemo_model: null
init_from_pretrained_model: null
model:
  sample_rate: 16000
  train_ds:
    manifest_filepath: ???
    sample_rate: ${model.sample_rate}
    batch_size: 16
    shuffle: true
    num_workers: 8
    pin_memory: true
    max_duration: 20
    min_duration: 0.1
  validation_ds:
    manifest_filepath: ???
    sample_rate: ${model.sample_rate}
    batch_size: 16
    shuffle: false
  tokenizer:
    update_tokenizer: false
    dir: null
    type: bpe
  char_labels:
    update_labels: false
    labels: null
  optim:
    name: adamw
    lr: 1e-4
trainer:
  devices: -1
  max_epochs: 50
  accelerator: auto
```

Initialization:

- `init_from_pretrained_model=<name>` for remote/cache-backed pretrained names.
- `init_from_nemo_model=<path>` for a local `.nemo` checkpoint.
- Do not set both.
- `init_from_ptl_ckpt` is intentionally unsupported by the generic fine-tune script.

Tokenizer/vocabulary:

```yaml
model:
  tokenizer:
    update_tokenizer: true
    dir: tokenizer_dir
    type: bpe
```

- For BPE/WPE models, set `model.tokenizer.update_tokenizer=true` with `dir` and `type`.
- For char models, set `model.char_labels.update_labels=true` with a label list.
- Do not set tokenizer update and char labels update together.
- If changing tokenizer with transducer/hybrid models, expect decoder/joint incompatibility and plan decoder/joint reinitialization or exclusion.

Optimization:

- Domain adaptation usually starts with a lower LR than full training, often `1e-4` to `1e-5`.
- Use spec augmentation for robustness, but avoid over-augmenting small validation/test sets.
- For max-step training, set `trainer.max_steps` and validation cadence explicitly rather than relying only on epochs.

## Lhotse Dynamic Bucketing

Minimal Lhotse training additions:

```yaml
model:
  train_ds:
    use_lhotse: true
    batch_duration: 1100
    quadratic_duration: 30
    num_buckets: 30
    num_cuts_for_bins_estimate: 10000
    bucket_buffer_size: 10000
    shuffle_buffer_size: 10000
trainer:
  use_distributed_sampler: false
  limit_train_batches: 1000
  val_check_interval: 1000
  max_steps: 300000
```

Key fields:

| Field | Meaning |
| --- | --- |
| `use_lhotse` | Enables Lhotse dataloading. |
| `batch_duration` | Total utterance seconds per minibatch. |
| `quadratic_duration` | Penalizes long utterances for more stable memory. |
| `num_buckets` | Dynamic bucket count; more buckets reduce padding but can reduce randomness. |
| `num_cuts_for_bins_estimate` | Startup sample count used to estimate duration bins. |
| `bucket_buffer_size` | Examples held for bucket assignment. |
| `shuffle_buffer_size` | Examples held for approximate shuffling. |
| `bucket_duration_bins` | Explicit bins; length must be `num_buckets - 1`. |
| `text_field` | Manifest text key, default `text`. |
| `lang_field` | Manifest language key, default `lang`. |
| `batch_size` | Caps examples per batch when used with `batch_duration`; static batch size when `batch_duration` is absent. |

Conflict cleanup:

- When applying OOMptimizer bucket batch sizes, set `batch_size=null`, `batch_duration=null`, and `quadratic_duration=null` before adding `bucket_batch_size`/per-bucket settings.
- When fine-tuning a checkpoint whose config uses `input_cfg`, set `input_cfg=null` if switching to plain `manifest_filepath` fields.
- For Lhotse with tarred or Shar data, use max-step/pseudo-epoch controls because dataloaders can be infinite.

Extended multi-dataset input example:

```yaml
input_cfg:
  - type: group
    weight: 0.7
    tags:
      task: asr
    input_cfg:
      - type: nemo_tarred
        manifest_filepath: asr_en_manifest.json
        tarred_audio_filepath: asr_en_audio__OP_0..512_CL_.tar
        weight: 0.6
        tags:
          source_lang: en
          target_lang: en
      - type: nemo_tarred
        manifest_filepath: asr_de_manifest.json
        tarred_audio_filepath: asr_de_audio__OP_0..512_CL_.tar
        weight: 0.4
        tags:
          source_lang: de
          target_lang: de
```

## Tarred Dataset Config

Non-Lhotse tarred config shape:

```yaml
model:
  train_ds:
    is_tarred: true
    manifest_filepath: tarred_audio_manifest.json
    tarred_audio_filepaths: audio__OP_0..63_CL_.tar
    shuffle_n: 2048
```

Rules:

- Use brace-equivalent `_OP_` and `_CL_` in configs/SLURM contexts to avoid shell brace expansion problems.
- Ensure shard count is divisible by world size when scattering shards across workers.
- Avoid tarred validation/test when exact once-per-epoch semantics matter.
- Generic tar conversion is routed to data tooling rather than this ASR sub-skill.

## Streaming Config

Common top-level fields:

```yaml
pipeline_type: buffered       # buffered or cache_aware
asr_decoding_type: rnnt       # ctc, rnnt, or buffered salm
matmul_precision: high
log_level: 20
audio_file: null
output_filename: null
output_dir: null
enable_itn: false
enable_nmt: false
asr_output_granularity: segment
lang: null
warmup_steps: 0
run_steps: 1
```

ASR block:

```yaml
asr:
  model_name: nvidia/parakeet-rnnt-1.1b
  device: cuda
  device_id: 0
  compute_dtype: bfloat16
  use_amp: false
```

Buffered streaming fields:

```yaml
streaming:
  sample_rate: 16000
  batch_size: 256
  left_padding_size: 1.6
  right_padding_size: 1.6
  chunk_size: 4.8
  word_boundary_tolerance: 4
  request_type: feature_buffer
  padding_mode: right
```

Cache-aware fields:

```yaml
streaming:
  batch_size: 64
  att_context_size: [70, 13]
  use_cache: true
  use_feat_cache: true
  chunk_size_in_secs: null
  request_type: frame
  num_slots: 256
```

Constraints:

- Cache-aware models must support streaming caches; otherwise wrappers raise a streaming-support error.
- `num_slots` must cover concurrent stream/batch needs.
- Cache-aware RNNT supports `greedy_batch` and `malsd_batch`; other strategies should be changed before running.
- Use `return_tail_result=true` when the right-padded tail labels need to be returned for analysis.

## Decoding, LM, Word Boosting, and Confidence

RNNT/TDT greedy CUDA graph config:

```yaml
rnnt_decoding:
  strategy: greedy_batch
  greedy:
    use_cuda_graph_decoder: true
```

RNNT/TDT beam config:

```yaml
rnnt_decoding:
  strategy: malsd_batch
  beam:
    beam_size: 12
    max_symbols_per_step: 10
    allow_cuda_graphs: true
```

Streaming RNNT customization block:

```yaml
asr:
  decoding:
    strategy: greedy_batch
    greedy:
      use_cuda_graph_decoder: true
      enable_per_stream_biasing: true
      preserve_frame_confidence: false
      ngram_lm_model: null
      ngram_lm_alpha: 0.0
      boosting_tree:
        model_path: null
        key_phrases_file: null
        key_phrases_list: null
        source_lang: en
      boosting_tree_alpha: 0.0
```

Confidence block:

```yaml
confidence:
  exclude_blank: true
  aggregation: mean
  method_cfg:
    name: entropy
    entropy_type: tsallis
    alpha: 0.5
    entropy_norm: exp
```

Customization guidance:

- NGPU-LM is the preferred production LM-fusion direction when the optional GPU LM stack is installed.
- KenLM/legacy CPU LM fusion is slower and mostly backward-compatible for CTC-heavy workflows.
- Word boosting can target CTC, RNNT/TDT, and AED/Canary depending on method and optional dependencies.
- Keep LM/boosting artifacts (`.nemo`, phrase lists, n-gram models) under user-controlled paths and document whether they were trained, downloaded, or provided.

## Evaluation Config

Offline evaluation fields:

```bash
calculate_wer=true \
clean_groundtruth_text=false \
langid=en \
use_cer=false \
gt_text_attr_name=text \
calculate_rtfx=true \
warmup_steps=1 \
run_steps=3
```

Streaming metric block shape:

```yaml
metrics:
  asr:
    gt_text_attr_name: text
    clean_groundtruth_text: false
    langid: en
    use_cer: false
    ignore_capitalization: true
    ignore_punctuation: true
    strip_punc_space: false
```

Multitask metric constraints:

```yaml
model:
  multitask_metrics_config:
    log_prediction: true
    metrics:
      wer:
        _target_: nemo.collections.asr.metrics.wer.WER
        use_cer: false
        constraint: ".source_lang==.target_lang"
      bleu:
        _target_: nemo.collections.asr.metrics.bleu.BLEU
        bleu_tokenizer: 13a
        constraint: ".source_lang!=.target_lang"
```

Rules:

- Choose raw, normalized, WER, CER, or BLEU before comparing runs.
- For Chinese/Japanese/Korean translation metrics, use suitable SacreBLEU tokenizers such as `zh`, `ja-mecab`, or `ko-mecab` when dependencies are available.
- With Lhotse and multilingual data, sample-level `bleu_tokenizer` can override the default when `check_cuts_for_bleu_tokenizers=true`.
