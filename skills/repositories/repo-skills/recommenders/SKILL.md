---
name: recommenders
description: "Use Microsoft Recommenders to prepare recommendation data, train
  and choose recommender models, evaluate offline metrics, tune experiments, and
  plan optional Spark/GPU/cloud workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Microsoft Recommenders

Use this repo skill when a task names `recommenders`, Microsoft/Recommenders, or needs package-specific guidance for recommendation-system data preparation, model selection/training/scoring, offline metrics, tuning, benchmarks, or operationalization patterns.

## Backend truth for this skill

- Verified in the base CPU scope: package import, pandas data utilities/splitters, Python evaluation metrics, SAR, TF-IDF utilities, Cornac/LightGBM helper imports, parameter sweep, K8s sizing utilities, and bundled tiny smoke scripts.
- Optional and not verified in this CPU scope: Spark/PySpark workflows, TensorFlow/PyTorch deep-learning/GPU models, AzureML, Databricks, AKS, SARplus, and experimental dependencies.
- A visible GPU or Spark host is not enough. Verify the matching package extra, framework, system runtime, data, and credentials before claiming backend coverage.

## Installation quick start

For ordinary CPU package use:

```bash
pip install recommenders
python - <<'PY'
import recommenders
print(recommenders.__version__)
PY
```

Optional workflow families use documented extras such as `recommenders[gpu]`, `recommenders[spark]`, or `recommenders[experimental]`. Install only the extra required by the selected workflow; avoid broad `[all]` installs for small tasks.

## Route map

- [data-preparation](sub-skills/data-preparation/SKILL.md): load or validate interaction data, split train/test data, sample negatives, convert sparse/LibFFM formats, and handle dataset download/cache issues.
- [modeling](sub-skills/modeling/SKILL.md): choose model families, instantiate, fit, score, and recommend with SAR, TF-IDF, Cornac, LightGBM helpers, optional Spark/deep-learning/news/sequential/experimental models, and run tiny model smokes.
- [evaluation](sub-skills/evaluation/SKILL.md): compute rating, ranking, diversity, novelty, serendipity, and optional Spark metrics; fix column/type/top-k metric failures.
- [operations-and-tuning](sub-skills/operations-and-tuning/SKILL.md): plan parameter sweeps, NNI/AzureML tuning, Databricks/AKS operationalization, benchmark comparisons, and environment/backend readiness.

## Shared references and scripts

- Read [package-overview.md](references/package-overview.md) for module families, extras, and workflow-to-sub-skill mapping.
- Read [troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, optional dependency, backend, cloud, and data-download failures.
- Read [repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is stale for a different checkout or package version.
- Run [check_recommenders_environment.py](scripts/check_recommenders_environment.py) to check base imports and optionally run all bundled CPU smoke helpers from an installed skill tree.

## Suggested workflow order

1. Start with `data-preparation` to validate columns, split strategy, and candidate generation.
2. Use `modeling` to choose the smallest model family that matches the data and backend.
3. Use `evaluation` to select metrics and validate prediction dataframe contracts.
4. Use `operations-and-tuning` only when the user needs tuning, benchmarks, deployment, or backend readiness beyond a local CPU smoke.

## Safety boundaries

- Do not run dataset downloads, notebooks, cloud scripts, Spark jobs, GPU training, benchmark loops, or cluster mutations unless the user explicitly authorizes the needed network, credentials, compute, and time budget.
- Do not treat skipped optional native cases as passing. Report them as optional or unverified.
- Runtime instructions in this skill are self-contained; do not ask a future agent to open the original source checkout for normal package usage.
