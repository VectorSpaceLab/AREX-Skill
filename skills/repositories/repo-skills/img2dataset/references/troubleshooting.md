# img2dataset Troubleshooting

## Purpose

Read this when a core `img2dataset` run, import, or environment check fails. This file covers cross-cutting package issues; image-processing, input/output, and distributed-specific details live in the sub-skill troubleshooting files.

## Fast triage

1. Run the root environment checker:
   ```bash
   python scripts/check_img2dataset_env.py --json
   ```
2. If the failure is format-specific, route to the relevant sub-skill:
   - Input/output schema or writer layout -> `input-output-formats`.
   - Resize, encoding, filters, or blur -> `image-processing`.
   - PySpark, Ray, W&B, or throughput -> `distributed-execution`.
   - CLI/API recovery, hashes, SSL, and incremental mode -> `core-download`.

## Common failures

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `ModuleNotFoundError: fire` or import failure for `img2dataset` | Package not installed in the current environment or the wrong Python is active | Install `img2dataset` in the target environment, then rerun the root environment checker. |
| Missing `cv2`, `pyarrow`, `webdataset`, `wandb`, `fsspec`, or `albumentations` | Incomplete runtime dependencies | Reinstall the package and verify `pip check`; use the root environment checker to confirm the base imports. |
| TFRecord writer errors or `tensorflow_io` import problems | TensorFlow/TFIO optional dependencies are missing or mismatched | Use `input-output-formats` and verify the optional TensorFlow dependencies before choosing `tfrecord`. |
| `java: command not found` or Spark local session failures | PySpark requires a Java runtime | Use the distributed sub-skill and install Java inside the inspection environment or choose multiprocessing/Ray instead. |
| Ray distributor does nothing useful or fails on old examples | Ray is optional and current guidance must not use deprecated `local_mode=True` | Verify Ray with `distributed-execution/scripts/check_distributed_backends.py` and use the current `ray.init(...)` patterns. |
| `ValueError: Unsupported hash to compute` or verify-hash mismatch | `compute_hash` and `verify_hash` do not match or the hash type is unsupported | Use `sha256`, `md5`, or `sha512`, and keep the verification column consistent with the compute hash. |
| `You cannot use in save_additional_columns...` | Reserved metadata columns were requested | Remove the reserved names and keep only user-defined extras. |
| `Image decoding error`, `image too small`, `image area too large`, or `aspect ratio too large` | The source image or resize thresholds are incompatible | Route to `image-processing` and adjust resize/filter settings. |
| `Use of image disallowed by X-Robots-Tag directive` | The server announced a disallowed robots policy | Keep the default policy unless the source is trusted and the user explicitly accepts the risk. |
| `SSL certificate verify failed` | Server certificate is invalid or self-signed | Use `ignore_ssl_certificate=True` only for trusted sources and explain the security trade-off. |
| `No file found at path ... with extension ...` | The input path is not a folder of the selected format or the extension is wrong | Recheck `--input_format`, folder contents, and column mapping. |
| Interrupted run or partially written output | The same output folder was resumed with the wrong mode or a different shard layout | Re-run the same command with the same URL list and `number_sample_per_shard` using `incremental`, or choose `overwrite` only if deletion is intended. |
| Empty or missing captions | The caption column was not present or `caption_col` was left unset | Use `input-output-formats` to verify the input schema and output writer behavior. |
| Paths or object-store URLs fail unexpectedly | Missing filesystem backend package, auth, or prefix handling | Check the `fsspec` prefix and install the relevant filesystem backend package. |

## Staleness and environment notes

- This skill was generated from a dirty checkout that already contained the generated skill tree.
- Compare the current checkout commit and package version with `references/repo-provenance.md` before reusing the skill.
- The repository's public package depends on a modern scientific Python stack; if the environment changed, re-run the root environment checker.
- Non-fatal warning noise such as Albumentations update notices can be suppressed with `NO_ALBUMENTATIONS_UPDATE=1` when it makes logs easier to read.

## Recovery reminders

- Prefer fixing the command, input schema, or runtime environment over suppressing failures.
- Do not recommend disabling SSL verification or robots filtering without stating the risk.
- Do not treat a CPU-only environment as proof of PySpark, Ray, or TFRecord backend coverage if those optional dependencies are missing.
