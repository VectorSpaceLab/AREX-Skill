# Paper/model copilot contract

## Source expectations

The source should be a PDF paper or report path that the active environment can read locally. When the source is a paper, extract the problem, model family, architecture, data type, training objective, and evaluation protocol before implementing.

## Output expectations

Keep the structured experiment summary, extracted claims, generated source, sample-shape checks, evaluator command, and any deviations from the paper. If the source omits a detail, record the omission and the assumption rather than filling it in silently.

## Model-class boundaries

The copilot flow is a general model-research path. Use the finance or data-science sub-skills when the task is fundamentally a Qlib or competition workflow instead of a paper-to-model implementation task.

## Validation

A successful PDF parse or import check does not prove the model is faithful. Require at least one tiny tensor-shape or evaluator smoke check, then document any unresolved mismatch between the paper and the implementation.
