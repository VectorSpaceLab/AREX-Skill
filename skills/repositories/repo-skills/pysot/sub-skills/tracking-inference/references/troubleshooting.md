# Tracking inference troubleshooting

Use this workflow-specific guide for demo, test, snapshot loading, tracker API, and output-shape failures.

## Fast triage

Run the safe validator first:

```bash
python scripts/validate_tracking_inputs.py \
  --mode demo \
  --config path/to/config.yaml \
  --snapshot path/to/model.pth \
  --video-name path/to/video.mp4
```

If the validator fails, fix that input issue before attempting OpenCV, CUDA, or dataset runs.

## Missing snapshot or wrong snapshot path

Signals:

- Validator reports `snapshot file does not exist`.
- Native demo/test raises `FileNotFoundError`, `No such file`, or a `torch.load` path error.

Actions:

1. Ask the user for the actual `.pth` snapshot path.
2. Confirm the snapshot belongs to the same model/config family as the YAML.
3. For demos, pass the path with `--snapshot path/to/model.pth`.
4. For tests, remember the result `model_name` is derived from the snapshot filename stem.

Do not download model zoo snapshots automatically unless the user explicitly asks and approves network/storage use.

## State-dict mismatch or `load NONE from pretrained checkpoint`

Signals:

- `missing keys` / `unused_pretrained_keys` warnings.
- `AssertionError: load NONE from pretrained checkpoint`.
- `SiamMaskTracker must have mask_head` or `refine_head` assertion.
- Good-looking commands produce nonsensical boxes from the first tracked frame.

Actions:

1. Check that the config and snapshot are from the same architecture family.
2. Check `TRACK.TYPE`, `MASK.MASK`, `BACKBONE.TYPE`, `RPN.TYPE`, and mask/refine settings.
3. If a checkpoint contains `state_dict` or `module.` prefixes, PySOT's loading helpers can remove prefixes; a plain snapshot may load directly.
4. If a training checkpoint is being reused for inference, verify whether it contains optimizer/epoch wrapper fields and whether model weights are under `state_dict`.
5. Route architecture/key-level reconciliation to `configuration-models`; this sub-skill should not rewrite the model architecture.

## `ModuleNotFoundError: No module named 'pysot'`

PySOT's `setup.py` installs distribution metadata for `toolkit`, not a normal installed `pysot` distribution. The `pysot` package is commonly imported by running from the checkout, adding the checkout root to `PYTHONPATH`, or using equivalent editable-development path registration.

Actions:

```bash
export PYTHONPATH=path/to/pysot-checkout:$PYTHONPATH
python -c "import pysot; import toolkit; print('ok')"
```

Also install runtime dependencies used by the scripts: PyTorch, OpenCV, YACS, PyYAML, tqdm, matplotlib, colorama, tensorboardX, and NumPy compatible with the user's stack.

## `ImportError: cannot import name region` or `toolkit.utils.region` build failure

`tools/test.py` imports `toolkit.utils.region` for VOT overlap/format helpers. The legacy extension is built from Cython sources.

Actions:

1. Ensure a C compiler is available.
2. Use `Cython<3` for this legacy extension; Cython 3 can break the old `.pyx`/`.pxd` code.
3. Build the extension in the checkout, for example:

   ```bash
   python setup.py build_ext --inplace
   ```

4. Re-test import:

   ```bash
   python -c "from toolkit.utils.region import vot_overlap; print('ok')"
   ```

Route dataset/result-layout details to `evaluation-toolkit` after the extension imports.

## OpenCV GUI, webcam, or video failures

Signals:

- `cv2.selectROI` fails or immediately exits.
- OpenCV cannot open a display/window in a headless server.
- `VideoCapture` returns no frames.
- Frames from `cv2.imread` are `None`.

Actions:

- In headless environments, avoid the native demo or use a virtual display only if the user approves. The bundled validator is the safe non-GUI check.
- For webcam mode, verify camera device 0 is accessible.
- For file mode, use `.avi` or `.mp4` with a codec OpenCV can decode.
- For image-folder mode, use `*.jpg`/`*.jpeg` files with numeric filename stems such as `0001.jpg`; the native sorter casts the stem to `int`.
- Always check `cv2.imread(path) is not None` before calling `tracker.init` or `tracker.track` in custom scripts.

## CUDA not available

Signals:

- `AssertionError: Torch not compiled with CUDA enabled`.
- `RuntimeError: Found no NVIDIA driver`.
- CUDA device mismatch errors.
- `tools/test.py` fails before dataset iteration.

Actions:

- The native demo can be CPU-capable because it loads weights to CPU first and sets `cfg.CUDA = torch.cuda.is_available() and cfg.CUDA` before choosing the device.
- The native benchmark `test.py` calls `load_pretrain(...).cuda().eval()` and `load_pretrain` maps tensors through the current CUDA device. Treat full unmodified `test.py` as CUDA-required.
- Do not claim a full benchmark native run is safe on CPU unless the user intentionally edits/wraps the script and accepts that this is no longer the unmodified native path.
- Confirm model and crop tensors use the same device: `cfg.CUDA`, `model.to(device)`, and `BaseTracker.get_subwindow` must agree.

## Dataset missing or wrong benchmark name

Signals:

- `DatasetFactory.create_dataset` cannot find a dataset.
- `--video` silently processes no videos because the name does not match.
- Result directories are empty after `test.py`.

Actions:

1. Confirm the requested dataset name exactly matches the toolkit adapter name, e.g. `VOT2018`, `VOT2018-LT`, `GOT-10k`, or an OPE dataset supported by the user's toolkit checkout.
2. Confirm the dataset is present under `testing_dataset/<DATASET>` in the checkout expected by `test.py`.
3. Check JSON sidecars and result layout with `evaluation-toolkit`.
4. For `--video`, use the dataset's internal video name, not a media filename path.

Do not download benchmark datasets automatically; they are external, large, and user-controlled artifacts.

## Unsupported `TRACK.TYPE`

Signals:

- Validator reports unsupported `TRACK.TYPE`.
- Native run raises `KeyError` in `build_tracker(model)`.

Supported values are exactly:

- `SiamRPNTracker`
- `SiamMaskTracker`
- `SiamRPNLTTracker`

Actions:

1. Fix the config or select a matching config/snapshot pair.
2. If the user is adding a new tracker class, route to `configuration-models` for model/tracker architecture work.

## Wrong bbox, mask, polygon, or confidence output

Common causes:

- Initial ROI is not 0-based `[x,y,w,h]`, has zero/negative size, or is outside the frame.
- RGB images are passed to an API path expecting OpenCV BGR images.
- Frames were resized or letterboxed inconsistently between initialization and tracking.
- A non-mask snapshot/config is used with `SiamMaskTracker`.
- The object is lost; `best_score` is low and long-term tracker may switch search state.
- Output floats are truncated too early for evaluation.

Actions:

1. Validate the first frame and ROI numerically before `tracker.init`.
2. Preserve float boxes until writing the target benchmark format.
3. For mask outputs, confirm `cfg.MASK.MASK`, mask/refine heads, and `TRACK.MASK_THERSHOLD`.
4. Compare one short sequence visually only when GUI/display is acceptable.
5. Route metric/result-format questions to `evaluation-toolkit`.

## NumPy/OpenCV legacy warnings

Some source code uses legacy aliases such as `np.int` and `np.float`, which fail on newer NumPy versions. If a native visualization or mask path fails with an alias error, either use a compatible NumPy version or apply a small compatibility patch in the user's working copy. Keep this distinct from tracker correctness: the validator and command construction do not require these aliases.
