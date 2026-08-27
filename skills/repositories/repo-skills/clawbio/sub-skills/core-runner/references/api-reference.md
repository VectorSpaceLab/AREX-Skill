# Public API and installation

## Choose the runtime layout

ClawBio requires Python 3.11 or newer.

### Installed package / wheel

Use a public package installation when the caller wants the stable library and
console command:

```bash
python -m pip install clawbio
# or, with conda/bioconda:
conda install -c bioconda clawbio
# or with uv's pip-compatible installer:
uv pip install clawbio

clawbio --version
clawbio list
clawbio run pharmgx --demo
```

The wheel bundles a curated content tree inside the package. Package data is
read-only in principle. The runner therefore places default writable data in
the caller's current working directory: `output/` for generated runs and
`profiles/` for uploaded patient profiles.

### Source checkout

A deliberate source checkout is useful for development, the complete skill
catalog, and native repository tests. Install it with the checkout's editable
package workflow (`pip install -e .` or the documented environment manager),
then use the public `clawbio` console command. In a checkout, bundled content is
resolved from that checkout and default writable output is rooted there;
installed wheels instead use the caller's writable directory. Do not write a
runtime workflow that assumes the checkout exists.

## Importable symbols

The stable package surface is:

```python
from clawbio import __version__, list_skills, run_skill, upload_profile
```

The callables are re-exported from the package runner and are the same callable
objects exposed by the CLI engine.

### `list_skills`

```python
list_skills() -> dict
```

Prints the registered and agent-readable skill listing, including whether a
registered script exists, and returns the registered skill mapping. The mapping
contains implementation metadata such as the script path, demo arguments,
description, input policy, and per-skill extra-flag allowlist. It is not a
stable scientific catalog schema; treat it as a runtime registry.

### `upload_profile`

```python
upload_profile(
    input_path: str,
    patient_id: str = "",
    fmt: str = "auto",
) -> dict
```

Parses a 23andMe, AncestryDNA, MyHeritage, or single-sample VCF input and saves
a JSON profile under the active writable `profiles/` directory. `fmt="auto"`
detects the header or VCF extension; explicit values are `23andme`, `ancestry`,
`myheritage`, and `vcf`.

A successful return has this shape:

```python
{
    "success": True,
    "profile_path": ".../profiles/PT001.json",
    "patient_id": "PT001",
    "genotype_count": 123,
    "checksum": "<64-hex SHA-256>",
}
```

When `patient_id` is omitted, it is derived from the input filename (spaces
become underscores and the stem is limited to 32 characters). Uploading again
with the same ID targets the same JSON path and can replace its prior profile;
choose IDs deliberately and copy/archive profiles before replacement. Parse or
file errors currently propagate from this callable rather than being converted
into the runner result envelope, so callers should catch them at the API
boundary.

### `run_skill`

```python
run_skill(
    skill_name: str,
    input_path: str | None = None,
    output_dir: str | None = None,
    demo: bool = False,
    extra_args: list[str] | None = None,
    timeout: int = 300,
    profile_path: str | None = None,
) -> dict
```

The runner launches the registered skill in a subprocess using the same Python
interpreter that called it. A normal result contains:

```python
{
    "skill": "pharmgx",
    "success": True,             # subprocess exit code == 0
    "exit_code": 0,
    "output_dir": "/abs/path/to/output",
    "files": ["report.md", "result.json", ...],
    "stdout": "...",
    "stderr": "...",
    "duration_seconds": 0.42,
}
```

On successful output, the runner may add `skill_result_json`,
`result_json_path`, `report_md`, `chat_summary_lines`, `preferred_artifacts`,
`suggested_actions`, `workflow_state`, and sanitised `contract_alerts` when the
skill emits those fields. A skill can succeed without emitting every optional
field.

The unknown-skill, missing-script, missing-input, timeout, and subprocess
failure paths remain structured dictionaries with `success=False`, an
`exit_code` (usually `-1` for preflight/timeout), output information, logs, and
a diagnostic `stderr`. Unknown skills include `Unknown skill`; missing input
says to use `--demo`, `--input`, or `--profile`. Do not parse `stderr` as JSON
unless the preflight output-directory error is being handled; that particular
error serializes an object with `ok=False`, `stage="preflight"`,
`error_code="OUTPUT_DIR_NOT_WRITABLE"`, `message`, `fix`, and `details`.

`extra_args` is not an unrestricted escape hatch. The runner filters flags
against the selected skill's registry allowlist and always blocks attempts to
inject `--input`, `--output`, or `--demo`. Pass only flags documented by the
selected skill.

## Profile object used by the API

For in-process profile work, the supported class is
`clawbio.common.profile.PatientProfile`:

```python
PatientProfile.from_genetic_file(path, patient_id="", fmt="auto")
profile.save(path)
profile = PatientProfile.load(path)
profile.get_genotypes(rsids=None)
profile.get_records(rsids=None)
profile.add_skill_result(skill_name, result_dict)
profile.get_skill_result(skill_name)
```

The JSON contains `metadata`, `genotypes`, `ancestry`, and `skill_results`.
Metadata records patient ID, the source path, upload time, and source SHA-256.
The profile stores serialisable genotype records, not a copy of the raw input.
A profile is only reusable while its recorded input path remains accessible to
skills that require a raw input file.
