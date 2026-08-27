# Planning and Quickrun Workflows

OpenFE CLI campaigns have three distinct phases:

1. **Plan** a network from molecular inputs into serialized campaign files.
2. **Execute** each transformation JSON with `openfe quickrun`.
3. **Gather** completed result JSONs into summary tables.

Do not collapse these phases. Planning and charge assignment are setup work; `quickrun` is simulation execution; gathering is post-run summary generation.

## Generated Planning Layout

Both `plan-rbfe-network` and `plan-rhfe-network` write a directory with this shape:

```text
network_setup/
  network_setup.json
  ligand_network.graphml
  transformations/
    <transformation-name-or-key>.json
    ...
```

- The top-level JSON serializes the alchemical network.
- `ligand_network.graphml` can be viewed with `openfe view-ligand-network` when a GUI is available.
- Each file under `transformations/` is a single `Transformation` JSON suitable for one `openfe quickrun` invocation.

The output directory name controls the top-level network JSON filename. For example, `-o network_setup` writes `network_setup/network_setup.json`.

## Standard RBFE CLI Campaign

Use this pattern for a command-line RBFE campaign:

```bash
openfe plan-rbfe-network \
  -M ligands.sdf \
  -p protein.pdb \
  -o network_setup \
  --n-protocol-repeats 3

openfe quickrun \
  network_setup/transformations/<edge>.json \
  -d work/<edge> \
  -o results/<edge>_results.json

openfe gather results
```

Planning notes:

- `-M` can point to one multi-molecule SDF, one MOL2/SDF, or a directory containing SDF/MOL2 files.
- RBFE requires exactly one protein context: `--protein`/`-p` for a protein file or `--protein-membrane` for a solvated membrane system.
- Optional `-C/--cofactors` can add SDF cofactors alongside the protein.
- Planning assigns or overwrites charges according to YAML and `--overwrite-charges`; this can be slow.
- Use `--n-protocol-repeats 1` if you intend to split repeats across separate jobs.

## Standard RHFE CLI Campaign

Use this pattern for hydration transformations without a protein context:

```bash
openfe plan-rhfe-network \
  -M ligands.sdf \
  -o hydration_network \
  --n-protocol-repeats 3

openfe quickrun \
  hydration_network/transformations/<edge>.json \
  -d work/<edge> \
  -o results/<edge>_results.json
```

RHFE planning uses the same YAML structure as RBFE planning, but does not take protein, membrane, or cofactor options.

## Repeat-Safe Quickrun Planning

OpenFE protocols often run multiple repeats serially by default. To distribute repeats across a scheduler, plan transformations with one repeat per quickrun execution:

```bash
openfe plan-rbfe-network -M ligands.sdf -p protein.pdb -o network_setup --n-protocol-repeats 1
```

Then run each transformation multiple times with unique result and work paths:

```bash
openfe quickrun network_setup/transformations/edge.json \
  -d work_0/edge \
  -o results_0/edge.json

openfe quickrun network_setup/transformations/edge.json \
  -d work_1/edge \
  -o results_1/edge.json
```

Do not reuse either `-o` or `-d` across parallel repeats. The quickrun cache key depends on the transformation and output path, and shared work directories can cause collisions or confusing resumes.

Use the bundled helper to generate commands without executing them:

```bash
python scripts/build_quickrun_repeat_commands.py \
  network_setup/transformations \
  --repeats 3 \
  --results-root results_parallel \
  --work-root work_parallel
```

Print simple Slurm scripts instead of bare commands:

```bash
python scripts/build_quickrun_repeat_commands.py \
  network_setup/transformations \
  --repeats 3 \
  --results-root results_parallel \
  --work-root work_parallel \
  --format slurm \
  --slurm-job-prefix openfe \
  --slurm-option '#SBATCH --gres=gpu:1'
```

The helper scans `*.json`, constructs deterministic output/work paths, detects duplicate generated paths, and prints text only. It does not run `openfe`, write job files, submit jobs, or create result directories.

## Quickrun Resume Semantics

At startup, `quickrun` creates a cache file under:

```text
<work-dir>/quickrun_cache/dag-cache-<key>.json
```

The cache key is based on the absolute output path and transformation identity. The cache is removed after successful completion.

Resume rules:

- Use the same transformation JSON, `-d/--work-dir`, and `-o` path as the original run.
- If the cache exists and `--resume` is supplied, quickrun attempts to load the cached `ProtocolDAG` and continue.
- If the cache exists but `--resume` is omitted, quickrun refuses to start a duplicate incomplete transformation.
- If `--resume` is supplied but no cache exists, quickrun warns and starts a fresh execution.
- If the cache JSON is corrupt, remove the named cache file before starting a fresh execution. Keep the old result/work directory until the user decides whether partial artifacts are useful for debugging.

## Gather Boundaries

Gather only after result JSONs exist.

```bash
openfe gather results_parallel
openfe gather-abfe abfe_results
openfe gather-septop septop_results
```

- Use `gather` for RBFE result JSONs.
- Use `gather-abfe` or `gather-septop` only for exploratory ABFE/SepTop outputs; these command surfaces are experimental.
- Point gather at the root containing repeat folders when using `results_0`, `results_1`, and similar layouts.
- For TSV columns, DG/DDG interpretation, failed-edge behavior, and partial/missing repeats, route to `../../results-analysis/SKILL.md`.

## Safe Dry-Run and Help Checks

Before execution, prefer these non-simulation checks:

```bash
openfe --help
openfe plan-rbfe-network --help
openfe quickrun --help
openfe gather --help
python scripts/build_quickrun_repeat_commands.py --help
```

To validate file layout without running simulations, list planned transformation JSONs and generate commands with the helper. Do not run `quickrun` as a dry-run; it executes simulations.
