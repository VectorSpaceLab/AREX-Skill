---
name: toolkit
description: "Build, encode, decode, sample, inspect, optimize, and reload PhySO
  symbolic programs without running SR orchestration."
read_when: "Use when a task concerns physo.toolkit, expression prefix encodings,
  token libraries, free constants, program trees, display, monitoring, or
  Pareto/result loading."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PhySO toolkit

## Role

Use this sub-skill for the low-level symbolic-expression layer of PhySO. It
turns a token library and prefix expressions into executable `Program` or
`VectPrograms` objects, and provides safe routes for sampling, inspecting,
optimizing, displaying, and reloading those objects. The verified baseline is
PhySO 1.2.0 in a CPU-only Python environment. Import-time warnings about
missing system LaTeX are expected and do not invalidate plain-text workflows.

## Boundaries

### Included

- `physo.toolkit.get_library`, `get_expressions`, `get_prior`, and
  `sample_random_expressions`.
- `Library.encode`/`decode`, prefix-token validation, one-hot encodings, and
  length/structural priors.
- `Dataset`, `Token` and its public typed subclasses, `Library`, `Program`,
  `VectPrograms`, `Cursor`, `FreeConstantsTable`, and differentiable
  `candidate_wrapper` usage at the expression layer.
- CPU-safe execution, autograd inspection, free-constant optimization, class versus
  realization-specific constants, tree relationships, and plain or optional
  display representations.
- `RunLogger`, Pareto-front inspection, `physo.read_pareto_csv`,
  `physo.read_pareto_pkl`, and `physo.load_expr`.

### Excluded

- `physo.SR` and `physo.ClassSR` orchestration, run presets, stopping rules,
  and dataset/task selection. Route those questions to
  [the SR sibling](../sr/SKILL.md) or [the Class SR sibling](../class-sr/SKILL.md).
- Feynman/Class benchmark problem definitions, selectors, and equivalence
  workflows. Route them to [the benchmarks sibling](../benchmarks/SKILL.md).
- Maintainer benchmark runners, cluster jobfile generation, long training,
  plotting-heavy analysis, CUDA-specific claims, and undocumented private
  helpers.

## Verified entry points

| Need | Start here | Result |
|---|---|---|
| Define variables, constants, operations, units, and free constants | `physo.toolkit.get_library(...)` | A `physo.physym.library.Library` |
| Encode readable prefix names | `library.encode(expressions_str, one_hot=False)` | One integer-token list per expression; `one_hot=True` returns one-hot matrices |
| Decode integer prefixes | `library.decode(expressions_idx, n_realizations=1)` | A `VectPrograms` batch with padded invalid placeholders |
| Make an empty program batch | `physo.toolkit.get_expressions(batch_size, max_length, library, ...)` | A `VectPrograms` ready for `append` or `set_programs` |
| Build priors for an existing batch | `physo.toolkit.get_prior(priors_config, max_length, expressions, library)` | A prior collection callable |
| Generate random valid candidates | `physo.toolkit.sample_random_expressions(...)` | A sampled `VectPrograms` batch |
| Inspect one candidate | `batch.get_prog(i)` | A `Program` with execution, constants, text, SymPy, and save methods |
| Inspect a batch/tree | `batch.status()`, `batch.tokens`, `Cursor`, family methods | Names, arities, units, parent/child/sibling/ancestor relations |
| Fit constants | `program.optimize_constants(...)`, `batch.batch_optimize_constants(...)` | Updated constant tables and a loss history for the single-program route |
| Reload results | `physo.read_pareto_pkl`, `physo.read_pareto_csv`, `physo.load_expr` | Programs or SymPy expressions, subject to the CSV/Class SR caveat |

See [API reference](references/api-reference.md) for source-verified
signatures, [workflows](references/workflows.md) for compact recipes, and the
[PhySO root skill](../../SKILL.md) for install/backend routing.

## Operating workflow

1. **Fix the data contract first.** For each realization, use `X` with shape
   `(n_dim, n_samples)` and `y` with shape `(n_samples,)`, both floating-point
   tensors or safely convertible arrays. A `Dataset` receives lists
   `multi_X` and `multi_y`, even for one realization (`[X]`, `[y]`). Keep all
   `X`, `y`, and weights on the same device.
2. **Build the smallest library.** Set `X_names`, `y_name`, aligned fixed and
   free-constant arrays, and an explicit `op_names` list. Use protected
   operations unless you deliberately need unprotected numerical behavior.
   With units, every terminal units vector must be aligned and consistent.
3. **Encode only choosable names.** Write expressions in prefix order, e.g.
   `['mul', 'c', 'x']`. Check `library.choosable_names`; placeholders such as
   the superparent, dummy, and invalid token are not encodable user tokens.
4. **Decode and validate.** Pass a batch-shaped list of Python `int` indices to
   `Library.decode`. Inspect `batch.status()`, `batch.n_lengths`,
   `batch.is_complete`, and `batch.get_infix_str(i)` before executing. A prefix
   expression must be a complete tree: `len(tokens) - sum(token.arity) == 1`.
5. **Sample under bounded priors.** Use a small `batch_size` and `max_length`
   for exploration. If `priors_config` is supplied, include a
   `HardLengthPrior`; its `max_length` controls the sampler and takes
   precedence over the top-level value. Seed NumPy and PyTorch when a
   reproducible fixture matters.
6. **Execute and inspect.** Get a `Program` with `get_prog`, call it with a
   tensor, or use `execute(..., i_realization=..., n_samples_per_dataset=...)`
   for realization-specific constants. Prefer `get_infix_str`,
   `get_infix_pretty`, and `get_infix_sympy` for non-graph output.
7. **Optimize constants only after shapes are stable.** Use differentiable
   PyTorch operations and a float target. If using a `candidate_wrapper`, it
   must be callable as `(func, X) -> wrapped_output` and remain differentiable.
   `Program.optimize_constants` uses
   MSE plus LBFGS by default; inspect `history`, `free_consts.class_values`,
   `free_consts.spe_values`, `is_opti`, and `opti_steps`.
8. **Save and reload deliberately.** Use the run visualizer/logger paths to
   identify the generated Pareto CSV/PKL. Prefer PKL for programs and Class SR
   expressions with spe constants. Use CSV loading only for non-spe Pareto
   fronts and pass a SymPy symbol dictionary when assumptions matter.
9. **Fall back when optional display tools are absent.** Missing `latex`,
   `pygraphviz`, `dot2tex`, `pdflatex`, `pdf2image`, or Pillow affects images
   and tree rendering, not prefix encoding or plain text. Do not turn a display
   dependency into a core-workflow failure.

## Input/output contracts

- **Library inputs:** `X_names` length must match the first dimension of data;
  units rows must align with their names and use at most seven dimensions.
  `fixed_consts_units`, `free_consts_units`, and spe-constant units align with
  their corresponding value/name arrays. For the toolkit convenience API,
  `free_consts_init_val` and `spe_free_consts_init_val` are array-like values
  aligned with names; low-level tokenization may use name-to-value dicts.
- **Prefix inputs:** outer sequence is a batch; each inner sequence is a list
  or NumPy array of strings for `encode`, or Python integers for `decode`.
  Variable expression lengths are accepted by `decode` and padded internally.
  One-hot output is for model input and is not a valid direct input to
  `decode`.
- **Program inputs:** `X` is `(n_dim, n_samples)`, target and weights are
  `(n_samples,)`. For flattened multiple realizations, concatenate datasets in
  realization order and pass `n_samples_per_dataset` with the matching counts.
- **Constant outputs:** `class_values` has shape
  `(batch_size, n_class_free_const)`; `spe_values` has shape
  `(batch_size, n_spe_free_const, n_realizations)`. A scalar spe initializer is
  broadcast; a vector must have exactly `n_realizations` entries.
- **Monitoring outputs:** `RunLogger.get_pareto_front()` returns
  `(complexities, programs, rewards, rmse)`. `read_pareto_pkl` returns a list
  of `Program` objects; `read_pareto_csv` returns SymPy expressions, or a
  `(expressions, DataFrame)` tuple when `return_df=True`.

## Verification and native evidence

The related native candidates are:

- `physo.toolkit.tests.codec_UnitTest`
- `physo.toolkit.tests.random_sampler_UnitTest`
- `physo.physym.tests.program_UnitTest`
- `physo.physym.tests.vect_programs_UnitTest`
- `physo.physym.tests.library_UnitTest`
- `physo.physym.tests.token_UnitTest`
- `physo.physym.tests.tokenize_UnitTest`
- `physo.physym.tests.dataset_UnitTest`
- `physo.physym.tests.free_const_UnitTest`
- `physo.physym.tests.program_display_UnitTest`
- `physo.learn.tests.monitoring_UnitTest`

Run the bundled CPU-safe checks before using a generated result:

```bash
python skills/disco/physo/sub-skills/toolkit/scripts/check_toolkit_roundtrip.py
python skills/disco/physo/sub-skills/toolkit/scripts/smoke_toolkit.py
```

These scripts do not access the network, plot, or launch a long search. They
exercise encoding/decoding, an expected unknown-token failure, bounded random
sampling, `Dataset` shape handling, and a small LBFGS constant fit.

## Troubleshooting

Use [troubleshooting](references/troubleshooting.md) when an error is not
immediately explained. In particular, check exact library names and token
arity before changing code; check spe initializer and flattened-data shapes
before changing an optimizer; and use text/SymPy output before installing
optional renderers. If the request asks for an SR/Class SR run or a benchmark
problem loader, hand it to the sibling skill instead of extending this route.
