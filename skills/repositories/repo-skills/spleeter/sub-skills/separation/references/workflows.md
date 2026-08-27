# Spleeter separation workflows

This reference contains concrete operating recipes for pretrained Spleeter source separation. It assumes Spleeter 2.4.2 is installed, `ffmpeg` and `ffprobe` are on `PATH`, and the input files are local audio files readable by ffmpeg. For package installation and environment checks, use the [root installation reference](../../../references/installation-and-runtime.md). For model cache and custom JSON descriptor details, use the [root models/configuration reference](../../../references/models-and-configuration.md).

## Choose the descriptor

| Descriptor | Common task | Expected stems |
| --- | --- | --- |
| `spleeter:2stems` | Vocal/accompaniment split | `vocals`, `accompaniment` |
| `spleeter:4stems` | Music demixing without piano stem | `vocals`, `drums`, `bass`, `other` |
| `spleeter:5stems` | Music demixing with piano stem | `vocals`, `drums`, `bass`, `piano`, `other` |
| `spleeter:2stems-16kHz`, `spleeter:4stems-16kHz`, `spleeter:5stems-16kHz` | Lower-bandwidth pretrained variants when the workflow intentionally uses those descriptors | Same stem names as the matching base descriptor |

Use the base descriptors for normal pretrained separation unless the user specifically asks for a 16 kHz variant or a supplied config requires it. The first use of a descriptor may download and checksum model artifacts before separation starts.

## CLI recipes

Prefer `python -m spleeter` in reusable instructions because it also works around known console-script issues on Windows. If the `spleeter` console command works in the user's shell, it is equivalent for these examples.

### Basic 2-stem split

```bash
python -m spleeter separate \
  --params_filename spleeter:2stems \
  --output_path separated \
  song.wav
```

Expected output with the default filename format:

```text
separated/
  song/
    vocals.wav
    accompaniment.wav
```

### 4-stem or 5-stem split

```bash
python -m spleeter separate -p spleeter:4stems -o separated song.wav
python -m spleeter separate -p spleeter:5stems -o separated song.wav
```

Expected 4-stem files are `vocals.wav`, `drums.wav`, `bass.wav`, and `other.wav`. Expected 5-stem files add `piano.wav`.

### Multiple input files

```bash
python -m spleeter separate \
  -p spleeter:2stems \
  -o separated \
  song_a.wav song_b.mp3 song_c.flac
```

With the default filename format, each input receives its own directory named after the input basename, for example `separated/song_a/vocals.wav` and `separated/song_b/accompaniment.wav`.

### Process only a time range

```bash
python -m spleeter separate \
  -p spleeter:2stems \
  -o separated \
  --offset 30 \
  --duration 90 \
  song.wav
```

`--offset/-s` is the start time in seconds. `--duration/-d` is the maximum number of seconds processed after the offset. Use a short duration for smoke tests before running long files or large batches.

### Output codec and bitrate

```bash
python -m spleeter separate \
  -p spleeter:2stems \
  -o separated_mp3 \
  --codec mp3 \
  --bitrate 192k \
  song.wav
```

Supported `Codec` values are `wav`, `mp3`, `ogg`, `m4a`, `wma`, and `flac`. WAV is the safest validation codec because it avoids encoder availability and bitrate surprises.

### Filename templates

Default template:

```text
{filename}/{instrument}.{codec}
```

Available variables are:

- `{filename}`: input basename without extension.
- `{foldername}`: basename of the input file's parent directory.
- `{instrument}`: stem name, such as `vocals` or `drums`.
- `{codec}`: selected output codec string.

Flat but collision-safe template for one output directory:

```bash
python -m spleeter separate \
  -p spleeter:2stems \
  -o separated_flat \
  --filename_format '{filename}_{instrument}.{codec}' \
  song_a.wav song_b.wav
```

Avoid templates that omit `{instrument}` because multiple stems from the same input map to the same path and Spleeter raises a source path conflict. For multi-file jobs, also include `{filename}` or `{foldername}` unless the output directory is unique per input.

### MWF decision

Add `--mwf` to enable multichannel Wiener filtering:

```bash
python -m spleeter separate -p spleeter:4stems --mwf -o separated song.wav
```

Use MWF for final-quality runs when the extra compute and memory are acceptable. Leave it off for quick smoke tests, troubleshooting, or large CPU-only batches unless quality is more important than runtime.

### Custom audio adapter

```bash
python -m spleeter separate \
  --adapter your_package.your_module.YourAudioAdapter \
  -p spleeter:2stems \
  -o separated \
  song.wav
```

The adapter descriptor must be importable in the active Python environment and resolve to a subclass of `spleeter.audio.adapter.AudioAdapter`. If the user only needs ordinary local files, use the default ffmpeg adapter.

### Deprecated input option warning

Do not use the old `-i` or `--inputs` style. In Spleeter 2.4.2 the command intentionally logs a deprecation error and exits with code 20. Replace this:

```bash
python -m spleeter separate -i song.wav -o separated
```

with this:

```bash
python -m spleeter separate -o separated song.wav
```

## Safe dry-run helper

Use the bundled helper to validate input paths and inspect the exact Spleeter command before running it:

```bash
python sub-skills/separation/scripts/separate_file.py \
  --params spleeter:2stems \
  --output-dir separated \
  --filename-format '{filename}_{instrument}.{codec}' \
  --dry-run \
  song.wav
```

Remove `--dry-run` to execute. The helper builds `python -m spleeter separate ...`, does not use deprecated `-i`, and warns about filename templates that are likely to collide.

## Python recipes

### File-to-file separation

```python
from spleeter.audio import Codec
from spleeter.audio.adapter import AudioAdapter
from spleeter.separator import Separator

adapter = AudioAdapter.default()
separator = Separator("spleeter:2stems", MWF=False, multiprocess=True)
separator.separate_to_file(
    "song.wav",
    "separated",
    audio_adapter=adapter,
    offset=0,
    duration=600.0,
    codec=Codec.WAV,
    bitrate="128k",
    filename_format="{filename}/{instrument}.{codec}",
    synchronous=True,
)
```

`synchronous=True` waits for pending asynchronous save tasks before returning when multiprocessing is enabled. If you call `separate_to_file(..., synchronous=False)` or `save_to_file(..., synchronous=False)`, call `separator.join()` before reading outputs.

### Separate an in-memory waveform

```python
from spleeter.audio.adapter import AudioAdapter
from spleeter.separator import Separator

adapter = AudioAdapter.default()
waveform, sample_rate = adapter.load("song.wav", offset=0, duration=30, sample_rate=44100)
separator = Separator("spleeter:2stems", multiprocess=False)
sources = separator.separate(waveform, audio_descriptor="song.wav")

# sources is a dict such as {"vocals": ndarray, "accompaniment": ndarray}
separator.save_to_file(sources, "song.wav", "separated", synchronous=True)
```

Spleeter converts mono or multi-channel waveforms to stereo for separation. The returned arrays follow the input time dimension and use the configured model sample rate.

## Validation steps after separation

1. Check the expected output paths from the descriptor and filename template exist.
2. Confirm each file is non-empty and decodable, for example with `ffprobe` or a trusted audio library.
3. For smoke tests, use `--duration` to keep runtime bounded, then rerun without truncation only after the short run succeeds.
4. If using a non-WAV codec, confirm the system ffmpeg build includes the needed encoder.
5. For batch jobs, verify a sample from every input family before launching the full batch.
6. If the first run fails before output files appear, check model download/cache troubleshooting before assuming the audio file is invalid.
