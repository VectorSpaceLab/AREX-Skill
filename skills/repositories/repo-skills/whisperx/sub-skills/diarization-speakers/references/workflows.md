# Diarization workflows

Use these workflows to set up speaker diarization safely, or to assign speaker labels when diarization intervals are already available.

## Choose the right workflow

| Situation | Use |
| --- | --- |
| User has audio and wants WhisperX to detect speakers | Model-backed CLI or Python diarization with `DiarizationPipeline`; requires model access and may download/load pyannote weights. |
| User already has transcript JSON and diarization intervals | Offline assignment with `assign_word_speakers` or the bundled CSV helper; no Hugging Face token and no model run. |
| User asks why labels are missing | Inspect transcript and diarization time ranges, then decide whether `fill_nearest` is appropriate. |
| User asks for SRT/VTT/JSON rendering | Assign speakers here first, then route output rendering to `outputs-subtitles`. |

## Model-backed CLI diarization

Minimum CLI shape:

```bash
whisperx AUDIO.wav --model large-v2 --diarize --hf_token "$HUGGINGFACE_TOKEN"
```

Known speaker count from the CLI:

```bash
whisperx AUDIO.wav --model large-v2 --diarize --hf_token "$HUGGINGFACE_TOKEN" --min_speakers 2 --max_speakers 2
```

CPU-oriented command shape:

```bash
whisperx AUDIO.wav --model small --diarize --hf_token "$HUGGINGFACE_TOKEN" --device cpu --compute_type int8
```

Before suggesting or running a real diarization command, confirm:

1. The user has accepted the selected pyannote model terms.
2. The token has read access to that model.
3. The token will not be copied into logs, committed files, or shared transcripts.
4. The selected device is intentional. CPU is safer and more portable but slower; CUDA is faster when a compatible PyTorch/CUDA stack is already working.
5. ASR/alignment and output-format needs are handled by their own sub-skills.

Avoid using command-line token examples in permanent scripts or reports. Shell history and process listings can expose command-line arguments on some systems.

## Model-backed Python diarization

The Python API exposes exact `num_speakers` in addition to min/max bounds.

```python
import os
import whisperx
from whisperx.diarize import DiarizationPipeline

# result should already be a WhisperX transcription/alignment result.
# audio can be a path or a waveform array accepted by DiarizationPipeline.
device = "cuda"  # or "cpu"
token = os.environ["HUGGINGFACE_TOKEN"]

diarize_model = DiarizationPipeline(token=token, device=device)
diarize_segments = diarize_model(audio, min_speakers=2, max_speakers=4)
result = whisperx.assign_word_speakers(diarize_segments, result)
```

If the exact count is known in Python:

```python
diarize_segments = diarize_model(audio, num_speakers=2)
```

If memory is tight, release ASR/alignment models before initializing the diarization model. Keep generic GPU/CUDA repair steps in the root troubleshooting reference; this sub-skill only chooses diarization API/device options.

## Offline assignment from transcript JSON plus diarization CSV

Use the bundled helper when the user already has speaker intervals from another diarization source or a previous WhisperX run:

```bash
python scripts/assign_speakers_from_csv.py \
  --transcript-json transcript.json \
  --diarization-csv diarization.csv \
  --output-json transcript.with-speakers.json
```

Add `--fill-nearest` only when the intervals and transcript times are known to be in the same timebase and small gaps/timestamp drift should be filled:

```bash
python scripts/assign_speakers_from_csv.py \
  --transcript-json transcript.json \
  --diarization-csv diarization.csv \
  --output-json transcript.with-speakers.json \
  --fill-nearest
```

The helper validates CSV `start,end,speaker` columns, numeric finite times, non-empty speakers, and transcript JSON shape. It refuses to overwrite an existing output file by default.

## Speaker embeddings

CLI:

```bash
whisperx AUDIO.wav --diarize --speaker_embeddings --hf_token "$HUGGINGFACE_TOKEN" --output_format json
```

Python:

```python
diarize_segments, embeddings = diarize_model(audio, return_embeddings=True)
result = whisperx.assign_word_speakers(diarize_segments, result, speaker_embeddings=embeddings)
```

Rules:

- `--speaker_embeddings` has no useful effect without `--diarize`.
- Embeddings are attached as top-level `speaker_embeddings` only when provided to `assign_word_speakers`.
- Embeddings are most useful with JSON output; subtitle/text formats focus on segment/word speaker labels.
- The CSV helper does not create embeddings; it preserves any unrelated top-level fields already present in the transcript JSON.

## Choosing speaker-count constraints

| Knowledge about the recording | Recommended setting |
| --- | --- |
| Exact number known in Python | `num_speakers=N` |
| Exact number known in CLI | `--min_speakers N --max_speakers N` |
| Small acceptable range | `min_speakers=M, max_speakers=N` or CLI equivalents |
| Unknown | Leave constraints unset and inspect results before constraining a rerun |

Do not set contradictory bounds. If speakers are merged or split unexpectedly, retry with a better range rather than post-editing labels blindly.

## Validate assignment results

After assignment, inspect a few segment and word records:

```python
for segment in result.get("segments", [])[:3]:
    print(segment.get("start"), segment.get("end"), segment.get("speaker"), segment.get("text"))
    for word in segment.get("words", [])[:3]:
        print("  ", word.get("word"), word.get("speaker"))
```

Expected signs of success:

- Segments with overlapping diarization intervals have `speaker` labels.
- Words with `start` timestamps and overlaps have `speaker` labels.
- Top-level `speaker_embeddings` appears only when embeddings were requested and provided.

If labels are absent, use [data formats](data-formats.md) to check time ranges and [troubleshooting](troubleshooting.md) for missing-token/model or overlap issues.
