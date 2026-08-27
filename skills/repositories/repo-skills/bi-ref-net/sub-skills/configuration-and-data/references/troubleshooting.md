# Troubleshooting

## Missing `im` or `gt` directories

**Symptom:** dataset creation fails immediately or no pairs are found.

**Cause:** the expected tree `<data-root>/<task>/<dataset>/{im,gt}` does not exist.

**Fix:** create both folders and keep the task/dataset names aligned with `Config` and `MyData`.

## Mismatched image and label counts

**Symptom:** the loader reports different numbers of images and labels.

**Cause:**

- a basename exists in `im/` but not in `gt/`
- a basename exists in `gt/` but not in `im/`
- duplicate basenames exist with different supported suffixes
- a file uses a suffix that the loader does not recognize

**Fix:** run the bundled dataset checker and rename or delete the offending files so every basename has exactly one matched pair.

## Unsupported file suffixes

**Symptom:** files are present but never enter the dataset.

**Cause:** the loader only considers the exact suffix set used in the source snapshot: `.png`, `.jpg`, `.PNG`, `.JPG`, `.JPEG`.

**Fix:** rename or convert the files to one of those suffixes.

## Empty or unexpected `training_set`

**Symptom:** `Config` builds an empty combined training list for `General`, `General-2K`, or `Matting`.

**Cause:** the task directory is missing, empty, or contains only the chosen testsets.

**Fix:** populate the task folder first or set `training_set` explicitly before constructing `MyData`.

## `Config` path assumptions

**Symptom:** automatic schedule or data-root behavior does not match expectations.

**Cause:** `Config` expects a project-root layout that can resolve `datasets/dis` and `weights/cv`, and it infers checkpoint-save fields from a nearby `train.sh` when visible.

**Fix:** keep the expected directory structure or override the relevant fields before dataset/model creation.

## `load_all` memory pressure

**Symptom:** host RAM grows quickly when training starts.

**Cause:** `load_all=True` preloads every sample, and multi-process loading multiplies the memory cost.

**Fix:** leave `load_all` off unless the dataset is small and the machine has enough RAM.

## Dynamic size and 32-multiple constraints

**Symptom:** batch-shape errors, compile instability, or unexpected padding-like behavior.

**Cause:** dynamic-size batches are sampled per batch and then floor-rounded to multiples of 32.

**Fix:** keep the configured range sensible, make sure both dimensions remain large enough after rounding, or fall back to a fixed `size`.

## Auxiliary class label lookup failures

**Symptom:** an `IndexError` or `KeyError` appears when auxiliary classification is enabled.

**Cause:** the ground-truth filename does not expose a class name in the fourth `#`-separated field.

**Fix:** rename the file to match the expected DIS-style format or disable `auxiliary_classification`.

## Custom task names

**Symptom:** a new task name does not pick up the expected testsets or training-set logic.

**Cause:** the built-in task switch only knows the six standard task names.

**Fix:** update the task tables and every literal task check consistently before relying on auto-derived settings.
