# Troubleshooting

## ClearVoice import fails
- Symptom: `ImportError` when the helper tries to import `clearvoice`.
- Fix: install the package with `pip install clearvoice` before rerunning the recipe.
- If you are working from a local checkout, install that checkout instead of trying to run the recipe in a bare environment.

## Unsupported task/model pair
- Symptom: the helper rejects the model or ClearVoice prints that the network is not supported.
- Fix: match the task to the catalog in `references/model-catalog.md`.
- Do not mix an audio model with the AV TSE task or vice versa.

## `model_names` passed as a string
- Symptom: unsupported model names that look like single characters.
- Cause: the constructor iterates `model_names`, so a bare string is treated like a sequence of characters.
- Fix: pass a list, even for one model, for example `['FRCRN_SE_16K']`.

## Tensor-to-tensor single-model limit
- Symptom: tensor-mode inference prints that only one model is supported.
- Fix: keep tensor input to one model only.
- If you need several models, use file-mode inference instead.

## Missing FFmpeg
- Symptom: non-WAV audio or video inputs fail to open or decode.
- Fix: install FFmpeg and verify it with `ffmpeg -version`.
- This matters for mp3, aac, ogg, webm, and AV TSE video inputs.

## Checkpoint download failure
- Symptom: the first inference cannot fetch a model checkpoint.
- Fix: verify network access, then rerun the job or pre-stage the checkpoint tree before running offline.
- If the runtime already printed a download warning, the model family was recognized but the fetch did not complete.

## Output path conflict
- Symptom: `write()` refuses to create or overwrite the target.
- Fix: delete the existing file or directory, or choose a fresh output path.
- For batch runs, prefer a directory that does not already exist.

## Sampling-rate mismatch
- Symptom: output sounds wrong, segmentation behaves oddly, or the model family seems mismatched to the source audio.
- Fix: use the correct model for 16 kHz or 48 kHz input, then resample before tensor-mode inference if your arrays are not already at the expected rate.
- For audio-only tensor mode, keep arrays shaped as `[batch, length]` after any resampling step.

## GPU unavailable or CPU is slow
- Symptom: the run falls back to CPU and feels too slow.
- Fix: use a GPU when you can, or reduce the input length and rely on the model's segmenting behavior.
- Long videos and 48 kHz models are the most likely to benefit from a GPU.

## AV TSE requirements
- Symptom: the AV model refuses to run or asserts on write mode.
- Fix: use video input, keep `online_write=True`, and ensure FFmpeg is available.
- If you only have audio, switch to a different ClearVoice task.
