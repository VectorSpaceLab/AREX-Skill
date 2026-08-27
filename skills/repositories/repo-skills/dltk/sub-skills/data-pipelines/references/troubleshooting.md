# Data-pipeline troubleshooting

Use the smallest failing synthetic fixture first. A reader failure should be
made actionable before any Estimator or full-volume run.

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `abstract_reader` fails at import with missing `tf.train.SessionRunHook` | TensorFlow 2.x is installed while the source uses TF1 APIs | Use the verified isolated Python 3.7/TensorFlow 1.15 runtime, or stop and plan a separately reviewed port. Do not patch one symbol and claim compatibility. |
| `resize_image_with_crop_or_pad` raises an indexing error on a current NumPy | The source passes a list of slices to `image[...]`; modern NumPy expects a tuple | Use the reviewed center crop/pad adaptation in the smoke script and preserve a final channel axis. Record the version change. |
| output shape is `[Z,Y,X]` but the model expects rank 5 after batching | Missing channel axis or wrong `example_shapes` | Add/stack channels to `[Z,Y,X,C]`, set an unbatched shape with the channel, and check the resulting batch shape `[B,Z,Y,X,C]`. See the model-building handoff. |
| `ValueError` says a key is missing or entries are incompatible | Yielded nested dictionaries/lists do not match `dtypes` | Compare the first yielded record with `dtypes` and `example_shapes`. Extra keys are removed, but expected keys and dict/list structure must be present. Run `validate_reader_contract.py --case malformed`. |
| a malformed nested dtype/shape map survives until graph construction | Validation only checked top-level keys or relied on TensorFlow inference | Recursively validate every dictionary/list level and check NumPy dtype and shape before yielding. Dictionaries nested inside lists are a known gap in the legacy cleaner; reject or normalize them yourself. |
| `PREDICT` emits labels, duplicates a sample, or raises a `params`/label error | Prediction branch yielded and then fell through to training code | In `read_fn`, yield exactly one feature record and immediately `return`; do not parse labels or index `params` in that branch. Test with `params=None`. |
| metadata such as `subject_id` or a SimpleITK image disappears | It is not declared in the `Reader` dtype tree and the cleaner removes it | Keep metadata in a parallel Python record, or encode only TensorFlow-compatible metadata with declared dtypes. Preserve the SimpleITK object for post-processing outside the dataset. |
| iterator is uninitialized | The hook returned by `get_inputs` was not attached to the TF1 monitored session/Estimator operation | Use the `(input_fn, iterator_initializer_hook)` pair and attach the hook. The hook runs `iterator.initializer` in `after_create_session`. |
| `flip([image, label])` breaks alignment | Image and label were flipped independently or different random decisions were made | Pass both in one mutable list to one `flip` call, or implement one explicit sampled decision and apply it to both. Never intensity-augment a label. |
| augmentation changes an earlier sample or normalized cache | `add_gaussian_offset` and `add_gaussian_noise` mutate the input array | Pass `image.copy()` when the original is reused. Ensure image arrays are floating point before `+=`; keep labels integer and untouched. |
| `flip` fails only for some runs with a tuple | The docstring permits tuple input but the implementation assigns into the sequence when a flip occurs | Pass a list or a single ndarray. Add a deterministic test by controlling the random decision if testing the legacy helper. |
| class-balanced extraction returns fewer patches or fails its assertions | `n_examples` is below the number of classes, a class is absent, image/label shapes differ, or the patch is larger than the volume | Check `image.shape[:-1] == label.shape`, ensure every requested class has voxels, choose a patch inside the spatial volume, and set `n_examples >= len(classes)`. Treat output count as data-dependent. |
| patch helper crashes under modern NumPy with `np.int` missing | The legacy source uses the removed `np.int` alias | Use the verified legacy environment or a reviewed local compatibility adaptation using an explicit integer dtype. Do not alter label semantics silently. |
| image and label patch shapes match but anatomy is misregistered | Modalities were resampled independently or axes were assumed from names | Use one reference image, reslice all modalities to it, use nearest-neighbor for labels, and check spacing/origin/direction as well as array shape. |
| SimpleITK cannot open a path | Dataset is not present, the CSV has a placeholder/relative path, or the row schema is wrong | Check external data/registration permissions, resolve paths under an explicit dataset root, verify required modality filenames, and report the missing prerequisite. Do not start a downloader from `read_fn`. |
| a smoke check attempts network access, credentials, or broad cleanup | Source data preparation script was copied instead of distilled | Keep downloader/resampling preparation separate. The bundled scripts use in-memory synthetic NumPy data, no network, no credentials, no archive extraction, and no destructive writes. |

## Stop conditions

Stop and report an unresolved block when the required TensorFlow 1.x runtime,
SimpleITK installation, external dataset permission, or label/modality contract
is unavailable. A passing synthetic script proves only local array/contract
logic; it does not prove NIfTI readability, physical registration, dataset
completeness, training convergence, or deployment compatibility.
