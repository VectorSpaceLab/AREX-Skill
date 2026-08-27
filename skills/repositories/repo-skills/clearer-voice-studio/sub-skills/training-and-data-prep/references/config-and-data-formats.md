# Config and Data Formats

Use this reference when editing ClearerVoice-Studio YAML/JSON configs and data lists. The examples below use placeholders and relative paths; replace them with real user-owned paths before launch.

## Config file families

| Task | Config type | Required launch fields | Required data fields |
| --- | --- | --- | --- |
| SE train | YAML | `mode`, `network`, `sampling_rate`, `checkpoint_dir` or launcher `--checkpoint_dir` | `tr_list`, `cv_list`, optional `tt_list` |
| SE inference | YAML | `mode`, `network`, `sampling_rate`, `checkpoint_dir`, `output_dir` | `input_path` |
| SS train | YAML | `mode`, `network`, `sampling_rate`, `num_spks`, `load_type`, checkpoint fields | `tr_list`, `cv_list`, optional `tt_list` |
| SS inference | YAML | `mode`, `network`, `sampling_rate`, `num_spks`, `checkpoint_dir`, `output_dir` | `input_path` |
| SR train | YAML + JSON | YAML `mode`, `network`, `config_json`, `checkpoint_dir`; JSON `sampling_rate`, `num_gpus`, upsample/FFT/mel fields | YAML `tr_list`, `cv_list`, optional `tt_list` |
| SR inference | YAML + JSON | YAML `mode`, `network`, `config_json`, `checkpoint_dir`, `sampling_rate`, `output_dir` | `input_path` |
| Offline TSE | YAML | `speaker_no`, `network_reference`, `network_audio`, `init_from`, training hyperparameters | `mix_lst_path`, `audio_direc`, `reference_direc`, `audio_sr`, `ref_sr` |
| Online TSE | YAML | same as offline TSE, with online model/cue settings | same as offline TSE, normally lip/video references |

## Path fields to review

Common path-valued keys:

- `tr_list`, `cv_list`, `tt_list`, `input_path`, `output_dir`
- `checkpoint_dir`, `init_checkpoint_path`, `init_from`, `config_json`
- TSE `mix_lst_path`, `audio_direc`, `reference_direc`
- data-generation `clean_list`, `noise_list`, `speech_dir`, `noise_dir`, `out_audio_root`, `output_path`

Treat literal `None`, empty strings, and intentionally new output directories differently from required existing paths. The bundled config inspector only warns for missing paths when `--check-paths` is set.

## SE list rows

SE training and validation lists use whitespace-separated rows:

```text
noisy/path/utt001.wav clean/path/utt001.wav
noisy/path/utt002.wav clean/path/utt002.wav
```

Some dataloader code also accepts a third duration column:

```text
noisy/path/utt001.wav clean/path/utt001.wav 4.32
```

SE inference lists can be one path per row; if a row has multiple columns, only the first column is decoded.

```text
noisy/path/utt001.wav
noisy/path/utt002.wav
```

## SS list rows

For the included two-speaker configs, use one mixture path followed by one path for each source:

```text
mix/path/utt001.wav source1/path/utt001.wav source2/path/utt001.wav
mix/path/utt002.wav source1/path/utt002.wav source2/path/utt002.wav
```

Set:

```yaml
num_spks: 2
load_type: one_input_multi_outputs
```

If `load_type: one_input_one_output`, each row is interpreted as only input and label. Do not use that mode for two-source separation unless the training target is genuinely one output.

SS inference lists can be a single audio path per row; if multi-column rows are reused from a test set, only the first column is used as mixture input.

## SR list rows

SR training lists are one path per row for high-resolution clean speech unless a custom conditioning setup is added:

```text
clean48k/path/utt001.wav
clean48k/path/utt002.wav
```

SR inference lists are one low-resolution input path per row or a directory/single audio file. The loader accepts common audio/media extensions, but FFmpeg-backed decoding is needed for compressed media.

The SR JSON config has the target `sampling_rate` and a `supported_sampling_rates` list. Check that the input material is one of the supported lower rates or that the preprocessing/resampling plan is intentional.

## TSE mixture CSV rows

Offline and online lip/gesture CSV rows encode a partition, one target speaker segment, one or more interferer segments, SNR offsets, and a duration. The pattern is:

```text
partition,set_a,speaker_a,utterance_a,snr_a,set_b,speaker_b,utterance_b,snr_b,duration_seconds
```

For three-speaker mixtures, one more `set,speaker,utterance,snr` group appears before the duration.

The first field must match the partition the dataloader requests (`train`, `val`, or `test`). The last field is used for duration-based batch sorting and truncation. The path reconstruction is cue-specific:

- Lip/offline video: `reference_direc + set/speaker/utterance + .mp4`.
- Online lip video: same path pattern, but frames are loaded as RGB and resized to the configured image size.
- Gesture: `reference_direc + set/speaker/utterance + .npy` with reshaped gesture features.
- Audio: `audio_direc + set/speaker/utterance + .wav`.

EEG CSV rows use subject/trial/file/start-style fields. The EEG dataloader preloads subject/trial `.npy` files from the reference directory and slices them according to the CSV starts.

Audio-only reference-speech TSE is different: `mix_lst_path` is a directory containing partition subdirectories with `mix_with_length.scp`, `ref.scp`, and `aux.scp`, plus a speaker-id list used during training.

## TSE modality cue mapping

| `network_reference.cue` | Required `reference_direc` contents | Typical reference rate |
| --- | --- | ---: |
| `lip` | video files at `set/speaker/utterance.mp4` | 25 fps |
| `gesture` | gesture arrays at `set/speaker/utterance.npy` | 15 fps |
| `eeg` | subject/trial arrays named by the EEG loader | 128 Hz |
| `speech` | auxiliary/reference speech paths from partition scp files | 8000 Hz or config value |

If a TSE request lacks visual/reference modality directories, stop before launch and ask for the matching directory or narrow the task to an available cue.

## Sampling-rate alignment

- SE 16 kHz networks expect 16 kHz lists; SE 48 kHz full-band work expects 48 kHz targets or a deliberate resampling plan.
- SS 8 kHz and 16 kHz configs use different `sampling_rate` values; list names are not proof of actual audio sample rate.
- SR targets 48 kHz but accepts lower-rate inputs for inference and training preprocessing; check JSON `supported_sampling_rates`.
- TSE has separate `audio_sr` and `ref_sr`; audio/video alignment depends on these values and `max_length`.

For a fine-tune of `MossFormer2_SE_48K`, do not reuse a 16 kHz SE list blindly. Either regenerate/resample clean/noisy pairs to 48 kHz, update `sampling_rate` and network consistently, or choose a 16 kHz network. Pair this with a deliberate `init_checkpoint_path` and new checkpoint directory.

## Using the config inspector

Examples:

```bash
python skills/disco/clearer-voice-studio/sub-skills/training-and-data-prep/scripts/inspect_training_config.py \
  --config train/speech_enhancement/config/train/MossFormer2_SE_48K.yaml \
  --expect-task speech-enhancement \
  --check-paths
```

```bash
python skills/disco/clearer-voice-studio/sub-skills/training-and-data-prep/scripts/inspect_training_config.py \
  --config train/target_speaker_extraction/config/config_LRS2_lip_mossformer2_2spk.yaml \
  --expect-task target-speaker-extraction \
  --as-json
```

The inspector reads only config files and filesystem metadata. It never imports repository training modules or launches training.
