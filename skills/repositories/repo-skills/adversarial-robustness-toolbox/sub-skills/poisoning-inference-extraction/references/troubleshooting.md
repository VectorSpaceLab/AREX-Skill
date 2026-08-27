# Troubleshooting

Use this reference when an attack, detector, or mitigation recipe fails because the split, labels, model capability, or query budget is wrong.

## Train / validation split and labels

- **`PoisoningAttackSVM` fails to initialize**
  - Likely cause: the classifier is not the verified `ScikitlearnSVC` wrapper, or the kernel/estimator type is unsupported.
  - Fix: wrap a supported `sklearn.svm.SVC` instance with `ScikitlearnSVC` and supply both `x_train/y_train` and `x_val/y_val`.

- **`HiddenTriggerBackdoor` or clean-label backdoor setup looks inconsistent**
  - Likely cause: the target and source classes are the same, the target label is not one-hot, or the backdoor callable does not return the same shape as the input.
  - Fix: choose distinct source and target classes, keep the trigger transformation shape-preserving, and pass a `PoisoningAttackBackdoor` instance.

- **Poisoning attacks silently behave like ordinary training**
  - Likely cause: poisoned samples were not appended to the retraining set, or the user never retrained after poisoning.
  - Fix: poison a tiny subset first, append the returned poison to the train set, then retrain and compare clean vs poison performance.

- **Classifier labels have the wrong format**
  - Likely cause: the attack expects one-hot labels but receives class indices, or vice versa.
  - Fix: convert classifier labels to one-hot unless the specific attack explicitly documents class indices.

## Trigger, feature-layer, and mitigation capability

- **`FeatureCollisionAttack` cannot find the layer**
  - Likely cause: the supplied `feature_layer` name or index does not exist on the wrapped model.
  - Fix: inspect layer names first and choose a stable hidden layer rather than the output layer.

- **`MIFace` complains about classifier capabilities**
  - Likely cause: the estimator does not expose class gradients.
  - Fix: use a classifier with class-gradient support; if only predictions are available, choose a privacy-inference attack instead of model inversion.

- **`NeuralCleanse` cannot be used on the current classifier**
  - Likely cause: the model is not the verified Keras pathway, or it does not expose the penultimate-layer activations needed for pruning/filtering.
  - Fix: use `art.defences.transformer.poisoning.NeuralCleanse` only with a Keras classifier that can be wrapped as `KerasNeuralCleanse`. If the classifier has no penultimate-layer access, switch to `ActivationDefence`, `SpectralSignatureDefense`, `ProvenanceDefense`, `RONIDefense`, or `STRIP`.

- **`STRIP` predicts but never abstains**
  - Likely cause: mitigation has not been calibrated on validation data yet.
  - Fix: call `mitigate(x_val)` before inference and use a clean validation set.

## Privacy inference data-split issues

- **`MembershipInferenceBlackBox` has no signal**
  - Likely cause: the user supplied only one split, only labels, or the wrong input type.
  - Fix: provide member and non-member examples; use `input_type="prediction"` when you have prediction probabilities/logits, and switch to `input_type="loss"` only when loss values are available.

- **Membership inference with only labels is requested**
  - Likely cause: black-box MIA was chosen when the victim only returns class labels.
  - Fix: route to `MembershipInferenceBlackBoxRuleBased` or `LabelOnlyDecisionBoundary` / `LabelOnlyGapAttack` and calibrate the threshold.

- **`AttributeInferenceBlackBox.infer()` raises because `pred` is missing**
  - Likely cause: the attack needs victim predictions for inference.
  - Fix: pass `pred=` from the victim classifier and remove the attacked feature from the inference input.

- **`AttributeInferenceBlackBox` behaves poorly on categorical features**
  - Likely cause: `values`, `encoder`, or `non_numerical_features` were not provided.
  - Fix: keep the attacked feature in a stable categorical encoding and pass the feature values explicitly when necessary.

## Query budgets and extraction limits

- **Extraction attacks are too slow or too expensive**
  - Likely cause: `nb_stolen`, `batch_size_query`, or `nb_epochs` is too large for the current budget.
  - Fix: shrink the stolen subset and query batch size for smoke checks first, then scale only if the user needs a higher-fidelity clone.

- **`FunctionallyEquivalentExtraction` fails to generalize**
  - Likely cause: the victim architecture is not the narrow two-dense-layer family expected by the attack.
  - Fix: fall back to `CopycatCNN` or `KnockoffNets` when the architecture is more complex.

- **`KnockoffNets` query policy is unclear**
  - Likely cause: the user did not choose between random and adaptive stealing.
  - Fix: start with `sampling_strategy="random"`; move to adaptive only when the query budget is large enough to justify the extra policy logic.

## Optional dependency / backend issues

- **Import errors on poisoning or extraction workflows**
  - Likely cause: missing framework extras for the victim estimator, detector, or mitigation wrapper.
  - Fix: verify the relevant backend first instead of assuming a pure-NumPy runtime.

- **`PoisoningAttackSVM` rejects `NuSVC` or unsupported kernels**
  - Likely cause: the attack is only verified for the supported `ScikitlearnSVC` path.
  - Fix: switch to the supported wrapper and kernel family before drafting the recipe.

- **`DatabaseReconstruction` is not available for the model family you chose**
  - Likely cause: the estimator is not one of the supported white-box classical paths.
  - Fix: route to membership or extraction instead of forcing reconstruction.

## Synthetic cases to keep in mind

- **Only prediction probabilities are available for membership inference**
  - Use `MembershipInferenceBlackBox` with `input_type="prediction"` and do not switch to label-only attacks unless the user explicitly drops to class labels.

- **Neural Cleanse requested for a classifier without penultimate-layer activations**
  - Treat this as a capability mismatch, not a parameter tweak. Route to a detector/mitigation that does not require penultimate-layer access.
