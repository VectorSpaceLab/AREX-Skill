# Troubleshooting

## Missing flist file
**Symptom:** a config points to a flist path that does not load.

**Likely causes:**
- the path is spelled incorrectly
- the path is relative to the wrong working directory
- the file exists in the checkpoint directory, but EdgeConnect is resolving it from the current shell directory

**Fix:**
- resolve the path from the runtime working directory
- use absolute paths when portability matters
- rebuild the list with `scripts/build_flist.py`

## Empty directory or empty flist
**Symptom:** the loader reports zero samples or the run stops immediately.

**Likely causes:**
- the directory has no top-level `jpg` or `png` files
- the flist file is empty
- all matching files live only in nested subdirectories

**Fix:**
- use the recursive flist builder
- confirm the dataset contains readable image files
- check that the flist is not just a directory listing placeholder

## Single-entry flist
**Symptom:** a text flist has exactly one path and the dataset breaks during loading.

**Likely causes:**
- the flist was generated from a one-image directory
- the list was manually edited down to one line

**Fix:**
- prefer a directory or multi-line text flist
- if a one-item dataset is intentional, treat it as a direct image path rather than a one-line text list
- regenerate the list and verify that it contains more than one entry

## Mask mismatch
**Symptom:** mask indices do not line up or the masked region is wrong.

**Likely causes:**
- `MASK=6` is active in test mode, but the mask list order does not match the image list order
- `MASK=4` or `MASK=5` is set without supplying an external mask list
- mask files are not binary or contain the wrong foreground convention

**Fix:**
- keep test image and mask lists in the same sorted order
- supply an external mask flist whenever the mask mode mixes in external masks
- store masks as clean foreground/background rasters and let the loader threshold them after resize

## External edge mismatch
**Symptom:** edge conditioning appears shifted, random, or index errors occur.

**Likely causes:**
- `EDGE=2` is enabled but the edge flist order does not match the image flist order
- the edge list is shorter than the image list
- the edge files are not aligned with the intended image size

**Fix:**
- build image and edge lists from the same ordering rule
- keep one edge entry per image entry
- use the validator before launching a run

## Deprecated image stack guidance
**Symptom:** the runtime model fails on image loading or resizing in a modern environment.

**Likely causes:**
- the legacy image-loading stack expected by EdgeConnect is unavailable
- a newer SciPy stack removed the old image helpers the runtime code expects

**Fix:**
- use a compatible legacy image-processing environment for the model runtime
- keep data-preparation work separate from model execution
- do not assume a successful flist build implies the training or test pipeline can decode images

## Config path confusion
**Symptom:** a flist path exists, but the model still cannot see it.

**Likely causes:**
- the config uses a relative path that only exists relative to the config file directory
- the loader resolves relative paths from the current working directory instead

**Fix:**
- prefer absolute paths for datasets and masks
- or run the model from the same base directory used when the paths were written
