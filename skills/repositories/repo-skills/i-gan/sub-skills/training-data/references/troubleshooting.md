# iGAN Training/Data Troubleshooting

## `ImportError: No module named theano` or CUDA/cuDNN import errors

Likely cause: the native training scripts target a Python2-era Theano stack with
CUDA/cuDNN assumptions. Modern Python and current CUDA packages are usually not
compatible without careful pinning.

Recovery:

1. For planning tasks, use the bundled helper scripts instead of importing
   Theano.
2. For real training, provision a dedicated legacy environment and document its
   Python, Theano, CUDA, cuDNN, NumPy, OpenCV, h5py, Fuel, Lasagne, and tqdm
   versions.
3. Run a minimal Theano GPU smoke test before starting long training.
4. If only CPU is available, mark DCGAN training and batchnorm native cases as
   blocked or optional, not verified.

## `Could not initialize device gpu0`, `nvcc` errors, or `dnn_conv` failures

Likely cause: `THEANO_FLAGS` points at a GPU/CUDA/cuDNN stack that is absent,
wrong-versioned, or not visible to the process.

Recovery:

1. Check GPU visibility with the user's normal CUDA probe.
2. Confirm Theano can compile a tiny GPU function.
3. Remove stale Theano compile caches after changing CUDA/cuDNN versions.
4. Reduce the batch size only after the GPU stack is known to compile.
5. Do not continue to predictor or pack steps until generator/discriminator
   checkpoints are actually written.

## `ImportError: No module named fuel` or `H5PYDataset` errors

Likely cause: Fuel is missing or the HDF5 file lacks Fuel split metadata.

Recovery:

1. Use `scripts/inspect_dataset_plan.py` to verify the intended split before
   conversion.
2. Install a Fuel version compatible with the chosen Python/Theano environment.
3. Confirm the HDF5 file has an `imgs` dataset and a `split` attribute with both
   `train` and `test` sets.
4. Recreate the HDF5 file if it was produced by a generic h5py script without
   Fuel split metadata.

## `cv2.imread` returns `None`, resize errors, or color channel surprises

Likely cause: a directory contains non-image files, unsupported encodings,
corrupt images, or the wrong channel mode.

Recovery:

1. Run the dry-run preflight and review ignored extensions.
2. Clean the directory so top-level entries are only intended images.
3. For RGB training, pass `--channel 3` and match a config with `nc=3`.
4. For edge/sketch training, pass `--channel 1` and match a config with `nc=1`.
5. If real conversion still fails, test OpenCV on one image before retrying the
   full directory.

## HDF5 file already exists but training data seems stale

Likely cause: the converter exits early when the output HDF5 path already
exists, prints the node names, and does not rewrite the file.

Recovery:

1. Inspect the existing HDF5 file before assuming conversion reran.
2. Move or delete the stale output only after confirming it is safe.
3. Re-run conversion with an explicit new output path when comparing datasets.

## Empty or tiny test split

Likely cause: the split formula is `min(int(N * 0.05), 10000)`. For fewer than
20 images, `int(N * 0.05)` is zero.

Recovery:

1. Accept this for tiny smoke fixtures only.
2. Use more images for any training-quality assessment.
3. If you need a non-empty validation split for a tiny custom experiment,
   create a custom HDF5 writer and document the deviation from the legacy split.

## Shape mismatch during training

Likely cause: the HDF5 file width/channel does not match the selected model
configuration.

Recovery:

1. Compare `imgs.shape[1:4]` with `(npx, npx, nc)` from the config table.
2. Recreate the HDF5 with the correct `--width` and `--channel`.
3. Or add a new training config with dimensions matching the data.
4. Do not pack a model trained with mismatched metadata for downstream use.

## `AttributeError` for an unknown `model_name`

Likely cause: the selected model name has no configuration function.

Recovery:

1. Use a known name from `references/configuration.md`.
2. For a custom dataset, add a configuration function returning
   `npx, n_layers, n_f, nc, nz, niter, niter_decay`.
3. Keep the HDF5 filename and model name aligned when relying on default paths.

## Training starts but never writes samples or logs

Likely cause: failure happens during dataset load, Theano compilation, or first
batch before output files are flushed.

Recovery:

1. Check for `real_samples.png`; its absence usually points to data loading or
   preprocessing.
2. Check for Theano compile errors before the epoch loop.
3. Start with a smaller batch size only after data and compilation work.
4. Monitor `log/training_log.ndjson` for one JSON line per completed epoch.

## Predictor training fails on AlexNet or Lasagne

Likely cause: predictor training uses AlexNet feature loss and Lasagne in
addition to Theano, OpenCV, h5py, and Fuel.

Recovery:

1. Skip predictor training if downstream projection can rely on direct latent
   optimization only.
2. If `cnn` or `cnn_opt` projection is required, provide the expected AlexNet
   model artifact and compatible Lasagne version.
3. Confirm DCGAN `gen_params` and `gen_batchnorm` exist before starting
   predictor training.
4. Keep predictor-specific failures separate from ordinary DCGAN generation;
   a model without predictor keys may still sample images.

## `batchnorm_precit_z.py: No such file or directory`

Likely cause: the historical training shell recipe misspelled the predictor
batchnorm script name.

Recovery:

1. Replace `batchnorm_precit_z.py` with `batchnorm_predict_z.py`.
2. Run it only after `train_predict_z.py` has produced `models/predict_params`.
3. Re-pack the model after predictor batchnorm is created.

## Packed model misses expected keys

Likely cause: the packer includes only files that already exist in the cache
`models/` directory.

Recovery:

1. Inspect packer output for `missing model file` lines.
2. Run missing batchnorm or predictor steps if those keys are required.
3. For inference-only generation, confirm at least generator parameters and
   generator batchnorm are present.
4. For projection with a learned predictor, require `predict_params` and
   `predict_batchnorm`.

## Upgrade fails with missing `postlearn_params`

Likely cause: the old packed model does not match the expected legacy key
schema.

Recovery:

1. Inspect the old pickle keys in a safe environment before upgrading.
2. If `postlearn_params` is absent, locate the separate batchnorm files or
   re-estimate batchnorm from the trained cache.
3. Write the upgraded model to a new path and keep the original untouched until
   downstream loading is verified.

## Network download stalls or disk fills

Likely cause: public HDF5 archives are large and the legacy script downloads a
ZIP before unzipping the HDF5.

Recovery:

1. Run the URL planner and check compressed size before downloading.
2. Reserve enough temporary disk for both ZIP and HDF5.
3. Prefer resumable/manual download tooling if the environment is unreliable.
4. Verify the HDF5 exists before deleting the ZIP.
5. Keep download cases marked skip-network in automated verification.
