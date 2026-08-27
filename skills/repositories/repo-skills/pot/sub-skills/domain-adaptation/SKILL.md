---
name: domain-adaptation
description: "Use POT optimal-transport domain-adaptation estimators, mappings,
  JCPOT target-shift adaptation, color/image transfer recipes, optional DR/WDA
  routes, and nearest Brenier potentials."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# POT Domain Adaptation

Use this sub-skill when the task is to align source and target sample distributions with POT domain-adaptation estimators: `EMDTransport`, `SinkhornTransport`, class-regularized Sinkhorn transports, `MappingTransport`, `LinearTransport`, `LinearGWTransport`, `UnbalancedSinkhornTransport`, `JCPOTTransport`, `NearestBrenierPotential`, `ot.mapping` map estimators, image/color-transfer recipes, or optional `ot.dr` WDA/EWCA workflows.

Read [references/api-reference.md](references/api-reference.md) to choose APIs, preserve verified signatures and defaults, use the correct `fit`/`transform` argument names, validate attributes such as `cost_`, `coupling_`, `mapping_`, `A_`, `B_`, `proportions_`, `phi`, and `G`, and decide which optional dependencies are required.

Read [references/workflows.md](references/workflows.md) for copy-pasteable workflows covering deterministic 2D EMD/Sinkhorn adaptation, class-regularized transport, semi-supervised labels with missing label `-1`, `MappingTransport` and linear Gaussian maps, multi-source JCPOT, RGB image/color adaptation from user-provided arrays, optional WDA/EWCA, and optional nearest Brenier potential usage.

Read [references/troubleshooting.md](references/troubleshooting.md) when `Xs`/`Xt`/`ys`/`yt` are missing or misnamed, array shapes or labels are invalid, normalization or `out_of_sample_map` choices fail, convergence stalls, optional `cvxpy`/`scikit-learn`/`autograd`/`pymanopt` dependencies are missing, JCPOT source lists are malformed, or image/color data has the wrong shape or range.

Run [scripts/domain_adaptation_smoke.py](scripts/domain_adaptation_smoke.py) after installing POT to exercise deterministic NumPy-only estimator, mapping, JCPOT, and dependency-probe fixtures without plotting, downloads, native test execution, original checkout access, or optional dependency installation:

```bash
python scripts/domain_adaptation_smoke.py --case all --json
```

Route low-level balanced solver math to `core-solvers`, unbalanced/partial mass modeling fundamentals to `unbalanced-partial`, GW/FGW graph modeling and optional GNN layer details to `gromov`, optional backend or accelerator installation to `backend-and-batch`, and large-scale approximation families to `sliced-gaussian-large-scale` unless the current task is specifically an OT domain-adaptation estimator or map.
