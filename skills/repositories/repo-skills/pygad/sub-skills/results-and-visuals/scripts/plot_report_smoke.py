#!/usr/bin/env python3
"""Headless smoke for PyGAD result visualizations and PDF reports.

This script uses only public PyGAD APIs, writes outputs to a temporary
workspace, and fails loudly when required optional dependencies are missing.
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

import numpy as np
import pygad


def require_matplotlib():
    try:
        import matplotlib
    except ImportError as exc:  # pragma: no cover - dependency gate
        raise SystemExit(
            "plot_report_smoke.py requires matplotlib. Install with "
            "`pip install pygad[visualize]` for plots or `pip install "
            "pygad[report]` for PDF exports."
        ) from exc

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    return plt


def require_reportlab():
    try:
        import reportlab  # noqa: F401
    except ImportError as exc:  # pragma: no cover - dependency gate
        raise SystemExit(
            "plot_report_smoke.py requires reportlab for PDF exports. "
            "Install with `pip install pygad[report]` or `pip install "
            "reportlab`."
        ) from exc


def make_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger(f"pygad.results_and_visuals_smoke.{log_path.stem}")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    logger.propagate = False

    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    return logger


def flush_logger(logger: logging.Logger) -> None:
    for handler in logger.handlers:
        handler.flush()


def assert_written(path: Path, label: str, min_bytes: int = 1) -> None:
    if not path.exists():
        raise RuntimeError(f"{label} was not written: {path.name}")
    if path.stat().st_size < min_bytes:
        raise RuntimeError(f"{label} is empty: {path.name}")


def run_single_objective(tmpdir: Path, logger: logging.Logger, plt) -> None:
    def fitness_func(ga_instance, solution, solution_idx):
        return float(np.sum(solution))

    ga = pygad.GA(
        num_generations=4,
        num_parents_mating=2,
        sol_per_pop=6,
        num_genes=3,
        fitness_func=fitness_func,
        save_solutions=True,
        save_best_solutions=True,
        random_seed=7,
        suppress_warnings=True,
        logger=logger,
    )
    ga.run()

    if not ga.run_completed or ga.generations_completed < 1:
        raise RuntimeError("single-objective smoke run did not complete")

    summary_text = ga.summary(
        print_step_parameters=False,
        print_parameters_summary=True,
    )
    if "PyGAD Lifecycle" not in summary_text or "Population Size" not in summary_text:
        raise RuntimeError("summary() did not return the expected lifecycle text")

    if ga.best_solution_generation < 0:
        raise RuntimeError("best_solution_generation was not populated after run()")

    plot_specs = [
        ("soo_fitness.png", ga.plot_fitness, {}),
        ("soo_new_solution_rate.png", ga.plot_new_solution_rate, {}),
        ("soo_genes_all.png", ga.plot_genes, {"solutions": "all", "graph_type": "boxplot"}),
        ("soo_fitness_band.png", ga.plot_fitness_band, {}),
        ("soo_population_diversity.png", ga.plot_population_diversity, {}),
    ]
    for filename, method, kwargs in plot_specs:
        path = tmpdir / filename
        fig = method(save_dir=str(path), **kwargs)
        assert_written(path, filename)
        plt.close(fig)


def run_multi_objective(tmpdir: Path, logger: logging.Logger, plt) -> None:
    def fitness_func(ga_instance, solution, solution_idx):
        total = float(np.sum(solution))
        spread = float(np.sum(np.asarray(solution) ** 2))
        return [total, -spread]

    ga = pygad.GA(
        num_generations=4,
        num_parents_mating=2,
        sol_per_pop=6,
        num_genes=3,
        fitness_func=fitness_func,
        parent_selection_type="nsga2",
        save_solutions=True,
        save_best_solutions=True,
        random_seed=11,
        suppress_warnings=True,
        logger=logger,
    )
    ga.run()

    if not ga.run_completed or ga.generations_completed < 1:
        raise RuntimeError("multi-objective smoke run did not complete")

    plot_specs = [
        ("moo_front_curve.png", ga.plot_pareto_front_curve, {}),
        ("moo_front_pcp.png", ga.plot_pareto_front_pcp, {}),
        ("moo_front_scatter_matrix.png", ga.plot_pareto_front_scatter_matrix, {}),
        ("moo_front_heatmap.png", ga.plot_pareto_front_heatmap, {}),
        ("moo_hypervolume.png", ga.plot_non_dominated_hypervolume, {}),
        ("moo_front_evolution.png", ga.plot_pareto_front_evolution, {"every_k": 2}),
        ("moo_genes_best.png", ga.plot_genes, {"solutions": "best", "graph_type": "plot"}),
    ]
    for filename, method, kwargs in plot_specs:
        path = tmpdir / filename
        fig = method(save_dir=str(path), **kwargs)
        assert_written(path, filename)
        plt.close(fig)

    report_path = Path(
        ga.generate_report(
            filename=str(tmpdir / "moo_report"),
            title="PyGAD results smoke",
            include_plots="all",
            notes="Headless smoke export.",
        )
    )
    if report_path.suffix.lower() != ".pdf":
        raise RuntimeError("generate_report() did not append a .pdf suffix")
    assert_written(report_path, "report", min_bytes=1500)


def main() -> None:
    plt = require_matplotlib()
    require_reportlab()

    with tempfile.TemporaryDirectory(prefix="pygad-results-smoke-") as tmp:
        tmpdir = Path(tmp)
        log_path = tmpdir / "pygad_results.log"
        logger = make_logger(log_path)
        try:
            run_single_objective(tmpdir, logger, plt)
            run_multi_objective(tmpdir, logger, plt)
            flush_logger(logger)

            log_text = log_path.read_text(encoding="utf-8")
            if "PyGAD Lifecycle" not in log_text:
                raise RuntimeError("summary() output was not written to the log file")
        finally:
            for handler in logger.handlers:
                handler.close()
            logger.handlers.clear()

    print("results-and-visuals smoke passed")


if __name__ == "__main__":
    main()
