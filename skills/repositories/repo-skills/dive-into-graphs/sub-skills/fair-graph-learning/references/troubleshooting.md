# Fair Graph Learning Troubleshooting

## CUDA Is Required for Real Execution

- The dataset classes and Graphair implementation call `.cuda()` directly in multiple places.
- CPU-only import checks do not prove the training path works.
- If CUDA is unavailable, use this sub-skill only for API guidance and metric reasoning, not for claims of runtime readiness.

## Downloaded Datasets

- NBA and POKEC are fetched from external URLs during dataset construction.
- Make sure the user accepts network and disk writes before instantiating them.

## Label and Metric Mismatch

- `fair_metric` expects binary outputs, index tensors, labels, and sensitive attributes.
- If labels are not binary or the index tensor does not align with the output tensor, the parity/equality calculations become invalid.
