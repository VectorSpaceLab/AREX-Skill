---
name: machine-learning-legacy
description: "Guides SimpleCV legacy classifier wrappers, feature extractors,
  Orange optionality, and safe ML workflow adaptation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Legacy Machine Learning

Use this sub-skill when a task asks about SimpleCV's bundled classifier wrappers or feature-extractor-based image classification examples.

## Read first

Read `references/workflows.md` for feature-extractor, classifier, and example-adaptation patterns.
Read `references/troubleshooting.md` for Orange dependency, dataset layout, feature mismatch, and network-example issues.
Read the root `../../references/api-reference.md` for verified classifier constructor signatures.
Run `scripts/ml_recipe.py --help` for a finite dry-run feature extraction helper.

## Use this for

- `KNNClassifier`, `NaiveBayesClassifier`, `TreeClassifier`, and `SVMClassifier`.
- `FeatureExtractorBase` implementations and bundled extractors such as hue, edge histogram, morphology, Haar-like, and bag-of-features extractors.
- Training/testing workflows that organize image classes as directories or `ImageSet` objects.
- Save/load and feature-vector compatibility planning.
- Adapting the original nuts-vs-bolts and color-clustering examples without network downloads.

## Route elsewhere

- Image preprocessing before extracting features → `../image-processing-basics/SKILL.md`.
- Blob/keypoint/feature geometry used as classifier inputs → `../feature-detection/SKILL.md`.
- Live camera capture or display loops → `../acquisition-display-shell/SKILL.md`.
- Segmentation-based object isolation before classification → `../segmentation-tracking/SKILL.md`.

## Critical compatibility note

The primary SimpleCV classifier wrappers are legacy Orange-backed wrappers. If `SimpleCV.base.ORANGE_ENABLED` is false, the classes may import but training/classification is not usable until Orange is installed.

Do not promise a full classifier run unless Orange is verified or the user accepts a dry-run feature extraction plan.

## Core workflow

1. Choose or implement feature extractors with `extract(img)`, `getFieldNames()`, and `getNumFields()`.
2. Build training data as one directory or `ImageSet` per class.
3. Keep class names aligned with image collections.
4. Train with the selected classifier wrapper only after Orange is available.
5. Save the classifier only after feature extractors and training data are stable.
6. Use the same feature extractors and field order for classification and testing.

## Safe adaptation pattern

Original ML examples may download datasets or use displays. Replace them with a dry-run feature table first:

```bash
python sub-skills/machine-learning-legacy/scripts/ml_recipe.py --output /tmp/simplecv-features.tsv
```

Then, if Orange is available and the user needs SimpleCV's classifier wrappers, train on a small local image set.

## Important decisions

- If the task is modern scikit-learn only, use SimpleCV only for image/feature extraction and keep the classifier outside this sub-skill.
- If the user asks for `SVMClassifier`, check Orange before exposing kernel properties.
- If feature extractors return `None`, the classifier silently skips or bails; validate feature extraction independently.
- Network examples require explicit approval and local datasets for reproducible checks.

## Verification hooks

Good final checks include the bundled dry-run feature extraction script, optional shape-context tests, and any small local classifier test that proves Orange availability. The original nuts-vs-bolts example is skip-network unless the dataset is already local and approved.
