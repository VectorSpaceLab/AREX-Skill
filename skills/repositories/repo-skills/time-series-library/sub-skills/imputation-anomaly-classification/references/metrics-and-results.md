# Metrics and Results for Imputation, Anomaly Detection, and Classification

## Imputation

The imputation experiment stores predictions, truths, and masks, then computes metrics only over masked values:

```text
results/<setting>/metrics.npy  # [mae, mse, rmse, mape, mspe]
results/<setting>/pred.npy
results/<setting>/true.npy
results/<setting>/mask.npy
result_imputation.txt
```

`test_results/<setting>/` contains PDF visualizations where masked positions are filled with model predictions.

Interpretation notes:

- `mask == 0` identifies values that were hidden and evaluated.
- `mask_rate` changes the evaluation difficulty; do not compare runs with different rates as if they were identical.
- Tiny synthetic data is useful for checking plumbing but not for quality claims.

## Anomaly detection

Anomaly detection prints and appends:

```text
Threshold : <value>
Accuracy : <...>, Precision : <...>, Recall : <...>, F-score : <...>
result_anomaly_detection.txt
```

The threshold is computed from combined train/test reconstruction energy using `100 - anomaly_ratio` percentile. Predictions are then adjusted at event level by `utils.tools.adjustment`, so point-wise raw predictions can differ from reported event-level metrics.

Interpretation notes:

- `anomaly_ratio` is a prior thresholding parameter, not the true label ratio for every dataset split.
- Very small synthetic data can make precision/recall undefined or unstable.
- Reconstruction metrics depend on matching train/test scaling and channel layout.

## Classification

Classification reports accuracy and writes:

```text
results/<setting>/result_classification.txt
```

The experiment uses cross-entropy loss during training and computes accuracy from softmax/argmax over logits.

Interpretation notes:

- `model_id` determines the UEA dataset name and therefore class labels.
- Accuracy from one tiny or one-epoch run is only a smoke signal.
- Variable-length sequences are padded; padding-mask handling is part of model behavior.
