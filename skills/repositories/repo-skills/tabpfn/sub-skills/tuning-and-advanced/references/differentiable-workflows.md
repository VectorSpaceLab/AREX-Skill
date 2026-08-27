# Differentiable Input and Prompt Tuning

## The main idea

Setting `differentiable_input=True` keeps the autograd graph intact so users can
backpropagate from predictions to the input features.

## Typical workflow

1. Create a `TabPFNClassifier` or `TabPFNRegressor` with `differentiable_input=True`.
2. Call `fit_with_differentiable_input(X_train_tensor, y_train_tensor)`.
3. Run `forward(X_test_tensor, use_inference_mode=True)` to get differentiable outputs.
4. Use PyTorch autograd to compute gradients with respect to the inputs.

## Important classifier-specific caveat

`fit_with_differentiable_input` does not infer `n_classes_` from a differentiable
y tensor. Set it manually when needed.

## Prompt tuning

Prompt tuning treats the in-context examples themselves as learnable parameters.
The common pattern is:

- create a differentiable TabPFN classifier,
- mark prompt tensors with `requires_grad=True`,
- optimize those tensors with an optimizer such as Adam,
- re-run `fit_with_differentiable_input` inside the training loop.

## Restrictions and warnings

- Categorical columns are not compatible with differentiable-input workflows.
- The estimator may automatically switch its `fit_mode` to `fit_preprocessors` for differentiable input.
- These workflows are much easier to run on a GPU, even though small CPU demos are possible.
