# I2VGen-XL troubleshooting

## Missing or wrong checkpoint

**Symptom:** `FileNotFoundError`, strict state-dict mismatch, or a checkpoint loads but the sample quality is clearly wrong.

**Likely cause:** `test_model` points at the wrong family, the file is missing, or the checkpoint does not contain the expected `state_dict` and `step` keys.

**Fix:**

- Use `models/i2vgen_xl_00854500.pth` for the default config.
- Use `models/i2vgen_xl_person_00854500.pth` for the person variant.
- Verify the file exists before launch.
- If a different checkpoint family is required, make that a deliberate config change instead of a silent fallback.

## Malformed input list

**Symptom:** the loader crashes while parsing `test_list_path`.

**Likely cause:** the line is blank, uses the wrong delimiter count, or contains an empty image path or caption.

**Fix:**

- Use exactly one `|||` per active line.
- Keep comment lines commented with `#`.
- Do not leave blank lines in the list.
- Do not leave the caption empty if you expect the sample to generate.
- Run the bundled checker before inference.

## Image path problems

**Symptom:** `Image.open(...)` fails or the run skips a sample after parsing.

**Likely cause:** the image path does not exist relative to the working directory, points to a directory, or the file is unreadable.

**Fix:**

- Re-run the checker with `--check-exists`.
- Resolve paths from the current VGen checkout unless the user has deliberately chosen another root.
- Keep image files under a stable repo-visible directory.
- The loader converts non-RGB images to RGB automatically, so mode conversion is not a failure by itself.

## CUDA or distributed initialization failures

**Symptom:** `torch.cuda` reports no devices, NCCL initialization fails, or distributed startup hangs.

**Likely cause:** the runtime is CPU-only, stale distributed environment variables are set, or the machine has a CUDA mismatch.

**Fix:**

- Use a CUDA-capable environment; this workflow is not validated on CPU only.
- Clear stale `RANK`, `WORLD_SIZE`, `MASTER_ADDR`, and `MASTER_PORT` values before retrying.
- Run one GPU first when debugging.
- If `pynvml` cannot inspect GPU 0, check that the NVIDIA driver stack is visible.

## Memory pressure or slow decoding

**Symptom:** out-of-memory errors, very slow sampling, or decoder failures.

**Likely cause:** too many frames, too large a batch, or overly aggressive repetition.

**Fix:**

- Use `round: 1` for smoke tests.
- Keep one active line in the test list while debugging.
- Lower `max_frames`, `decoder_bs`, or `chunk_size` first.
- Preserve `use_fp16: True` for the supported CUDA path.

## Save/playback issues

**Symptom:** the run finishes but no playable video appears, or the generated file is hard to open.

**Likely cause:** video encoding dependencies are missing, the save helper raised an exception, or the browser/player is unhappy with the output.

**Fix:**

- Ensure the environment has the repo's video I/O stack plus `ffmpeg` support.
- Inspect the log file for `save_i2vgen_video_safe` warnings.
- Re-test with a different player or browser if the file exists but will not play.
- The Gradio demo notes that Chrome is a safe fallback for playback issues.

## Demo wrapper dependency failures

**Symptom:** `predict.py` or `gradio_app.py` fails before inference starts.

**Likely cause:** Cog, ModelScope, or Gradio dependencies are unavailable, or the runtime cannot reach the network-backed model/demo services.

**Fix:**

- Treat both files as reference-only unless the user explicitly wants those deployment surfaces.
- Do not make them part of the required offline inference path.
- Install the demo dependencies in an isolated environment if the demo is truly needed.

## Content limitations

**Symptom:** anime-style inputs or dark/black-background images look poor compared with natural-image inputs.

**Likely cause:** the README explicitly notes this model weakness.

**Fix:**

- Set expectations before the run.
- Prefer more natural-image test cases when checking the core path.
- Use this note when explaining degraded samples rather than treating it as an implementation bug.
