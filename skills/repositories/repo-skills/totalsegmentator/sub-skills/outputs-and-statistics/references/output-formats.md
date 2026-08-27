# Output Formats and Post-processing

This reference covers how to consume TotalSegmentator outputs after a run has completed. It does not cover how to choose tasks, launch segmentation, or configure devices.

## Per-class NIfTI Directory

Default NIfTI output is a directory containing one binary mask per class:

```bash
TotalSegmentator -i ct.nii.gz -o seg/ --task total --report seg/run_report.json
```

Expected properties:

- Files are named with class names, for example `liver.nii.gz` or `spleen.nii.gz`.
- `run_report.json` records the produced class names in `classes` and records direct `*.nii.gz` outputs in `output_files` when `output` is a directory.
- If `--roi_subset` is used, only requested classes appear in the report class map and output expectations should be filtered accordingly.
- When `--skip_saving` is used for statistics-only runs, do not expect per-class mask files.

Use per-class masks when a downstream tool expects binary masks or when `--radiomics` is needed, because radiomics is not supported for `--ml`.

## Multilabel NIfTI

Use `--ml` to write one NIfTI file containing all labels instead of one file per class:

```bash
TotalSegmentator -i ct.nii.gz -o seg.nii.gz --ml --report seg-run-report.json
```

Expected properties:

- The `-o` value is a file path, not a directory.
- `run_report.json` has `multilabel: true`.
- `output_files` can be empty because the report only lists files when `output` is a directory.
- The segmentation image can contain a NIfTI extension header with label-id-to-class-name metadata.
- Loading that label map requires `xmltodict` in addition to `nibabel`.

Inspect a label map safely:

```bash
python scripts/inspect_multilabel_header.py seg.nii.gz --require-label spleen
```

If the extension header is missing, the file may still be a valid labeled image, but the helper cannot recover class names from the header. Route to capability discovery for the selected task’s class map and check that the run report matches the file.

## Probability Outputs

`--save_probabilities <path.npz>` writes softmax probabilities for experienced users:

```bash
TotalSegmentator -i ct.nii.gz -o seg/ --task lung_nodules --save_probabilities probs.npz
```

Important handling notes:

- The probability output is a NumPy `.npz` file.
- A companion `.pkl` file contains geometry information.
- Probability geometry may not be identical to the input image geometry.
- This option does not work well for the `total` task because `total` is based on multiple models.
- Treat probabilities as expert debugging or research output, not as a replacement for the final mask files.

## Radiomics Output

`--radiomics` writes `statistics_radiomics.json` next to per-class NIfTI masks. It requires `pyradiomics`, NIfTI input, and non-`--ml` output. Use `statistics.json` for simple volume/intensity tasks and radiomics only when the downstream consumer specifically needs radiomics feature families.

## Combining Existing Masks

Use `totalseg_combine_masks` to combine already-produced masks without rerunning segmentation:

```bash
totalseg_combine_masks -i seg/ -o lung.nii.gz -m lung
```

Supported modes from the CLI:

| Mode | Combined structures |
| --- | --- |
| `lung` | All five lung lobes. |
| `lung_left` | Left upper and lower lung lobes. |
| `lung_right` | Right upper, middle, and lower lung lobes. |
| `vertebrae` | Vertebra classes from the total five-part map. |
| `ribs` | Left and right ribs 1 through 12. |
| `vertebrae_ribs` | Vertebrae plus ribs. |
| `heart` | Accepted by the CLI parser, but verify behavior in the installed version before relying on it because the inspected library implementation has no explicit heart group. |
| `pelvis` | `femur_left`, `femur_right`, `hip_left`, `hip_right`. |
| `body` | `body_trunc` and `body_extremities`. |

Build a command without executing it:

```bash
python scripts/combine_masks_command.py --input seg/ --output combined-lung.nii.gz --mode lung
```

Add `--multilabel` when the combined output should be a multilabel NIfTI with a label-map extension:

```bash
python scripts/combine_masks_command.py --input seg/ --output body.nii.gz --mode body --multilabel
```

`totalseg_combine_masks` accepts either a directory of per-class masks or a single multilabel NIfTI as `-i`. When the input is multilabel, it relies on a readable label-map extension to map class names to label IDs.

## Combining Custom Masks in Python

The library function accepts either a predefined mode or a list of custom class names:

```python
from pathlib import Path
import nibabel as nib
from totalsegmentator.libs import combine_masks

combined_img = combine_masks(Path("seg/"), ["lung_upper_lobe_left", "lung_lower_lobe_left"])
nib.save(combined_img, "left-lung-custom.nii.gz")
```

For predefined CLI modes, prefer the CLI or the command-builder helper so the next agent can review the exact command before running it.

## Output Selection Guidance

- Choose per-class NIfTI when post-processing tools need separate binary masks, radiomics, or simple file-based QA.
- Choose `--ml` when saving many individual files is too slow or a downstream pipeline expects one labeled volume.
- Choose `--report` for every automated run so downstream steps can verify task, class, device, and file expectations.
- Choose `--statistics_extra` when downstream logic needs non-empty voxel counts, centroids, or bounding boxes.
- Choose `totalseg_combine_masks` when a broader anatomical region can be built from already-generated class masks.
