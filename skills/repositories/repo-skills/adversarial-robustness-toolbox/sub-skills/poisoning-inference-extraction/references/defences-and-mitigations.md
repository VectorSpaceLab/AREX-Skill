# Defences and mitigations

This reference routes poisoning detectors, trigger detectors, and mitigation workflows.

## Quick chooser

| Goal | Prefer | Required signals | Main caveat |
| --- | --- | --- | --- |
| Cluster poisoned points in hidden space | `ActivationDefence` | Classifier with accessible hidden activations plus `x_train`, `y_train` | Needs a neural-network-style classifier; it is not a black-box-only detector |
| Detect outlier poisoned samples spectrally | `SpectralSignatureDefense` | Classifier with hidden activations plus `x_train`, `y_train` | You still need a train set with representation access |
| Use provenance metadata to flag suspicious points | `ProvenanceDefense` | `x_train`, `y_train`, `p_train`, optional validation data | Requires provenance labels or metadata |
| Calibrate sample removal against validation loss/accuracy | `RONIDefense` | Train set plus validation/calibration data | Needs a meaningful validation split |
| Detect / mitigate backdoors in Keras models | `NeuralCleanse` | `KerasClassifier` plus validation data | Keras-only in the verified runtime path; needs access to penultimate-layer activations for pruning/filtering |
| Abstain on suspicious inputs at inference time | `STRIP` | A classifier with `predict` and a clean validation set | Adds runtime abstention, not model repair |

## Detector and mitigation routing

### ActivationDefence

Use `ActivationDefence` when you suspect poisoned training examples and the victim exposes hidden-layer activations.

- Inputs: classifier, `x_train`, `y_train`, optional generator, optional `ex_re_threshold`.
- Typical workflow: cluster activations, analyze clusters, then evaluate the defence against known or suspected poison.
- Good when you can afford representation analysis and want a detector that separates clean vs suspicious training points.

### SpectralSignatureDefense

Use `SpectralSignatureDefense` when you want a spectral outlier pass over training activations.

- Inputs: classifier, `x_train`, `y_train`, expected poison fraction, batch size, epsilon multiplier.
- Good when you know roughly how much poison to expect.
- This is a detection-first route; it does not itself retrain the model.

### ProvenanceDefense

Use `ProvenanceDefense` when each training sample has metadata or provenance labels.

- Inputs: classifier, `x_train`, `y_train`, `p_train`, and optionally validation data.
- Best fit: data pipelines where you can tag sample origin, source, or trust level.
- This is the most natural route when the label is not the only trustworthy signal.

### RONIDefense

Use `RONIDefense` when you can score the impact of removing a suspicious point on validation performance.

- Inputs: classifier, training data, validation data, performance function, and calibration/quiz splits.
- Good when you want a data-removal policy rather than a representation-based detector.
- Expect to trade runtime for more direct performance-based filtering.

### NeuralCleanse

Use `art.defences.transformer.poisoning.NeuralCleanse` when you need the ART transformer wrapper for Keras models.

- This wrapper returns a `KerasNeuralCleanse` classifier with `mitigate()` support.
- Lower-level support lives in `art.estimators.poison_mitigation.KerasNeuralCleanse` and `art.estimators.poison_mitigation.neural_cleanse.NeuralCleanseMixin`.
- Mitigation modes: `filtering`, `pruning`, and `unlearning`.
- Best fit: a Keras classifier whose internals expose the penultimate layer for activation analysis and pruning.

### STRIP

Use `art.defences.transformer.poisoning.STRIP` when you want runtime abstention for suspicious inputs rather than model surgery.

- The transformer wraps the classifier in a `STRIPMixin`-backed predictor.
- Call `mitigate(x_val)` to calibrate the entropy threshold on validation data.
- This is especially useful when you have a working classifier and a validation set, but you do not want to modify the model weights.

## Mitigation workflow patterns

### Pattern 1: detector first, then selective retraining

1. Run `ActivationDefence`, `SpectralSignatureDefense`, `ProvenanceDefense`, or `RONIDefense`.
2. Inspect flagged points and decide whether to drop, relabel, or quarantine them.
3. Retrain the base classifier on the cleaned data.

### Pattern 2: backdoor mitigation on a Keras classifier

1. Wrap the trained Keras model with `NeuralCleanse`.
2. Call the returned classifier’s `mitigate(x_val, y_val, mitigation_types=[...])`.
3. Choose one or more of:
   - `filtering` to abstain on suspicious activations,
   - `pruning` to zero out highly suspicious neurons,
   - `unlearning` to adapt to the generated backdoor examples.

### Pattern 3: inference-time abstention

1. Wrap the victim with `STRIP`.
2. Calibrate on clean validation data.
3. Use the returned classifier for prediction and abstention checks.

## Constraint notes

- Do not route ordinary evasion preprocessing here; that belongs to the evasion sub-skill.
- `NeuralCleanse` is not a generic black-box detector. If the classifier does not expose the needed hidden-layer access, prefer `ActivationDefence`, `SpectralSignatureDefense`, `ProvenanceDefense`, `RONIDefense`, or `STRIP`.
- `NeuralCleanse` and `STRIP` are mitigation transformers, not evaluation metrics. If the user wants success rates or robustness scoring, route to the evaluation sub-skill.
- If the user asks for the wrong import path, prefer the verified path in this skill tree and avoid detector-module aliases that are not present in the inspected runtime.
