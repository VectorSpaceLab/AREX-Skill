# Troubleshooting

## Common failure modes

### Caption eval fails in the COCO helper

- Make sure the prediction file is COCO-format JSON.
- Confirm that `pycocotools` and `pycocoevalcap` are installed.
- If SPICE complains about Java, stop short of the full metric run until Java 1.8 is available.

### VQA evaluation looks like the wrong mode

- Check whether the command is beam-search or all-candidate.
- Verify the answer-label sidecar and the selected columns.
- If the task is open-ended, beam-search is the valid fallback for evaluation.

### RefCOCO or SNLI-VE predictions are nonsense

- Re-check the prompt type and the selected columns.
- Make sure the checkpoint belongs to the same task family.
- Validate the TSV with the data-format helper before blaming the model.

### OCR output is garbled

- Confirm the BPE resources and the document/scene resizing choice.
- For Chinese OCR, check the normalization and the selected columns.
- Watch both exact-match and edit-distance metrics; one may fail before the other.

### ImageNet output is a class label mismatch

- Verify the class mapping file.
- Make sure the selected columns match the repo script.
- Use the ImageNet checkpoint for ImageNet data; other checkpoints are not interchangeable.

## Recovery order

1. Validate the input TSV.
2. Confirm the checkpoint and sidecar mapping.
3. Render the command.
4. Only then run the GPU workflow.
