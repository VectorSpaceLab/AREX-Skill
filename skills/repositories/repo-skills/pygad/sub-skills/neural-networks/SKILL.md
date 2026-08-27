---
name: neural-networks
description: "Use PyGAD's pure NumPy neural helpers and Keras/Torch adapters for
  GA-based model optimization."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# neural-networks

Use this sub-skill when the task asks to evolve neural-network weights with PyGAD: pure NumPy dense networks, pure NumPy CNNs, GANN/GACNN populations, or Keras/PyTorch model adapters.

## Route elsewhere

- Generic `pygad.GA` tuning, custom operators, batch fitness, callbacks, or multi-objective selectors: use `genetic-algorithm`.
- Built-in benchmark problems or quality indicators: use `benchmarks`.
- Plotting training/fitness curves or exporting reports after a GA run: use `results-and-visuals`.

## Choose the right neural path

| User goal | PyGAD module path | Dependency profile | Notes |
| --- | --- | --- | --- |
| Small dense network in NumPy | `pygad.nn` + `pygad.gann` | Core PyGAD only | Best for transparent examples and tiny classification/regression tasks. |
| Small CNN in NumPy | `pygad.cnn` + `pygad.gacnn` | Core PyGAD only | CPU-only forward pass; keep fixtures tiny. |
| Existing Keras model | `pygad.kerasga` | `tensorflow`/`keras` extra | Supports Sequential and Functional models; only trainable layer weights enter the chromosome. |
| Existing PyTorch model | `pygad.torchga` | `torch` extra | Works from `state_dict()` order; predictions use a copied model so the caller model is preserved. |

## Operating flow

1. **Build or receive the model architecture.** Use PyGAD's pure NumPy layer classes, a Keras model, or a `torch.nn.Module`.
2. **Convert model weights into GA chromosomes.** Use `GANN.population_networks` plus `population_as_vectors()`, `GACNN.population_networks`, `KerasGA.population_weights`, or `TorchGA.population_weights` as `initial_population`.
3. **Write a fitness bridge with the modern PyGAD signature.** The fitness function must accept `(ga_instance, solution, solution_idx)` and return a higher-is-better score. For Keras/Torch, load the candidate solution through the adapter's `predict()` or restore helper inside fitness; for GANN/GACNN, predict from the matching population model and synchronize matrices in `on_generation`.
4. **Run `pygad.GA`.** Start with few generations, small populations, explicit `random_seed`, and a simple maximization score before scaling to expensive data.
5. **Copy the best solution back into the model.** Convert the best vector with the matching matrix/dict helper and update the model or use the module's `predict()` helper.
6. **Inspect and export results elsewhere.** For plots/reports, route to `results-and-visuals` after the GA is complete.

## Reference map

- API signatures, model-weight conversion rules, optional dependency boundaries, and data contracts: [references/api-reference.md](references/api-reference.md)
- End-to-end dense/CNN/Keras/Torch recipes and decision points: [references/workflows.md](references/workflows.md)
- Common dependency, shape, label, and weight-conversion failures: [references/troubleshooting.md](references/troubleshooting.md)

## Bundled safe scripts

- [scripts/neural_internal_smoke.py](scripts/neural_internal_smoke.py): verifies pure NumPy `nn`, `gann`, `cnn`, and `gacnn` conversion paths with tiny deterministic data.
- [scripts/keras_torch_templates.py](scripts/keras_torch_templates.py): lazy-imports either Keras/TensorFlow or PyTorch and runs a tiny CPU GA template; it exits clearly when the optional framework is missing.

## Safety notes

- GA-based neural training is expensive compared with gradient descent. Keep initial checks tiny and scale only when the user accepts runtime cost.
- Classification labels used by PyGAD's pure NumPy examples should be integers from `0` to `num_classes - 1`.
- Keras/Torch adapters are optional; do not install deep-learning frameworks unless the user's task requires them.
- GPU is not required for these helpers. If a user asks for CUDA/MPS/ROCm, verify the framework backend separately before promising accelerator execution.
