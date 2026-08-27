# Troubleshooting

## Config inheritance issues
- **Symptom:** the validator says `inherit_from` is missing or cannot be resolved.
- **Likely cause:** the base config path is wrong, or the config is being opened from a directory that does not contain the repo root.
- **Fix:** point `inherit_from` at the shared base file for that family and rerun the validator.

## TUM path problems
- **Symptom:** `rgb.txt`, `depth.txt`, or a pose file is missing.
- **Likely cause:** the archive was extracted one directory too high or the sequence folder name is wrong.
- **Fix:** the parser wants the sequence root itself, not the tarball file or its parent directory.

## Replica path problems
- **Symptom:** the config points at `Replica/` but the loader cannot find `results/frame*.jpg`.
- **Likely cause:** the archive was extracted but not renamed to the lowercase `replica/` tree expected by the configs.
- **Fix:** keep the final dataset root at `datasets/replica/<scene>/` and leave `results/` under that scene folder.
- **Extra note:** the bundled downloader refuses to overwrite a leftover `Replica/` staging directory; remove or rename it manually if a partial extraction is already present.

## EuRoC path problems
- **Symptom:** the validator cannot find `mav0/cam0/data`, `mav0/cam1/data`, or `data.csv`.
- **Likely cause:** the archive was extracted into an extra `MH_02_easy/` directory or into the wrong root.
- **Fix:** make the configured dataset path resolve to the folder that directly contains `mav0/`.

## RealSense config confusion
- **Symptom:** a live RealSense config fails file checks.
- **Likely cause:** the config is hardware-driven, not dataset-driven.
- **Fix:** use the live camera only when `pyrealsense2` and the device are available. If `dataset_path` is set in the RGB-D variant, validate only that the directory exists.

## Single-thread flags
- **Symptom:** changing one `single_thread` key does not affect the process you expected.
- **Likely cause:** MonoGS reads `Training.single_thread` in the frontend and `Dataset.single_thread` in the backend when that key is present.
- **Fix:** update the flag in the section that matches the behavior you want.

## Result directory surprises
- **Symptom:** saving goes into a timestamped directory you did not expect.
- **Likely cause:** MonoGS groups outputs by the dataset path tail and current time.
- **Fix:** that behavior is normal; change `Results.save_dir` only if you want the parent bucket to move.

## Script help
Every bundled helper supports `--help`:
- `bash scripts/download_tum.sh --help`
- `bash scripts/download_replica.sh --help`
- `bash scripts/download_euroc.sh --help`
- `python scripts/validate_monogs_config.py --help`
