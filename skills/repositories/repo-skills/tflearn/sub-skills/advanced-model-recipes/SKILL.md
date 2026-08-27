---
name: advanced-model-recipes
description: "Choose and adapt higher-level TFLearn recipes for vision, NLP,
  sequence generation, generative models, recommenders, RL, estimators, and
  custom TensorFlow graph integration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Advanced Model Recipes

Use this sub-skill when a future agent needs to choose a TFLearn example family, adapt it to a safe local fixture, combine TFLearn with a custom TensorFlow graph, or diagnose advanced recipe-specific failures without reopening the source repository.

## Route by Need

- For recipe selection across vision, NLP, sequence generation, generative models, recommenders, RL, and estimators, read [Model Recipes](references/model-recipes.md).
- For custom TensorFlow graphs, `tflearn.TrainOp`, `tflearn.Trainer`, multiple optimizers, validation monitors, and graph collections, read [TensorFlow Integration](references/tensorflow-integration.md).
- For verified signatures and public API reminders used by these recipes, read [API Reference](references/api-reference.md).
- For downloads, optional dependencies, TensorFlow 1.x/2.x issues, expensive examples, GPU assumptions, `SequenceGenerator`, estimator, notebook, and plotting failures, read [Troubleshooting](references/troubleshooting.md).
- For a safe no-network custom graph smoke, run [`scripts/custom_trainer_smoke.py`](scripts/custom_trainer_smoke.py) with `--help` first.

## Safe Default Workflow

1. Confirm the runtime is a TensorFlow 1.x-compatible TFLearn environment. The verified CPU stack for this skill was TFLearn `0.5.0`, TensorFlow `1.15.5`, NumPy `1.18.5`, and protobuf `3.20.3`; CUDA is optional and unverified for this skill.
2. Do **not** run the original examples as validation. Many examples download datasets, open plots, run for hundreds of epochs, use Gym/Atari, or depend on TensorFlow contrib.
3. Pick a recipe from [Model Recipes](references/model-recipes.md), then replace dataset loaders with tiny in-memory arrays that preserve shape, dtype, and label assumptions.
4. Shrink units, filters, image size, text length, epochs, and batch size. Prefer `tensorboard_verbose=0`, `snapshot_epoch=False`, and temporary output directories for smoke tests.
5. Validate graph construction and one tiny fit/predict or generate path before recommending long training.

## Smoke Command

From this sub-skill directory:

```bash
python scripts/custom_trainer_smoke.py --help
python scripts/custom_trainer_smoke.py --epochs 2
```

A successful run prints an `OK custom_trainer_smoke ...` line with finite loss, accuracy, and prediction shape. If imports fail, the script prints a targeted TensorFlow/TFLearn compatibility message instead of attempting downloads.

## Boundaries

- Detailed layer and operation catalogs belong in `layers-and-ops`.
- Routine `DNN.fit`, checkpoint, save/load, callback, and TensorBoard mechanics belong in `training-and-persistence`.
- Data loading, CSV/HDF5/Dask conversion, image preloading, preprocessing, and augmentation details belong in `data-input-pipelines`.
- This sub-skill owns higher-level architecture family selection, safe recipe adaptation, optional dependency gates, `SequenceGenerator`, estimators, recommender/RL caveats, and custom TensorFlow graph integration.
