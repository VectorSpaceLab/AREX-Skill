# Audio Data and Evaluation

## Training Data Types

OpenCLIP audio training is selected through `--dataset-type`:

- `webdataset-audio`: real audio-caption shards for CLAP, NaFlexClap, and GenLAP.
- `synthetic-audio`: synthetic waveform/text batches for fixed CLAP smoke tests.
- `auto`: can route to audio when paired with audio model/data settings.

Audio loaders emit dict batches, not tuples:

```python
batch = {
    "audio": {...},
    "text": LongTensor[B, context_length],
}
```

When variable text is enabled, `batch` can also include `text_valid`.

## WebDataset Audio Contract

`webdataset-audio` expects each sample to include a caption member and an audio member.

Caption members:

- `txt`
- `json`
- `cls`

Audio members:

- `wav`
- `flac`
- `mp3`
- `ogg`

Use `--audio-ext` to choose which audio extension `wds.rename(audio=...)` reads. The default is `flac`.

The modern audio pipeline orders stages as tokenize/optional length bucketing before audio decode and transform. This keeps raw compressed bytes in the bucket pool instead of large decoded waveforms.

Important flags:

```bash
--dataset-type webdataset-audio
--train-data 'shards/{000000..000999}.tar'
--train-num-samples 1000000
--audio-ext flac
--audio-fill repeatpad
--audio-trunc rand_trunc
--audio-fusion
--audio-int16-normalize
--audio-multiprocessing-context forkserver
```

With `--workers > 0`, audio loaders default to `forkserver` because torchaudio/mel work can deadlock when forked after audio libraries create threads. Use `spawn` if forkserver is unsupported in the host environment.

## Fixed CLAP Batch Shapes

For HTSAT/Whisper CLAP, `_audio_collate` produces:

```python
batch["audio"] = {
    "waveform": FloatTensor[B, clip_samples],
    "longer": BoolTensor[B],
    # optional when fusion preprocessing is active:
    "mel_fusion": FloatTensor[B, 4, frames, mel_bins],
}
batch["text"] = LongTensor[B, context_length]
```

`frames = clip_samples // hop_size + 1`. With the default `CLIPAudioCfg`, this is `1001`.

`synthetic-audio` uses the resolved transform config to choose `sample_rate` and `clip_samples`. It is useful for smoke tests but not a substitute for real audio-caption data.

## NaFlexClap Data Contract

For `naflexclap_*`, the CLI parser sets `args.naflexclap=True`, `args.use_naflex=True`, and `args.force_naflex_vision=False`. NaFlexClap uses the audio NaFlex path, not the image NaFlex transform.

NaFlexClap audio batches contain:

```python
batch["audio"] = {
    "patches": FloatTensor[B, N, patch_dim],
    "patch_coord": LongTensor[B, N, 2],
    "patch_valid": BoolTensor[B, N],
}
```

Use `webdataset-audio` for NaFlexClap. `synthetic-audio` intentionally raises for NaFlex audio transforms because synthetic samples feed a raw `(waveform, sample_rate)` tuple directly, while NaFlex data batching expects a transform factory and patchified rows.

Useful NaFlexClap flags:

```bash
--model naflexclap_little
--dataset-type webdataset-audio
--naflex-seq-lens 256 512
--naflex-pad-multiple 64
--length-bucketing
--bucket-pool 20000
--bucket-chunk 2000
--audio-ext flac
```

`--length-bucketing` for NaFlexClap uses audio token estimates, not constant caption length, so similar-duration clips batch together and padding shrinks.

## Hugging Face Audio Zero-Shot

Audio zero-shot uses Hugging Face audio classification datasets and the CLAP text classifier path.

Main training/eval CLI flags:

```bash
python -m open_clip_train.main \
  --model CLAP-HTSAT-tiny-Roberta-base-fused \
  --pretrained laion \
  --audio-zeroshot-dataset ashraq/esc50 \
  --audio-zeroshot-split train \
  --audio-zeroshot-audio-key audio \
  --audio-zeroshot-target-key target \
  --audio-zeroshot-class-key category \
  --audio-zeroshot-template 'This is a sound of {}.' \
  --batch-size 64 \
  --workers 4 \
  --audio-zeroshot-workers 0 \
  --device cuda \
  --zeroshot-frequency 1
```

`audio_zero_shot_eval()` validates that the model has `audio` and `encode_audio`. It builds class names from:

1. HF `ClassLabel.names` on the target feature, when available.
2. `--audio-zeroshot-class-key`, mapping each numeric target to a readable class name.
3. Numeric labels as strings, if no class names are available.

Templates must contain `{}`. Multiple `--audio-zeroshot-template` flags are allowed.

## Zero-Shot Data Shape Details

`HFAudioClassificationDataset` accepts several audio sample layouts:

- `sample[audio_key]` is `(waveform, sample_rate)`.
- `sample[audio_key]` is a dict with `array` and `sampling_rate`.
- `sample[audio_key]` is decoder-like and supports `audio["array"]` and `audio["sampling_rate"]`.
- If the audio value has no sampling rate, the wrapper falls back to `sample["sampling_rate"]`.

Fixed CLAP zero-shot uses `_collate_audio_zero_shot`, producing waveform/longer/maybe-fusion dicts. NaFlexClap zero-shot detects `model.audio.cfg.model_type == "naflexvit"`, builds `AudioNaFlexTransformFactory`, and uses `collate_naflex_dicts` with `image_key="audio"`.

## Safe Evaluation Planning

Use this sub-skill's `scripts/clap_zero_shot_args.py` first when you need a safe dry run of the intended model, dataset, key, template, and runtime arguments. It prints the installed-module evaluation plan and performs no checkpoint loading, dataset downloading, model building, or GPU work.

For hosted pretrained models, run real zero-shot through `python -m open_clip_train.main` with `--audio-zeroshot-*` flags. For custom checkpoints, load the checkpoint in your own trusted wrapper or training/evaluation harness, then reuse `open_clip_train.audio_zero_shot.build_hf_audio_zero_shot_dataset()` and `audio_zero_shot_eval()`.
