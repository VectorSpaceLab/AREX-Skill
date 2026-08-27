# Package Overview

## Purpose

Read this when you know you need `scikit-opt` but you have not yet decided which family, run mode, or route representation to use. This page summarizes the verified package surface so you can choose the right sub-skill quickly.

## Public package facts

- Distribution name: `scikit-opt`
- Import package: `sko`
- Verified snapshot version: `0.6.6`
- Core requirements: `numpy`, `scipy`
- Optional presentation/development surfaces: `matplotlib`, `pandas`, `joblib`, `torch`

## Workflow families

| Family | Main classes | Best for |
| --- | --- | --- |
| GA-family optimization | `GA`, `EGA`, `RCGA` | Bounded optimization, integer grids, custom operators, continuation runs. |
| Continuous optimization | `DE`, `PSO`, `SAFast`, `SABoltzmann`, `SACauchy`, `AFSA` | Real-valued optimization, penalties, swarm search, or temperature-based search. |
| Route/permutation optimization | `GA_TSP`, `SA_TSP`, `ACA_TSP`, `IA_TSP` | TSP-style or permutation search with a distance matrix and route cost. |
| Objective shaping and speedups | `set_run_mode`, `func_transformer`, `sko.demo_func` | Scalar/vectorized objective contracts, caching, threads, and benchmark functions. |

## Common user signals and the owning sub-skill

| User signal | Owns it |
| --- | --- |
| "genetic algorithm", "elitist GA", "real-coded GA", "custom selection", "integer precision" | `genetic-algorithms` |
| "differential evolution", "particle swarm", "simulated annealing", "fish swarm", "constrained real-valued" | `continuous-optimizers` |
| "TSP", "route", "permutation", "distance matrix", "fixed depot", "tour" | `routing-and-combinatorial` |
| "vectorization", "cached", "multithreading", "benchmark function", "objective shape", "GA.to(device)" | `objective-functions-and-speedups` |

## Notable verified behavior

- `PSO` accepts inequality constraints but not equality constraints in the verified package version.
- `PSO_TSP` construction raised a `TypeError` during inspection in version `0.6.6`; route users should prefer the other route optimizers in this skill snapshot.
- `GA` and `EGA` require even population sizes.
- `set_run_mode(func, mode)` should be applied before constructing the optimizer.

## How to choose

If the task names a class, use the sub-skill that owns that class. If the task only names the problem shape, use this table and the root router:
- discrete or mixed precision -> `genetic-algorithms`
- continuous objective -> `continuous-optimizers`
- permutation / TSP -> `routing-and-combinatorial`
- objective shape / speed / caching / demo functions -> `objective-functions-and-speedups`
