# Feature extraction and verification troubleshooting

Use this page when extraction or verification fails after the model checkpoint and data have already been selected.

## Checkpoint / backbone mismatch

Symptoms:

- `Missing key(s) in state_dict` or `Unexpected key(s) in state_dict`;
- `size mismatch for output_layer` or `fc`;
- embeddings have a dimension other than the expected `512`;
- extraction succeeds but verification accuracy is nonsensical.

Likely causes and fixes:

- The checkpoint was trained with a different backbone. Match `IR_50` with `IR_50`, `IR_SE_50` with `IR_SE_50`, and `ResNet_50` with `ResNet_50`.
- The checkpoint was trained for a different input size. Most face.evoLVe model-zoo checkpoints use `112 x 112`; a `224 x 224` model changes the final flatten size.
- The file may contain margin-head weights such as ArcFace, CosFace, SphereFace, or Am_softmax instead of the backbone state dict. Extract only the backbone weights.
- DataParallel checkpoints may prefix keys with `module.`. Strip this prefix before loading into a plain module.
- Some training checkpoints wrap the state dict under keys such as `state_dict`, `model_state_dict`, `backbone`, or `model`. Inspect the top-level keys before deciding that the checkpoint is invalid.

## CPU / GPU `map_location` issues

Symptoms:

- `Attempting to deserialize object on a CUDA device but torch.cuda.is_available() is False`;
- `invalid device ordinal`;
- GPU checkpoint loads only on the training machine.

Fixes:

- Load with `torch.load(checkpoint, map_location=device)`.
- For portable inspection, use `--device cpu` with the bundled extraction wrapper.
- If CUDA is requested, ensure the selected device exists and that the installed PyTorch build supports CUDA.

## Python 3 DataLoader iteration

The original v1 helper uses `iter_loader.next()`, which fails in Python 3 with an attribute error. Replace it with one of these patterns:

```python
for batch, _ in loader:
    ...
```

or

```python
iter_loader = iter(loader)
batch, labels = next(iter_loader)
```

The bundled wrapper uses the safe `for batch, _ in loader` pattern.

## OpenCV BGR/RGB and normalization drift

Symptoms:

- v1 and v2 embeddings differ more than expected;
- verification accuracy drops after switching preprocessing paths;
- visual checks show color channels swapped.

Checklist:

- OpenCV reads BGR. Convert to RGB before channel-first tensor conversion.
- v1 uses torchvision `ToTensor()` followed by `Normalize([0.5] * 3, [0.5] * 3)`.
- v2 uses OpenCV arrays and `(pixel - 127.5) / 128.0`.
- Compare with the same checkpoint, same input size, same crop, and same `--no-tta` or default TTA setting.
- For raw or loosely cropped faces, run alignment first; this sub-skill assumes extraction-ready face crops.

## Odd embedding rows or wrong pair layout

Verification expects flat pair order: `[pair0_image0, pair0_image1, pair1_image0, pair1_image1, ...]`.

Fixes:

- Reject any embeddings array with an odd number of rows.
- Require `len(issame) == embeddings.shape[0] // 2`.
- If you extracted from an ImageFolder root, confirm that the feature row order matches the intended pair order before evaluating.
- Do not evaluate class-sorted training embeddings with an LFW `issame` file unless you created the embeddings in the exact pair order for that file.

## Fold count is too high

Symptoms:

- `Cannot have number of splits n_splits greater than the number of samples` from scikit-learn `KFold`.

Fixes:

- Use `nrof_folds <= num_pairs`.
- For tiny synthetic checks, set `--nrof-folds 2`.
- For standard LFW-style protocols, use `10` folds only when at least 10 pairs are present.

## bcolz validation arrays are missing

Training-time `perform_val` expects each validation set to contain:

```text
validation_root/
  lfw/             # bcolz carray directory
  lfw_list.npy     # boolean issame labels
```

The same naming pattern is used for datasets such as `cfp_ff`, `cfp_fp`, `agedb_30`, `calfw`, `cplfw`, and `vgg2_fp`.

Fixes:

- If `bcolz.carray(rootdir=...)` cannot open the directory, the validation data was not prepared or the dataset name is wrong.
- If `_list.npy` is missing, pair labels are unavailable; route data acquisition/layout work to `data-preparation`.
- If you only need to evaluate embeddings already saved as `.npy`, use `evaluate_pairs.py` and avoid bcolz entirely.

## BatchNorm or dropout instability

Symptoms:

- Batch size `1` extraction produces unstable results;
- repeated runs differ with the same input;
- CUDA and CPU embeddings differ more than normal floating-point tolerance.

Fixes:

- Always call `model.eval()` before feature extraction.
- Wrap inference in `torch.no_grad()`.
- Use the same TTA flag and preprocessing path for all embeddings in a verification run.
