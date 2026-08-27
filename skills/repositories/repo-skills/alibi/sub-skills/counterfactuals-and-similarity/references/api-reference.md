# API Reference

## Purpose

This file records the public counterfactual and similarity APIs that matter to the route.

## Constructors

- `Counterfactual(predict_fn, shape, distance_fn='l1', target_proba=1.0, target_class='other', max_iter=1000, early_stop=50, lam_init=0.1, max_lam_steps=10, tol=0.05, learning_rate_init=0.1, feature_range=(-1e10, 1e10), eps=0.01, init='identity', decay=True, write_dir=None, debug=False, sess=None)`
- `CEM(predict, mode, shape, kappa=0.0, beta=0.1, feature_range=(-1e10, 1e10), gamma=0.0, ae_model=None, learning_rate_init=0.01, max_iterations=1000, c_init=10.0, c_steps=10, eps=(0.001, 0.001), clip=(-100.0, 100.0), update_num_grad=1, no_info_val=None, write_dir=None, sess=None)`
- `CounterfactualProto(predict, shape, kappa=0.0, beta=0.1, feature_range=(-1e10, 1e10), gamma=0.0, ae_model=None, enc_model=None, theta=0.0, cat_vars=None, ohe=False, use_kdtree=False, learning_rate_init=0.01, max_iterations=1000, c_init=10.0, c_steps=10, eps=(0.001, 0.001), clip=(-1000.0, 1000.0), update_num_grad=1, write_dir=None, sess=None)`
- `CounterfactualRL(predictor, encoder, decoder, coeff_sparsity, coeff_consistency, latent_dim=None, backend='tensorflow', seed=0, **kwargs)`
- `CounterfactualRLTabular(predictor, encoder, decoder, encoder_preprocessor, decoder_inv_preprocessor, coeff_sparsity, coeff_consistency, feature_names, category_map, immutable_features=None, ranges=None, weight_num=1.0, weight_cat=1.0, latent_dim=None, backend='tensorflow', seed=0, **kwargs)`
- `GradientSimilarity(predictor, loss_fn, sim_fn='grad_dot', task='classification', precompute_grads=False, backend='tensorflow', device=None, verbose=False)`

## Main call patterns

- `Counterfactual.explain(X)`
- `CEM.fit(train_data, no_info_type='median')`
- `CEM.explain(X, Y=None, verbose=False)`
- `CounterfactualProto.fit(train_data, trustscore_kwargs=None, d_type='abdm', w=None, disc_perc=(25, 50, 75), standardize_cat_vars=False, smooth=1.0, center=True, update_feature_range=True)`
- `CounterfactualProto.explain(X, Y=None, target_class=None, k=None, k_type='mean', threshold=0.0, verbose=False, print_every=100, log_every=100)`
- `CounterfactualRL.fit(X)`
- `CounterfactualRL.explain(X, Y_t, C=None, batch_size=100)`
- `CounterfactualRLTabular.fit(X)`
- `CounterfactualRLTabular.explain(X, Y_t, C=None, batch_size=100, diversity=False, num_samples=1, patience=1000, tolerance=0.001)`
- `GradientSimilarity.fit(X_train, Y_train)`
- `GradientSimilarity.explain(X, Y=None)`

## Output notes

- The classic counterfactual family returns counterfactual instances and metadata about the search or prototype path.
- CFRL returns original and counterfactual batches plus conditioning metadata.
- GradientSimilarity returns similarity scores and ordered indices for training instances.

## Gotchas

- The classic counterfactual family is TF1-style in this repo.
- Tree models are not a good fit for the gradient-based counterfactual route.
- CFRL tabular decoding must emit a list of tensors.
- Gradient similarity can be memory-heavy when precomputing gradients.
