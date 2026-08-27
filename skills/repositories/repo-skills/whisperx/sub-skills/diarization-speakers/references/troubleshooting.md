# Diarization troubleshooting

Use this reference for speaker-diarization-specific failures. Keep generic package install, CUDA/cuDNN dynamic-linker, and PyTorch backend repair in the root WhisperX troubleshooting reference.

## Quick diagnosis table

| Symptom | Likely cause | Safe diagnosis | Fix |
| --- | --- | --- | --- |
| Model loading fails with authentication, 401/403, gated-model, or repository access errors | Missing HF token / Hugging Face token, token lacks read access, or pyannote terms were not accepted | Do not ask for the token value. Ask whether the user has a read token and accepted the selected model terms in the same account. Confirm the model id. | Accept the pyannote model terms, create/rotate a read token, and pass it securely to `--hf_token` or `DiarizationPipeline(token=...)`. |
| CLI warns that no `--hf_token` was provided | `--diarize` was set but no token argument was supplied | Treat this as the missing HF token case unless the user intentionally relies on an already-authenticated local cache. If not, expect model loading to fail. | Provide a secret token securely or switch to offline assignment if diarization intervals already exist. |
| `pyannote/speaker-diarization-community-1` is unavailable | Gated access not granted, model id changed/typed wrong, network unavailable, or cache missing | Check model id and access status without printing secrets. If offline, check that the intended model is already cached. | Use a valid accessible model id, accept terms, restore network/cache access, or pass a supported local/cache model reference. |
| Too many/few speakers | Speaker-count constraints are absent, too loose, too tight, or contradictory | Ask what speaker count is known. Compare `min_speakers`, `max_speakers`, and Python-only `num_speakers`. | Use `num_speakers=N` in Python, or `--min_speakers N --max_speakers N` in CLI for exact counts; otherwise use a realistic range. |
| `--speaker_embeddings` seems ignored | It was used without `--diarize`, or output format does not expose embeddings clearly | The CLI warns that embeddings have no effect without diarization. Inspect JSON output/result dictionary. | Add `--diarize` and request JSON output, or in Python call diarization with `return_embeddings=True` and pass embeddings to `assign_word_speakers`. |
| Assignment produces no speaker labels | Diarization intervals do not overlap transcript times, diarization data is empty, or words lack usable timestamps | Compare min/max transcript times and CSV/DataFrame times; confirm both are seconds; inspect a few rows. | Fix the timebase, rerun diarization, repair alignment, or use `fill_nearest=True` only for acceptable small gaps. |
| Empty diarization DataFrame | No detected speech, wrong audio, model failed, token/model access issue, or an empty CSV was supplied | Check whether the model actually ran and whether CSV has data rows. Do not assume assignment failed. | Resolve model/audio/access issue. The CSV helper rejects empty data so the user sees the problem early. |
| CPU diarization is very slow | Pyannote diarization is running on CPU | Check the selected `--device` or Python `device` value and available hardware. | Use CUDA only when the user's PyTorch/CUDA stack is already working; otherwise keep CPU and set expectations. |
| CUDA selected but diarization fails before assignment | Device/backend mismatch or broader CUDA/PyTorch issue | Confirm `torch.cuda.is_available()` in the user's runtime if they can run it. Do not debug dynamic linker details here. | Route generic CUDA/cuDNN/PyTorch repairs to the root troubleshooting reference, then rerun diarization. |

## Token and gated-model access

WhisperX diarization uses pyannote models. The default model is gated and requires both:

1. A Hugging Face account that has accepted the model terms.
2. A read token from that account.

Safe handling rules:

- Do not request the literal token in chat.
- Do not save tokens in transcript JSON, diarization CSV, notebooks, shell scripts, or reports.
- Prefer secret stores or environment variables in local execution contexts.
- If a command must include `--hf_token`, warn that shell history and process listings may expose command-line arguments on some systems.
- Redact tokens from copied errors before sharing logs.

## Speaker-count constraints

The Python API supports exact `num_speakers`; the CLI exposes `--min_speakers` and `--max_speakers`.

- Exact known count in Python: `diarize_model(audio, num_speakers=2)`.
- Exact known count in CLI: `--min_speakers 2 --max_speakers 2`.
- Unknown count: leave constraints unset for a first pass.
- Known range: set a realistic min/max, for example 2 to 4.

If labels are fragmented, try a tighter count or range. If distinct people are merged, try a wider range or an exact known count. Do not set `min_speakers` greater than `max_speakers`.

## Empty diarization data

`assign_word_speakers` returns the transcript unchanged when diarization data is empty. That is expected behavior, not proof that transcript assignment is broken.

Diagnose in this order:

1. Did `DiarizationPipeline` instantiate successfully?
2. Did the selected model run on the intended audio?
3. Was the Hugging Face token/model access accepted?
4. Are the diarization rows in seconds with `end > start`?
5. If using CSV, does it contain data rows under `start,end,speaker`?

## Missing overlaps and `fill_nearest`

No-overlap causes:

- Transcript times and diarization times use different units.
- Transcript was trimmed or offset relative to the diarized audio.
- Word records have missing or zero-duration timestamps.
- Diarization intervals are sparse or model output is poor.

Use `fill_nearest=True` when nearby assignment is acceptable for small timing drift. Do not use it when diarization output is empty, badly offset, or from a different audio file.

Safe check with the bundled helper:

```bash
python scripts/assign_speakers_from_csv.py --help
```

Then run once without `--fill-nearest`; compare assigned counts. If only small gaps remain, rerun with `--fill-nearest` and inspect boundary cases manually.

## CPU/GPU device choices

- `device="cpu"` or `--device cpu`: portable and safe for setup checks, but slow for real model diarization.
- `device="cuda"` or `--device cuda`: faster when the user's GPU runtime is already healthy.
- `--compute_type int8` helps ASR CPU use, but it is not a pyannote diarization accuracy setting.
- If CUDA/PyTorch installation fails, route to root troubleshooting instead of changing diarization semantics.

## Boundaries with other sub-skills

- No transcript or missing transcript segments: route to `asr-python-api`.
- Missing word timestamps or words skipped during speaker assignment: route to `alignment-timestamps`.
- Speaker labels exist but do not appear in SRT/VTT/TXT/JSON as expected: route to `outputs-subtitles`.
