---
name: local-launchers
description: "Run and author service-free local FATE launchers with
  fate.arch.launchers, dataframe readers, and direct fate.ml module APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Local Launchers

Use this sub-skill when the task is to run, inspect, or author **service-free local FATE launchers** for direct `fate.ml` modules. These launchers simulate federated parties with local multiprocessing and do **not** require FateFlow, Pipeline, Docker, or a running FATE service.

## Route map

- Read [references/launcher-recipes.md](references/launcher-recipes.md) for local launcher structure, party/data rules, and recipes for SSHE LR/LinR, SecureBoost, Pearson, Hetero/Homo NN, FedPass, and SMPC-style `proc` launchers.
- Read [references/module-api.md](references/module-api.md) when selecting imports, checking constructor signatures, choosing `CSVReader`/`PandasReader`/`TableReader`, or wiring `create_context`, `launch`, `HfArgumentParser`, and `fate.ml` trainers.
- Run [scripts/check_launcher_imports.py](scripts/check_launcher_imports.py) for cheap import/signature checks before any training. It is safe by default and will not spawn launcher training unless an explicit heavy-run flag is supplied.
- Read [references/troubleshooting.md](references/troubleshooting.md) for missing `fate_utils`/`setuptools`, bad party tuples, missing CSVs, local-vs-cluster context mistakes, GPU-only assumptions, and SMPC import issues.

## Use this instead of service-backed routes when

- The user says “local launcher”, “without FateFlow”, “no Pipeline service”, “direct `fate.ml` API”, “multiprocess launcher”, or “local federated simulation”.
- The user has local CSV/Pandas data and wants to test a FATE algorithm module without uploading tables through FateFlow.
- The task is to adapt launcher patterns around `launch(run_fn)`, `create_context(...)`, `CSVReader`, `PandasReader`, `TableReader`, or local `TrainingArguments`.

## Route elsewhere

- For installing PyPI packages, starting/stopping FateFlow services, Docker/Compose, cluster service ports, or service smoke checks, use [../deployment/SKILL.md](../deployment/SKILL.md).
- For service-backed `FateFlowPipeline` workflows, upload/Reader/components, model deployment, or service prediction, use [../pipeline-workflows/SKILL.md](../pipeline-workflows/SKILL.md).
- For `python -m fate.components`, component descriptors, component `task-schema`, or component CLI execution planning, use [../component-runtime/SKILL.md](../component-runtime/SKILL.md).

## Safe default workflow

1. Confirm this is a local launcher task, not a FateFlow Pipeline task.
2. Select the party layout:
   - Hetero algorithms: usually `guest:9999 host:10000`.
   - Homo NN FedAVG: `guest`, `host`, and `arbiter`; the arbiter is the server.
   - SMPC-style `proc` wrappers: parties must match the target MPC module’s expectation.
3. Check imports and signatures before training:
   ```bash
   python scripts/check_launcher_imports.py --check-standard
   python scripts/check_launcher_imports.py \
     --module fate.ml.glm.hetero.sshe --object SSHELogisticRegression
   ```
4. Prepare tiny local data first. Guest-side hetero tabular recipes normally carry labels; host-side hetero recipes normally omit labels but share the match-id column.
5. Only after import/data checks pass, run `launch(run_fn)` or an explicit launcher command. Treat this as a heavy training run because it spawns one process per party and may run cryptographic or neural-network code.

## Backend caveat

The verified construction baseline was CPU-only. Local launcher imports, dataframe readers, component-free algorithms, and CPU PyTorch patterns are in scope. GPU and DeepSpeed-on-Eggroll are documented optional/advanced paths, not required or verified defaults for this sub-skill.
