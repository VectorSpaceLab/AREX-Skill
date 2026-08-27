---
name: runtime-data
description: "Guides SecretFlow local runtime setup, device objects, and
  federated data containers such as FedNdarray and federated dataframes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Runtime and data

Use this sub-skill when the task is about getting SecretFlow running locally,
creating devices, moving objects between devices, or shaping data into the
federated containers used by later model or component workflows.

## Owns

- `sf.init`, `sf.shutdown`, and the basic local simulation flow
- `PYU`, `SPU`, `HEU`, `TEEU`
- `reveal`, `to`, `wait`, and device-object transfer rules
- `FedNdarray`, `HDataFrame`, `VDataFrame`, `MixDataFrame`, `partition`
- CSV/ORC IO and small data-loading helpers
- common direct-device and partition-alignment failures

## Does not own

- component CLI / evaluation / export workflows — use `component-cli`
- preprocessing/statistics/model training — use `analytics`
- PSI, Kuscia, TEEU deployment, or production orchestration — use `privacy-orchestration`

## Trigger phrases

Use this route when a user asks things like:
- how to start SecretFlow locally
- how to reveal or transfer objects between devices
- how to build a vertical or horizontal dataframe
- how to read CSV or ORC into a federated structure
- why `to(SPU)` or `to(HEU)` failed
- how to align partitions or select columns across parties

## Reading order

1. Read `references/runtime-data.md` for the API map and flow choices.
2. Read `references/troubleshooting.md` in the root skill when install/runtime
   symptoms are not clearly local to this workflow.
3. Use `scripts/local_quickstart.py` as the tiny smoke helper when you need to
   confirm that a local runtime works from the target environment.

## Workflow

1. Confirm the party/device layout first. Decide whether the workflow is a
   simple local simulation or an explicit multi-party cluster config.
2. Put data on a plain device first, then move it onward. Direct placement on
   SPU or HEU is intentionally rejected by the runtime.
3. For federated dataframes, verify which party owns each partition before you
   start selecting, joining, or assigning columns.
4. If a task only needs a tiny end-to-end proof, run the bundled quickstart
   smoke helper and inspect its output before moving on to a larger workflow.
5. When the task later needs component evaluation or model training, hand off
   to the sibling sub-skill rather than expanding this one.

## Common decisions

- Use `address='local'` for the fastest local simulation proof.
- Use `cluster_config` only when the task truly depends on explicit party
  addresses and ports.
- Prefer `PYU` as the staging device for plain Python objects and small data.
- Treat `reveal` as a last-mile inspection tool, not as the default data path.

## Bundled files

- `references/runtime-data.md` — API table, quick-start flow, and runtime caveats.
- `scripts/local_quickstart.py` — minimal local hello-world smoke helper.
