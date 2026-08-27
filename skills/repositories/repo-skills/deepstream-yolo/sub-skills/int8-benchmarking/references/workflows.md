# INT8 calibration workflow

The commands below assume the generated skill root is the current working directory.

## 1. Prepare the calibration build path

- Install OpenCV dev headers on the host when you want calibration support.
- Export `CUDA_VER` to the DeepStream-matched CUDA version.
- Set `OPENCV=1` before rebuilding `nvdsinfer_custom_impl_Yolo`.

Example:

```bash
CUDA_VER=12.8 OPENCV=1 sub-skills/int8-benchmarking/scripts/build-nvdsinfer-plugin.sh --output-dir ./deepstream-yolo-runtime
```

If the current host lacks DeepStream but you want to verify that the packaged parser and configs are present, run the same helper with `--stage-only`.

## 2. Build the calibration image list

Use the helper to write absolute image paths into `calibration.txt`:

```bash
sub-skills/int8-benchmarking/scripts/make-calibration-list.sh ./calibration calibration.txt
```

Then point the DeepStream calibration environment at that file:

- `INT8_CALIB_IMG_PATH=calibration.txt`
- `INT8_CALIB_BATCH_SIZE=1` or a host-safe batch size

## 3. Switch the infer config to INT8

In the chosen `config_infer_primary*.txt` file:

- set `model-engine-file` to the INT8 engine name,
- uncomment or set `int8-calib-file=calib.table`, and
- change `network-mode=1`.

## 4. Run the app

Launch `deepstream-app` from the staged runtime tree after the calibration path and config are ready. The calibration run should generate `calib.table` and a matching INT8 engine cache.

## 5. Read the result

- If the calibration file is missing, check the image list and environment variables first.
- If the build path fails, confirm the OpenCV dev package and `OPENCV=1` switch.
- If accuracy is lower than expected, compare the NMS / threshold settings to the benchmark notes.