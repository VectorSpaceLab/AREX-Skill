# Evaluation troubleshooting

## `Skipped N image pairs`

`lfw.get_paths()` skips a pair if either image path is missing. Validate that identity names, zero-padded indices, directory root, and `.jpg`/`.png` extensions match the pair file.

## Batch-size assertion fails

The evaluator requires `number_of_pairs * 2 * flips` to be divisible by `--lfw_batch_size`. Lower the batch size or choose one that divides the expanded image count.

## Accuracy unexpectedly low

Check:

- model path is the intended checkpoint/frozen graph;
- input images are aligned and at the expected image size;
- fixed image standardization is enabled for models that require it;
- the pair file matches the same dataset split;
- distance metric and `subtract_mean` match the comparison baseline.

## Too few pairs for folds

`KFold(n_splits=...)` needs enough pairs for the selected fold count. For tiny smoke tests, lower `--lfw_nrof_folds` to `2`; for benchmark comparisons, use the standard fold count and full pair file.

## Frozen graph tensor errors

If a `.pb` model lacks `embeddings:0`, `input:0`, or `phase_train:0`, route to the model-export sub-skill. The graph may have been frozen with different tensor names or output nodes.
