# Basics and Math Troubleshooting

## Purpose

Read this when a foundational ML explanation, formula, or snippet seems confusing, inconsistent, or outdated. It captures the ML Glossary source caveats and common learner misunderstandings.

## Conceptual mistakes to catch

| Symptom | Likely issue | Correction |
| --- | --- | --- |
| User says linear regression is a classifier | Confusing regression with logistic regression. | Linear regression predicts continuous values. Logistic regression uses a linear score plus sigmoid/softmax to estimate class probabilities. |
| User asks why MSE is not used for logistic regression | Treating all losses as interchangeable. | MSE is fine for the repo's linear-regression walkthrough. For logistic regression, use cross-entropy/log loss because sigmoid plus MSE can create a non-convex optimization surface. |
| User thinks sigmoid returns a class | Skipping thresholding. | Sigmoid returns a probability-like value in `(0,1)`. A decision boundary maps that value to a class. |
| User treats accuracy as sufficient for imbalanced data | Ignoring base rates and error asymmetry. | Compare to null accuracy and discuss precision/recall/specificity/ROC. |
| User asks why gradient descent subtracts the gradient | Confusing gradient direction. | The gradient points toward steepest increase. Minimization moves in the opposite direction. |
| User asks why learning rate matters | Step-size intuition missing. | Too large can overshoot; too small can converge slowly. |
| Matrix multiplication dimensions do not line up | Confusing dot product, elementwise product, and transpose. | Check `(m,n) @ (n,k) -> (m,k)`; transpose one matrix only when that matches the intended algebra. |
| User uses `feature`, `attribute`, and `column` interchangeably | Spreadsheet vs ML vocabulary. | Attribute is the quality/column; feature is the model-ready value representation; feature vector is one row of values. |

## Legacy source-snippet caveats

The original educational code snippets were useful for teaching but not always runnable in a modern Python environment.

- `logistic_regression.py` and `logistic_regression_scipy.py` used Python 2 print syntax.
- Some snippets import `numpy` but call `np`, or refer to plotting variables without imports.
- Some doc examples are pseudocode inside RST blocks rather than complete modules.
- Logistic-regression code in the docs is best treated as explanatory unless modernized.

Use `../scripts/linear_logistic_demo.py` when the user wants executable code. It is a pure-Python runtime-owned replacement.

## Numerical stability notes

- Clip logistic probabilities before `log`: `p = min(max(p, eps), 1 - eps)`.
- Feature normalization helps gradient descent when features have very different scales.
- Bias terms can be represented separately or by adding a constant feature column of ones.
- Numerical derivatives depend on the choice of `h`; too large is inaccurate, too small can suffer floating-point cancellation.

## Documentation-maintenance notes

- When writing a glossary entry, define variables before equations.
- Put deep derivations in a math section and keep the top explanation concise.
- If a formula appears in both linear and neural contexts, explain the bridge: neural weighted input is a linear model plus activation.
- If adding a code block to a live RST page, prefer Python 3 syntax and explicit imports.

## When to route elsewhere

- If the user asks about decision-tree split criteria, KNN neighbor selection, SVM margins, boosting, or Q-learning, route to `../../classical-algorithms/SKILL.md`.
- If the user asks about backpropagation through layers, activation-function pros/cons, optimizers, dropout, CNN/RNN/GAN/VAE, or PyTorch examples, route to `../../neural-networks/SKILL.md`.
