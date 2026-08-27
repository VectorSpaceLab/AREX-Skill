---
name: cirq
description: "Use Cirq to build, simulate, transform, serialize, validate, and
  provider-package quantum circuits."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Cirq Repo Skill

Use this skill when a task is about Cirq, the Python framework for quantum
circuits and near-term quantum computing workflows. It covers the Cirq package
family: `cirq`/`cirq-core`, `cirq-google`, `cirq-ionq`, `cirq-aqt`,
`cirq-pasqal`, and `cirq-web`.

## First checks

- For package layout, Python support, optional dependencies, and route selection,
  read [references/package-overview.md](references/package-overview.md).
- For install/import, provider credential, serialization, or environment issues,
  read [references/troubleshooting.md](references/troubleshooting.md).
- For source freshness, read
  [references/repo-provenance.md](references/repo-provenance.md) before relying
  on this skill for a different checkout or package version.
- To verify an active Python environment without credentials or network calls,
  run [scripts/check_cirq_environment.py](scripts/check_cirq_environment.py)
  with `--help` or `--text`.

## Install stance

For ordinary package use, prefer public packages:

```bash
python -m pip install cirq          # full Cirq family
python -m pip install cirq-core     # core circuits/simulation only
python -m pip install cirq-google   # add Google Quantum AI package
```

Cirq requires Python 3.11+. Local circuit construction and CPU simulation do not
require CUDA, ROCm, MPS, TPU, cloud credentials, or live quantum hardware.
Provider packages can be imported offline, but live service execution requires
provider credentials and account/project/target access.

## Route by task

| User task | Read next |
| --- | --- |
| Build circuits, choose qubit classes, work with gates/operations/moments, debug measurement keys, parameters, diagrams, custom gates, JSON/QASM basics | [core-circuits-and-ops](sub-skills/core-circuits-and-ops/SKILL.md) |
| Run local simulations, sample measurements, sweep parameters, inspect results/histograms/state vectors/density matrices, add noise/channels | [simulation-study-and-noise](sub-skills/simulation-study-and-noise/SKILL.md) |
| Optimize, decompose, transform, route, or compile circuits to a gateset, topology, or provider constraint | [transformers-and-compilation](sub-skills/transformers-and-compilation/SKILL.md) |
| Implement or validate algorithm examples, QFT/phase estimation/Grover/QAOA-like circuits, Pauli observables, expectation values | [algorithms-and-observables](sub-skills/algorithms-and-observables/SKILL.md) |
| Use `cirq_google`, IonQ, AQT, Pasqal, `cirq_web`, provider serializers, credentials, offline provider validation, or JSON custom resolvers | [hardware-providers-and-serialization](sub-skills/hardware-providers-and-serialization/SKILL.md) |

## Operating guidance

1. Start with the narrowest sub-skill that matches the user intent. Avoid
   answering provider, simulator, transformer, or algorithm questions only from
   the root router.
2. Prefer verified public APIs and bundled examples over memory. The sub-skill
   references include inspected signatures, workflow recipes, and failure modes.
3. Use bundled scripts only for safe local checks. They do not contact cloud
   services, download data, or require the original repository checkout.
4. For live provider execution, stop and verify credentials, project/account,
   target/processor, queue/service availability, and provider-specific supported
   gates before calling remote APIs.
5. If a circuit fails provider serialization or device validation, route first
   through `transformers-and-compilation` to decompose, route, or target-gateset
   optimize the circuit.
6. If a sampled or simulated result looks wrong, check measurement key order,
   qubit order, unresolved parameters, random seeds, simulator choice, and noise
   model assumptions before changing algorithm logic.

## Bundled root assets

- [references/package-overview.md](references/package-overview.md) — package
  family, dependency stance, and top-level route map.
- [references/troubleshooting.md](references/troubleshooting.md) — cross-cutting
  install/import, optional dependency, provider credential, and serialization
  recovery steps.
- [references/repo-provenance.md](references/repo-provenance.md) — source commit,
  version, and evidence baseline for staleness checks.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json)
  — structured scenario metadata for managed repo-skill import.
- [scripts/check_cirq_environment.py](scripts/check_cirq_environment.py) — local
  import/version/tiny simulation/JSON roundtrip diagnostic.
