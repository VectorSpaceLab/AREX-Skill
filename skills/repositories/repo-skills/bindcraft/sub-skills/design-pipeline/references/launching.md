# Direct and SLURM launching

## Exact program contract

The Python entry point accepts exactly these user-facing flags:

```text
python -u <BindCraft installation>/bindcraft.py \
  --settings <target.json> \
  [--filters <filters.json>] \
  [--advanced <advanced.json>]
```

`--settings` is mandatory. `--filters` and `--advanced` are optional and use
BindCraft's default preset when omitted. Use explicit paths for reproducible
campaigns. Paths may be absolute or relative to the process working directory;
quote paths containing spaces. Activate the prepared environment before the
command. Do not put a private environment path into a shared JSON or skill
file.

A direct launch, with all choices explicit, is:

```bash
python -u ./bindcraft.py \
  --settings ./settings_target/my_target.json \
  --filters ./settings_filters/default_filters.json \
  --advanced ./settings_advanced/default_4stage_multimer.json
```

The process creates its output under `design_path`; it does not expose a
separate output or resume CLI flag. Use a distinct output directory for a new
campaign and the same directory for a deliberate continuation.

## SLURM wrapper contract

The checked-in wrapper accepts only the following wrapper flags and then passes
them to Python:

```text
sbatch [scheduler-options] <BindCraft installation>/bindcraft.slurm \
  --settings <target.json> [--filters <filters.json>] [--advanced <advanced.json>]
```

The wrapper's short aliases are `-s`, `-f`, and `-a`. It rejects a missing
settings value before starting Python. Its source defaults request one node,
one task, one CPU, one GPU, 42 GB memory, a `gpu` partition and QoS, and a
72-hour wall time. These are examples, not portable cluster requirements;
partition, QoS, account, memory, time, GPU syntax, and environment activation
must be adapted to the site.

For example, resource options can override wrapper directives on schedulers
that support command-line overrides:

```bash
sbatch --partition=gpu --qos=gpu --gres=gpu:1 \
  --cpus-per-task=4 --mem=40G --time=72:00:00 \
  ./bindcraft.slurm --settings ./settings_target/my_target.json \
  --filters ./settings_filters/default_filters.json \
  --advanced ./settings_advanced/default_4stage_multimer.json
```

The wrapper activates an environment by a site-specific name in the repository
version. Replace that activation with the environment prepared for this
machine, or use a local wrapper, before submitting. Do not assume the sample
partition, QoS, `LD_LIBRARY_PATH`, or environment name exists. The job log is
scheduler output; the design CSVs and PDBs remain under `design_path`.

## Safe command builder

Use the bundled builder when a command should be reviewed or recorded without
execution:

```bash
python skills/disco/bindcraft/sub-skills/design-pipeline/scripts/build_bindcraft_command.py \
  --mode slurm --settings ./settings_target/my_target.json \
  --filters ./settings_filters/default_filters.json \
  --advanced ./settings_advanced/default_4stage_multimer_hardtarget.json \
  --partition gpu --gres gpu:1 --cpus-per-task 4 --mem 40G --time 72:00:00 \
  --dry-run
```

For direct mode use `--mode direct`; for a non-current installation use
`--bindcraft-dir /path/to/installation`. The builder prints a shell-quoted
command (or JSON with `--format json`) and never calls `conda`, `python`,
`sbatch`, or the BindCraft script. Run `--help` before using it and review all
paths and scheduler options before submitting.

## Preflight and resume safety

Before launching, check all of the following in the actual target environment:

1. `jax.devices()` includes a CUDA device and a tiny JAX operation succeeds.
2. Imports for JAX, ColabDesign, PyRosetta, and the BindCraft package surface
   succeed in the prepared environment.
3. The AF2 parameter directory contains the expected external parameter files;
   the skill does not download them.
4. `dssp_path` and `dalphaball_path` point to readable, executable tools and
   PyRosetta can initialize with the DAlphaBall path.
5. Target, filter, and advanced JSONs are readable; `design_path` is writable
   and has enough space for PDBs, CSVs, plots, optional animations, and
   optional pickles.

Do not run two jobs against one `design_path`. Before resuming, snapshot or
record the three settings files and inspect `failure_csv.csv`, accepted PDB
counts, and the last scheduler log. A rerun has no atomic checkpoint protocol:
partial PDBs or CSV rows may require manual quarantine, and changing filters
mid-campaign makes acceptance and ranking comparisons difficult. Use a new
`design_path` when the provenance cannot be established.

The full design loop is long-running and CUDA-only. A command that merely
parses, imports, or prints `--help` does not validate AF2 weights, model
compilation, MPNN, relaxation, or target-dependent acceptance.
