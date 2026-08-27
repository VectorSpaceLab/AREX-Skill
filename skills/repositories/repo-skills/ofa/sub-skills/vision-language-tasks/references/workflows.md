# Workflows

## Captioning

1. Prepare the caption TSV family and the COCO checkpoint.
2. Use the caption selected columns (`1,4,2` in the repo scripts).
3. Run evaluation with the caption task and beam size 5.
4. Use the bundled COCO caption helper if you need offline metric computation.

## VQA

1. Prepare the VQA TSV family and answer-label sidecar file.
2. Choose the evaluation mode explicitly: beam-search or all-candidate.
3. Keep the selected columns aligned with the repo scripts (`0,5,2,3,4`).
4. Use the task output JSON for submission or local inspection.

## RefCOCO / RefCOCO+ / RefCOCOg

1. Prepare the region-coordinate TSV family.
2. Use the correct dataset split name and checkpoint.
3. Keep the selected columns aligned with the script (`0,4,2,3`).
4. Check the max-len and beam settings if box decoding behaves oddly.

## SNLI-VE

1. Prepare the SNLI-VE TSV family and the correct checkpoint.
2. Use the selected columns from the repo scripts (`0,2,3,4,5`).
3. Choose prompt type and zero-shot settings deliberately.
4. Watch the `snli_score` metric rather than a generic text metric.

## OCR

1. Prepare OCR TSV rows and the Chinese BPE resources.
2. Verify whether the task is document-style or scene-style before launch.
3. Keep the selected columns (`0,1,2`) and the max output length aligned.
4. Compare exact-match accuracy with normalized edit distance when diagnosing errors.

## Image classification

1. Prepare the ImageNet TSV layout and the class-to-label mapping file.
2. Use the image-classification task and the selected columns (`0,2`).
3. Keep the validation subset or full validation split straight.
4. Inspect the accuracy output after generation.
