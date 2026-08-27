# Troubleshooting

Use this guide when the layout checker or a preprocessing script reports a path,
shape, or dependency problem.

## Quick triage

1. Confirm the config field points at the correct leaf directory.
2. Check whether the dataset expects paired images, unpaired folders, or frame
   sequences.
3. Validate the tree with `scripts/check_dataset_layout.py` before trying a
   longer preprocessing or training run.
4. For generated outputs, make sure you are inspecting the processed folder,
   not the raw input folder.

## Common failures and fixes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Empty dataset or zero images | Config points to the wrong folder or the tree contains only unsupported files | Update the dataset path field to the correct leaf folder and keep supported image extensions. |
| CycleGAN data loads from the wrong place | Only one of `dataroot_a` / `dataroot_b` was updated, or the root is not the one used by the active split | Update both train and test domain paths or point the checker at the exact parent folder that holds `trainA`, `trainB`, `testA`, and `testB`. |
| Pix2Pix evaluation fails on a custom dataset | The dataset has `train` but no `val`, or the paired images are not split correctly | Use `test` for evaluation or create a `val` split from the same paired images. Ensure each paired file has even width and a clean left/right split. |
| DIV2K patch extraction exits immediately | The output `*_sub` folders already exist, or the raw `DIV2K_train_*` folders are missing | Use a fresh data root or remove only the generated outputs before rerunning the bundled DIV2K helper. |
| DIV2K patch counts do not match | The raw folders are out of sync, or a manual edit changed one branch only | Rebuild from untouched raw DIV2K inputs and check that the HR and LR folders have matching filenames before cropping. |
| REDS loader rejects the clip split | The annotation file keys do not match the chosen `REDS4` or `official` partition | Choose the partition that matches the data snapshot and keep `num_frames` odd for the REDS dataset classes. |
| Vimeo90K samples are empty or mismatched | The sequence folder path is wrong, or the LQ and GT sequence lengths differ | Restore the `sequence` folder structure and verify the LQ and GT frame counts for the sampled keys. |
| Wav2Lip preprocessing cannot find faces | Face detection is unavailable, the video crop is too small, or the frame contains no detectable face | Ensure the face detector dependency is present, try a larger or clearer video crop, and expect some clips to be skipped if no face is found. |
| Wav2Lip preprocessing cannot find audio or `ffmpeg` | `ffmpeg` is missing from the environment or not on the path | Install or expose `ffmpeg` before preprocessing; the helper extracts `audio.wav` from each source video. |
| Wav2Lip filelists are ignored | The reader still looks for `filelists/<split>.txt` in the working directory | Put the split files in that folder or adjust the helper before running. The config field alone does not move the lookup. |
| RealSR helper cannot find its roots | The source utility still assumes a repo-local path map | Use the bundled helper with explicit local folders, or replace the source `paths.yml` logic with your own local mapping. |
| RealSR generated folders are incomplete | The HR/LR output tree was only partially created | Check the generated `HR` and `LR` folders directly and rerun the helper from a clean output directory. |
| Download script left a broken link | The archive download was interrupted or the target symlink already existed | Remove the broken link and retry the download instead of stacking another partial cache entry on top. |

## Dataset-specific reminders

- CycleGAN / unpaired data: the image counts may differ between domains. That is
  normal.
- Pix2Pix / paired data: the two halves must stay aligned in a single image.
- REDS and Vimeo90K: sequence keys must stay stable because the loaders build
  frame paths from the clip names.
- LRS2: preprocessing is a video pipeline, not a single-image pipeline. Expect
  GPU, ffmpeg, and face-detection assumptions.
- RealSR: generated data is the product, not the source of truth. Keep the local
  output roots explicit and avoid hidden path maps.
