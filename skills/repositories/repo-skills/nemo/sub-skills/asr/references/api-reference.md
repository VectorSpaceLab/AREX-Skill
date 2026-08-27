# ASR API Reference

This reference summarizes the ASR APIs most often needed by coding agents. Evidence was distilled from ASR model classes under `nemo/collections/asr/models/*.py`, transcription mixins, streaming inference wrappers/builders, ASR decoding tests, and `examples/asr/transcribe_speech.py`.

## Import Roots

```python
import nemo.collections.asr as nemo_asr
from nemo.collections.asr.models import ASRModel, EncDecCTCModel, EncDecRNNTModel, EncDecHybridRNNTCTCModel
from nemo.collections.asr.models import EncDecMultiTaskModel
```

Installed facts captured during generation:

- Distribution: `nemo-toolkit` version `3.1.0+8f85359`.
- Import root `nemo` was verified from an editable source-backed inspection environment.
- Package metadata declares Python `>=3.10`, while current NeMo Speech docs recommend Python 3.12+, PyTorch 2.7+, and GPU/CUDA for training.
- Optional broad extras, compiled extensions, CUDA extras, dev, and docs groups were not installed during skill generation; optional-heavy workflows should document prerequisites rather than assume them.

## Model Families

| Family | Main classes | Use when |
| --- | --- | --- |
| Generic loader | `ASRModel` | Load an unknown `.nemo` checkpoint or pretrained ASR model. |
| CTC | `EncDecCTCModel`, `EncDecCTCModelBPE` | Fast non-autoregressive transcription, CTC timestamps, CTC LM/boosting. |
| RNNT/TDT | `EncDecRNNTModel`, `EncDecRNNTBPEModel` | Transducer accuracy, streaming-friendly decoding, timestamps. |
| Hybrid RNNT-CTC | `EncDecHybridRNNTCTCModel`, `EncDecHybridRNNTCTCBPEModel` | Switch between RNNT and CTC decoding heads. |
| Prompt streaming | `EncDecRNNTBPEModelWithPrompt`, `EncDecHybridRNNTCTCBPEModelWithPrompt` | Cache-aware/prompt-conditioned multilingual streaming. |
| AED/Canary | `EncDecMultiTaskModel` | Prompt-conditioned ASR/AST, language control, PnC, timestamps, chunked Canary inference. |

## Loading and Saving

```python
model = nemo_asr.models.ASRModel.restore_from("checkpoint.nemo")
model = nemo_asr.models.ASRModel.from_pretrained("nvidia/parakeet-tdt-0.6b-v2")
model.save_to("fine_tuned.nemo")
```

Notes:

- `restore_from()` is local-file oriented.
- `from_pretrained()` may contact remote model registries or use a local cache.
- Use a concrete subclass only when you know the checkpoint architecture and need class-specific methods.

## `transcribe()` Core Contract

Common arguments:

```python
outputs = model.transcribe(
    audio=["a.wav", "b.wav"],
    batch_size=4,
    return_hypotheses=False,
    timestamps=False,
)
```

Input forms:

- A single path, list of paths, manifest path, numpy arrays, or PyTorch tensors depending on model/mixin support.
- Audio should be 16 kHz mono for the standard ASR examples and pretrained-model assumptions.
- Multi-channel handling is available through config/script `channel_selector`, including integer channel selection and `average`.

Output forms:

- Plain text/string-like results when `return_hypotheses=false` and timestamps are not requested.
- `Hypothesis` objects when `return_hypotheses=true` or `timestamps=true`.
- Canary/multitask models often expose `.text`, timestamp fields, and task/language-conditioned behavior.

Incremental batch consumption:

```python
config = model.get_transcribe_config()
config.batch_size = 32
for batch_outputs in model.transcribe_generator(audio_files, override_config=config):
    process(batch_outputs)
```

Use `transcribe_generator()` only when output must be handled batch-by-batch to avoid holding all predictions in memory. Regular `model.transcribe()` already batches internally.

## Transcribe Config Fields

Common `TranscribeConfig`/script-equivalent fields:

| Field | Meaning |
| --- | --- |
| `batch_size` | Inference batch size; higher improves throughput but increases memory. |
| `return_hypotheses` | Return `Hypothesis` objects instead of plain strings. |
| `timestamps` | Request word/segment/character timestamps where supported; implies hypothesis output. |
| `use_lhotse` | Use Lhotse dataloading for inference when available. |
| `num_workers` | DataLoader workers. |
| `channel_selector` | Select one channel or average multi-channel audio. |
| `augmentor` | Optional augmentation during transcription/evaluation. |
| `verbose` | Progress display. |

Canary/multitask transcribe configs extend this with prompt/language fields such as `source_lang`, `target_lang`, `pnc`, `text_field`, `lang_field`, `prompt`, and `enable_chunking`.

## Decoding Strategy APIs

Change decoding in Python:

```python
decoding_cfg = model.cfg.decoding
decoding_cfg.strategy = "greedy_batch"
model.change_decoding_strategy(decoding_cfg)
```

Hybrid model head selection:

```python
model.change_decoding_strategy(decoding_cfg, decoder_type="ctc")
model.change_decoding_strategy(decoding_cfg, decoder_type="rnnt")
```

`transcribe_speech.py` decoder checks:

- CTC models only accept `decoder_type=ctc`.
- RNNT models only accept `decoder_type=rnnt`.
- Hybrid models accept `decoder_type=ctc` or `decoder_type=rnnt`.
- `compute_langs` is not supported for CTC decoding in the transcription script.

Common decoding strategy names:

| Decoder | Typical strategies |
| --- | --- |
| CTC | `greedy`, beam/LM-backed CTC strategies when optional dependencies are installed. |
| RNNT/TDT | `greedy`, `greedy_batch`, `beam`, `malsd_batch`, `maes_batch` depending on model and runtime. |
| Cache-aware RNNT streaming | `greedy_batch` or `malsd_batch` only. |
| AED/Canary | Multitask decoding config with greedy/beam fields and prompt handling. |

## Timestamps and Hypotheses

Timestamp setup:

```python
from omegaconf import open_dict

with open_dict(model.cfg.decoding):
    model.cfg.decoding.preserve_alignments = True
    model.cfg.decoding.compute_timestamps = True
model.change_decoding_strategy(model.cfg.decoding)
hyps = model.transcribe(["audio.wav"], return_hypotheses=True)
```

Timestamp structures may include:

- `hyp.timestamp["char"]`
- `hyp.timestamp["word"]`
- `hyp.timestamp["segment"]`
- transducer/raw alignment fields when `preserve_alignments=true`

Tests under ASR decoding validate that timestamps align with decoded characters/subwords/words/segments and that repeated `transcribe(timestamps=True)` should not unnecessarily reinstate the decoder when already configured.

## Confidence APIs

Confidence config shape:

```yaml
decoding:
  confidence_cfg:
    preserve_frame_confidence: false
    preserve_token_confidence: false
    preserve_word_confidence: false
    exclude_blank: true
    aggregation: mean
    method_cfg:
      name: entropy
      entropy_type: tsallis
      alpha: 0.33
      entropy_norm: exp
```

Supported confidence methods include `max_prob` and entropy-based confidence (`gibbs`, `tsallis`, `renyi`). Aggregation choices include `mean`, `min`, `max`, and `prod`. Streaming RNNT confidence is wired through the top-level streaming `confidence` block only when greedy `preserve_frame_confidence=true`, and requires `exclude_blank=true`.

## Vocabulary and Tokenizer APIs

Character vocabulary change:

```python
model.change_vocabulary(new_vocabulary=[" ", "a", "b", "c", "'"])
```

BPE/WPE tokenizer change:

```python
model.change_vocabulary(new_tokenizer_dir="tokenizer_dir", new_tokenizer_type="bpe")
```

Fine-tune script behavior:

- `model.tokenizer.update_tokenizer=true` requires `model.tokenizer.dir` and `model.tokenizer.type`.
- `model.char_labels.update_labels=true` calls `change_vocabulary(new_vocabulary=...)`.
- Setting both tokenizer update and char-label update is invalid.
- If tokenizer vocabulary size changes, decoder parameters are reinitialized by the generic fine-tune flow.

## Canary and Multitask APIs

Canary direct transcription:

```python
from nemo.collections.asr.models import EncDecMultiTaskModel

model = EncDecMultiTaskModel.from_pretrained("nvidia/canary-1b-v2")
hyps = model.transcribe(
    audio=["audio.wav"],
    source_lang="en",
    target_lang="en",
    pnc=True,
    timestamps=True,
)
```

Prompt dict style used by the transcription script:

```bash
+prompt.source_lang=en +prompt.target_lang=en +prompt.task=asr +prompt.pnc=yes
```

or explicit slot style:

```bash
+prompt.role=user +prompt.slots.source_lang=en +prompt.slots.target_lang=es +prompt.slots.task=s2t_translation +prompt.slots.pnc=yes
```

For single-language ASR with multilingual Canary, set `source_lang` and `target_lang` to the same value in both training data and inference.

## Streaming Pipeline APIs

Builder entry:

```python
from nemo.collections.asr.inference.factory.pipeline_builder import PipelineBuilder

pipeline = PipelineBuilder.build_pipeline(cfg)
output = pipeline.run(audio_filepaths, progress_bar=progress_bar, options=options)
```

Pipeline classes by mode:

| Pipeline | Builder class | Decoding types |
| --- | --- | --- |
| Buffered CTC | `BufferedPipelineBuilder` | `ctc` |
| Buffered RNNT/TDT | `BufferedPipelineBuilder` | `rnnt` |
| Buffered SALM | `BufferedPipelineBuilder` | `salm` |
| Cache-aware CTC | `CacheAwarePipelineBuilder` | `ctc` |
| Cache-aware RNNT | `CacheAwarePipelineBuilder` | `rnnt` |

Request/options concepts:

- `audio_file` can be a single file, directory, or manifest JSON/JSONL.
- Streaming input is sorted by duration by the entry script for throughput.
- Per-request options can include source/target language, language code, ITN flags, timestamps, and prompt-like metadata depending on pipeline/model.
- `num_slots` must be at least the configured streaming `batch_size` in cache-aware configs.

## Prompt Streaming APIs

Prompt-enabled streaming models expose:

```python
model.set_inference_prompt("en-US")
```

Cache-aware prompt wrappers can encode prompt vectors and pass them through streaming steps. Use `target_lang=auto` in manifest-driven prompt streaming to read per-sample `target_lang` when the script supports it, otherwise pin one language with `target_lang=<code>`.

## Evaluation Helpers

`transcribe_speech.py` computes WER/CER when `calculate_wer=true`, with controls such as:

- `gt_text_attr_name=text`
- `clean_groundtruth_text=true/false`
- `langid=en`
- `use_cer=true/false`
- `calculate_rtfx=true` with `warmup_steps` and `run_steps` for throughput measurement

Streaming inference configs additionally support ASR/NMT metric blocks with capitalization and punctuation normalization switches.
