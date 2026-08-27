# Cosmos and Visual Augmentation

## What this workflow does

Cosmos-based augmentation transforms recorded demonstration videos to create new visual appearances while preserving the task-relevant robot motion and control structure.

## Typical phase order

1. Convert HDF5 camera recordings to MP4 files.
2. Build or edit prompt templates for the augmentation model.
3. Run the visual augmentation pass on the exported videos.
4. Convert the augmented MP4 files back into HDF5.
5. Merge original and augmented datasets when needed; the bundled `scripts/merge_hdf5_datasets.py` helper covers the simple `data/demo_*` merge case.

## Prompt generation

Prompt templates are simple JSON structures with lists of scene descriptors. The bundled `scripts/generate_cosmos_prompt.py` helper combines one random choice from each populated section into a single text prompt and supports a seed for reproducibility.

## Conversion notes

- HDF5-to-MP4 conversion should preserve the original demo ID in the output filename.
- Depth and segmentation modalities often need special handling during conversion.
- MP4-to-HDF5 conversion should keep the original non-visual episode data and replace only the visual frames.
- A merge step should preserve dataset-level environment metadata from the first input file.

## Hardware and dependency constraints

- Cosmos Transfer1-style augmentation is GPU-bound and documented for Ampere/Hopper-class hardware.
- OpenCV, h5py, NumPy, and a video codec path are needed for the conversion steps.
- This is an optional augmentation path, not a required baseline for teleoperation or core Mimic use.

## Naming and pairing rules

- Use the original demo ID in the intermediate video filename.
- Keep the camera or modality suffix stable so the round-trip pairing remains unambiguous.
- Treat missing files or malformed video names as data integrity errors rather than generic augmentation failures.
