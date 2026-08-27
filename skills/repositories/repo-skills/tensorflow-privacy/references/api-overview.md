# API overview

## Purpose

Use this page to find the right sub-skill and the right deeper reference. It is a map, not a full API manual.

## Core families

| Family | Primary modules | Main use | Owner |
| --- | --- | --- | --- |
| DP training | `tensorflow_privacy.privacy.optimizers`, `tensorflow_privacy.privacy.keras_models`, `tensorflow_privacy.privacy.estimators`, `tensorflow_privacy.privacy.logistic_regression` | Replace standard optimizers with DP optimizers, wrap Keras models, or use the repo's supervised training helpers | `training` |
| Privacy accounting | `tensorflow_privacy.privacy.analysis.compute_dp_sgd_privacy_lib`, `compute_noise_from_budget_lib`, `tree_aggregation_accountant`, `gdp_accountant` | Compute epsilon, delta, or target noise for a DP-SGD run | `privacy-accounting` |
| DP queries | `tensorflow_privacy.privacy.dp_query` | Compose Gaussian, discrete Gaussian, Skellam, nested, normalized, quantile, or tree-aggregation query mechanisms | `queries` |
| Privacy tests | `tensorflow_privacy.privacy.privacy_tests`, `tensorflow_privacy.privacy.privacy_tests.membership_inference_attack`, `secret_sharer` | Run membership inference, privacy reports, callbacks, or secret-sharer exposure analysis | `privacy-tests` |
| Fast clipping | `tensorflow_privacy.privacy.fast_gradient_clipping`, `tensorflow_privacy.privacy.sparsity_preserving_noise` | Use layer registries, clipped-gradient helpers, or sparse-noise support for faster DP training | `fast-clipping` |

## Verified signature highlights

- `compute_dp_sgd_privacy_statement(number_of_examples, batch_size, num_epochs, noise_multiplier, delta, used_microbatching=True, max_examples_per_user=None, accountant_type=AccountantType.RDP) -> str`
- `compute_noise(n, batch_size, target_epsilon, epochs, delta, noise_lbd)`
- `run_attacks(attack_input, slicing_spec=None, attack_types=(AttackType.THRESHOLD_ATTACK,), privacy_report_metadata=None, balance_attacker_training=True, min_num_samples=1, backend=None, return_slice_indices=False)`
- `run_membership_probability_analysis(attack_input, slicing_spec=None)`
- `AttackInputData(...)` accepts logits, probabilities, labels, losses, entropy, sample weights, and extra features for train/test splits
- `LayerRegistry` is the registry container used by fast clipping helpers
- `add_aggregate_noise(clipped_grads, batch_size, l2_norm_clip, noise_multiplier, loss_reduction=None, loss_model=None, sparse_noise_config=None)` adds dense or sparse noise

## When to read deeper

- Read `sub-skills/training/references/api-reference.md` for optimizer/model/estimator signatures and training-specific decisions.
- Read `sub-skills/privacy-accounting/references/api-reference.md` for CLI flags, accountant options, and user-level privacy notes.
- Read `sub-skills/queries/references/api-reference.md` for query classes and composition patterns.
- Read `sub-skills/privacy-tests/references/api-reference.md` for attack inputs, result objects, and callback/report APIs.
- Read `sub-skills/fast-clipping/references/api-reference.md` for layer registry behavior and sparse-noise helpers.
