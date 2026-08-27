# Data and alignment troubleshooting

## No class directories found

`facenet.get_dataset()` only reads immediate subdirectories. A flat folder of images is not a training/classifier dataset. Create one directory per identity before alignment or training.

## Labels do not match expected identities

Labels are assigned by sorted directory order. If saved labels or classifier outputs look shifted, compare the sorted class-directory list with the class names saved alongside the classifier.

## LFW pairs report skipped images

Causes:

- `lfw_dir` is not the aligned LFW root.
- Names in the pair file do not match class directory names exactly.
- Image files use an unsupported extension; Facenet checks `.jpg` then `.png`.
- Indices in `pairs.txt` do not match zero-padded filenames such as `Name_0001.jpg`.

Use `scripts/validate_facenet_dataset.py --lfw-pairs PAIRS --lfw-dir LFW_DIR` to list missing references.

## MTCNN detects no face

Likely causes:

- raw image is too small, grayscale/corrupt, not a face, or has hard pose/occlusion;
- SciPy/OpenCV image read returned unexpected channels;
- the detector dependencies or MTCNN `.npy` weights are not importable.

Recovery:

1. Test a small representative subset.
2. Check the bounding-box log for no-box rows.
3. Increase image quality or choose a different detector if many true faces fail.
4. Do not silently train on classes with many missing aligned images.

## Multiple faces in one image

If `--detect_multiple_faces` is disabled, one face is selected by size/center. If enabled, output filenames receive suffixes for each detected face. Enable only when multiple faces per input image are intended labels; otherwise it contaminates identity folders.

## Deprecated `scipy.misc` functions

Alignment and loading scripts were written for older SciPy. If `imread`, `imresize`, or `imsave` are missing, use an older compatible SciPy or patch the runtime script to Pillow/OpenCV equivalents before executing full alignment.
