# Evaluation Troubleshooting

Use this matrix when batch evaluation or onset scoring fails. Prefer read-only checks and command-builder validation before launching long CUDA jobs.

## Batch evaluation failures

| Symptom | Likely cause | Action |
|---|---|---|
| `KeyError: 'LOCAL_RANK'` or `KeyError: 'WORLD_SIZE'` before Hydra output appears | The evaluator was run with plain `python` instead of `torchrun`. | Rebuild the command with `scripts/build_batch_eval_command.py` and launch with `torchrun --standalone --nproc_per_node=<N> batch_eval.py ...`, including for one GPU. |
| NCCL initialization hangs or rendezvous errors | Bad distributed launch, blocked port, stale shell rank variables, or GPU visibility mismatch. | Start with one GPU: `CUDA_VISIBLE_DEVICES=0 OMP_NUM_THREADS=4 torchrun --standalone --nproc_per_node=1 ...`. In interactive shells, clear stale `RANK`, `LOCAL_RANK`, `WORLD_SIZE`, `MASTER_ADDR`, and `MASTER_PORT` before rebuilding the command. |
| `Unknown model variant` | `model=` is not one of the five configured variants. | Use one of `small_16k`, `small_44k`, `medium_44k`, `large_44k`, or `large_44k_v2`. For faster evaluation, start with `small_16k`. |
| Model or external checkpoint download starts unexpectedly | Weights are absent from the expected `weights/` or `ext_weights/` locations and the real evaluator calls the model download helper. | Decide whether network downloads are allowed. If not, stage the pretrained MMAudio model, VAE, Synchformer, and BigVGAN assets before running. The command builder never downloads anything. |
| `FileNotFoundError` for AudioCaps audio directory | AudioCaps generation is text-only, but the dataset constructor still lists `audio_path`. | Create or point `eval_data.AudioCaps.audio_path` / `eval_data.AudioCaps_full.audio_path` at the intended directory, even if the audio content is only used for naming sanity. |
| AudioCaps CSV loads but outputs are overwritten or missing | Duplicate or unsafe `name` values in the CSV. | Ensure the `name` column is unique and contains filename-safe stems. The generated output is `<name>.flac`. |
| VGGSound reports zero usable videos | CSV/file naming mismatch or wrong split. | Confirm the CSV has no header and columns `id,sec,caption,split`; only `split == test` rows are used. Files must be named `<id>_<sec:06d>.mp4`. |
| MovieGen metadata error or missing prompt | Metadata files are absent, named incorrectly, or are not single JSON objects with `audio_prompt`. | For each `video_stem.mp4`, provide `jsonl_path/video_stem.jsonl` containing a JSON object with `audio_prompt`. |
| `CLIP video too short` / `Sync video too short` | Video duration is shorter than `duration_s` at 8 FPS and/or 25 FPS decoding requirements. | Reduce `duration_s`, remove the short sample, or provide a longer/reencoded video. For an 8-second run, expect 64 CLIP frames and 200 Sync-rate frames before downstream sequence shaping. |
| DataLoader collate errors after many video warnings | Every item in a batch decoded to `None`, so filtering leaves an empty batch. | Lower `batch_size`, prefilter bad media, set `num_workers=0` for a diagnostic pass, then relaunch. |
| CUDA out of memory | Model variant, batch size, compile mode, or video preprocessing is too heavy. | Reduce `batch_size` first; disable `compile`; use `small_16k`; lower `--nproc_per_node` if GPUs are oversubscribed; keep `num_workers` conservative. |
| First iteration is very slow | `compile=True` triggers compilation and video workers may be decoding many files. | Use `compile=False` for smoke/debug. Run with a tiny dataset slice if possible before the full dataset. |
| Generated directory is not where expected | Hydra run directory or `output_name` changed the path. | Check `exp_id`, `hydra.run.dir`, and `output_name`. Output goes to `<hydra-run-dir>/<dataset>` or `<hydra-run-dir>/<dataset>-<output_name>`. |
| No MP4 or composited video outputs | Expected behavior for batch evaluation. | Use the inference route if the deliverable requires video compositing. Batch evaluation writes `.flac` only. |
| Quantitative metrics command is unavailable | Batch evaluation only generates audio; project quantitative metrics live in external av-benchmark tooling. | Install and use the external metric suite only when the user requests those metrics and reference/generated sets are ready. Do not treat missing metrics as a failed generation run. |

## Path and schema preflight

Use the command builder's read-only validation when paths are present locally:

```bash
python skills/disco/mmaudio/sub-skills/evaluation/scripts/build_batch_eval_command.py \
  --dataset vggsound \
  --vgg-video-path ./data/test-videos \
  --vgg-csv-path ./data/vggsound.csv \
  --check-paths
```

For debugging video decode, use small values in the printed command:

```text
batch_size=1 num_workers=0 compile=False output_name=debug
```

## Onset scoring failures

| Symptom | Likely cause | Action |
|---|---|---|
| Script prints missing GT files | Prediction-to-GT naming convention does not match your files. | Use `--strip-pred-suffix` and `--gt-suffix`. For `clip_denoised.flac` -> `clip_times.txt`, the defaults are correct. For `clip.flac` -> `clip.txt`, pass `--gt-suffix ''`. |
| `librosa`, `numpy`, or `sklearn` import error | CPU metric dependencies are not installed in the active environment. | Install the audio analysis dependencies in the evaluation environment, or run onset scoring in the prepared MMAudio environment that includes them. The script imports heavy dependencies only when scoring, so `--help` still works. |
| `No audio files found` | Wrong prediction directory or unsupported extension. | Put `.flac` or `.wav` files in `--input-dir`, or pass the correct directory. |
| Metrics are all zero | Missing/empty GT times, overly high onset threshold, silent predictions, or naming mismatch. | Run once with `--per-file`; lower `--delta` for onset detection only after confirming GT alignment; inspect audio duration and amplitude. |
| Average precision is unstable for sparse files | A file has no positives, no predictions, or only one label class. | The bundled script returns a conservative value instead of crashing, but inspect per-file results before comparing benchmark claims. |
| Output file was not written | Safe default avoids writes. | Add `--write-results` to write `eval_results.txt` under the prediction directory, or provide `--output-file <path>`. Existing files are overwritten only when you explicitly request writing. |
| Results differ from a 44.1 kHz generation sample rate expectation | The onset metric intentionally analyzes at 22,050 Hz by default. | Keep the default for compatibility with the original onset logic, or explicitly set `--sample-rate` and document that the result is not directly comparable. |

## Minimal recovery sequence

1. Render, but do not run, a command with the builder.
2. Add `--check-paths` and fix all reported path/schema errors.
3. Launch a one-GPU, tiny-batch, `compile=False`, `num_workers=0` run.
4. Verify that `.flac` files exist and sample rates match the selected model.
5. Only then scale GPUs, batch size, workers, and external metrics.
