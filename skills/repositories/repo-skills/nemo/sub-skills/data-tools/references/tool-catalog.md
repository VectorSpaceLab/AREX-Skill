# Tool Catalog

This catalog distills NeMo data utilities from `scripts/speech_recognition/*.py`, `scripts/tokenizers/*.py`, `scripts/dataset_processing/**`, `scripts/checkpoint_averaging/**`, `tools/asr_evaluator/**`, `tools/ctc_segmentation/**`, `tools/speech_data_explorer/**`, `tools/speech_data_simulator/**`, and `tools/customization_dataset_preparation/**`.

Public runtime guidance is self-contained. Original NeMo scripts are evidence and reference-only unless a safe replacement is bundled in this sub-skill.

## Bundled in This Sub-Skill

| Bundled file | Source handling | Why |
| --- | --- | --- |
| `scripts/validate_manifest.py` | Adapted as a small standalone validator | Safe by default, deterministic, no NeMo imports, no network, no training, no destructive writes. |

Use it before long-running tools:

```bash
python scripts/validate_manifest.py data/train.jsonl \
  --required audio_filepath duration text \
  --min-duration 0.1 --max-duration 30 \
  --summary
```

## Speech Recognition Data Scripts

| Utility | Primary use | Safe planning notes | Source handling |
| --- | --- | --- | --- |
| `estimate_duration_bins.py` | Estimate 1D Lhotse `bucket_duration_bins` from manifest, weighted list, `input_cfg`, or Shar directory. | Reads metadata through NeMo/Lhotse; use bounded `-n`; optional dependencies required. | Reference-only; future agents should use the distilled commands in `lhotse-and-tarred-data.md`. |
| `estimate_duration_bins_2d.py` | Estimate duration/token 2D buckets for AED/prompted models. | Requires tokenizers and sometimes prompt format; can iterate large data; bounded samples recommended. | Reference-only due optional tokenizer/model dependencies. |
| `estimate_data_weights.py` | Compute `input_cfg` weights by hours or example count, with temperature reweighting. | Requires readable input datasets; `num_hours` fails when duration is absent. | Reference-only; behavior distilled in references. |
| `convert_to_tarred_audio_dataset.py` | Convert ASR manifest/audio into NeMo tarred data and metadata. | Reads audio, writes many tar/manifest files, optional DALI index; run `--dry_run` first. | Reference-only because it is long-running and mutates output directories. |
| `filter_tarred_audio_dataset.py` | Re-tar a filtered subset as Lhotse Shar or NeMo tarred data. | Reads tarred audio and writes output archives; requires Lhotse/audio dependencies. | Reference-only because it performs bulk data transformation. |
| `partial_conversion_to_tarred_audio_dataset.py` | Create selected tar shards after manifest-only planning. | Requires metadata from prior tar conversion; writes shards. | Reference-only because it depends on prior generated metadata and writes archives. |
| `create_dali_tarred_dataset_index.py` | Build DALI/WebDataset `.index` files for tar directories. | Requires optional DALI `wds2idx`; writes `dali_index/`. | Reference-only due optional compiled dependency and writes. |
| `convert_hf_dataset_to_nemo.py` | Convert Hugging Face datasets to NeMo manifests. | May download datasets or touch remote cache; Hydra config heavy. | Reference-only because it is network/cache-dependent. |
| `convert_torchaudio_nemo.py` | Convert torchaudio datasets to NeMo shape. | May require external datasets/downloads. | Reference-only. |
| `oomptimizer.py` | Empirically find max per-bucket batch sizes. | GPU/training-heavy; intentionally triggers CUDA OOM search. | Reference-only; route model interpretation to ASR/SpeechLM2 sub-skills. |
| `confidence/benchmark_asr_confidence.py` | ASR confidence benchmarking. | Runs model inference/evaluation. | Reference-only; route model details to ASR. |
| `code_switching/*` | Code-switching audio/manifest creation. | Data-generation workflow with task-specific assumptions. | Reference-only; route model/dataset-specific details to ASR. |

## Tokenizer Scripts

| Utility | Use | Key options and cautions | Source handling |
| --- | --- | --- | --- |
| `process_asr_text_tokenizer.py` | Train ASR text tokenizers from manifests or text files. | Mutually exclusive `--manifest` or `--data_file`; `--data_root`; `--vocab_size`; `--tokenizer spe|wpe`; lowercases by default; SentencePiece options include `--spe_type`, `--spe_character_coverage`, special symbols, byte fallback, digit splitting, sample size, and extremely-large-corpus mode. | Reference-only because it trains/writes tokenizer artifacts and depends on tokenizer libraries. |
| `add_special_tokens_to_sentencepiece.py` | Add special tokens to an existing SentencePiece model. | Requires generated `sentencepiece_model_pb2.py` from protoc and `sentencepiece`; exits if token exists or model cannot load. | Reference-only due generated protobuf prerequisite and tokenizer mutation. |
| `get_hf_text_data.py` | Fetch/process Hugging Face text data using Hydra config. | Network/cache-dependent. | Reference-only. |
| `conf/*.yaml` | Tokenizer data configs. | Use as evidence for option names only; do not require runtime agents to open original configs. | Reference-only. |

Tokenizer planning contract for the reference-only tokenizer utility:

- Choose exactly one corpus input: `--manifest train.jsonl,dev.jsonl` or `--data_file corpus.txt`.
- Set `--data_root tokenizer_out`, `--vocab_size 1024`, and `--tokenizer spe` or `--tokenizer wpe`.
- For SentencePiece, choose `--spe_type bpe`, `--spe_character_coverage 1.0`, special symbol flags, byte fallback, digit splitting, and corpus sampling options as needed.
- Use `--log` for verbose progress when running the utility in a prepared NeMo source environment.

Preflight:

- Validate manifests and transcript field names first.
- Decide case handling before training; default lowercasing may be wrong for case-sensitive tasks.
- Use `--spe_character_coverage 0.9995`-style values for large-character-set languages only when appropriate.
- Keep generated tokenizer artifacts under a deliberate output directory.

## Dataset Processing Scripts

Dataset processing scripts span downloads, format conversion, augmentation, TTS preparation, speaker tasks, VAD, G2P helpers, and corpus-specific workflows.

Common categories:

| Category | Examples | Runtime cautions | Source handling |
| --- | --- | --- | --- |
| Dataset downloads | `get_librispeech_data.py`, `get_commonvoice_data.py`, `get_aishell_data.py`, `get_demand_data.py`, `get_openslr_rir_data.py`, speaker-task downloaders | Network, licenses, large storage, archive extraction. | Reference-only because they are network-bound and dataset-specific. |
| Format conversion | `kaldi2json.py`, `process_an4_data.py`, `process_fisher_data.py`, `process_hub5_data.py`, `process_vad_data.py` | Corpus-specific inputs, writes manifests/audio outputs. | Reference-only. |
| Augmentation/generation | `add_noise.py`, VAD processing, TTS feature/mel generation, `resynthesize_dataset.py` | Reads/writes audio, may need GPUs/models for resynthesis. | Reference-only. |
| TTS data prep | `scripts/dataset_processing/tts/**` | TTS-specific configs and output layouts; route model usage to TTS when present. | Reference-only. |
| G2P helpers | `g2p/convert_cmu_arpabet_to_ipa.py`, `g2p/syllabify.py` | Text/dictionary conversion; verify language assumptions. | Reference-only unless a future narrow skill bundles a small pure-text helper. |
| Spoken Wikipedia scripts | `spoken_wikipedia/preprocess.py`, `run.sh` | Corpus-specific and shell workflow. | Reference-only. |

Safe process for corpus scripts:

1. Read the script help or config in a disposable shell; do not launch downloads by accident.
2. Confirm data license, expected input layout, and output location.
3. Validate source manifests with bundled validator when JSONL is involved.
4. Use small subsets or dry-run flags when available.
5. Record generated manifest field names for downstream model configs.

## Checkpoint Utilities

| Utility | Use | Cautions | Source handling |
| --- | --- | --- | --- |
| `scripts/checkpoint_averaging/checkpoint_averaging.py` | Deprecated utility that restores `.nemo`, averages neighboring `.ckpt` state dicts on CPU, and writes `*-averaged.nemo`. | Mutates model artifacts by writing new `.nemo`; requires class imports and compatible checkpoints. | Reference-only because it loads checkpoints and writes model files. |
| `scripts/checkpoint_averaging/average_model_checkpoints.py` | Hydra-based checkpoint averaging variant. | Checkpoint/model specific; writes artifacts. | Reference-only. |

Use checkpoint utilities only in a deliberate model artifact workspace. For model-class compatibility and `.nemo` restoration details, route to the relevant model sub-skill such as `../asr/SKILL.md`.

## ASR Evaluator

ASR evaluator is a Hydra tool with two high-level parts:

- Engine: ASR inference in offline, chunked, or offline-by-chunked modes, with optional augmentation such as noise.
- Analyst: WER/CER-style error analysis, including metadata groups such as duration intervals or emotion labels.

Reference-only ASR evaluator Hydra option shape:

- `engine.pretrained_name=stt_en_conformer_transducer_large` or an explicit checkpoint/config option selects the model.
- `engine.inference.mode=offline`, `chunked`, or `offline_by_chunked` selects inference mode.
- `engine.test_ds.manifest_filepath=data/eval.jsonl` points to evaluation data.
- Optional noise augmentation points to a separate noise manifest under the engine test dataset augmentor settings.

Use when the task is evaluation, not just validation. It may download/load models, run inference, need GPU, and write outputs. Validate data first with the bundled manifest validator and route decoding/model decisions to `../asr/SKILL.md`.

## CTC Segmentation

CTC segmentation aligns long audio and transcripts into shorter ASR training segments. It is useful when source data has long recordings plus text transcripts, not pre-cut utterances.

Pipeline stages from the tool sources:

1. `prepare_data.py`: normalize/prepare text and audio into a segmentation workspace.
2. `run_ctc_segmentation.py`: run CTC segmentation with a model and segmentation parameters.
3. `cut_audio.py`: cut accepted segments from original audio.
4. `get_metrics_and_filter.py`: compute CER/WER/edge metrics and filter segments.
5. `verify_segments.py`: inspect segment quality.
6. Shell wrappers `run_segmentation.sh` and `run_filter.sh` combine steps.

Cautions:

- Requires NeMo ASR, `ctc-segmentation`, and optional audio tooling such as pysox/sox for formats beyond basic WAV.
- Runs ASR model inference and audio cutting; GPU is strongly recommended for practical workloads.
- Input text normalization choices materially affect segment quality.
- Metrics thresholds such as `--max_cer`, `--max_wer`, `--max_edge_cer`, `--min_duration`, and `--max_duration` should be chosen from a pilot subset.

Source handling: reference-only because it is model/audio-heavy and multi-step. Distilled workflow and failure modes are bundled here.

## Speech Data Explorer

Speech Data Explorer is a Dash web app for inspecting manifests, audio, statistics, vocabulary, OOVs, waveform/spectrograms, error metrics, two-model comparisons, local/S3/AIS paths, and tarred audio with optional DALI indexes.

Reference-only Speech Data Explorer option shapes:

- Local manifest: positional manifest such as `data/eval.jsonl` plus `--port 8050`.
- Tarred data: positional tarred manifest pattern plus `--tar-base-path data/tarred/audio__OP_0..127_CL_.tar` and optional `--dali-index-base data/tarred/dali_index`.
- Two-model comparison: one manifest with two `pred_text_*` fields and `--names_compared pred_text_model_a pred_text_model_b`, or two manifests plus `--names_compared`.
- Remote data: `--s3cfg` for S3-compatible credentials or the literal `AIS` mode when the environment provides AIS variables.

Cautions:

- It starts a web server; choose a safe port and avoid unsuitable headless environments.
- `--force` loads malformed rows but makes WER/CER for empty references meaningless.
- S3/AIS usage requires credentials or environment variables; do not hard-code secrets.
- Audio metrics estimation opens audio and can be slow.

Source handling: reference-only because it is an interactive app with optional web/cloud dependencies.

## Speech Data Simulator

Speech Data Simulator generates synthetic multispeaker sessions for ASR/diarization, with overlap, silence, speaker dominance, turn-taking, background noise, and optional RIR/multichannel simulation.

Reference-only Speech Data Simulator Hydra option shape:

- Config selection uses the simulator's `data_simulator.yaml` configuration.
- Common overrides include `data_simulator.random_seed=42`, `data_simulator.manifest_filepath=data/train_align.json`, and `data_simulator.outputs.output_dir=simulated_sessions`.
- Background-noise and RIR options should be enabled only after a near-field pilot succeeds.

Cautions:

- Requires single-speaker audio and word alignments.
- Optional RIR simulation needs packages such as `gpuRIR` or `pyroomacoustics` and possibly compiled dependencies.
- It writes audio/session labels and can be storage-heavy.
- Route diarization/model usage to a speaker-diarization sub-skill when present.

Source handling: reference-only because it is data-generation-heavy and optional-backend-heavy.

## Customization Dataset Preparation

The customization dataset tool prepares `.jsonl` prompt/completion data for NeMo customization workflows.

Reference-only customization preparation option shapes:

- Validation-only usage sets `--filename data/customization.jsonl` and no templates.
- Column conversion sets `--filename data/qa.csv`, `--prompt_template "Context: {context} Question: {question} Answer:"`, and `--completion_template "{answer}\n"`.
- Optional cleanup/splitting flags include `--drop_duplicates`, `--split_train_validation`, and `--val_proportion 0.1`.

Supported source file extensions are `.jsonl`, `.json`, `.csv`, `.tsv`, and `.xlsx`. The tool writes prepared files next to or derived from the input; use a working copy when experimenting.

Evidence tests cover hyperparameter recommendations, empty completion warnings, imbalanced completion warnings, suffix checks, template parsing/validation, duplicate rows, long-sample filtering, and train/validation splitting.

Source handling: reference-only because it depends on pandas/numpy and writes prepared datasets, but its contracts and warnings are distilled here.

## Source Scripts Excluded from Bundling

Most assigned source scripts are intentionally not copied into the runtime sub-skill because they are long-running, network-bound, GPU/training-heavy, checkpoint-mutating, web-app based, object-store credential dependent, generated/protobuf dependent, corpus-specific, or tightly coupled to the original checkout's package layout. Future agents should use this catalog to understand required options and risks, then run equivalent installed or checked-out NeMo utilities only when the user has provided an appropriate environment. Use bundled `scripts/validate_manifest.py` for preflight validation independent of NeMo imports.
