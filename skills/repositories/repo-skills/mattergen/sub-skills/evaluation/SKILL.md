---
name: evaluation
description: "Evaluate MatterGen crystal structures with MatterSim or
  precomputed energies, matching ordered or disordered structures against
  compatible reference datasets and exporting aggregate, detailed, and
  relaxed-structure results."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MatterGen evaluation

Use this sub-skill when the task is to score generated crystal structures for
validity, uniqueness, novelty, stability, energy above hull, relaxation RMSD,
or related metrics. It covers MatterGen 1.0.3's evaluation API and CLI. It
does not generate structures, run DFT, or acquire large model/reference assets.

## Start with the mode decision

Choose exactly one mode before loading data:

- **Relaxed evaluation** (`relax=True`): pass structures to MatterSim's
  `BatchRelaxer`; its final structures and total energies are evaluated. Do not
  pass `energies`/`--energies_path` in this mode.
- **Precomputed-energy evaluation** (`relax=False`): pass already relaxed
  structures and one externally computed total energy per structure. The array
  must have the same count and order as the loader result.

The implementation raises if both `relax=True` and energies are supplied, even
though an older docstring says energies would be ignored. Use the safe wrapper
at [`scripts/evaluate_structures.py`](scripts/evaluate_structures.py) for
input/mode validation and clear errors; it only invokes package APIs when the
script is explicitly run.

Read the applicable reference before running:

- [`references/workflows.md`](references/workflows.md) for recipes, output
  precedence, and expensive/network boundaries.
- [`references/api-reference.md`](references/api-reference.md) for exact
  Python and CLI parameters, defaults, and metrics.
- [`references/data-formats.md`](references/data-formats.md) for structure,
  energy-array, reference, and output formats.
- [`references/troubleshooting.md`](references/troubleshooting.md) for
  install/backend, data, matcher, correction, and workflow failures.

## Minimal preflight

1. Confirm the input path exists and is one of `.xyz`, `.extxyz`, `.zip`, or a
   directory containing lowercase `.cif`, `.xyz`, or `.extxyz` files.
2. Record the loader order. A direct XYZ/EXTXYZ file is read frame-by-frame;
   a ZIP is extracted temporarily; a directory is traversed in the exact
   `os.listdir` order (not sorted). Keep any energy array in that same order.
3. For `relax=False`, load a one-dimensional, numeric, finite `energies.npy`
   and verify `len(energies) == len(structures)` before calling `evaluate`.
4. Select a matcher: `disordered` is the robust default for generated alloys,
   partial occupancies, and mixed ordered/disordered sets; use `ordered` only
   when the data and reference are genuinely ordered and strict reduced-formula
   grouping is intended.
5. Select a correction/reference pair. MP2020 is the historical benchmark
   pairing. TRI2024 (`TRI110Compatibility2024`) plus the TRI2024 reference is
   recommended for work outside historical benchmarking. Never mix a
   correction scheme with a reference corrected under another scheme.
6. Check device, MatterSim availability/cache, disk space for outputs, and
   whether a large relaxation is affordable. The wrapper does not download
   datasets or potential files.

## Canonical API

The package function is:

```python
evaluate(
    structures, relax=True, energies=None, reference=None,
    structure_matcher=DefaultDisorderedStructureMatcher(),
    save_as=None, save_detailed_as=None, potential_load_path=None,
    device="cuda", structures_output_path=None,
    energy_correction_scheme=MaterialsProject2020Compatibility(),
)
```

It returns a dictionary of aggregate metric values. With `reference=None`, the
metric evaluator selects the MP2020 preset, or the TRI2024 preset when the
TRI2024 correction object is supplied. A supplied reference is deserialized by
the CLI from the gzip-compressed LMDB format. Missing terminal systems can make
energy metrics unavailable while structure metrics remain computable; treat
warnings and absent metrics as results to investigate, not as zeros.

## CLI routing

The safe script uses these exact underscore flags:

```text
--structures_path PATH                 required
--relax {True,False}                   default True
--energies_path PATH                   required in no-relax mode
--structure_matcher {ordered,disordered}
--save_as PATH                         aggregate JSON
--save_detailed_as PATH                per-structure serialized table
--potential_load_path PATH             local MatterSim checkpoint
--reference_dataset_path PATH          .gz LMDB reference
--device DEVICE                        auto, cpu, cuda[:N], or mps
--structures_output_path PATH          relaxed EXTXYZ, relax mode only
--energy_correction_scheme {MP2020,TRI2024}
```

Example relaxed evaluation:

```bash
python <mattergen-skill-root>/sub-skills/evaluation/scripts/evaluate_structures.py \
  --structures_path results \
  --relax True --structure_matcher disordered \
  --reference_dataset_path data/reference_TRI2024correction.gz \
  --energy_correction_scheme TRI2024 \
  --save_as results/metrics.json \
  --save_detailed_as results/detailed_metrics.json \
  --structures_output_path results/relaxed.extxyz
```

Example with external energies:

```bash
python <mattergen-skill-root>/sub-skills/evaluation/scripts/evaluate_structures.py \
  --structures_path results.extxyz --relax False \
  --energies_path energies.npy --structure_matcher disordered \
  --reference_dataset_path data/reference_TRI2024correction.gz \
  --energy_correction_scheme TRI2024 --save_as metrics.json
```

## Interpret the result

The evaluator can report structure metrics (`precision`, `recall`,
`frac_unique_structures`, `frac_novel_structures`, `frac_novel_unique_structures`,
chemical-system novelty, validity, and composition validity), energy metrics
(`avg_energy_above_hull_per_atom`, `frac_stable_structures`,
`frac_novel_unique_stable_structures`), and relaxation RMSD when original and
final structures are both available. `energy_above_hull` is per atom; stability
uses the implementation's 0.1 eV/atom threshold. Detailed output exposes
per-structure columns such as `energy_above_hull`,
`self_consistent_energy_above_hull`, `stable`, `novel`, `unique`, and RMSD.

MatterSim energies are MLFF predictions, not DFT energies. Agreement with DFT
is not guaranteed, especially for uncommon chemistry; confirm important claims
with an explicitly documented DFT workflow. A TRI2024 result is not directly
comparable with MP2020 metrics: corrections alter entries and therefore hulls,
stability, and any stability-conditioned novelty/uniqueness aggregate.

## Recovery rules

- Import or dependency failures: inspect [`references/troubleshooting.md`](references/troubleshooting.md), then run the wrapper's `--help` and a small import/device probe before an expensive job.
- Optional backend failures: use CPU only for a small diagnostic; relaxation is
  substantially more expensive and may require CUDA plus compatible MatterSim.
- Input/config failures: fix suffixes, lowercase directory extensions, ZIP
  contents, energy shape/order, reference `.gz` path, and mode conflicts first.
- Matcher failures: use `disordered` for any partial occupancy or disordered
  structure; an ordered matcher is not valid when the evaluator detects a
  disordered structure.
- Reference/correction failures: rebuild or select a reference with the same
  correction convention; do not silence compatibility assertions.
- Workflow failures: preserve input files and partial metrics, rerun a small
  subset or no-relax path, and only then retry relaxation. Do not make the
  wrapper fetch a missing reference or potential implicitly.

## Linked runtime material

- [`scripts/evaluate_structures.py`](scripts/evaluate_structures.py) — safe,
  lazy-importing CLI adapter.
- [`references/api-reference.md`](references/api-reference.md) — API, defaults,
  flags, and metric contract.
- [`references/workflows.md`](references/workflows.md) — evaluation recipes,
  output precedence, and resource boundaries.
- [`references/data-formats.md`](references/data-formats.md) — accepted input,
  energy, reference, and output serialization.
- [`references/troubleshooting.md`](references/troubleshooting.md) — actionable
  diagnosis and recovery.
