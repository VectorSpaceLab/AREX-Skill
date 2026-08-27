# Training troubleshooting

## `either --cfg or --weights must be specified`

Training needs at least one of the architecture or checkpoint inputs.

Recovery:

- Supply a YAML model when starting from scratch.
- Supply checkpoint weights when fine-tuning or resuming.

## Resume confusion

Resume logic uses the latest run or the explicit checkpoint path depending on the flag value.

Recovery:

- Check the `--resume` value before launch.
- Confirm the checkpoint still exists.
- Make sure the run directory is the one you intended to continue.

## Batch size vs. world size

Distributed training requires the total batch size to be divisible by the number of devices.

Recovery:

- Reduce the world size or adjust the batch size.
- Re-run the preflight helper before relaunching.

## TensorBoard import crashes early

The training module imports `SummaryWriter` at module import time. Mixed TensorBoard/TensorFlow installations can fail before the run begins.

Recovery:

- Fix the environment before retrying.
- Use the lightweight CLI check first when you only need parser validation.

## `label class exceeds nc`

Your dataset labels contain a class id that is greater than the number of classes in the dataset YAML.

Recovery:

- Fix the label set or the class count.
- Re-run the data inspection helper.
- Do not try to paper over the mismatch with training flags.

## Autoanchor warnings

The run may warn that the anchors fit poorly.

Recovery:

- Check the dataset format and the class distribution first.
- Only change anchors after the labels are clean.

## Image-size warnings

The model expects image sizes that are compatible with its stride.

Recovery:

- Let the preflight helper round the size.
- Keep the train and test sizes aligned.

## No validation split

Training can still start, but epoch-end validation will not behave the way a normal run does.

Recovery:

- Make sure the dataset YAML exposes a usable validation split.
- If you intentionally have no validation split, expect less informative run summaries.

## Memory pressure

Large image sizes, big batch sizes, and multi-scale training can exhaust GPU memory quickly.

Recovery:

- Lower the image size or batch size.
- Temporarily disable `multi_scale`.
- Check the dataset before assuming the model is at fault.
