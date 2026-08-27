# Speaker Workflows

This reference covers NeMo Speech speaker tasks: recognition, speaker embeddings, verification, diarization, VAD, ASR+diarization, Sortformer training/inference, and evaluation. It distills evidence from `docs/source/asr/speaker_diarization/**`, `docs/source/asr/speaker_recognition/**`, `docs/source/asr/speech_classification/**`, `examples/speaker_tasks/**`, `scripts/speaker_tasks/**`, `scripts/voice_activity_detection/**`, `nemo/collections/asr/models/label_models.py`, `nemo/collections/asr/models/sortformer_diar_models.py`, and `tests/collections/speaker_tasks/**`.

## Choose the Workflow

- Use `SortformerEncLabelModel` for end-to-end diarization when the task asks for Sortformer, neural diarization, offline/streaming diarization, overlap-aware speaker activity, or speaker labels directly from audio.
- Use `ClusteringDiarizer` for cascaded diarization when the task asks for VAD + speaker embeddings + clustering, oracle VAD, external VAD, unknown speaker-count estimation, domain-specific meeting/telephonic settings, or embedding reuse.
- Use `EncDecSpeakerLabelModel` for speaker identification, verification, language/speaker classification variants, embedding extraction, TitaNet, ECAPA-TDNN, or SpeakerNet training/fine-tuning.
- Use VAD workflows when the task is speech/non-speech segmentation, VAD threshold tuning, VAD post-processing, or preparing speech regions for diarization.
- Use ASR+diarization when the task asks for speaker-attributed transcripts, word-level diarization error, cpWER, reference CTM comparison, or ASR-based VAD.
- Use `references/forced-alignment.md` when the task asks for token/word/segment timestamps, CTM/ASS subtitle-style outputs, or start/end-of-utterance timing from text plus audio.

## Environment and Checkpoint Assumptions

- Use a NeMo Speech installation compatible with the current docs: Python 3.12+, PyTorch 2.7+, and CUDA-capable GPU for training. CPU-only inference may work for small probes but is slow and not the recommended path.
- Pretrained names such as `titanet_large`, `ecapa_tdnn`, `speakerverification_speakernet`, `vad_multilingual_marblenet`, and `stt_en_conformer_ctc_large` may download model assets. For offline or hermetic runs, provide local `.nemo` checkpoints instead.
- Speaker example scripts are Hydra entry points. Override nested config fields with `key=value`, quote list or string values when the shell may reinterpret them, and use `+key=value` only when adding a new field.
- Long training/evaluation scripts are GPU- and dataset-heavy; do not run them as smoke checks. Validate manifests first with `../scripts/check_speaker_manifest.py`.

## Sortformer Diarization Inference

Sortformer is an end-to-end diarizer. Repository docs identify offline and streaming Sortformer variants; streaming uses an Arrival-Order Speaker Cache (AOSC) to preserve speaker labels across chunks. Current public examples load HuggingFace-style names such as `nvidia/diar_sortformer_4spk-v1`, `nvidia/diar_streaming_sortformer_4spk-v2`, and `nvidia/diar_streaming_sortformer_4spk-v2.1`.

Python shape:

```python
from nemo.collections.asr.models import SortformerEncLabelModel

model = SortformerEncLabelModel.from_pretrained("nvidia/diar_streaming_sortformer_4spk-v2.1")
model.eval()
segments = model.diarize(audio="audio.wav", batch_size=1, num_workers=0)
```

Expected output is a nested list of segments in the model API shape `[begin_seconds, end_seconds, speaker_index]`. If `include_tensor_outputs=True`, `diarize()` also returns raw speaker activity probability tensors.

When using streaming checkpoints for latency-sensitive inference, tune model module attributes only when you understand the latency/accuracy trade-off:

```python
model.sortformer_modules.chunk_len = 340
model.sortformer_modules.chunk_right_context = 40
model.sortformer_modules.fifo_len = 40
model.sortformer_modules.spkcache_update_period = 300
```

Important choices:

- Use `batch_size=1` when reproducing published DER with the longest inference window and lowest memory surprises.
- Use `postprocessing_yaml` only when you have a tuned YAML for binarization/padding/filtering. Default inference bypasses post-processing except binarization.
- Provide a manifest with `rttm_filepath` when evaluating DER; omit `rttm_filepath` for pure inference.
- The common Sortformer configs are fixed around a maximum speaker count, often 4. Do not expect a 4-speaker model to perform well on sessions with many more speakers.

## Sortformer Training and Fine-Tuning

Sortformer training is a heavy GPU workflow. The source training scripts use PyTorch Lightning plus Hydra and instantiate `SortformerEncLabelModel(cfg=cfg.model, trainer=trainer)`, then optionally call `maybe_init_from_pretrained_checkpoint(cfg)` before `trainer.fit(model)`.

Typical override shape:

```bash
python sortformer_diar_train.py \
  --config-path='../conf/neural_diarizer' \
  --config-name='sortformer_diarizer_hybrid_loss_4spk-v1.yaml' \
  trainer.devices=1 \
  trainer.precision=bf16 \
  model.train_ds.manifest_filepath=train_manifest.json \
  model.validation_ds.manifest_filepath=dev_manifest.json \
  exp_manager.exp_dir=sortformer_runs \
  exp_manager.name=sample_train
```

Config facts distilled from the source configs:

- `model.max_num_of_spks` sets the supported speaker-count ceiling.
- `model.train_ds.session_len_sec` and validation/test `session_len_sec` cap each training/eval segment duration.
- `soft_label_thres` controls binarization of diarization targets; higher values make the model more conservative.
- `pil_weight` and `ats_weight` combine permutation-invariant and arrival-time-sort losses in hybrid configs.
- `use_lhotse`, `use_bucketing`, `bucket_duration_bins`, `batch_duration`, and `quadratic_duration` affect data batching and memory.
- Streaming configs add `model.streaming_mode=True` plus `sortformer_modules` cache/chunk parameters such as `spkcache_len`, `fifo_len`, `chunk_len`, `chunk_left_context`, `chunk_right_context`, and `spkcache_update_period`.

Training data should cover every speaker count you need at inference time. If the target domain needs 1 through N speakers, include examples for each count. Long recordings can be represented by multiple manifest lines with the same audio/RTTM files and distinct `offset`, `duration`, and `uniq_id` values.

## Clustering Diarizer Inference

Cascaded diarization combines VAD, speaker embedding extraction, and clustering. It is a good choice when you need oracle VAD, external VAD, explicit speaker embedding checkpoints, or clustering knobs.

Hydra command shape:

```bash
python offline_diar_infer.py \
  diarizer.manifest_filepath=manifest.json \
  diarizer.out_dir=diar_output \
  diarizer.vad.model_path=vad_multilingual_marblenet \
  diarizer.speaker_embeddings.model_path=titanet_large \
  diarizer.speaker_embeddings.parameters.save_embeddings=False
```

Equivalent API shape:

```python
from omegaconf import OmegaConf
from nemo.collections.asr.models import ClusteringDiarizer

cfg = OmegaConf.load("diar_infer_meeting.yaml")
cfg.diarizer.manifest_filepath = "manifest.json"
cfg.diarizer.out_dir = "diar_output"
model = ClusteringDiarizer(cfg=cfg).to(cfg.device)
model.diarize()
```

Key config sections:

- `diarizer.manifest_filepath`: JSONL manifest. `audio_filepath` is mandatory; `rttm_filepath`, `uem_filepath`, `ctm_filepath`, and `num_speakers` enable evaluation/oracle behavior.
- `diarizer.oracle_vad`: when true, speech regions come from RTTM labels in the manifest instead of a VAD model.
- `diarizer.vad.model_path`: local `.nemo` checkpoint or pretrained VAD name. Do not also set `external_vad_manifest` unless the workflow explicitly expects externally generated VAD labels.
- `diarizer.speaker_embeddings.model_path`: local `.nemo` checkpoint or pretrained name such as `titanet_large`, `ecapa_tdnn`, or `speakerverification_speakernet`.
- `diarizer.speaker_embeddings.parameters.window_length_in_sec`, `shift_length_in_sec`, and `multiscale_weights`: scalar for single-scale or same-length lists for multiscale diarization.
- `diarizer.clustering.parameters.oracle_num_speakers`: when true, use manifest `num_speakers`; otherwise estimate speaker count up to `max_num_speakers`.
- `diarizer.collar` and `diarizer.ignore_overlap`: DER scoring choices.

Domain settings matter. Meeting and telephonic configs tune VAD thresholds, multiscale windows, and clustering defaults differently. If the user reports high false alarm/miss rates, inspect the VAD parameters before changing the speaker embedding model.

## ASR plus Diarization

Use ASR+diarization when the user needs a transcript with speaker labels or combined DER/WER/cpWER reporting. The source workflow runs ASR first for word hypotheses and timestamps, then diarization, then maps words to speaker labels.

Hydra command shape:

```bash
python offline_diar_with_asr_infer.py \
  diarizer.manifest_filepath=manifest.json \
  diarizer.out_dir=asr_diar_output \
  diarizer.speaker_embeddings.model_path=titanet_large \
  diarizer.asr.model_path=stt_en_conformer_ctc_large \
  diarizer.asr.parameters.asr_based_vad=True \
  diarizer.speaker_embeddings.parameters.save_embeddings=False
```

Important ASR diarization settings:

- `diarizer.asr.parameters.asr_based_vad=True` uses ASR word timestamps to derive speech regions.
- `asr_based_vad_threshold` caps the gap between adjacent words when generating ASR-based VAD timestamps.
- `word_ts_anchor_pos` can be `start`, `end`, or `mid`; `word_ts_anchor_offset` shifts the chosen anchor and is commonly tuned in the range `[-0.05, 0.2]` seconds.
- `fix_word_ts_with_VAD=True` requires a VAD model and can repair word timestamps with VAD output.
- `ctc_decoder_parameters.pretrained_language_model` enables optional KenLM/pyctcdecode beam search; install optional dependencies only when needed.
- Reference CTM files in the manifest enable WER and cpWER comparisons. CTM speaker IDs must match RTTM speaker IDs for speaker-attributed scoring.

ASR+diarization routes model selection and decoding details to `../asr/SKILL.md`; keep this sub-skill focused on speaker-label mapping, diarization configs, and speaker scoring.

## Speaker Recognition and Embeddings

Speaker recognition uses `EncDecSpeakerLabelModel`. It covers speaker identification, speaker verification, TitaNet, ECAPA-TDNN, SpeakerNet, and embedding extraction.

Single-audio embedding:

```python
from nemo.collections.asr.models import EncDecSpeakerLabelModel

model = EncDecSpeakerLabelModel.from_pretrained(model_name="titanet_large")
embedding = model.get_embedding("speaker.wav")
```

Speaker verification:

```python
same_speaker = model.verify_speakers("enroll.wav", "test.wav", threshold=0.7)
```

Batch inference over a manifest:

```python
embs, logits, gt_labels, trained_labels = model.batch_inference(
    "speaker_manifest.json", batch_size=32, sample_rate=16000, device="cuda"
)
predicted = [trained_labels[i] for i in logits.argmax(axis=-1)]
```

Speaker identification inference requires enrollment and test manifests. Enrollment labels are known speaker IDs; test labels are commonly `infer`. The cosine-similarity backend averages enrollment embeddings per label and maps each test embedding to the highest similarity speaker. A neural-classifier backend requires a model trained/fine-tuned on the enrollment label set.

Training/fine-tuning facts:

- Recognition configs set `model.train_ds.manifest_filepath`, `model.validation_ds.manifest_filepath`, `model.decoder.num_classes`, preprocessor settings, encoder, decoder, loss, optimizer, and trainer fields.
- TitaNet and ECAPA configs use `SpeakerDecoder` with attention/xvector pooling and angular softmax loss in the examples.
- Fine-tuning a pretrained TitaNet-style model uses `init_from_pretrained_model.speaker_tasks.name='titanet_large'`, includes preprocessor/encoder weights, and excludes decoder layers when the class set changes.
- Use tarred datasets only when the data-tools/ASR sharding guidance is appropriate; generic sharding belongs outside this sub-skill.

## VAD Workflows

VAD is represented in the speech-classification docs as a MarbleNet-style speech/non-speech classifier and is a component of cascaded diarization.

Use VAD for:

- producing speech activity regions before speaker embedding extraction;
- `oracle_vad=True` comparisons using RTTM ground truth;
- external VAD manifests when a separate system already produced regions;
- threshold tuning when false alarms/misses dominate diarization error;
- long-audio splitting to avoid CUDA memory issues.

VAD config parameters to tune:

- `window_length_in_sec` and `shift_length_in_sec`: frame/context resolution.
- `smoothing`: usually `median` or false.
- `overlap`: overlap ratio for mean/median smoothing.
- `onset` and `offset`: binarization thresholds.
- `pad_onset` and `pad_offset`: padding around detected speech.
- `min_duration_on` and `min_duration_off`: remove short speech or fill short non-speech gaps.
- `filter_speech_first`: ordering of filtering operations.

Source VAD helper scripts are reference-only here because they depend on NeMo runtime utilities, frame prediction directories, RTTM directories, and can generate large outputs. Their distilled purposes are:

- long-audio manifest writing: split audio into manageable chunks for frame-level VAD;
- overlap posterior smoothing: convert frame predictions into speech/no-speech tables;
- threshold tuning: search onset/offset/padding/min-duration ranges against ground-truth RTTM.

## Evaluation and Metrics

Speaker diarization evaluation primarily uses DER. Tests and source utilities also cover online DER statistics, speaker-count accuracy, cpWER, RTTM parsing, and conversion between label strings and RTTM-like annotations.

Evaluation checklist:

1. Validate the manifest has `audio_filepath`, `rttm_filepath`, and suitable `offset`/`duration` fields when clipping matters.
2. Ensure each RTTM file contains `SPEAKER <recording-id> <channel> <start> <duration> <NA> <NA> <speaker-id> <NA> <NA>` lines.
3. Confirm manifest base names and RTTM recording IDs align with the unique IDs NeMo derives from audio file names.
4. Decide whether scoring should ignore overlap and what collar to use.
5. For ASR+diarization, provide CTM files whose speaker IDs exactly match RTTM speaker IDs.
6. Treat wrong speaker count separately from boundary errors; clustering can estimate an incorrect count even when VAD is good.

## Source Script Handling

Bundled runtime script:

- `../scripts/check_speaker_manifest.py` is an adapted, safe validator inspired by NeMo speaker manifest conventions. It is deterministic, local-only, and does not import NeMo.

Reference-only source scripts and why they are not bundled verbatim:

- diarization inference/training scripts: GPU/checkpoint-heavy, rely on Hydra configs and optional downloads, and can write large output trees;
- speaker recognition training/fine-tuning/evaluation scripts: dataset/training-heavy, can download checkpoints, and mutate experiment/checkpoint directories;
- VAD post-processing/threshold scripts: depend on NeMo runtime outputs and can write many files while sweeping parameters;
- data creation/simulation scripts: can be long-running, multiprocessing-heavy, and may depend on audio decoding, sox, librosa, scipy, soundfile, and generated datasets;
- forced-aligner scripts: useful, but long, ASR-checkpoint-bound, and output-generating; their input/output contract is distilled in `forced-alignment.md`.
