# Troubleshooting

## 1. Input shape and format problems

**Symptom:** `labels_multiannotator must be a 2D array or dataframe`

- Make sure rows are examples and columns are annotators.
- Convert long-form tables with `convert_long_to_wide_dataset` before calling the multiannotator APIs.

**Symptom:** `Labels cannot be strings`

- Convert labels to zero-indexed integer class IDs first.
- Use `format_multiannotator_labels` if your source labels are strings or mixed types.

**Symptom:** `cannot have rows with all NaN`

- Every example in the labeled table must have at least one annotation.
- Keep unlabeled examples in `pred_probs_unlabeled` for active learning instead of leaving them as all-NaN rows.

**Symptom:** `cannot have columns with all NaN`

- Every annotator column must label at least one example.
- Drop unused annotator columns before analysis.

## 2. Long-format conversion issues

**Symptom:** `convert_long_to_wide_dataset` does not give the table you expected

- Verify the input table has exactly `task`, `annotator`, and `label` columns.
- Check that each task/annotator pair is unique before pivoting.
- Use the resulting wide table directly as `labels_multiannotator`.

## 3. Probability shape and class-count mismatches

**Symptom:** `pred_probs must be a 2d array` or `use the ensemble version of this function`

- Use `(N, K)` probabilities for the single-model APIs.
- Use `(P, N, K)` probabilities for the ensemble APIs.
- Keep the same number of classes in the annotation table and the probabilities.

**Symptom:** `pred_probs must have at least X columns`

- Your classifier is missing a class that appears in the annotations.
- Re-train the classifier route so the model sees every class used by the annotators.

**Symptom:** You want to reuse a prediction array after calling the ensemble helper.

- Copy the array first; the ensemble active-learning path temp-scales the model arrays it receives.

## 4. Consensus, weights, and quality-method settings

**Symptom:** `return_weights=True` fails

- `return_weights=True` only works with `quality_method="crowdlab"` in the single-model API.
- If you want agreement-only scores, set `quality_method="agreement"` and keep `return_weights=False`.

**Symptom:** `majority vote` and `best_quality` columns differ

- That is expected when the model-aware consensus changes the label choice.
- Review the corresponding `consensus_quality_score` and `annotator_agreement` columns.

**Symptom:** The console prints a class-reduction caution

- Some classes are missing from the current consensus labels.
- This usually means the class was rare in the annotations or the model collapsed it.
- If you train a classifier on those consensus labels, it will never see the missing class unless you add it back manually.

## 5. Tie handling and reproducibility

**Symptom:** Majority vote ties resolve differently across runs

- `get_majority_vote_label` breaks ties using model probabilities, then class frequencies, then annotator-quality fallback, then random choice.
- Set a NumPy seed if you need reproducible random tie-breaking.

## 6. Output interpretation problems

**Symptom:** You do not recognize the output columns

- `label_quality` columns:
  - `consensus_label`
  - `consensus_quality_score`
  - `annotator_agreement`
  - `num_annotations`
- `detailed_label_quality` columns start with `quality_annotator_`.
- `annotator_stats` is sorted by lowest annotator quality first.

**Symptom:** `NaN` values appear in `detailed_label_quality`

- That is expected for annotator/example pairs that were not labeled.

## 7. Active-learning surprises

**Symptom:** The active-learning score is not a class probability

- The score is a relabeling priority score, not a class posterior.
- Lower scores mean the example should be annotated sooner.

**Symptom:** Labeled and unlabeled scores seem incomparable

- Compare them only when they come from the same call.
- The function is designed so labeled and unlabeled scores returned together are directly comparable.

**Symptom:** You only have one annotator

- The active-learning helper can still run in the degenerate single-annotator case.
- For ordinary single-annotator noisy-label workflows, use the classification route.

## 8. When to leave this sub-skill

- If you need the classifier training loop that supplies `pred_probs`, go to `../classification/`.
- If you need broader auditing or custom issue managers, go to `../datalab/`.
