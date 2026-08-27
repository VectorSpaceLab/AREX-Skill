# Capture Workflows

## Purpose

Use this when operating SplaTAM's iPhone/NeRFCapture capture paths. Commands assume the current working directory is a SplaTAM checkout root.

## Capture-only dataset creation

Use this when the user only wants an RGB-D dataset saved from the NeRFCapture app.

1. Copy or edit a config like `configs/iphone/dataset.py`.
2. Set:
   - `workdir`: output dataset directory.
   - `num_frames`: number of frames to capture.
   - `depth_scale`: scale used when saving depth to 16-bit PNG.
   - `overwrite`: whether an existing output directory may be deleted after prompt.
3. Run the Python script:

   ```bash
   python scripts/nerfcapture2dataset.py --config <capture-config.py>
   ```

4. In the NeRFCapture app, send frames until the script reports the requested count.
5. Validate the captured dataset:

   ```bash
   python sub-skills/capture/scripts/validate_nerfcapture_dataset.py \
     --dataset-dir <captured-scene> --require-depth
   ```

Expected output: `rgb/`, `depth/`, and `transforms.json` under `workdir`.

## Capture-to-offline reconstruction

Use this when the user wants to capture a dataset and then run standard offline SplaTAM.

Safe manual sequence:

```bash
python scripts/nerfcapture2dataset.py --config <capture-config.py>
python sub-skills/capture/scripts/validate_nerfcapture_dataset.py \
  --dataset-dir <captured-scene> --require-depth
python scripts/splatam.py <offline-splatam-config.py>
```

The offline SplaTAM config should set:

- `data.dataset_name="nerfcapture"`.
- `data.basedir` to the capture root's parent directory.
- `data.sequence` to the captured scene directory name.
- `data.num_frames` to the captured count or `-1` where supported.
- iPhone-specific downscale/densification image sizes that match the capture assumptions.

Public `configs/iphone/nerfcapture.py` combines capture settings and SplaTAM settings for this pattern.

## Online live SplaTAM demo

Use this when the user wants SplaTAM to build a reconstruction while frames stream.

1. Verify CUDA/rasterizer and `cyclonedds` imports.
2. Copy/edit `configs/iphone/online_demo.py`.
3. Set `workdir`, `run_name`, `num_frames`, `depth_scale`, `overwrite`, resolutions, tracking/mapping iterations, and W&B.
4. Run:

   ```bash
   python scripts/iphone_demo.py --config <online-demo-config.py>
   ```

5. Send frames from the NeRFCapture app. The script writes dataset frames and SplaTAM outputs, then saves final `params.npz` in the configured result directory.
6. Visualize after completion with the reconstruction sub-skill.

The live script uses the DDS topic `Frames` with `SplatCaptureData.SplatCaptureFrame`, converts ARKit poses to the GradSLAM convention, initializes Gaussians from the first depth frame, and performs tracking/mapping as frames arrive.

## Bash wrapper boundaries

The repo includes three convenience wrappers:

- `bash_scripts/nerfcapture2dataset.bash <config_file>`: buffer checks, capture-only Python script.
- `bash_scripts/nerfcapture.bash <config_file>`: buffer checks, capture dataset, run offline SplaTAM, visualize final output.
- `bash_scripts/online_demo.bash <config_file>`: buffer checks, run online live demo, visualize final output.

These wrappers check `net.core.rmem_max` and `net.core.wmem_max` and may run:

```bash
sudo sysctl -w net.core.rmem_max=2147483647
sudo sysctl -w net.core.wmem_max=2147483647
```

Only use wrappers after explicit authorization for this system mutation. Without authorization, run the Python scripts directly and document any network-buffer limitation.

## Expected live capture signals

- Script prints `Waiting for frames...`.
- Each received frame increments `N/<num_frames> frames received`.
- Frames without depth are skipped with a warning to check depth support in the app.
- At completion, capture-only writes `transforms.json`; live demo writes both dataset files and SplaTAM result files.

## Hand off to reconstruction

After a valid dataset or online result exists:

- For offline SLAM: use the reconstruction sub-skill's offline workflow.
- For result validation/export/viewing: use the reconstruction result checker and export/viewer workflows.
- For a captured dataset schema question: use [data-format.md](data-format.md).
