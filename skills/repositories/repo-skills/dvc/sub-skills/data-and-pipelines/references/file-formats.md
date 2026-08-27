# DVC Data And Pipeline File Formats

This reference summarizes the file formats future agents most often need to inspect or edit for DVC data and pipeline workflows. Prefer DVC commands for mutations; hand-edit only when the intended schema is clear and validate afterward with `dvc status`, `dvc repro --dry`, and `dvc dag`.

## `.dvc` Files

A `.dvc` file represents a single data-source stage, usually created by `dvc add`. It is Git-tracked metadata for a file or directory stored in the DVC cache or a configured remote.

Core fields commonly present:

- `outs`: list of tracked outputs; each output entry includes `path` and checksum information such as `md5` after commit/cache operations.
- Output details may include metadata, directory file lists, cloud/hash fields, cache flags, remote selection, and annotations depending on how the output was created.
- The file path often follows the output basename plus `.dvc`, such as `data/raw.csv.dvc`; DVC's stage creation logic derives this path from the first output for single-stage data files.

Operational notes:

- Use `dvc add <path>` to create or update data-source `.dvc` files.
- Use `dvc commit <target>` after `--no-commit` or manual data changes that should update cache metadata.
- Use `dvc checkout <target>` to restore workspace contents from cache.
- Avoid mixing `.dvc` data-source outputs with pipeline outputs that are defined in `dvc.yaml`; overlapping outputs produce DVC graph errors.

## `dvc.yaml`

`dvc.yaml` stores multi-stage pipeline declarations. The top-level schema accepts these keys:

- `stages`: mapping of stage name to stage definition.
- `vars`: list of variable files or inline variable dictionaries.
- `params`: list of parameter files used by the project.
- `metrics`: list of project-level metric files.
- `plots`: list of project-level plot files or named plot definitions.
- `datasets`: object for dataset metadata.
- `artifacts`: mapping of artifact definitions.

A normal stage definition can include:

- `cmd`: required command string or command list.
- `wdir`: optional repo-contained working directory.
- `deps`: list of dependency paths.
- `params`: list of params, including strings or mappings for selected keys.
- `outs`: list of output paths or detailed output mappings.
- `metrics`: list of metric outputs or detailed output mappings.
- `plots`: list of plot outputs or plot-definition mappings.
- `frozen`: boolean for freeze/unfreeze behavior.
- `always_changed`: boolean for stages that should always be considered changed.
- `desc`: human-readable stage description.
- `meta`: arbitrary metadata.
- `matrix` plus `foreach`/`do` forms for generated stages; route complex matrix/foreach review through target syntax and DAG checks.

Detailed output entries may specify properties such as `cache`, `persist`, `checkpoint`, `remote`, `push`, and annotations. Plot entries may also specify `template`, `x`, `y`, axis labels, title, and header handling. For reporting semantics beyond declaring outputs, use `../metrics-params-plots/SKILL.md`.

Stage name rules from DVC's validation:

- Valid examples include `copy_name`, `copy-name`, `copyName`, and `12`.
- Invalid examples include names containing `$`, `?`, or `@`, such as `copy$name`, `copy-name?`, and `copy-name@v1`.
- Prefer concise lowercase hyphen names for agent-created stages because they are easy to target from CLI and Git diffs.

Minimal example:

```yaml
stages:
  featurize:
    cmd: python src/featurize.py --config params.yaml
    deps:
      - src/featurize.py
      - data/raw.csv
    params:
      - params.yaml:featurize
    outs:
      - data/features.parquet
  train:
    cmd: python src/train.py
    deps:
      - src/train.py
      - data/features.parquet
    params:
      - params.yaml:train.lr,train.epochs
    outs:
      - models/model.pkl
    metrics:
      - metrics/train.json:
          cache: false
    plots:
      - plots/loss.json
```

## `dvc.lock`

`dvc.lock` records materialized pipeline state for `dvc.yaml` stages after commands run or outputs are committed. It is generated/updated by DVC and should normally not be hand-edited.

The lockfile schema includes:

- `schema: "2.0"` as the required schema version.
- `stages`: mapping of stage name to locked stage data.
- Optional `datasets` data.

Each locked stage includes:

- `cmd`: required command string or command list.
- `deps`: list of locked dependency data entries.
- `params`: mapping from params file to selected key/value data.
- `outs`: list of locked output data entries.

Data entries include a required `path`, checksum fields, metadata, cloud/hash fields, directory file listings, and dataset-dependency fields when applicable.

Test-backed lockfile behavior:

- A stage with no deps or outs can still lock as `schema: "2.0"` plus `stages: {stage: {cmd: ...}}`.
- Dumping a new stage preserves other stage entries and overwrites the matching stage entry by name.
- Missing lockfiles load as empty state; corrupted lockfiles raise YAML validation errors that include the lockfile path.
- A Git-ignored `dvc.lock` is an error even when it is also DVC-ignored or missing on disk.

Validation pattern:

```bash
dvc repro --dry <target>
dvc status <target>
git diff -- dvc.yaml dvc.lock
```

If `dvc.lock` was deleted or does not match `dvc.yaml`, `dvc status` and `dvc repro --dry` usually reveal changed deps, changed outs, changed commands, or missing lock information.

## `.dvcignore`

`.dvcignore` excludes paths from DVC's file walking and output checks. It is initialized with a comment header by `dvc init` and can be inspected with `dvc check-ignore`.

Useful checks:

```bash
dvc check-ignore path/to/file
dvc check-ignore --details path/to/file
dvc check-ignore --details --non-matching path/to/file
dvc check-ignore --stdin < candidate-paths.txt
```

Command constraints:

- Provide either positional targets or `--stdin`, not both.
- `--non-matching` only makes sense with `--details`.
- `--details` and `--quiet` cannot be used together.

Operational notes:

- If a dependency or output appears invisible to DVC, check `.dvcignore` before changing stage definitions.
- A path ignored by Git can still break DVC metadata flows when the metadata file itself, such as `dvc.lock`, is Git-ignored.
- Do not use `.dvcignore` to hide real pipeline outputs from DVC; declare outputs accurately or adjust stage paths.

## Hand-Edit Checklist

When a task requires reviewing or editing DVC metadata:

1. Prefer `dvc stage add --force`, `dvc freeze`, `dvc unfreeze`, `dvc remove`, or `dvc move` over manual YAML edits.
2. If editing `dvc.yaml`, preserve stage names and target syntax expected by downstream commands.
3. Keep dependencies and outputs non-overlapping; a dependency cannot be the same path as an output for the same stage.
4. Avoid cached external outputs unless the DVC project is intentionally configured for them.
5. Run `dvc repro --dry <target>` before `dvc repro` to check command order without executing stage commands.
6. Review `git diff -- dvc.yaml dvc.lock .dvcignore '*.dvc'` before finalizing.
