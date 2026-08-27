---
name: objective-functions-and-speedups
description: "Shape scikit-opt objectives, benchmark functions, and safe run-mode speedups."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# objective-functions-and-speedups

Use this sub-skill when a task needs objective-function contracts, built-in `sko.demo_func` benchmarks, `set_run_mode` acceleration/cache choices, or optional plotting/GPU dependency guidance for `scikit-opt` / `sko`.

## Route here when

- An optimizer fails because the objective receives the wrong shape or returns the wrong shape.
- You need to convert a scalar objective to vectorization mode, cached mode, or a safe thread-based mode.
- You need a quick built-in benchmark such as `sphere`, `schaffer`, `rosenbrock`, or `ackley`.
- You need to explain `matplotlib`, `pandas`, `joblib`, `torch`, or CUDA as optional dependencies rather than core requirements.

## Route elsewhere

- Algorithm-specific parameters, bounds, constraints, continuation, and history interpretation belong to the owning algorithm sub-skill.
- GA integer/precision encoding and the `x2gray` relationship belong to `../genetic-algorithms/`.
- TSP route-cost design and permutation outputs belong to `../routing-and-combinatorial/`.

## Bundled references

- Read [references/objective-contracts.md](references/objective-contracts.md) before writing or adapting objective functions for scalar, vectorized, cached, threaded, or method-based use.
- Read [references/acceleration.md](references/acceleration.md) when choosing `set_run_mode(func, mode)`, deciding whether to use `common`, `vectorization`, `cached`, `multithreading`, `multiprocessing`, `joblib`, or interpreting the `parallel` alias.
- Read [references/demo-functions.md](references/demo-functions.md) when selecting built-in benchmark/demo objective functions or using `function_for_TSP` as a tiny route fixture generator.
- Read [references/troubleshooting.md](references/troubleshooting.md) when run-mode assertions, vectorized shape errors, cached input errors, multiprocessing/joblib failures, plotting display problems, or optional GPU issues appear.

## Bundled script

- Run [scripts/smoke_run_modes.py](scripts/smoke_run_modes.py) to check that the installed package can execute tiny GA objectives in `common`, `vectorization`, `cached`, and `multithreading` modes without source-checkout data, plotting, network, or GPU requirements.

## Fast operating rules

1. Set the run mode before constructing the optimizer; constructors wrap the function immediately.
2. Use scalar objectives for `common`, `multithreading`, `multiprocessing`, `cached`, and `joblib`: one candidate vector in, one finite scalar out.
3. Use vectorized objectives only after adapting the function to accept an `X` matrix and return one value per row.
4. Treat multiprocessing, joblib, plotting, pandas workflows, and `GA.to(device)` as optional surfaces with extra dependency/platform checks.
