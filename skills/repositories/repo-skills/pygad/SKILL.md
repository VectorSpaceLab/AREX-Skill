---
name: pygad
description: "Route PyGAD genetic-algorithm optimization, benchmarks,
  visualization/reporting, and neural-model weight workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# PyGAD repo skill

Use this repo skill when a task involves PyGAD, the Python genetic-algorithm package from `GeneticAlgorithmPython`: creating or tuning `pygad.GA` runs, solving single- or multi-objective optimization problems, using bundled benchmark problems, plotting/reporting completed runs, or optimizing neural-network weights through PyGAD helpers.

## First checks

Install the core package when PyGAD is not already available:

```bash
python -m pip install pygad
```

Then verify the import in the same environment that will run the optimization:

```python
import pygad
print(pygad.__version__)
```

Core PyGAD usage needs `numpy` and `cloudpickle`. Optional plotting/reporting and deep-learning integrations need extra dependencies; see [references/installation.md](references/installation.md) before installing heavy extras.

## Route by task

| If the user asks for... | Read this sub-skill |
| --- | --- |
| Build or debug a `pygad.GA` fitness function, population, genes, operators, callbacks, stop criteria, save/load, single-objective optimization, or NSGA-II/NSGA-III custom multi-objective run | [sub-skills/genetic-algorithm/SKILL.md](sub-skills/genetic-algorithm/SKILL.md) |
| Use built-in benchmark classes (`Sphere`, `ZDT`, `DTLZ`, `Knapsack`, `TSP`) or quality indicators (`hypervolume`, IGD, GD, spacing) | [sub-skills/benchmarks/SKILL.md](sub-skills/benchmarks/SKILL.md) |
| Summarize, plot, export PNGs, handle headless `matplotlib`, configure logging, or generate a PDF report from a completed GA run | [sub-skills/results-and-visuals/SKILL.md](sub-skills/results-and-visuals/SKILL.md) |
| Optimize dense NN/CNN/Keras/PyTorch model weights with PyGAD (`pygad.nn`, `gann`, `cnn`, `gacnn`, `kerasga`, `torchga`) | [sub-skills/neural-networks/SKILL.md](sub-skills/neural-networks/SKILL.md) |

## Root references and scripts

- [references/capability-map.md](references/capability-map.md): high-level package map, module boundaries, and cross-sub-skill dependencies.
- [references/installation.md](references/installation.md): core install, optional extras, import checks, and backend/dependency choices.
- [references/troubleshooting.md](references/troubleshooting.md): cross-cutting install/import, optional dependency, runtime, and API triage.
- [references/repo-provenance.md](references/repo-provenance.md): source commit, version, and evidence baseline for refresh decisions.
- [scripts/pygad_quick_check.py](scripts/pygad_quick_check.py): safe import/API smoke that runs a tiny GA and reports optional dependency availability.
- [scripts/run_skill_smokes.py](scripts/run_skill_smokes.py): optional local verification helper that runs the bundled deterministic smoke scripts in this skill tree.

## Operating priorities

1. **Keep PyGAD's maximization convention explicit.** Convert losses/minimization objectives to higher-is-better fitness before constructing `pygad.GA`.
2. **Validate shapes early.** Most failures are inconsistent `initial_population`, `num_genes`, `gene_space`, custom operators, batch fitness returns, or model-weight vector restoration.
3. **Start with tiny deterministic runs.** Use `random_seed`, small populations, and short generation counts before scaling to expensive objective functions.
4. **Install only needed extras.** Plot/report dependencies and deep-learning frameworks are optional. Do not install TensorFlow/PyTorch unless the user's workflow requires them.
5. **Use bundled references/scripts instead of the original checkout.** This skill is self-contained; runtime guidance should not depend on reopening repository examples or docs.

## Handoff notes

- If the user is asking to perform a new downstream optimization experiment, load the relevant sub-skill in Researcher mode and execute the experiment there.
- If source APIs or docs changed after the provenance commit, refresh this repo skill before relying on old defaults.
- If a task depends on external services such as Vilvik cloud export, confirm credentials, service intent, and dependency installation separately; the safe default is local PyGAD execution only.
