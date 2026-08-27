# Facenet evaluation metrics reference

## Distance metrics

`facenet.distance(embeddings1, embeddings2, distance_metric=0)` supports:

- `0`: squared Euclidean distance (`sum((a-b)^2)`)
- `1`: angular distance derived from cosine similarity (`arccos(cosine) / pi`)

Lower distance means more similar in both cases. Do not compare thresholds between metric types.

## ROC accuracy

`facenet.calculate_roc()` cross-validates thresholds across folds. For each fold, it chooses the best threshold on the training fold and computes test accuracy, true-positive rate, and false-positive rate.

Inputs must be paired arrays: `embeddings1`, `embeddings2`, and boolean `actual_issame`.

## Validation rate at FAR

`facenet.calculate_val()` estimates validation rate at a target false accept rate (default evaluator target is `1e-3`). If training-fold FAR never reaches the target, the selected threshold becomes `0.0`.

## AUC and EER

`validate_on_lfw.py` computes AUC from FPR/TPR arrays and EER by solving `1 - x - TPR(FPR=x) = 0`. EER and AUC are meaningful only when the evaluated pair set has enough positive/negative pairs.

## Standardization and flips

- Fixed image standardization applies `(image - 127.5) / 128.0`.
- Per-image standardization uses TensorFlow image standardization.
- `--use_flipped_images` doubles image passes and concatenates embeddings, so batch divisibility must account for flips.

The README explicitly warns that the newer pretrained models use fixed image standardization. A mismatch can degrade accuracy even when model loading succeeds.
