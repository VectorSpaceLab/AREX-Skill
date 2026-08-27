# Regression Visualization

## Main helper

`plot_regression_distribution` plots the distribution returned by
`TabPFNRegressor.predict(..., output_type="full")`.

## Typical workflow

1. Fit a regressor.
2. Call `predict(X_test, output_type="full")` on the samples you want to visualize.
3. Pass the returned object to `plot_regression_distribution` with a sample index.
4. Optionally overlay a truth line or save the figure.

## Notes

- This workflow is part of the optional visualization extra.
- It is useful for inspecting uncertainty, quantiles, and distribution shape.
- It is not a substitute for the core prediction API; it is a post-processing aid.
