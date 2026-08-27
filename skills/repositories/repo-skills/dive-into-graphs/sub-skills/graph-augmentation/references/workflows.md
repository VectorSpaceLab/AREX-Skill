# Graph Augmentation Workflows

## Reward Model

1. Load a TU dataset.
2. Wrap it in `TripleSet` so each anchor sample gets positive and negative counterparts.
3. Train `RunnerRewardGen` to distinguish same-label and different-label graphs.

## Augmentation Generator

1. Reuse the reward generator checkpoint.
2. Train `RunnerGenerator` so the generator proposes augmentations that preserve labels.
3. Save intermediate generator states so the classifier can reuse them.

## Augmented Classifier

1. Load the trained generator checkpoint.
2. Instantiate `RunnerAugCls` with the augmentation config.
3. Train the classifier over the augmented dataset and compare 10-fold validation accuracy.

## S-Mixup

1. Prepare a TU dataset.
2. Instantiate `smixup` with a graph-matching config.
3. Run its train/test loop to mix graphs and evaluate the classifier.
