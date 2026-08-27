# Data formats

This reference captures the file layouts and tensor shapes that the data-preparation workflow consumes and produces.

## Raw audio preparation inputs

### Audio directory

- Directory contains `.flac` or `.wav` files.
- File stem becomes the audio `name` used in the clip manifest.
- Files are processed in sorted filename order.

### Caption TSV

Required columns:

| column | meaning |
| --- | --- |
| `id` | Audio sample id or clip-group id used to look up the caption. |
| `caption` | Text caption for the audio source. |

Notes:

- Duplicate `id` values are tolerated by the upstream loader, but the last caption wins.
- If an `id` is missing from this table, matching clip rows are skipped.

### Clip TSV

Produced by the clip partitioner and consumed by audio feature extraction.

| column | meaning |
| --- | --- |
| `id` | Clip id, usually `<audio_stem>_<index>`. |
| `name` | Original audio stem without extension. |
| `start_sample` | Inclusive start offset at the source-file sample rate. |
| `end_sample` | Exclusive end offset at the source-file sample rate. |

Notes:

- Rows are deterministic and ordered by source file order, then segment index.
- The clip window is measured before resampling.
- The partitioner never writes trimmed audio files; it only writes metadata.

## Raw video preparation inputs

### Video directory

- Directory contains `.mp4` files.
- File stem must match the TSV `id`.
- The extractor reads each video once and builds two frame streams: CLIP and synchronization.

### Video subset TSV

| column | meaning |
| --- | --- |
| `id` | Video sample id, usually the filename stem. |
| `label` | Text label or caption for the video clip. |

Notes:

- Duplicate ids are skipped by the video combiner after the first occurrence.
- Missing videos are reported and skipped during dataset construction.

## Dataset classes and sample schemas

| class | input tables | sample payload | key shape facts |
| --- | --- | --- | --- |
| `WavTextClipsDataset` | audio directory, caption TSV, clip TSV | `waveform`, `id`, `caption`, `tokens` | Audio is normalized optionally, resampled to the target rate, truncated to `num_samples`, and tokenized to 77 text tokens. |
| `VGGSound` | video directory, subset TSV | `id`, `caption`, `audio`, `clip_video`, `sync_video` | Returns an 8-second audio chunk plus CLIP video at 8 FPS and sync video at 25 FPS. |
| `ExtractedAudio` | extracted audio TSV + memmap | `id`, `a_mean`, `a_std`, `clip_features`, `sync_features`, `text_features`, `caption`, `video_exist`, `text_exist` | Audio-only training rows use fake zero video features and `video_exist = False`. |
| `ExtractedVGG` | extracted VGG TSV + memmap | `id`, `a_mean`, `a_std`, `clip_features`, `sync_features`, `text_features`, `caption`, `video_exist`, `text_exist` | Video rows carry all three feature streams and `video_exist = True`. |
| `MultiModalDataset` | any video datasets + any audio datasets | concatenated dataset view | Training uses video datasets first, then audio datasets. |

## Feature tensor layouts

### Audio feature extraction output

Per sample:

| tensor | 16k mode | 44.1k mode |
| --- | --- | --- |
| `mean` | `[N, 250, 20]` | `[N, 345, 40]` |
| `std` | `[N, 250, 20]` | `[N, 345, 40]` |
| `text_features` | `[N, 77, 1024]` | `[N, 77, 1024]` |

Accompanying TSV:

- filename: `{basename(output_dir)}.tsv`
- columns: `id`, `caption`

Memmap directory:

- filename: `{basename(output_dir)}/`
- contents: `mean.memmap`, `std.memmap`, `text_features.memmap`, `meta.json`

### Video feature extraction output

Per sample:

| tensor | shape |
| --- | --- |
| `mean` | `[N, 250, 20]` for 16k, `[N, 345, 40]` for 44.1k |
| `std` | `[N, 250, 20]` for 16k, `[N, 345, 40]` for 44.1k |
| `clip_features` | `[N, 64, 1024]` |
| `sync_features` | `[N, 192, 768]` |
| `text_features` | `[N, 77, 1024]` |

Accompanying TSV:

- filename: `vgg-{split}.tsv`
- columns: `id`, `label`

Memmap directory:

- filename: `vgg-{split}/`
- contents: `mean.memmap`, `std.memmap`, `clip_features.memmap`, `sync_features.memmap`, `text_features.memmap`, `meta.json`

## Config entries and fixture names

### Data config inventory

| config entry | meaning |
| --- | --- |
| `VGGSound` | Raw video training split. |
| `VGGSound_test` | Raw video test split. |
| `VGGSound_val` | Raw video validation split. |
| `ExtractedVGG` | Pre-extracted video features for training. |
| `ExtractedVGG_test` | Pre-extracted video features for test. |
| `ExtractedVGG_val` | Pre-extracted video features for validation. |
| `AudioCaps` | Pre-extracted audio-text features for AudioCaps. |
| `AudioSetSL` | Pre-extracted audio-text features for AudioSet. |
| `BBCSound` | Pre-extracted audio-text features for BBCSound. |
| `FreeSound` | Pre-extracted audio-text features for FreeSound. |
| `Clotho` | Pre-extracted audio-text features for Clotho. |
| `Example_video` | Tiny local video smoke-test set. |
| `Example_audio` | Tiny local audio smoke-test set. |

### Fixture names

- Audio fixture manifest: `example_audio.tsv`
- Video fixture manifest: `example_video.tsv`
- Audio fixture files: `00008004.flac`, `00008009.flac`
- Video fixture files: `0B4dYTMsgHA_000130.mp4`, `F8Zt3mYlOqU_000094.mp4`

## Sequence-length and mode facts

The training code fills `latent_seq_len`, `clip_seq_len`, and `sync_seq_len` from the selected model family before constructing the datasets.

| mode | sample rate | audio samples | latent seq len | clip seq len | sync seq len | VAE embed dim |
| --- | --- | --- | --- | --- | --- | --- |
| `16k` | 16000 | 128000 | 250 | 64 | 192 | 20 |
| `44k` | 44100 | 353280 | 345 | 64 | 192 | 40 |

The `data_dim` config supplies the text and feature-channel dimensions, while the model family supplies the sequence lengths.
