# Evaluation troubleshooting

## `weights` or `data` does not exist

The evaluator checks both inputs before it can score a split.

Recovery:

- Resolve the paths from the repository root.
- Make sure the checkpoint name is correct.
- Make sure the dataset YAML still points to live split files.

## Image-size mismatch

Evaluation uses the same stride rules as the model builder.

Recovery:

- Round the image size to a compatible value.
- Keep the evaluation image size aligned with the run you want to compare against.

## `pycocotools unable to run`

The JSON path is optional and needs the COCO API package.

Recovery:

- Install the optional dependency if you need the COCO summary.
- Otherwise, rely on the non-JSON metric output.

## Empty or malformed split

If the validation or test split resolves to nothing, the metrics are not meaningful.

Recovery:

- Inspect the dataset YAML and the split source.
- Use the data-preparation helper first.

## Unexpectedly low AP

Low AP can come from bad labels, a class-count mismatch, or a checkpoint that simply was not trained for the target dataset.

Recovery:

- Verify the labels and class names.
- Confirm that the checkpoint matches the dataset.
- Compare with a simpler validation split before blaming the evaluator.

## `save_txt` output confusion

The evaluator can write text output and COCO JSON at the same time.

Recovery:

- Treat the evaluation output directory as scratch space.
- Check whether you actually asked for `save_txt` before looking for text files.
- Remember that `study` produces a different output shape than a normal `val` run.
