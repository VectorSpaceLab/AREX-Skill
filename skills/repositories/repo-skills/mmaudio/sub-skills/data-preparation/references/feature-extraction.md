# Feature extraction

This reference describes the data-preparation flow for MMAudio audio-text and audio-video-text features.

## End-to-end flow

1. Collect raw media and the matching caption or label TSV.
2. Partition long audio into clip windows when you need audio-text training data.
3. Validate the manifest, source files, and expected output layout.
4. Launch the extractor with `torchrun` so distributed CUDA setup is initialized correctly.
5. Let rank 0 combine the per-worker latents into a TensorDict memmap and companion TSV.

## Audio-text feature preparation

### 1) Partition clips

Use the skill-owned CPU utility when you need to build a clip manifest from raw audio:

```bash
python skills/disco/mmaudio/sub-skills/data-preparation/scripts/partition_audio_clips.py \
  --data_dir <audio_root> \
  --output_tsv <clips_tsv>
```

The partitioner:

- scans `.flac` and `.wav` files in sorted order,
- keeps only files long enough for the nominal clip window,
- emits up to 5 segments per source file,
- stores sample offsets in the original file's sample rate,
- writes only metadata, never trimmed audio files.

Default window facts:

- `min_length_sec = 8.1`
- `max_segments_per_clip = 5`

### 2) Validate the plan

Use the plan inspector before launching extraction:

```bash
python skills/disco/mmaudio/sub-skills/data-preparation/scripts/inspect_feature_plan.py audio \
  --data_dir <audio_root> \
  --captions_tsv <captions_tsv> \
  --clips_tsv <clips_tsv> \
  --latent_dir <latent_dir> \
  --output_dir <output_dir> \
  --mode 16k
```

What it checks:

- caption TSV columns (`id`, `caption`),
- clip TSV columns (`id`, `name`, `start_sample`, `end_sample`),
- duplicate caption ids,
- missing source audio files,
- expected output file names and tensor shapes,
- the copy-paste `torchrun` command to launch the extractor.

### 3) Launch the extractor

The upstream audio extractor runs under `torchrun` and expects distributed setup to be available:

```bash
torchrun --standalone --nproc_per_node=<N> <audio-extractor> \
  --data_dir <audio_root> \
  --captions_tsv <captions_tsv> \
  --clips_tsv <clips_tsv> \
  --latent_dir <latent_dir> \
  --output_dir <output_dir> \
  --batch_size <per_gpu_batch> \
  --num_workers <per_gpu_workers>
```

Mode switch facts:

| mode | sample rate | audio samples | VAE checkpoint family | vocoder |
| --- | --- | --- | --- | --- |
| `16k` | 16000 | 128000 | 16 kHz VAE | local BigVGAN checkpoint |
| `44k` | 44100 | 353280 | 44 kHz VAE | built-in 44 kHz vocoder path |

Important details:

- `16k` uses 128000 audio samples for an 8-second clip.
- `44k` uses 353280 samples, not 352800, so the audio length aligns with the VAE/STFT grid.
- The extractor uses CUDA, NCCL, and `torch.distributed.init_process_group`.
- Rank 0 merges `mean`, `std`, and `text_features` into the final memmap.

### Expected outputs

For `output_dir = /path/to/audio-example`, the extractor creates:

- `/path/to/audio-example/` for the TensorDict memmap,
- `/path/to/audio-example.tsv` for the metadata TSV.

The TSV rows contain `id` and `caption`.

The memmap stores:

- `mean`
- `std`
- `text_features`

Expected shapes are listed in `references/data-formats.md`.

## Video feature preparation

### 1) Validate the plan

```bash
python skills/disco/mmaudio/sub-skills/data-preparation/scripts/inspect_feature_plan.py video \
  --data_dir <video_root> \
  --subset_tsv <subset_tsv> \
  --latent_dir <latent_dir> \
  --output_dir <output_dir> \
  --split <split_name> \
  --mode 16k
```

What it checks:

- video subset TSV columns (`id`, `label`),
- missing `.mp4` files,
- duplicate ids in the subset manifest,
- expected `vgg-{split}` output names,
- expected CLIP and synchronization tensor shapes,
- the copy-paste `torchrun` command to launch the extractor.

### 2) Launch the extractor

```bash
torchrun --standalone --nproc_per_node=<N> <video-extractor> \
  --latent_dir <latent_dir> \
  --output_dir <output_dir>
```

The upstream video extractor uses an in-script split dictionary with the keys `example`, `train`, `test`, and `val`.

Mode switch facts:

| mode | sample rate | audio samples | VAE checkpoint family | vocoder |
| --- | --- | --- | --- | --- |
| `16k` | 16000 | 128000 | 16 kHz VAE | local BigVGAN checkpoint |
| `44k` | 44100 | 353280 | 44 kHz VAE | no local BigVGAN checkpoint |

### Expected outputs

For `split = train`, the extractor creates:

- `<output_dir>/vgg-train/` for the TensorDict memmap,
- `<output_dir>/vgg-train.tsv` for the metadata TSV.

The TSV rows contain `id` and `label`.

The memmap stores:

- `mean`
- `std`
- `clip_features`
- `sync_features`
- `text_features`

Expected shapes:

- `clip_features`: `[N, 64, 1024]`
- `sync_features`: `[N, 192, 768]`
- `text_features`: `[N, 77, 1024]`

`mean` and `std` follow the same 16k/44k shapes as the audio extractor.

## Validation checklist

Before you start a long extraction run, confirm all of the following:

- the source media directory only contains the expected extension(s),
- the manifest columns match the downstream extractor,
- the output directory is empty or intentionally reusable,
- the chosen mode matches the target checkpoint family,
- the worker count matches the available GPUs,
- the required weights exist in the local weights directory.

## Why the 44.1k path uses 353280 samples

The 44.1kHz path is aligned to the VAE/STFT grid rather than the raw 8-second arithmetic:

- raw 8 seconds at 44.1kHz is 352800 samples,
- that value does not divide cleanly into the latent grid used by the model,
- 353280 is the next valid length that satisfies the downstream sequence math.

Use 353280 whenever you prepare 44.1kHz training features.
