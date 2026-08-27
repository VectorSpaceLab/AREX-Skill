# Evaluation troubleshooting

- **Metric shape exception:** print shapes and dtypes; ensure labels and
  probabilities have the same sample order. Use binary for 1-D binary outputs
  and multilabel for aligned 2-D label matrices.
- **ROC-AUC/PR-AUC undefined:** a split contains one class or no valid labels.
  Fix the split/report the limitation; do not add fabricated negatives.
- **Threshold disagreement:** state the threshold and whether it was selected
  on validation data. Keep raw probabilities for calibration/ranking.
- **Calibration leakage:** calibration and test rows/patients overlap. Rebuild
  the protocol with a separate calibration partition and verify IDs.
- **Unexpected ECE:** inspect probability range, bin count, adaptive versus
  equal-width policy, and whether the metric receives `(probability, label)` in
  the expected order.
- **Explanation failure:** model lacks gradients, target is not differentiable,
  preprocessing was not retained, or dimensions do not map back to fields. Use
  a tiny differentiable fixture and verify the method's required interface.
- **Attribution overclaim:** an explanation score is not causality, fairness,
  or clinical utility. Pair it with perturbation checks and subgroup analysis.
