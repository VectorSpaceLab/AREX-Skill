---
name: basics-and-math
description: "Explains ML Glossary foundations including glossary terms,
  calculus, linear algebra, gradient descent, linear regression, logistic
  regression, notation, and loss bridges."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Basics and Math

Use this sub-skill for foundational ML Glossary tasks: beginner definitions, formula explanations, regression walkthroughs, gradient descent, calculus/linear-algebra notation, loss-function bridges, and logistic-vs-linear regression comparisons.

## Read when

- The user asks for a concise glossary definition or beginner-friendly explanation.
- The task mentions linear regression, logistic regression, sigmoid, decision boundary, MSE, log loss, gradient descent, learning rate, cost/loss, feature/label/model, bias/variance, overfitting/underfitting, train/validation/test splits, precision/recall, ROC, or confusion-matrix terms.
- The user needs formulas connected to code-like steps: derivatives, chain rule, dot products, matrix dimensions, normalizing features, and vectorized gradients.
- A documentation-maintenance task needs the correct topic owner for basics/math pages.

## Main references

- `references/topic-map.md` contains the self-contained glossary and topic map for basics/math concepts.
- `references/formula-cheatsheet.md` contains compact formulas, update rules, and script examples for regression, logistic classification, calculus, and matrix operations.
- `references/troubleshooting.md` covers common conceptual mistakes and legacy source-snippet caveats.
- `scripts/linear_logistic_demo.py` is a safe, pure-Python toy script for linear regression gradient descent and logistic-regression probability/loss demonstrations.

## Fast routing

| Task | Use |
| --- | --- |
| Define a single ML term | `topic-map.md` glossary table, then answer in one or two accessible paragraphs. |
| Explain why gradient descent uses derivatives | `formula-cheatsheet.md` sections on derivatives, gradients, MSE, and update rules. |
| Connect linear regression to neural-network weighted inputs | `formula-cheatsheet.md` linear model notes, then cross-link to `../neural-networks/SKILL.md`. |
| Explain sigmoid/logistic regression/classification threshold/log loss | `topic-map.md` logistic-regression section and `formula-cheatsheet.md` log-loss section. |
| Help rewrite old Python 2 regression snippets | Use `linear_logistic_demo.py` as the runnable replacement and `troubleshooting.md` for caveats. |
| Explain precision vs recall, FPR/TPR/ROC, specificity | `topic-map.md` glossary and evaluation metrics section. |

## Workflow for answers

1. Start from the user's knowledge level. The repo's preferred style is concise and visual; use intuition before formulas.
2. Define the terms and variables before using symbols.
3. If formulas are requested, show the formula and then explain each term in words.
4. If code is requested, prefer the bundled pure-Python demo or a short self-contained snippet. Do not point to original source files.
5. If the topic crosses into neural-network activations, losses, backpropagation, or optimizers, route to `../neural-networks/SKILL.md` after explaining the basics bridge.
6. If the topic is a classical algorithm beyond logistic regression, route to `../classical-algorithms/SKILL.md`.

## Boundaries

This sub-skill owns:

- General glossary vocabulary.
- Calculus and linear algebra needed for ML explanations.
- Linear regression, multivariable linear regression, gradient descent, and logistic regression.
- Foundational loss/evaluation terms used by both classical and neural workflows.

Route elsewhere:

- Decision trees, KNN, random forests, boosting, SVM, clustering, and RL algorithm comparisons → `../classical-algorithms/SKILL.md`.
- Neural-network layers, activations as layer components, forward/backpropagation, optimizers, regularization, and architectures → `../neural-networks/SKILL.md`.
- Datasets, libraries, papers, courses, blogs, applications → `../../references/resources-catalog.md`.
- RST/Sphinx maintenance → `../../references/site-maintenance.md`.

## Quality checks

- Keep beginner answers accurate but not overly formal.
- Warn when source examples were legacy/pseudocode rather than runnable Python 3.
- Separate regression output types: linear regression predicts continuous values; logistic regression estimates probabilities and maps them to classes.
- Do not describe MSE as ideal for logistic regression; the repo explicitly uses cross-entropy/log loss because sigmoid plus MSE is non-convex and can have poor minima.
