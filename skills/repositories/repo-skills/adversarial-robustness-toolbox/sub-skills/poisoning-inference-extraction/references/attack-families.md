# Attack families and workflow recipes

This reference groups the bundled ART attack families by the capability they need from the victim model and the data you already have.

## Quick chooser

| Family | Choose when | Minimum capability | Core ART classes |
| --- | --- | --- | --- |
| Poisoning / backdoor | You can influence training data, labels, or a trigger pattern | A trainable classifier; some variants need gradients or feature-layer access | `PoisoningAttackSVM`, `FeatureCollisionAttack`, `PoisoningAttackBackdoor`, `PoisoningAttackCleanLabelBackdoor`, `HiddenTriggerBackdoor`, `PoisoningAttackAdversarialEmbedding`, `GradientMatchingAttack`, `SleeperAgentAttack` |
| Privacy inference | You want to infer membership, attributes, or training records | Prediction vectors or losses for black-box MIA; class gradients for inversion; structured tabular features for attribute inference | `MembershipInferenceBlackBox`, `MembershipInferenceBlackBoxRuleBased`, `LabelOnlyDecisionBoundary`, `LabelOnlyGapAttack`, `ShadowModels`, `AttributeInferenceBlackBox`, `MIFace`, `DatabaseReconstruction` |
| Extraction / stealing | You want a surrogate that matches the victim’s behavior | Query access plus a thievable classifier to train against | `CopycatCNN`, `KnockoffNets`, `FunctionallyEquivalentExtraction` |

## Poisoning and backdoor recipe

Use this path when the goal is to make the victim model learn a hidden trigger, move a decision boundary, or create mislabeled training examples.

1. Decide whether the attack is SVM-specific, feature-collision, label-flipping/backdoor, or trigger-based.
2. Verify the victim model type and training access.
   - `PoisoningAttackSVM` is for the sklearn SVM wrapper family.
   - `FeatureCollisionAttack`, `GradientMatchingAttack`, `SleeperAgentAttack`, and the backdoor families expect a neural-network-style classifier.
3. Prepare clean train and validation splits before poisoning.
   - SVM poisoning needs both training and validation data.
   - Clean-label and hidden-trigger attacks need a proxy or feature-layer-aware classifier.
4. Build the attack with the smallest useful perturbation budget.
5. Poison a few points first, then retrain the victim or surrogate classifier on the poisoned set.
6. Validate against a held-out clean set and check whether the trigger or target sample now causes the intended misclassification.

### PoisoningAttackSVM

Use `PoisoningAttackSVM` when the victim is an ART `ScikitlearnSVC` wrapper and you want the classical SVM poisoning workflow.

- Inputs: `classifier`, `step`, `eps`, `x_train`, `y_train`, `x_val`, `y_val`, `max_iter`.
- Best fit: small tabular problems with a supported `sklearn.svm.SVC` kernel.
- Route note: unsupported sklearn estimators or kernels should be rejected before you draft a recipe.

### FeatureCollisionAttack

Use `FeatureCollisionAttack` when you want one base sample to be nudged toward a target representation in a hidden layer.

- Inputs: a neural-network classifier, a target sample, and a `feature_layer` name or index.
- Typical flow: poison a base sample, append the poisoned output to the training set, then retrain.
- Best fit: image or embedding models with a known intermediate layer.

### Backdoor / clean-label / hidden-trigger family

Use these when the attack is trigger-based.

- `PoisoningAttackBackdoor` wraps a perturbation callable or list of callables.
- `PoisoningAttackCleanLabelBackdoor` adds clean-label poisoning on top of a backdoor and needs a proxy classifier with loss gradients.
- `HiddenTriggerBackdoor` needs distinct target and source classes, a `feature_layer`, and a `PoisoningAttackBackdoor` instance.
- `PoisoningAttackAdversarialEmbedding` is the embedding-style backdoor variant; use it when the target is an embedding-space representation rather than a simple pixel trigger.

Workflow tip: keep the trigger definition separate from the training recipe so you can swap between a pattern trigger, a patch, or a custom perturbation without rewriting the whole attack.

### GradientMatchingAttack and SleeperAgentAttack

Use these for more stealthy image poisoning.

- `GradientMatchingAttack` needs a neural-network classifier, `percent_poison`, `epsilon`, and a clipping range.
- `SleeperAgentAttack` adds a patch, target indices, and retraining strategy controls.
- Both attacks are expensive compared with simple backdoor poisoning; start with tiny `max_trials` and `max_epochs` when drafting a recipe.

## Privacy inference recipe

Use this path when the goal is to infer whether a record was in training, reconstruct an attribute, or recover representative inputs.

### Membership inference

Prefer `MembershipInferenceBlackBox` when you can query predictions or losses.

- `input_type="prediction"` is the default and is the right choice when you have prediction probabilities or logits.
- `input_type="loss"` is only appropriate when you can compute loss values.
- `attack_model_type` can be `nn`, `rf`, `gb`, `lr`, `dt`, `knn`, or `svm`, or you can pass a custom `attack_model`.
- `ShadowModels` is the supporting utility when you want to synthesize member/non-member attack data instead of relying on a single split.

Use `MembershipInferenceBlackBoxRuleBased` when you want a lighter-weight rule-based variant and already have a classifier with accessible predictions.

Use `LabelOnlyDecisionBoundary` or `LabelOnlyGapAttack` when the attacker only sees class labels.

- Calibrate the distance threshold before trusting results.
- Keep the true labels for calibration and evaluation.
- This is the correct fallback when prediction probabilities are unavailable.

### Attribute inference

Use `AttributeInferenceBlackBox` when one feature or feature block is hidden and the rest of the record plus victim predictions are visible.

- Fit on complete records that include the attacked feature.
- Infer from records where the attacked feature has been removed.
- Pass `pred=` from the victim at inference time.
- For categorical targets, provide `values` if the class set was not learned during fitting.
- Set `is_continuous=True` only when the attacked feature is numeric and should be treated as a regression target.

### Model inversion and reconstruction

Use `MIFace` when the victim exposes class gradients and you want representative synthetic inputs.

- Best fit: image classifiers with `ClassGradientsMixin` support.
- You may start from `x=None` to synthesize from scratch or provide noisy examples to refine.
- Keep `batch_size` small for stable optimization.

Use `DatabaseReconstruction` when the task is white-box reconstruction for a supported classical estimator family.

- It is a reconstruction route, not a general black-box privacy attack.
- Use it when the model structure itself leaks records through its parameters or probabilities.

## Extraction / stealing recipe

Use this path when the goal is to clone a victim model’s behavior.

### CopycatCNN

Use `CopycatCNN` when you can query a victim classifier and train a surrogate on those outputs.

- Inputs: victim `classifier`, `batch_size_fit`, `batch_size_query`, `nb_epochs`, `nb_stolen`, `use_probability`.
- Provide a separate thieved classifier to `extract`.
- Best fit: image classifiers where the surrogate architecture is close to the victim.

### KnockoffNets

Use `KnockoffNets` when you want the query policy to alternate between random and adaptive stealing.

- Same basic query-and-train pattern as Copycat CNN.
- Add `sampling_strategy` and `reward` when you want adaptive query selection.
- Prefer `use_probability=True` when the victim exposes probability vectors and you want a richer stolen signal.

### FunctionallyEquivalentExtraction

Use `FunctionallyEquivalentExtraction` only when the victim is a neural network with two dense layers and the architecture is known enough to recover exactly.

- It is not a general substitute for Copycat CNN or Knockoff Nets.
- Use it when the user explicitly wants exact-function extraction rather than imitation.

## Explicit exclusions and scope notes

- `BackdoorAttackDGM*` examples are documented in ART but are not bundled as runtime recipes here because they rely on generative-model backdoor workflows.
- `BadDet*` object-detection poisoning attacks are outside the selected runtime scope.
- Malware, audio, and other special-purpose attack families are likewise out of scope unless a future refresh adds their backend coverage.
- Ordinary evasion attacks and preprocessing defences belong to the sibling evasion sub-skill, not here.

## What to prefer first

- If you have only prediction probabilities and membership leakage is the concern, start with `MembershipInferenceBlackBox`.
- If you only have class labels, switch to `LabelOnlyDecisionBoundary` or `LabelOnlyGapAttack` and calibrate the threshold.
- If you need a trigger detector or mitigation, go to [defences-and-mitigations.md](defences-and-mitigations.md) before trying to invent a new poisoning recipe.
