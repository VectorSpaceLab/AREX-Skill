# Advanced Topics: Projections, Trees, Assignment, Second Order, and Contrib

Use this reference when the request is not a standard optimizer or loss/schedule question. It covers the lower-frequency Optax modules that still appear in real workflows: constrained optimization, tree utilities, linear algebra helpers, assignment, second-order utilities, and contrib/experimental algorithms.

## Constrained optimization and projections

`optax.projections` provides Euclidean projection helpers for common feasible sets:

- `projection_non_negative`
- `projection_simplex`
- `projection_l1_ball`, `projection_l1_sphere`
- `projection_l2_ball`, `projection_l2_sphere`
- `projection_linf_ball`
- `projection_box`, `projection_hypercube`
- `projection_hyperplane`, `projection_halfspace`
- `projection_vector`

Use this family when the user wants to clip or project parameters after an update, or to enforce feasibility during constrained optimization.

## Assignment

`optax.assignment.hungarian_algorithm` solves the linear assignment problem. It is the right route when the user asks about bipartite matching, cost matrices, or assignment-style selection.

## Tree utilities

`optax.tree_utils` contains tree-shaped arithmetic and inspection helpers such as:

- `tree_add`, `tree_sub`, `tree_mul`, `tree_div`, `tree_scale`
- `tree_norm`, `tree_sum`, `tree_max`, `tree_min`, `tree_dtype`, `tree_size`
- `tree_map_params`, `tree_cast`, `tree_cast_like`, `tree_random_like`
- `tree_where`, `tree_zeros_like`, `tree_ones_like`, `tree_full_like`

These are useful when the request is about manipulating parameter trees, not about optimizer construction.

## Linear algebra and second order

`optax._src.linear_algebra` and `optax.second_order` expose helpers used by more advanced algorithms:

- `power_iteration`, `matrix_inverse_pth_root`, `nnls`, `global_norm`
- `hvp`, `fisher_diag`, `hessian_diag`

These helpers are often more sensitive to dtypes, conditioning, and tensor shape assumptions than the core optimizer paths.

## Contrib and experimental algorithms

`optax.contrib` holds algorithms and wrappers that are not part of the main stable surface or that are still evolving. Common examples in this repo include:

- `acprop`, `adopt`, `ademamix`, `dadapt_adamw`, `dog`, `galore`, `madgrad`
- `mechanic`, `momo`, `muon`, `prodigy`, `sam`, `schedule_free`, `sophia`
- `reduce_on_plateau`, `dpsgd`, `differentially_private_aggregate`
- complex-valued support helpers and Hessian-estimation utilities

`optax.experimental.aggregating` is currently the visible experimental submodule.

## Source example evidence distilled into this route

The following source notebooks informed this route and the examples index; treat these paths as provenance labels rather than runtime dependencies:

- `examples/linear_assignment_problem.ipynb`
- `examples/freezing_parameters.ipynb`
- `examples/lookahead_mnist.ipynb`
- `examples/adversarial_training.ipynb`
- `examples/meta_learning.ipynb`
- `examples/contrib/sam.ipynb`
- `examples/contrib/differentially_private_sgd.ipynb`
- `examples/contrib/muon.ipynb`
- `examples/contrib/reduce_on_plateau.ipynb`
- `examples/contrib/rosenbrock_ademamix.ipynb`

## Common failure modes

- **Tree mismatch**: projection or tree helpers expect compatible PyTree structure and leaf shapes.
- **Constraint infeasibility**: projections can fail or return unexpected results if the input violates the assumed feasible set semantics.
- **Cost matrix shape confusion**: Hungarian assignment expects the cost matrix to be the right rank and orientation for the intended rows/columns.
- **Numerical instability**: second-order and linear algebra helpers can be sensitive to dtype, conditioning, and large magnitude values.
- **Contrib drift**: contrib and experimental features may change faster than the stable optimizer surface, so prefer reading the bundled provenance and troubleshooting notes before assuming old examples still match.

## Good cross-checks

- When the request is about selecting an algorithm outside the stable main optimizer surface, start here.
- Use `core-optimization` if the user actually wants to build an ordinary gradient transformation pipeline and only mentioned a helper that can be composed into it.
