# FunClip troubleshooting

This page groups the common failure modes for the clip workflow and the most likely fixes.

## 1) Gradio launch or import fails

### Symptom

- The Gradio index page returns HTTP 500 on a fresh install.
- The service crashes during launch with a Starlette/Jinja2 template error.
- `funasr` cannot be imported, or recognition complains about missing compatibility behavior.

### Likely cause

- The environment has Gradio 4 with an incompatible `starlette>=1` install.
- `funasr` is older than the compatibility floor used by the FunClip release.

### Fix

- Reinstall the declared requirements.
- Ensure `starlette<1.0` remains installed.
- Upgrade `funasr` to `>=1.3.29` before starting the service.

## 2) `--listen` and `--share` behave differently than expected

### Symptom

- A remote host still appears to bind only to localhost.
- A user expects a public Gradio URL after passing `--listen`.

### Likely cause

- `--listen` only changes the bind address and disables the local browser/frontend probe.
- It does not create a share tunnel.

### Fix

- Use `--listen` for container or remote binding.
- Add `--share` only when you explicitly want a public Gradio link.

## 3) Text clipping says no match was found

### Symptom

- The message says `No period found in the speech` or `No period found in the video`.
- The clip output is the original audio or no video file.

### Likely cause

- The target text does not match the normalized transcript.
- The transcript was copied with different spacing or punctuation.
- The phrase is repeated and the offsets were applied to all matches.
- ASCII case differs, but the text is still expected to match after lowercasing.

### Fix

- Copy the exact transcript text from the recognition result first.
- Use `#` to separate multiple target phrases.
- Use bracket offsets like `text[0, 100]` only when needed.
- For explicit boundaries, skip text matching and pass `timestamp_list` from AI output.
- If the text is Chinese, normalize the prompt text the same way FunClip does before matching.

## 4) Speaker clipping does nothing

### Symptom

- `--dest_spk` or the speaker field in the UI returns no result.

### Likely cause

- Speaker diarization was not enabled during recognition.
- The saved state does not contain `sd_sentences`.
- The requested segment is too short to survive the speaker filter.

### Fix

- Re-run recognition with speaker diarization enabled.
- Use speaker ids such as `spk0` or `spk0#spk3`.
- Keep in mind that very short speaker segments are ignored.

## 5) Subtitles do not render or overlay fails

### Symptom

- `Clip+Subtitles` fails.
- MoviePy raises a font, ImageMagick, or ffmpeg-related error.
- The video clip succeeds but the subtitle overlay does not.

### Likely cause

- ffmpeg, ImageMagick, or the bundled font is missing.
- The environment blocks ImageMagick text rendering.

### Fix

- Install ffmpeg and ImageMagick.
- Make sure the bundled font path exists.
- Keep `add_sub=False` if you only need the clip output and not the overlay.

## 6) Stage 1 or stage 2 file handling fails

### Symptom

- The runner says the file format is unsupported.
- The output directory cannot be created.
- Stage 2 cannot find the state files written during stage 1.

### Likely cause

- The input suffix is not one of the supported audio/video suffixes.
- The CLI runner uses a simple directory creation path and does not create missing parent directories for nested paths.
- Stage 2 points at a different `output_dir` from stage 1.

### Fix

- Convert the media to a supported suffix.
- Create the output directory first, especially for nested paths.
- Reuse the same `output_dir` for both stage 1 and stage 2.

## 7) The video has no audio track

### Symptom

- Recognition exits with a no-audio error.

### Likely cause

- The video file does not contain an audio stream.

### Fix

- Use a file with audio, or mux audio into the video first.
- For audio-only work, use a supported audio file instead of a silent video.

## 8) SenseVoice or Fun-ASR-Nano returns empty subtitle boundaries

### Symptom

- Recognition text appears, but subtitles or clipping boundaries look empty or incomplete.

### Likely cause

- The installed FunASR version is too old to return the compatible `sentence_info` fallback.

### Fix

- Upgrade to `funasr>=1.3.29`.
- Re-run recognition so FunClip can synthesize sentence boundaries from top-level timestamps when needed.

## 9) Model downloads or caches fail

### Symptom

- The first run pauses on model acquisition or cache lookup.
- Recognition cannot start because the model weights are unavailable.

### Likely cause

- The model weights are not bundled with FunClip.
- The environment has no network access or an empty cache.

### Fix

- Pre-populate the required model cache in the target environment.
- Do not assume the smoke script proves live model downloads; it only checks the no-network text-matching path.

## 10) Offset handling looks wrong

### Symptom

- A clip starts too early or too late.
- Multiple matches all receive the same offset.

### Likely cause

- `start_ost` and `end_ost` are applied after the transcript match.
- A bracketed offset applies to every match of that text fragment.

### Fix

- Use small positive or negative millisecond offsets to pad the clip.
- Split repeated phrases into separate targets when you need different offsets for each one.
