---
name: model-ops-interpretability
description: "Guides StellarGraph saved-model loading, custom Keras layers,
  calibration, ensembles, saliency and integrated gradients, randomness
  utilities, plotting, and optional Neo4j connector workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model Operations and Interpretability

Use this sub-skill for operational tasks around StellarGraph models after or
around training: saved-model loading, probability calibration, ensembles,
interpretability, plotting/history, random seeds, and optional Neo4j connector
workflows.

## Read first

- [`references/operations.md`](references/operations.md) for
  `custom_keras_layers`, calibration, ensembles, history plotting, and seed
  utilities.
- [`references/interpretability.md`](references/interpretability.md) for GCN/GAT
  saliency and integrated-gradient workflows.
- [`references/neo4j.md`](references/neo4j.md) for optional Neo4j connector
  classes, service requirements, ID/features properties, and warnings.
- [`references/troubleshooting.md`](references/troubleshooting.md) for saved
  model, calibration/ensemble, saliency, TensorFlow, and Neo4j failures.
- [`scripts/calibration_smoke.py`](scripts/calibration_smoke.py) for a safe tiny
  calibration smoke.

## Route here when the user asks to

- load a Keras model containing StellarGraph custom layers;
- calibrate model outputs with `TemperatureCalibration`, `IsotonicCalibration`,
  expected calibration error, or reliability diagrams;
- build `Ensemble` or `BaggingEnsemble` wrappers;
- explain node/edge importance with GCN/GAT saliency maps or integrated
  gradients;
- check reproducibility utilities such as random seeds;
- use `Neo4jStellarGraph`, `Neo4jStellarDiGraph`, or Neo4j GraphSAGE generators.

## Route elsewhere

Core model training still belongs to the owning workflow route:

- node models: [`../node-classification-gnns/SKILL.md`](../node-classification-gnns/SKILL.md);
- link prediction/KG: [`../link-prediction-kg/SKILL.md`](../link-prediction-kg/SKILL.md);
- embeddings: [`../embedding-workflows/SKILL.md`](../embedding-workflows/SKILL.md);
- graph/time-series: [`../graph-time-series-workflows/SKILL.md`](../graph-time-series-workflows/SKILL.md).

## Operating workflow

1. Identify the operational surface: saved model, probability outputs,
   uncertainty/ensemble, saliency, or Neo4j-backed graph access.
2. Verify package/TensorFlow import with the root diagnostic if the environment
   is suspect.
3. For saved models, pass `stellargraph.custom_keras_layers` as Keras
   `custom_objects`.
4. For calibration, use logits or probabilities with the shapes required by the
   calibration class; validate with a tiny smoke before applying to model
   outputs.
5. For saliency, keep generator sparse/dense settings consistent with the model
   and use node indices/classes that exist.
6. For Neo4j, confirm `py2neo`, service reachability, ID property, feature
   property, and uniqueness constraints before expecting model generators to
   work.

## Safe check

```bash
python sub-skills/model-ops-interpretability/scripts/calibration_smoke.py --help
python sub-skills/model-ops-interpretability/scripts/calibration_smoke.py
```
