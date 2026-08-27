# Classical Algorithms Troubleshooting

## Purpose

Read this when a classical-algorithm explanation, comparison, or code snippet needs caveats. It preserves the ML Glossary source limits and common algorithm-selection mistakes.

## Common mistakes

| Symptom | Likely issue | Recovery |
| --- | --- | --- |
| User expects KNN to train a parametric model | KNN is instance-based/lazy learning. | Explain that KNN stores examples and predicts by neighbor lookup; there are no learned weights in the simple version. |
| KNN result is dominated by one feature | Feature scales differ. | Normalize/standardize features before distance-based methods. |
| User asks for the best tree split criterion universally | Criteria depend on algorithm and data. | Compare information gain, gain ratio, and Gini; avoid claiming one is always best. |
| User treats random forest and boosting as the same | Both are ensembles, but training differs. | Random forests train many trees in parallel-ish on resampled/randomized data; boosting trains learners sequentially to focus on mistakes. |
| User expects SVM kernels to literally add a hand-built feature | Kernel trick is implicit. | Explain the feature-space intuition without requiring explicit transformation. |
| User asks for full clustering guide from repo | Source clustering page was placeholder. | Provide a concise starter and label deeper detail as beyond original repo coverage. |
| User asks for modern scikit-learn code | Repo snippets are educational and old. | Give modern code only if useful, clearly labeled as external modern practice rather than source-derived API. |

## Legacy source-code caveats

- `code/knn.py` was small and safe enough to adapt. Use `../scripts/knn_demo.py` as the runnable version.
- `code/decision_tree.py`, `code/id3_decision_tree_simple.py`, and `code/random_forest_classifier.py` were useful evidence for tree concepts, but not polished package APIs.
- Several snippets used old style or incomplete imports. Do not ask future users to run original code files.
- Logistic-regression source snippets belong conceptually to basics/math and had Python 2 syntax in the original lineage.

## Documentation caveats

- For algorithm entries, begin with the prediction problem and intuition before formulas.
- Include a minimal list of strengths and weaknesses; avoid long implementation dumps in the main glossary page.
- Use cross-references: logistic regression → basics/math; neural-network classifiers → neural-networks; datasets/libraries → resource catalog.
- If adding a code example to live docs, prefer a tiny self-contained snippet or pseudocode. Large examples should be linked as external references or converted into separate maintainable files.

## Selection caveats

- Interpretability vs performance: single trees are easier to explain; ensembles usually perform better but are less transparent.
- Distance methods need scaling and suffer in high dimensions.
- SVMs can work well for medium-size feature spaces but kernel/regularization choices matter.
- Lasso can zero coefficients; ridge shrinks but keeps all coefficients.
- Boosting can overfit noisy data if allowed too much complexity.
- RL should not be suggested for ordinary supervised classification/regression; use it when there is sequential decision-making and rewards.

## Safe verification

For a quick KNN educational check, run:

```bash
python sub-skills/classical-algorithms/scripts/knn_demo.py
```

This checks the bundled demo only. It does not execute original repo files, project tests, lint, or formatters.
