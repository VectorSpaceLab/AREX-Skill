"""Tiny CPU-only smoke for pymoo ElementwiseProblem with starmap threads."""

from __future__ import annotations

from multiprocessing.pool import ThreadPool

import numpy as np
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.core.problem import ElementwiseProblem
from pymoo.optimize import minimize
from pymoo.parallelization.starmap import StarmapParallelization


class TinyElementwiseSphere(ElementwiseProblem):
    """One-candidate-at-a-time problem suitable for elementwise runners."""

    def __init__(self, **kwargs):
        super().__init__(
            n_var=4,
            n_obj=1,
            n_ieq_constr=0,
            xl=-2.0,
            xu=2.0,
            **kwargs,
        )

    def _evaluate(self, x, out, *args, **kwargs):
        # Keep this deterministic; stochastic simulations should seed explicitly.
        out["F"] = float(np.sum((np.asarray(x) - 0.25) ** 2))


def run_smoke() -> None:
    pool = ThreadPool(2)
    try:
        runner = StarmapParallelization(pool.starmap)
        problem = TinyElementwiseSphere(elementwise_runner=runner)
        algorithm = GA(pop_size=12)

        res = minimize(
            problem,
            algorithm,
            termination=("n_gen", 3),
            seed=7,
            verbose=False,
        )

        f = np.asarray(res.F, dtype=float)
        assert f.size > 0, "expected at least one objective value"
        assert np.isfinite(f).all(), "objective values must be finite"
        assert res.algorithm.evaluator.n_eval > 0, "pymoo evaluator did not run"

    except BaseException:
        pool.terminate()
        pool.join()
        raise
    else:
        pool.close()
        pool.join()

    print(
        "parallel elementwise smoke passed: "
        f"n_eval={res.algorithm.evaluator.n_eval}, best_F={float(np.min(f)):.6g}, "
        f"exec_time={res.exec_time:.6f}s"
    )


if __name__ == "__main__":
    run_smoke()
