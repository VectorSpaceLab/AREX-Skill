# Output and reproducibility contracts

## Standard output bundle

When an output directory is used, inspect it as a bundle rather than relying
on terminal text:

```bash
find ./results/pharmgx -maxdepth 3 -type f -print | sort
```

The shared helpers establish these conventions:

- `report.md`: primary human-readable Markdown report when the skill emits a
  report. The common header records UTC date, skill, version, and checksums for
  existing input files; the common footer carries the ClawBio research and
  educational disclaimer.
- `result.json`: structured envelope when the skill uses the shared report
  helper. It contains `skill`, `version`, `completed_at`, `input_checksum`
  (`sha256:<digest>` or empty), `datasets`, `summary`, and `data`. Some newer
  pipeline wrappers opt into top-level `status` and `ok`; those keys are not
  universal.
- `figures/`, `tables/`, and other skill-specific files: generated artifacts
  described by that skill's contract.
- `reproducibility/`: optional bundle; do not report it as guaranteed merely
  because the runner succeeded.

A successful subprocess means only that the child exited zero. Check
`result.json` when present, confirm the report and expected artifacts exist,
and read the skill-specific `SKILL.md` before interpreting content. The runner
also promotes structured fields from `result.json` into its return dictionary,
including report text and preferred artifacts when supplied.

## Report helper signatures

Domain skills commonly use:

```python
from clawbio.common.report import (
    DISCLAIMER,
    generate_report_header,
    generate_report_footer,
    write_result_json,
    write_audit_log,
)

header = generate_report_header(
    title="...",
    skill_name="...",
    skill_version="...",
    input_files=[input_path],
    extra_metadata={"Key": "value"},
)
result_path = write_result_json(
    output_dir,
    skill="...",
    version="...",
    summary={...},
    data={...},
    input_checksum="<hex>",
    datasets={...},
    status="ok",       # optional
    ok=True,             # optional
)
```

`write_result_json` creates the output directory and serialises JSON with
indentation. It does not itself create `report.md`; the skill must write the
report. The exact report/disclaimer contract belongs to the emitting skill, but
ClawBio's shared footer is the required safe wording for standard reports.

## Reproducibility bundle

Many skills write these files under `<output_dir>/reproducibility/`:

```text
commands.sh       # recorded replay command
 environment.yml  # suggested Conda environment (spacing shown conceptually)
checksums.sha256  # SHA-256 for selected files
```

Optional files can include `conda-lock.yml`, `runtime-lock.json`, RO-Crate
metadata, or skill-specific logs. The exact contents vary by skill. The bundle
is not a guarantee of bit-for-bit replay: required external programs, remote
resources, user-owned inputs, and the same output policy must still be
available.

Typical safe inspection and verification:

```bash
cat ./results/pharmgx/reproducibility/commands.sh
cat ./results/pharmgx/reproducibility/environment.yml
( cd ./results/pharmgx && sha256sum -c reproducibility/checksums.sha256 )
```

Some portable command bundles define `OUTPUT_DIR` from the bundle location and
allow an override such as `CLAWBIO_ROOT=/path/to/checkout`. Other skills record
a direct invocation or absolute user-input paths. Read the generated command
before executing it. Never execute a replay command containing unreviewed
remote or patient-data behavior.

The shared helpers include these useful construction APIs:

```python
from clawbio.common.checksums import sha256_file, sha256_hex
from clawbio.common.reproducibility import (
    ReproPath, ReproCommand,
    write_checksums, write_commands_sh, write_environment_yml,
    write_portable_commands_sh, write_conda_lock, write_ro_crate,
)

sha256_file(path) -> str                 # full 64-hex digest
sha256_hex(path, length=16) -> str       # truncated display digest
write_checksums(paths, output_dir, anchor=None) -> Path
write_commands_sh(output_dir, command) -> Path
write_environment_yml(output_dir, env_name, pip_deps,
                      conda_deps=None, python_version="3.10",
                      channels=None) -> Path
```

`write_conda_lock` requires an existing `reproducibility/environment.yml` and
an installed `conda-lock`; it can raise `FileNotFoundError` or subprocess
errors. `write_ro_crate` packages every file under the output directory, so do
not call it after placing credentials or raw patient files there.

## Audit and privacy

The common report audit helper appends a `skill_run` record to
`~/.clawbio/audit.jsonl` by default, including skill/version, input checksum,
and output directory. The low-level audit module warns that paths and future
attributes can contain PII; scrub patient identifiers before passing custom
values. Audit logging is best-effort and must not be treated as a complete
clinical record. Contract alerts can also be written to
`<output_dir>/contract_alerts.jsonl` when structured result data contains
validated alerts.

Keep raw patient data outside output bundles unless the individual skill
explicitly requires it. Reproducibility artifacts should record enough to
replay, not expose genome files, credentials, or secrets.
