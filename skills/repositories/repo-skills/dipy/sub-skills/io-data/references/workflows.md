# Dipy IO Workflows

This reference gives safe, repeatable IO workflows. For model choice, tractography generation, registration, or full CLI parser behavior, route to the sibling sub-skills named in `SKILL.md`.

## Load A DWI And Build A GradientTable

1. Load image data and metadata:

   ```python
   from dipy.io.image import load_nifti
   data, affine, img, voxsize, axcodes = load_nifti(
       "dwi.nii.gz", return_img=True, return_voxsize=True, return_coords=True
   )
   ```

2. Read gradients:

   ```python
   from dipy.io.gradients import read_bvals_bvecs
   bvals, bvecs = read_bvals_bvecs("dwi.bval", "dwi.bvec")
   ```

3. Validate before modeling:

   ```python
   if data.ndim != 4:
       raise ValueError(f"DWI data must be 4D, got shape {data.shape}")
   if data.shape[-1] != len(bvals) or bvecs.shape[0] != len(bvals):
       raise ValueError("DWI volume count does not match bvals/bvecs")
   ```

4. Build the table:

   ```python
   from dipy.core.gradients import gradient_table
   gtab = gradient_table(bvals, bvecs=bvecs, b0_threshold=50)
   ```

5. Route the validated `data`, `affine`, `img.header`, and `gtab` to `../../reconstruction-models/` or preprocessing/tracking as needed.

## Save A Derived NIfTI Safely

- Reuse the affine from the loaded image when the derivative is in the same space.
- Reuse the source header for direct derivatives, but ensure the data shape and dtype are compatible with the intended output.
- For masks or label images, pick an explicit small integer dtype instead of relying on platform defaults.

```python
from dipy.io.image import save_nifti
save_nifti("mask.nii.gz", mask.astype("uint8"), affine, hdr=img.header, dtype="uint8")
```

## Diagnose DWI Versus bvals/bvecs Mismatch

1. Print `data.shape`, `bvals.shape`, and `bvecs.shape` after Dipy has parsed sidecars.
2. If bvecs are `(3, N)` before parsing, let `read_bvals_bvecs` normalize them to `(N, 3)`.
3. Confirm `data.shape[-1]` equals `N`. If not, identify whether the image has been split/extracted, gradients belong to another image, or the protocol contains removed volumes.
4. Check `gtab.b0s_mask.sum()` and non-b0 b-vector norms to catch threshold or normalization problems.
5. Do not trim or pad gradients silently. Create an explicit repaired sidecar only when the user confirms which volumes were removed or added.

## Construct And Round-Trip A Tiny StatefulTractogram

```python
import nibabel as nib
import numpy as np
from dipy.io.stateful_tractogram import Space, StatefulTractogram
from dipy.io.streamline import load_tractogram, save_tractogram

reference = nib.Nifti1Image(np.zeros((4, 4, 4), dtype="float32"), np.eye(4))
streamlines = [np.array([[0.5, 0.5, 0.5], [1.5, 1.5, 1.5]], dtype="float32")]
sft = StatefulTractogram(streamlines, reference, Space.RASMM)
assert sft.is_bbox_in_vox_valid()
save_tractogram(sft, "tiny.trk")
loaded = load_tractogram("tiny.trk", "same")
```

For non-TRK/TRX formats, pass a real reference instead of `"same"`. When saving converted tractograms, verify `StatefulTractogram.are_compatible(...)` before concatenating and keep `bbox_valid_check=True` for final outputs.

## Convert A Tractogram

1. Choose the input format and determine whether it carries a usable reference.
2. If the format lacks reference metadata, provide a NIfTI image/header from the same native diffusion space.
3. Load into an SFT with the desired output state:

   ```python
   from dipy.io.stateful_tractogram import Space
   from dipy.io.streamline import load_tractogram, save_tractogram

   sft = load_tractogram("bundle.tck", "reference.nii.gz", to_space=Space.RASMM)
   if not sft.is_bbox_in_vox_valid():
       raise ValueError("Streamlines do not fit the reference image")
   save_tractogram(sft, "bundle.trk")
   ```

4. For CLI conversion, use `dipy_convert_tractogram` with explicit reference and output paths, and see `../../cli-workflows/` for parser details.

## Save And Convert PAM5 Files

- Save only `PeaksAndMetrics` objects that have ndarray `peak_dirs`, `peak_values`, and `peak_indices`.
- Preserve `pam.affine` when available or pass `affine=` to `save_pam` if the object lacks it.
- Use `pam_to_niftis` when downstream tools need peak directions, values, indices, SH coefficients, or GFA as separate files.
- Use `niftis_to_pam` or `dipy_nifti2pam` when returning from separate NIfTI fields to a Dipy PAM5 bundle.

## Dataset Discovery And Fetching

Safe discovery:

```python
from dipy.workflows.io import FetchFlow
available = FetchFlow.get_fetcher_datanames()
```

CLI discovery:

```bash
dipy_fetch list
```

Download only with user intent:

```bash
dipy_fetch sherbrooke_3shell --out_dir data_folder
```

When fetch fails, distinguish network, permissions, checksum, and unknown-dataset errors before trying another dataset or path.

## IO Command Routing

| Task | Prefer |
| --- | --- |
| Inspect mixed files | `dipy_info` or `IoInfoFlow` |
| List/fetch datasets | `dipy_fetch` or `FetchFlow` |
| Split or extract image volumes | `dipy_split`, `dipy_extract_b0`, `dipy_extract_shell`, `dipy_extract_volume` |
| Convert tractogram formats | `dipy_convert_tractogram` |
| Concatenate compatible tractograms | `dipy_concatenate_tractograms` |
| Convert tensor or SH conventions | `dipy_convert_tensors`, `dipy_convert_sh` |
| Convert PAM5 and peak NIfTIs | `dipy_nifti2pam`, `dipy_pam2nifti`, `dipy_tensor2pam` |
| Perform simple image math | `dipy_math` |

For global command listing, help-probing, or translating an API recipe into a CLI invocation, use `../../cli-workflows/`.
