# Workflow Map

## Purpose

Read this when you need to decide which Alibi route to follow before opening a focused sub-skill.

## Package-level flow

1. Identify the workflow family from the user's wording.
2. Check `references/optional-dependencies.md` if the user mentions SHAP, TensorFlow, Torch, Ray, or a MissingDependency placeholder.
3. Use the matching sub-skill for the detailed workflow, script, and troubleshooting guidance.
4. Run the bundled smoke script for that family when a quick CPU check is enough.

## Route map

| Task family | Open this entry point | Typical objects |
| --- | --- | --- |
| Package overview, install, extras, or task routing | `alibi/SKILL.md` | package import, extras, smoke helpers |
| Global tabular explanations | `alibi/sub-skills/global-tabular-explanations/SKILL.md` | ALE, PartialDependence, TreePartialDependence, PartialDependenceVariance, PermutationImportance |
| Anchors on tabular, text, or image inputs | `alibi/sub-skills/anchors-local-explanations/SKILL.md` | AnchorTabular, AnchorText, AnchorImage |
| SHAP or gradient attribution | `alibi/sub-skills/attribution-and-shap/SKILL.md` | KernelShap, TreeShap, IntegratedGradients |
| Counterfactuals and similarity | `alibi/sub-skills/counterfactuals-and-similarity/SKILL.md` | Counterfactual, CEM, CounterfactualProto, CounterfactualRL, GradientSimilarity |
| Confidence, prototypes, persistence | `alibi/sub-skills/confidence-prototypes-utilities/SKILL.md` | TrustScore, LinearityMeasure, ProtoSelect, load_explainer, save_explainer |

## Common input conventions

- Tabular explainers expect `numpy.ndarray` inputs with shape `(n_samples, n_features)`.
- Anchor text explainers expect batches of raw text, typically `List[str]`.
- Anchor image explainers expect a single image with shape `(height, width, channels)`.
- Most methods need a predictor that returns `numpy` outputs and accepts batched input.
- Save/load helpers require a predictor to be passed again when reloading explainers.

## Read the right reference file next

- Use the sub-skill `references/workflows.md` for the concrete step-by-step workflow.
- Use the sub-skill `references/troubleshooting.md` when a call fails.
- Use `scripts/check_optional_backends.py` when an optional export appears to be missing.
