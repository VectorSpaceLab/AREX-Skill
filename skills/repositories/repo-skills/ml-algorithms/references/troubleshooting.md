# MLAlgorithms troubleshooting

## Purpose

Use this for cross-cutting package failures before drilling into a sub-skill's workflow-specific troubleshooting.

## Install/import problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'mla'` | The `mla` package is not installed in the active environment. | Install the distribution and run `scripts/run_import_smoke.py --json`. |
| Missing `autograd`, `scipy`, `sklearn`, `matplotlib`, `seaborn`, `gym`, or `tqdm` | Runtime requirements are incomplete. | Install only the package requirements needed for the selected workflow; avoid broad unrelated extras because none are declared. |
| `python setup.py develop` works but isolated import fails | The checkout path is masking a broken install. | Test from a neutral directory or use the root smoke helper in the target environment. |
| No CLI command is found | The package defines no console entry points. | Use Python APIs or generated bundled scripts. |

## Version compatibility

- **NumPy and dataset loader**: `load_nietzsche()` uses deprecated `np.bool` in version `0.0.1`. Use NumPy below `1.24` for that loader or patch the dtype in the source.
- **Gym and DQN**: `DQN` expects legacy Gym `reset()` and four-value `step()` returns. Newer Gym/Gymnasium needs an adapter before training.
- **Python version**: the package is old but pure Python. Prefer a stable scientific-stack Python such as 3.10 or 3.11 when building an inspection or user environment.

## Shape, metric, and label problems

- Most tabular estimators need `X` shaped `(n_samples, n_features)`.
- Supervised estimators need `fit(X, y)`. Missing targets raise `ValueError("Missed required argument y")`.
- `LogisticRegression` returns probabilities; threshold them for hard-label accuracy.
- `SVM` expects labels encoded as `-1` and `1`.
- `NaiveBayesClassifier` expects binary labels exactly `[0, 1]`.
- `NeuralNet` losses and final activations must match target shapes: one-hot + softmax for categorical cross entropy, one-column output for MSE regression.

## Plotting and long-running examples

- KMeans/GMM/t-SNE/RBM examples can call Matplotlib or `plt.show()`. Avoid plot calls in headless environments.
- ConvNet MNIST, RNN text generation, optimizer sweeps, and DQN training can be long-running. Use bundled smoke scripts unless the user explicitly wants those educational runs.
- DQN `play()` and rendering may block without a display.

## Safe diagnosis sequence

1. Run root import smoke:

   ```bash
   python scripts/run_import_smoke.py --json
   ```

2. Pick the nearest sub-skill helper:
   - `classical-estimators/scripts/run_classical_smoke.py`
   - `unsupervised-and-reduction/scripts/run_unsupervised_smoke.py`
   - `neural-network-building-blocks/scripts/run_neural_smoke.py`
3. If a smoke passes but user data fails, inspect shapes, label values, dependency versions, and whether the workflow needs display, long training, or legacy Gym.
4. If a native checkout test fails, treat that as repo-maintenance verification evidence; do not make the generated runtime skill depend on running original tests.
