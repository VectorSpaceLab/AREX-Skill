# Privacy tests troubleshooting

## Too few samples

### Symptom
- `run_attacks()` fails or returns empty / unstable slices.

### Likely cause
- There are too few train or test examples for the requested slice.
- The default balancing removed too much data.

### Recovery
- Use the tiny membership-inference smoke helper first.
- Reduce the slice complexity or provide more samples.

## Loss, logit, or label shape mismatch

### Symptom
- The attack constructor or attack run raises a shape error.

### Likely cause
- The model outputs and labels do not have compatible dimensions.
- A multilabel fixture was passed without `multilabel_data=True`.

### Recovery
- Check the `AttackInputData` field shapes.
- Use a small synthetic fixture and add one field at a time.

## Wrong attack signal

### Symptom
- The result looks too weak or too strong compared with expectations.

### Likely cause
- Losses were used when logits or probabilities would be more informative, or vice versa.
- The wrong `AttackType` was selected.

### Recovery
- Start with the default threshold attack.
- Add a trained attack only after the baseline works.

## Privacy report metadata confusion

### Symptom
- The report summary omits the model variant or epoch context.

### Likely cause
- `PrivacyReportMetadata` was not passed in.

### Recovery
- Supply the metadata object when the user wants report annotations.

## Keras callback issues

### Symptom
- `MembershipInferenceCallback` fails during `on_epoch_end()`.

### Likely cause
- The `(data, labels)` tuples passed as `in_train` or `out_train` do not match the model's prediction shape.
- The callback expects probabilities unless `is_logit=True` is supplied.

### Recovery
- Run the analysis once through `run_attack_on_keras_model()` before adding the callback to a long training job.
- Keep `batch_size` small enough for the callback prediction pass.

## Secret-sharer exposure issues

### Symptom
- Exposure values are strange or hard to interpret.

### Likely cause
- The toy vocabulary or reference perplexity set is too small.
- The secret set and reference set are not representative.

### Recovery
- Treat the smoke helper as an API check, not a scientific benchmark.
- Expand the fixture only after the shape path works.

## Missing optional dependencies

### Symptom
- Plotting, pandas, or sklearn imports fail.

### Likely cause
- The environment is missing a scientific-Python dependency.

### Recovery
- Reinstall the runtime requirements in a clean prefix.
- Keep the bundled smoke helpers small and dependency-light.
