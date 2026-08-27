# Troubleshooting

Use this table when the plan inspector or feature extractor reports an error.

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Duplicate caption ids | The caption TSV contains repeated `id` values. The upstream audio loader keeps the last caption it sees. | Deduplicate the TSV upstream if you need deterministic captions, or keep the duplicates only if the last-write-wins behavior is intentional. |
| Missing source audio files | A clip row references a stem that does not exist in the audio directory. | Confirm that `name` matches a `.flac` or `.wav` stem exactly. Regenerate the clip TSV if needed. |
| Missing source videos | A subset TSV references an `.mp4` stem that is not present. | Fix the manifest or restore the missing media file before extracting features. |
| `Audio is too short` / `Audio too short` | The clip window is shorter than the required sample count after resampling. | Rebuild the clip manifest with the correct minimum length, or verify that the source file duration really covers the requested window. |
| `Rejecting silent audio` | The source audio is silent and `reject_silent=True` is active. | Replace the file, lower the silent-audio filter only if you truly want to keep silence, or remove that sample from the manifest. |
| `CLIP video returned None` / `Sync video returned None` | Video decode failed or the file is unreadable. | Re-encode the video, check the decoder stack, and confirm that the `.mp4` opens locally. |
| `CLIP video too short` / `Sync video too short` | The video is shorter than the 8-second extraction window. | Use longer source videos or trim the manifest to valid clips. |
| Frame-size assertion failures | The video transform received the wrong resolution. | CLIP expects 384×384 input; sync encoding expects 224×224 after center crop. |
| `torch.distributed` hangs | The extractor was launched without `torchrun` or without the required rank environment. | Use `torchrun --standalone ...` and do not launch the distributed extractor with plain `python`. |
| CUDA OOM | Batch size or worker count is too high for the available GPU memory. | Lower `--batch_size`, lower `--num_workers`, or reduce `--nproc_per_node`. |
| Missing weights | The local weight directory does not contain the VAE, vocoder, or Synchformer checkpoint for the selected mode. | Place the correct weights in the expected local weight directory before launching extraction. |
| Video extractor output is incomplete | Rank 0 did not reach the combine step. | Re-run with the same plan after cleaning the partial `latent_dir` and any half-written output directory. |
| TSV rows do not match the number of clips | Rows were skipped because of missing source files, duplicate ids, or malformed rows. | Review the plan inspector output and fix the manifest before retrying. |
| 44.1k sample-count mismatch | The plan used 352800 samples instead of the aligned 353280 count. | Switch the plan to 353280 samples and keep the 44k mode active. |
| `ffmpeg` or decoder errors | The host codec stack cannot read the media file. | Install a compatible ffmpeg build and re-check the media locally before extracting again. |

## Quick checks

1. Confirm the manifest headers.
2. Confirm the source file stems.
3. Confirm the mode-specific sample rate and sample count.
4. Confirm the required weights are present.
5. Confirm the launch command uses `torchrun` for distributed extraction.

## When to stop and fix the plan

Treat these as plan problems, not runtime noise:

- missing input media,
- malformed TSV headers,
- duplicate ids when you need deterministic row identity,
- 44k plans that still use 352800 samples,
- output paths that would overwrite a useful previous run.

Fix the plan before launching extraction. The skill-owned plan inspector should catch most of these before the first GPU is used.
