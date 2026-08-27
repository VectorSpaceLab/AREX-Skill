# Training troubleshooting

## Training exits before the first batch

Check:

- the dataset is not empty;
- class directories contain enough images;
- the selected model definition module imports successfully;
- the batch size and triplet grouping constraints are valid;
- the learning-rate schedule contains an epoch value usable at the current epoch.

## Learning-rate schedule causes early stop

`train_softmax.py` treats a schedule value of `-` or a non-positive learning rate as a stop condition in some branches. Verify the schedule file format before starting a long run.

## `ValueError: Invalid optimization algorithm`

The optimizer must be one of `ADAGRAD`, `ADADELTA`, `ADAM`, `RMSPROP`, or `MOM`.

## `tf.contrib` or `slim` import failure

Use a TensorFlow 1.x environment. These scripts depend on `tensorflow.contrib.slim` and queue/session behavior removed in TensorFlow 2.x.

## Checkpoint save or restore problems

Common causes:

- model directory has no `.meta` file;
- checkpoint state points to a missing file;
- user passed a frozen graph where a checkpoint directory was expected;
- pretrained model path points to a different embedding size or architecture.

Route to the model-export sub-skill when the issue is path/format related rather than training logic.

## LFW validation during training fails

If `--lfw_dir` is set, training scripts call the same LFW evaluator used by the evaluation sub-skill. Pair-file, batch-size, and fixed-standardization issues are usually the reason.

## Memory pressure

Reduce `--batch_size`, `--people_per_batch`, `--images_per_person`, or `--nrof_preprocess_threads` before trying to debug model math.
