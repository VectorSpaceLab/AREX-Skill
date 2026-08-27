# Privacy tests API reference

## Purpose

Read this for the verified attack-input, attack-output, and secret-sharer surfaces.

## Membership inference core

### `AttackInputData`

A dataclass that can contain:

- `logits_train`, `logits_test`
- `probs_train`, `probs_test`
- `labels_train`, `labels_test`
- `sample_weight_train`, `sample_weight_test`
- `loss_train`, `loss_test`
- `entropy_train`, `entropy_test`
- `extra_features_train`, `extra_features_test`
- `loss_function`, `loss_function_using_logits`
- `multilabel_data`, `force_multilabel_data`

It can derive losses and entropies when explicit values are not supplied.

### `SlicingSpec`

Constructor fields:

- `entire_dataset=True`
- `by_class=False`
- `by_percentiles=False`
- `by_classification_correctness=False`
- `all_custom_train_indices=None`
- `all_custom_test_indices=None`
- `custom_slices_names=None`

### `AttackType`

Verified values:

- `LOGISTIC_REGRESSION`
- `MULTI_LAYERED_PERCEPTRON`
- `RANDOM_FOREST`
- `K_NEAREST_NEIGHBORS`
- `THRESHOLD_ATTACK`
- `THRESHOLD_ENTROPY_ATTACK`

### `run_attacks`

```python
run_attacks(
    attack_input,
    slicing_spec=None,
    attack_types=(AttackType.THRESHOLD_ATTACK,),
    privacy_report_metadata=None,
    balance_attacker_training=True,
    min_num_samples=1,
    backend=None,
    return_slice_indices=False,
)
```

Returns `AttackResults`.

### `run_membership_probability_analysis`

```python
run_membership_probability_analysis(attack_input, slicing_spec=None)
```

Returns `MembershipProbabilityResults`.

### `run_attack_on_keras_model`

```python
run_attack_on_keras_model(
    model,
    in_train,
    out_train,
    slicing_spec=None,
    attack_types=(AttackType.THRESHOLD_ATTACK,),
    is_logit=False,
    batch_size=32,
)
```

Convenience helper for callback-style evaluation on a trained Keras model.

### `MembershipInferenceCallback`

```python
MembershipInferenceCallback(
    in_train,
    out_train,
    slicing_spec=None,
    attack_types=(AttackType.THRESHOLD_ATTACK,),
    tensorboard_dir=None,
    tensorboard_merge_classifiers=False,
    is_logit=False,
    batch_size=32,
)
```

A `tf.keras.callbacks.Callback` that runs membership inference at epoch end and can optionally write summaries to TensorBoard.

## Results and report metadata

### `PrivacyReportMetadata`

Fields:

- `accuracy_train`
- `accuracy_test`
- `loss_train`
- `loss_test`
- `model_variant_label`
- `epoch_num`

### `AttackResults`

Important methods:

- `summary(by_slices=False)`
- `calculate_pd_dataframe()`
- `get_result_with_max_auc()`
- `get_result_with_max_attacker_advantage()`
- `get_result_with_max_epsilon()`

### `MembershipProbabilityResults`

Important method:

- `summary(threshold_list)`

## Secret sharer

### `generate_secrets`

Verified helpers:

- `generate_random_sequences(vocab, pattern, n, seed=1)`
- `TextSecretProperties(vocab, pattern)`
- `SecretConfig(num_repetitions, num_secrets_for_repetitions, num_references, name='', properties=None)`
- `SecretsSet(config, secrets, references)`
- `construct_secret(secret_config, seqs)`
- `generate_text_secrets_and_references(secret_configs, seed=0)`
- `construct_secret_dataset(secrets_sets)`

### `exposures`

Verified helpers:

- `compute_exposure_interpolation(perplexities, perplexities_reference)`
- `compute_exposure_extrapolation(perplexities, perplexities_reference)`

## Decision points

- Use `loss_train` / `loss_test` if you already have per-example losses; otherwise supply logits or probabilities plus labels.
- Use `entropy_train` / `entropy_test` only when entropy is the desired attack signal.
- Keep the attack fixture tiny when validating the API path; the smoke helper uses synthetic losses and a threshold attack.
