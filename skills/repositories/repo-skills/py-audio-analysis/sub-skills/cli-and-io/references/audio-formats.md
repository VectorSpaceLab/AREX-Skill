# Audio Formats and Conversion Behavior

pyAudioAnalysis 0.3.14 centralizes most file reading and batch conversion behavior in `audioBasicIO`. The package is CPU-only for these paths, but compressed-media support depends on Python media packages plus external decoder/encoder executables.

## Installed dependency surface

Package requirements include `numpy`, `scipy`, `matplotlib`, `simplejson`, `hmmlearn`, `eyeD3`, `pydub`, `scikit_learn`, `tqdm`, `plotly`, `pandas`, and `imblearn`. For CLI and I/O work, the critical import names are:

- `numpy` and `scipy.io.wavfile` for WAV arrays.
- Python `aifc` for AIFF support; pyAudioAnalysis imports it at module import time, so runtimes without `aifc` can fail before even reading WAV.
- `pydub` for generic compressed/container audio reads through `AudioSegment.from_file`.
- `eyed3` for MP3 tag inspection during directory MP3-to-WAV conversion.
- External `ffmpeg` for `dirMp3toWav`, `convertToWav.py`, and pydub decoding in many environments.
- External `avconv` for `dirWavResample`; this command is not automatically substituted with `ffmpeg` by pyAudioAnalysis.

Use [`../scripts/audio_io_smoke.py`](../scripts/audio_io_smoke.py) to synthesize/read a WAV and report the optional media tools visible to the current Python process.

## `audioBasicIO.read_audio_file(input_file)` behavior

`read_audio_file` returns `(sampling_rate, signal)` and prints errors instead of consistently raising exceptions.

| Input extension | Backend | Return shape and notes | Failure mode |
|---|---|---|---|
| `.wav` | `scipy.io.wavfile.read` | Returns the sample rate and a NumPy array. Mono is usually 1-D; stereo/multichannel is 2-D. | Exceptions from scipy may propagate for malformed files. |
| `.aif`, `.aiff` | `aifc.open`, byte-swapped `np.short` | Reads AIFF frames into a NumPy array when `aifc` is available. | Prints `Error: read aif file. (DECODING FAILED)` and returns `(-1, empty array)` for decode failures; missing `aifc` can prevent importing `audioBasicIO`. |
| `.mp3`, `.au`, `.ogg` | `pydub.AudioSegment.from_file` | Converts raw pydub data into `int16` or `int32`, preserving channel columns as a 2-D array when multichannel. | Prints `Error: file not found or other I/O error. (DECODING FAILED)` and returns `(-1, empty array)`. Often caused by missing `ffmpeg`/decoder support. |
| Other string extension | none | No decoded audio. | Prints a literal unknown-type error and returns `(0, empty array)`. |
| Non-string file-like input | `pydub.AudioSegment.from_file` | Treated as generic audio. | Same generic decoding failure behavior. |

After reading, if the signal has shape `(n, 1)`, pyAudioAnalysis flattens it to 1-D. It does not automatically downmix stereo with two channels; use `audioBasicIO.stereo_to_mono` or an API wrapper that calls it.

Always check both values before downstream analysis:

```python
from pyAudioAnalysis import audioBasicIO
fs, signal = audioBasicIO.read_audio_file(audio_path)
if fs <= 0 or getattr(signal, "size", 0) == 0:
    raise ValueError("audio decode failed or produced no samples")
signal = audioBasicIO.stereo_to_mono(signal)
```

## `stereo_to_mono(signal)` behavior

- If the signal is 1-D, it is returned unchanged.
- If shape is `(n, 1)`, it is flattened.
- If shape is `(n, 2)`, output is `(right / 2) + (left / 2)`.
- More-than-two-channel arrays are returned unchanged, so normalize those before calling pyAudioAnalysis feature or segmentation routines.

## Conversion helpers and side effects

### `convert_dir_mp3_to_wav(audio_folder, sampling_rate, num_channels, use_tags=False)`

Used by the `audioAnalysis.py dirMp3toWav` subcommand with `use_tags=True`.

- Scans only `*.mp3` files directly under the folder.
- Uses `eyed3.load` to inspect tags when tag-based output names are enabled.
- Builds and executes `ffmpeg -i "input.mp3" -ar RATE -ac CHANNELS "output.wav"` through `os.system`.
- Writes WAV outputs into the same folder as the MP3 files.
- If tags contain artist and title, output can be `Artist --- Title.wav`; commas are replaced by spaces.
- Existing output-name collisions are not guarded by pyAudioAnalysis.

### `convert_dir_fs_wav_to_wav(audio_folder, sampling_rate, num_channels)`

Used by `audioAnalysis.py dirWavResample`.

- Scans only `*.wav` files directly under the folder.
- Creates an output folder named `Fs<RATE>_NC<CHANNELS>` under the input folder.
- If that output folder already exists and is not `.`, pyAudioAnalysis removes it with `shutil.rmtree` before conversion.
- Uses `avconv -i "input.wav" -ar RATE -ac CHANNELS "output_folder/file.wav"` through `os.system`.
- Missing `avconv` results in failed conversions even if `ffmpeg` is installed.

### `convertToWav.py`

The standalone helper scans a folder for `.webm`, `.avi`, `.mkv`, `.mp4`, `.mp3`, `.flac`, and `.ogg`, then calls `ffmpeg` to create same-basename `.wav` files in place:

```text
ffmpeg -i "input.ext" -ar <samplingRate> -ac <channels> "input.wav"
```

Use a scratch directory or preflight for output collisions. The helper does not ask before overwriting and does not provide structured error handling.

## Format-specific operating advice

- Prefer WAV for deterministic feature, training, classification, and segmentation tasks. It avoids pydub/decoder variability and is the format used by the lightweight native pytest data.
- Treat AIFF and compressed formats as import/dependency-sensitive. Probe `aifc`, `pydub`, and `ffmpeg` before assuming AIFF/MP3/AU/OGG decode will work.
- For MP3-to-WAV conversion, validate output filenames if tag-derived names are enabled; artist/title tags can produce unexpected spaces and repeated names.
- For paths with spaces, use subprocess argument lists from Python or quote every shell variable.
- For audio folders passed to `classifyFolder`, ensure the path pattern matches how the legacy script concatenates the folder/prefix and glob suffixes.
- Keep conversion and segmentation writes out of original or valuable data folders. Use copies when the exact pyAudioAnalysis side effects are uncertain.
