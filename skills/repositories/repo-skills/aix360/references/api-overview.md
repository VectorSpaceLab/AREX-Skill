# AIX360 API and Method Overview

## Purpose

Read this when a request names an AIX360 algorithm but does not make its task
family clear. This is a route-selection map, not a substitute for the detailed
API reference in the owning sub-skill.

## Select by explanation goal

| Goal | Representative AIX360 entry points | Route | Key contract to establish first |
|---|---|---|---|
| Local post-hoc feature attribution | `LimeTabularExplainer`, `LimeTextExplainer`, `LimeImageExplainer`; SHAP wrappers | `local-black-box` | batched model callable, classes, feature names, output shape |
| Local response/profile analysis | `GroupedCEExplainer` | `local-black-box` | scalar or selected-class prediction function and grouped features |
| Similar-example explanation | `NearestNeighborContrastiveExplainer` | `local-black-box` | fitted embedding, integer labels, query/exemplar shapes |
| Pertinent positive/negative | `CEMExplainer`, `CEM_MAFImageExplainer` | `counterfactual-and-certification` | target class, input bounds, legacy TensorFlow/Keras-compatible model |
| Actionable recourse | GLANCE components and counterfactual costs | `counterfactual-and-certification` | favorable class, actionable features, constraints, cost function |
| Certify a local explanation | `Ecertify`/`Certify` APIs | `counterfactual-and-certification` | black-box explanation function, center, sampling/query budget |
| Constrained matching | `OTMatchingExplainer` | `counterfactual-and-certification` | matching filters, marginals/order constraints, optional `otoc` dependency |
| Select representative prototypes | `ProtodashExplainer` | `interpretable-models` | candidate and target matrices with matching feature width |
| Learn sparse Boolean rules | `FeatureBinarizer`, `BooleanRuleCG`, `BRCGExplainer` | `interpretable-models` | tabular schema, binary target, solver availability |
| Learn linear/logistic rule models | `FeatureBinarizerFromTrees`, `LinearRuleRegression`, `LogisticRuleRegression`, `GLRMExplainer` | `interpretable-models` | fitted trees or binarized rules, feature names, regularization |
| Learn RIPPER rules or transform/export rules | rule-induction and TRXF APIs | `interpretable-models` | categorical/numeric schema, class labels, supported export objects |
| Compare two decision-tree models | `IMDExplainer` | `interpretable-models` | compatible feature spaces and fitted tree models |
| Learn with teaching explanations | `TED_CartesianExplainer` | `interpretable-models` | examples, labels, explanation labels, base estimator |
| Explain forecasts by conditional effects | `TSICEExplainer` | `time-series` | history length, forecast lookahead, variable/exogenous shape |
| Explain a temporal prediction with a surrogate | `TSLimeExplainer` | `time-series` | batched time-series model, relevant history, perturbation plan |
| Compute temporal integrated-gradient saliency | `TSSaliencyExplainer` | `time-series` | feature names, differentiable/gradient callable, baseline |
| Load/preprocess benchmark data | classes under `aix360.datasets` | `datasets-and-metrics` | local directory layout, download policy, optional dependencies |
| Score a local explanation | `faithfulness_metric`, `monotonicity_metric` | `datasets-and-metrics` or `local-black-box` | model callable, one sample, aligned coefficients, scalar baseline |

## Taxonomy distinctions

- **Directly interpretable** methods fit or expose a model whose decision logic
  is inspectable. Rule models, CoFrNet, and some teaching/model-differencing
  workflows belong here.
- **Post-hoc** methods explain an already-trained model. LIME, SHAP, GroupedCE,
  TSICE, TSLime, saliency, CEM, and certification generally start from a model
  callable.
- **Local** results apply to one query or neighborhood. Do not present them as
  global model behavior without aggregating and validating many cases.
- **Global** results summarize or embody broader model/data behavior, such as a
  fitted rule model or model-difference tree.
- **Counterfactual/contrastive** results describe changes, alternatives, or
  pertinent evidence. They are not the same object as attribution weights.
- **Metrics** test properties of an explanation relative to a model and input;
  they do not prove causal correctness or fairness.

## Compatibility boundary

AIX360 0.3.0 exposes algorithm-specific extras rather than one uniform runtime.
The base installation supplies NumPy, pandas, scikit-learn, and matplotlib.
Extras may pin old or mutually incompatible stacks. Inspect the chosen module
and install only its documented extra in a separate environment when needed.
The root environment checker can report module availability, but an import does
not replace a tiny workflow-specific run.
