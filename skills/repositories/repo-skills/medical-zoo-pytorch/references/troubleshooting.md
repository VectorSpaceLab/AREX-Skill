# Troubleshooting

Use this page for cross-cutting import, dependency, backend, writer, and path
issues. Workflow-specific details live in the owning sub-skill.

## Common failures

| Symptom | Likely cause | What to do | Owner |
| --- | --- | --- | --- |
| `ImportError` while importing `lib.medzoo`, `lib.losses3D`, or `lib.visual3D_temp` | Missing optional runtime dependencies such as `torchsummary`, `torchsummaryX`, `tensorboard`, `torchvision`, `nibabel`, `scipy`, or `Pillow`. | Install the missing package(s) and rerun [scripts/smoke_repo_imports.py](../scripts/smoke_repo_imports.py). | segmentation-workflows / data-loading-preprocessing / covid-2d-classification |
| `AssertionError` from `create_model` | `args.model` is not one of the uppercase factory ids. | Use the exact model name from the segmentation route or the COVID route. | segmentation-workflows |
| `DENSENET2` fails during the all-model smoke | The source channel math in `DualPathDenseNet` is known to be fragile. | Keep it skipped unless you are explicitly reproducing the bug with `--include-known-broken`. | segmentation-workflows |
| `CUDA was requested but is not available` | CPU-only host or a torch build without CUDA support. | Use CPU-only smoke checks or install a CUDA-enabled torch build. | segmentation-workflows / data-loading-preprocessing / covid-2d-classification |
| `save_checkpoint` writes files in a surprising place | The API expects a directory path and derives filenames from that directory name. | Pass a dedicated checkpoint directory, not a file path. | segmentation-workflows |
| TensorBoard files appear in an odd directory | `TensorboardWriter` concatenates `log_dir` strings directly. | Use a simple sandbox path and verify the `save` directory before logging. | segmentation-workflows |
| `find_crop_dims` or `non_overlap_padding` behaves badly on odd shapes | The inference helper expects dimensions that tile cleanly. | Pad or crop to a divisible shape before running the helper. | segmentation-workflows |
| `load_medical_image` or `create_sub_volumes` cannot find files | Dataset folders, file extensions, or glob patterns do not match the expected layout. | Check the dataset layout in the data-preprocessing route before debugging deeper. | data-loading-preprocessing |
| A paired augmentation changes shape or crashes on labels | The augmentation operator expects a real label volume or uses a reshape-prone transform. | Pass a label map and use the synthetic smoke script to confirm the operator behavior. | data-loading-preprocessing |
| A loss returns the wrong shape or a tuple is unpacked incorrectly | The target tensor shape or the `classes` count does not match the criterion contract. | Re-read the loss route and match the target rank to the documented return type. | losses-and-metrics |
| `COVIDxDataset` or `CovidCTDataset` raises path/manifest errors | The manifest format or root directory does not match the expected layout. | Check the data-layout notes in the COVID route and verify the manifest entries are relative paths where required. | covid-2d-classification |
| `CovidNet` raises `NameError: pepx` | The constructor still uses the source typo instead of `PEPX`. | Treat it as a known source caveat and use the guidance in the COVID route. | covid-2d-classification |
| `CNN` tries to download pretrained weights | The torchvision wrapper uses `pretrained=True`. | Avoid network-backed smoke runs and keep the bundled COVID smoke synthetic-only. | covid-2d-classification |

## Quick recovery checklist

1. Run the root smoke script to separate import/dependency problems from
   workflow problems.
2. Open the owning sub-skill for the failing route.
3. Use the synthetic smoke script in that sub-skill before switching to real
   data.
4. If the failure is data-shaped, fix the layout or manifest first.
5. If the failure is backend-shaped, confirm whether CPU is enough or whether a
   CUDA path is required.
