# Optax Example Index

This index records which source notebooks informed each skill route. Treat the notebook paths as provenance/evidence labels, not as files the runtime skill requires.

| Notebook | Best route | Why it matters |
| --- | --- | --- |
| `examples/flax_example.ipynb` | `core-optimization` | Shows a standard Optax optimizer loop in a Flax training setup. |
| `examples/mlp_mnist.ipynb` | `core-optimization` | Compact end-to-end optimizer + update example. |
| `examples/lbfgs.ipynb` | `core-optimization` | Useful when the user asks about quasi-Newton or line-search-style usage. |
| `examples/lookahead_mnist.ipynb` | `core-optimization` | Demonstrates wrapper composition with a base optimizer. |
| `examples/gradient_accumulation.ipynb` | `losses-and-schedules` | Shows accumulation and batch handling patterns. |
| `examples/gradient_accumulation_and_microbatching.ipynb` | `losses-and-schedules` | Same theme, but with explicit microbatching helpers. |
| `examples/perturbations.ipynb` | `losses-and-schedules` | Demonstrates perturbation-based wrappers and objective smoothing. |
| `examples/cifar10_resnet.ipynb` | `losses-and-schedules` | Larger training loop where schedules and loss selection matter. |
| `examples/freezing_parameters.ipynb` | `advanced-topics` | Useful for parameter partitioning and selective updates. |
| `examples/linear_assignment_problem.ipynb` | `advanced-topics` | Evidence for assignment-style workflows. |
| `examples/contrib/sam.ipynb` | `advanced-topics` | Contrib algorithm route. |
| `examples/contrib/differentially_private_sgd.ipynb` | `advanced-topics` | Privacy-oriented contrib route. |
| `examples/contrib/muon.ipynb` | `advanced-topics` | Another contrib algorithm route. |
| `examples/contrib/reduce_on_plateau.ipynb` | `losses-and-schedules` or `advanced-topics` | Schedule-like behaviour driven by a monitored metric. |
| `examples/adversarial_training.ipynb` | `advanced-topics` | Often combines multiple advanced helpers rather than a plain optimizer. |
| `examples/meta_learning.ipynb` | `advanced-topics` | Best for higher-level experimental workflows. |

## How to use this index

- Use the route mapping to decide which sub-skill owns a workflow that resembles a source notebook.
- Do not require future agents or users to open, execute, or depend on these notebooks from the original checkout.
- If more detail is needed, rely on the bundled route references and live installed-package inspection before proposing code.
