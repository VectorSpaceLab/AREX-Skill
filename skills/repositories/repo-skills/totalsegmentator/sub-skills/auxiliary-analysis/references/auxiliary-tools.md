# Auxiliary Tool Reference

This reference covers the four TotalSegmentator auxiliary commands owned by this sub-skill. They may invoke segmentation internally and can download or load model weights, so treat them as model-running commands even though they are not ordinary segmentation entry points.

## Quick Command Builder

Use the bundled helper to construct commands without executing them:

```bash
python scripts/build_auxiliary_command.py phase -i ct.nii.gz -o contrast_phase.json --device cpu --quiet
python scripts/build_auxiliary_command.py modality -i image.nii.gz -o modality.json --normalized-intensities --device gpu:0
python scripts/build_auxiliary_command.py body-stats -i ct.nii.gz -o body_stats.json --modality ct --device cpu --model-type cnn
python scripts/build_auxiliary_command.py evans-index -i ct_skull.nii.gz -o evans_index.json --preview evans_index.png
```

The helper prints a shell-quoted command and warnings for optional dependencies, licenses, and heavyweight internal segmentation. It does not import TotalSegmentator, read images, download weights, or run inference.

## Contrast Phase: `totalseg_get_phase`

Purpose: predict CT post-injection time and map it to a contrast phase.

Typical command:

```bash
totalseg_get_phase -i ct.nii.gz -o contrast_phase.json -d cpu -q
```

Flags and behavior:

| Flag | Meaning |
| --- | --- |
| `-i <path>` | CT input file. Supported suffix handling is `.nii.gz`, `.nii`, or `.zip` for DICOM. |
| `-o <path.json>` | Required output JSON path. |
| `-m <classifier>` | Optional classifier pickle path; otherwise the packaged contrast-phase classifier is used. |
| `-s <statistics.json>` | Optional existing statistics JSON. When provided, the tool skips the initial fast TotalSegmentator statistics run but may still run the head/neck model if brain volume indicates head/neck vessels are needed. |
| `-d/--device cpu|gpu|gpu:N|mps` | Device used for internal TotalSegmentator calls. |
| `-q` | Suppress progress/result printing. |
| `--call_via_subprocess` | Run internal TotalSegmentator models through the CLI instead of Python API; useful in hosted UI/runtime contexts where direct API calls are problematic. |
| `--debug` | Print additional debug information on errors. |

Model method distilled from docs/source:

- Runs or reuses TotalSegmentator statistics for liver, pancreas, bladder, gallbladder, heart, aorta, inferior vena cava, portal/splenic vein, iliac vessels, pulmonary vein, brain, colon, and small bowel.
- If the brain volume is present, it also computes head/neck vessel statistics for internal carotid and jugular veins.
- Uses median intensities as features for a five-model XGBoost ensemble.
- Produces `native`, `arterial_early`, `arterial_late`, or `portal_venous`; delayed scans are folded into low-probability `portal_venous` behavior in the current implementation.

Output JSON shape:

```json
{
  "pi_time": -0.04,
  "phase": "native",
  "probability": 1.0,
  "pi_time_min": -0.13,
  "pi_time_max": 0.14,
  "stddev": 0.0993
}
```

Interpretation rules:

- Low `stddev` means the five ensemble models agree more closely.
- `probability` reflects closeness of the predicted post-injection time to the ideal range for the mapped phase, not a full calibrated clinical probability.
- Use `-s <statistics.json>` only when the statistics were produced with compatible TotalSegmentator settings and contain all required ROI intensity keys.

## Modality: `totalseg_get_modality`

Purpose: classify an image as CT or MR.

Typical commands:

```bash
totalseg_get_modality -i image.nii.gz -o modality.json -q
totalseg_get_modality -i normalized_image.nii.gz -o modality.json -n -d cpu -q
```

Flags and behavior:

| Flag | Meaning |
| --- | --- |
| `-i <path>` | Input CT/MR image. |
| `-o <path.json>` | Required output JSON path. |
| `-d/--device cpu|gpu|gpu:N|mps` | Used only for normalized-intensity ROI mode, because that mode runs internal segmentation. |
| `-q` | Suppress progress/result printing. |
| `-n` | Use normalized intensities within ROIs. This is slower because it runs TotalSegmentator with `task="total_mr"`, `fast=True`, `statistics=True`, and normalized-intensity statistics. |

Model method distilled from source:

- Default mode uses global image intensity features: mean, standard deviation, min, and max. It is fast but assumes original intensity scale is still meaningful.
- `-n` mode uses ROI median intensities from brain, esophagus, colon, spinal cord, scapulae, femurs, hips, gluteus maximus, autochthon, and iliopsoas muscles; use it when images have been normalized and global HU-like values are unreliable.
- Both modes use five XGBoost folds and report the ensemble mean as a CT/MR class with confidence.

Output JSON shape:

```json
{
  "modality": "ct",
  "probability": 0.97
}
```

Interpretation rules:

- If the input was heavily preprocessed or normalized, prefer `-n` and budget for internal segmentation time.
- If the image is DICOM rather than NIfTI, route input-layout questions to the DICOM/formats sub-skill first; this CLI expects a direct image path.

## Body Stats: `totalseg_get_body_stats`

Purpose: predict body weight, size, age, sex, BMI, and body surface area from CT or MR images.

Typical commands:

```bash
totalseg_get_body_stats -i ct.nii.gz -o body_stats.json -m ct -d cpu -q
totalseg_get_body_stats -i mr.nii.gz -o body_stats.json -m mr --only_weight -d gpu:0 -q
totalseg_get_body_stats -i ct.nii.gz -o body_stats.json -m ct --model_type xgboost -l LICENSE_NUMBER -d gpu -q
```

Flags and behavior:

| Flag | Meaning |
| --- | --- |
| `-i <path>` | CT/MR input file. Supported suffix handling is `.nii.gz`, `.nii`, or `.zip` for DICOM. |
| `-o <path.json>` | Optional output JSON path; if omitted, results print to stdout. Use an explicit path for automation. |
| `-m ct|mr` | Required modality argument; do not confuse this with the phase command's model-file flag. |
| `-mf <path>` | Model base path for XGBoost or experiment directory for CNN. |
| `-mt/--model_type cnn|xgboost` | Prediction backend. Default is `cnn`. XGBoost is slower/lower-accuracy baseline or fallback. |
| `--only_weight` | Predict only weight and skip size, age, sex, BMI, and BSA. |
| `-d/--device cpu|gpu|gpu:N|mps` | Device for CNN and internal segmentation. CLI default is CPU. |
| `-f/--fold 0..4` | Use one fold; omit for the five-fold ensemble. |
| `-q` | Suppress progress/result printing. |
| `-l/--license_number <key>` | License number for licensed tasks such as `tissue_types` used by XGBoost feature extraction. |
| `--call_via_subprocess` | Run internal TotalSegmentator models through subprocesses instead of Python API. |
| `--debug` | Print CNN input tensor shape and additional debug information. |

CNN method distilled from docs/source:

- Default body-stats backend is a five-fold CNN ensemble using EfficientNetV2-S-style 2D models.
- Separate CT/MR and target-specific models are used for `weight`, `size`, `age`, and `sex`.
- The image is canonicalized, resampled to 2 mm spacing, sliced, normalized, and center cropped/padded to CT 240x240 or MR 210x210 pixels.
- CNN inference requires PyTorch and `timm`; checkpoint loading can require `monai` metadata support.

XGBoost method distilled from docs/source:

- Runs TotalSegmentator feature extraction from organ, vertebra, and tissue-type segmentations.
- CT lung lobes are combined into `lung_left` and `lung_right` features.
- For MR, a separate `vertebrae_mr` model supplies vertebra statistics.
- Tissue-type features use `subcutaneous_fat`, `torso_fat`, and `skeletal_muscle` slices at vertebral levels; the underlying tissue-type tasks require a license.
- Uses volume and median intensity features with XGBoost models; it is documented as slower and lower accuracy than CNN, but useful as a fallback.

Output JSON shape:

```json
{
  "weight": {"value": 76.99, "min": 75.58, "max": 78.43, "stddev": 1.2121, "unit": "kg"},
  "size": {"value": 177.12, "min": 172.84, "max": 180.58, "stddev": 2.5367, "unit": "cm"},
  "age": {"value": 47.54, "min": 26.67, "max": 55.85, "stddev": 10.6838, "unit": "years"},
  "sex": {"value": "M", "probability": 0.7447, "stddev": 0.2041, "unit": null},
  "bmi": {"value": 24.54, "unit": "kg/m^2"},
  "bsa": {"value": 1.95, "unit": "m^2"}
}
```

Interpretation rules:

- Use the ensemble `stddev` as an uncertainty hint; high disagreement needs manual review.
- Do not use for patients younger than 16 years; the model was not trained on children.
- Larger field of view gives better predictions. Whole abdomen+thorax is expected to perform better than pelvis-only or narrow-FOV scans.
- BMI and BSA are derived from predicted weight and height, not directly measured values.
- For XGBoost, plan license setup before running because tissue-type segmentation is license-gated.

## Evans Index: `totalseg_evans_index`

Purpose: calculate Evans index from a skull/brain CT and save both numeric JSON and a preview PNG.

Typical command:

```bash
totalseg_evans_index -i ct_skull.nii.gz -o evans_index.json -p evans_index.png
```

Flags and behavior:

| Flag | Meaning |
| --- | --- |
| `-i/--ct_img <path>` | CT input path. Supported suffix handling is `.nii.gz`, `.nii`, or `.zip` for DICOM. |
| `-o/--output_file <path.json>` | Required JSON output path. |
| `-p/--preview_file <path.png>` | Required preview PNG path; use it to check whether the measurement slice and masks are plausible. |
| `-v/--verbose` | Print detailed progress. |

Method distilled from docs/source:

1. Run internal TotalSegmentator models for brain+skull and ventricle parts.
2. Rigidly register brain/skull/ventricle masks to a CT brain atlas.
3. Fill cranial cavity from brain+skull, keep large structures, and isolate frontal horns.
4. Compute maximum left-right frontal horn and brain diameters on the relevant slice.
5. Write JSON plus a PNG overlay. The raw returned brain mask is not the dilated cranial-cavity mask.

Output JSON shape:

```json
{
  "evans_index": 0.281,
  "brain_volume_ml": 1180.4,
  "ventricle_volume_ml": 32.1,
  "ventricle_brain_ratio": 0.027
}
```

If segmentation is empty or the input does not contain the full brain, numeric fields can be `null` and the PNG contains an explanatory empty-result message.

Dependency notes:

- Requires `antspyx` importable as `ants` and `blosc` before it starts the calculation.
- Uses registration utilities internally, so failures may surface as `ants`/registration errors rather than TotalSegmentator CLI argument errors.
- Uses internal `TotalSegmentator` subprocess calls and can be expensive; do not use it as a quick discovery command.

## Validation Checklist

After any auxiliary run:

- Confirm the output JSON path exists, is valid JSON, and has the expected top-level keys for the selected tool.
- For phase/body-stats ensemble outputs, inspect `stddev` before using the value downstream.
- For Evans index, inspect the PNG overlay and treat `null` JSON values as a failed/non-applicable case.
- For commands that internally run segmentation, preserve the command, device, input, output, and optional model/license choices in pipeline metadata.
- If the command failed before model execution, use [`troubleshooting.md`](troubleshooting.md) before rerunning with broader dependencies or expensive settings.
