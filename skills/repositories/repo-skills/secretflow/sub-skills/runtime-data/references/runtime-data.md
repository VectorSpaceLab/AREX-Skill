# Runtime and data reference

This reference covers the basic SecretFlow runtime, device objects, and
federated data containers that appear before any model-training or component
workflow.

## Core runtime APIs

| API | Purpose | Notes |
| --- | --- | --- |
| `sf.init(...)` | Start a local or clustered SecretFlow runtime | `address='local'` is the safest local smoke path |
| `sf.shutdown()` | Stop the runtime | Call before re-initializing a local session |
| `sf.PYU('alice')` | Create a plain device for a party | Used as the staging device for normal Python objects |
| `sf.SPU(cluster_def)` | Create a secure-computation device | Needs a cluster definition with nodes and runtime config |
| `sf.HEU(...)` | Create a homomorphic-encryption device | Stage data on a plain device first |
| `sf.TEEU('carol', mr_enclave='')` | Create a TEE device | Simulation mode can omit a real enclave value |
| `sf.reveal(obj)` | Pull a device object back to plaintext | Use sparingly; this is the privacy boundary |
| `sf.wait(obj_or_list)` | Wait for device objects to finish | Helpful when tasks write files or have side effects |
| `secretflow.device.driver.to(device, data)` | Send plaintext or device data to a device | Direct-to-SPU and direct-to-HEU placement are rejected |
| `secretflow.data.partition(...)` | Wrap partition data | Used by dataframe partition containers |

## Federated containers

| Container | What it represents | Typical owner module |
| --- | --- | --- |
| `FedNdarray` | Federated array split across parties | `secretflow.data.ndarray` |
| `HDataFrame` | Horizontal federation: the same columns, different rows | `secretflow.data.horizontal` |
| `VDataFrame` | Vertical federation: different columns, same rows | `secretflow.data.vertical` |
| `MixDataFrame` | A mix of horizontal and vertical partitions | `secretflow.data.mix` |

## Read helpers

| Helper | Purpose | Important parameters |
| --- | --- | --- |
| `secretflow.data.horizontal.read_csv(...)` | Load a horizontal dataframe | `filepath`, `aggregator`, `comparator`, `backend` |
| `secretflow.data.vertical.read_csv(...)` | Load a vertical dataframe | `filepath`, `usecols`, `dtypes`, `converters`, `spu`, `keys`, `drop_keys`, `psi_protocl`, `backend` |
| `secretflow.data.read_orc(...)` | Read ORC into the matching container | Usually paired with the IO helpers from the same module family |

## Quick flow

1. Start with `sf.init(parties=['alice', 'bob', 'carol'], address='local',
   debug_mode=True)` for the bundled proof-of-life smoke helper when the build
   does not register the simulation backend.
2. Create the plain devices you need, usually `PYU('alice')` and `PYU('bob')`.
3. Put the first object on a plain device, then move it to the secure or TEE
   device if the workflow needs it.
4. Build federated dataframes from partitions, then use their pandas-like
   selection and aggregation methods.
5. Reveal only the tiny result you need to inspect.

## Data-shape guidance

- Horizontal data keeps the same feature columns on each party and splits rows.
- Vertical data keeps the same sample ids and splits columns by party.
- Mixed data combines both forms and is the most common source of alignment
  mistakes.
- If you need to use a secure device, stage the source value on a plain device
  first; the runtime intentionally blocks direct placement on SPU and HEU.

## Troubleshooting

### `You cannot put data to SPU directly`
Stage the object on a `PYU` first and then move it to `SPU`.

### `You cannot put data to HEU directly`
Stage the object on a `PYU` first and then move it to `HEU`.

### Device mismatch or missing partition errors
Check the party-to-partition mapping before selecting columns or assigning
values.

### `sf.init` fails with an explicit cluster config
Confirm that the party names and addresses match the devices you create, and
that the ports are unique and reachable.

### Objects appear stuck
Use `sf.wait(...)` on the returned device objects before revealing them.

### local quickstart fails after a previous run
Call `sf.shutdown()` first and then initialize again.

## Cross-links

- Root troubleshooting: `../../references/troubleshooting.md`
- Smoke helper: `../scripts/local_quickstart.py`
