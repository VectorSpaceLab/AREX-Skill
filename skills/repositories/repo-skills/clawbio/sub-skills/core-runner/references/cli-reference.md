# CLI reference

The installed console entry point and an editable source environment expose the same
main commands:

```bash
clawbio --version
clawbio list
clawbio upload --input <genetic-file> [--patient-id PT001] [--format auto]
clawbio run <skill> [--demo | --input <file> | --profile <profile.json>] \
  [--output <directory>] [--timeout SECONDS]
```

In an editable source environment, use the same `clawbio ...` commands after
installation. `clawbio --help`, `clawbio list`, and a registered skill's own
help are safe discovery operations. Pipeline wrappers may own their full help;
those are outside this sub-skill.

## Listing

```bash
clawbio list
```

The command prints registered skills, script names and OK/MISSING status, then
agent-readable `SKILL.md`-only directories where present. It returns exit 0
through the CLI and `list_skills()` returns only the registered mapping. The
registry is the source of truth for names accepted by `run`.

## Upload and profile lifecycle

Create a persistent, local profile once:

```bash
clawbio upload \
  --input ./data/patient_23andme.txt \
  --patient-id PT001 \
  --format auto
```

The CLI prints the profile path, genotype count, and checksum. `--format`
accepts `auto`, `23andme`, `ancestry`, `myheritage`, or `vcf`; use explicit
format when auto-detection cannot identify an ambiguous file. The default
profile location is `profiles/PT001.json` in the active writable root. The
uploaded file is parsed locally and is not uploaded to a remote service by
this command.

Then run a genotype-consuming skill from the profile:

```bash
clawbio run pharmgx \
  --profile profiles/PT001.json \
  --output ./results/pharmgx
```

For a profile-backed run, the runner loads `metadata.input_file` and resolves a
relative stored path against the ClawBio content root. If the input file has
moved or disappeared, the child skill may fail even though the JSON profile
loads; restore the file or use the domain skill's supported profile behavior.
Do not confuse a genomic patient profile path with the `--profile` backend
profile used by some pipeline wrappers.

## Single runs and input precedence

Use one primary mode:

```bash
# bundled demo data
clawbio run pharmgx --demo --output ./results/pharmgx-demo

# caller-owned input
clawbio run pharmgx --input ./data/sample.txt --output ./results/pharmgx

# persisted profile (genotype-consuming skills)
clawbio run pharmgx --profile ./profiles/PT001.json --output ./results/pharmgx
```

`--demo` wins over `--input`/profile resolution in the Python runner because it
selects the registry's declared demo arguments. If neither demo nor input nor
profile supplies an input, a skill that requires input returns a structured
failure. Skills marked no-input-required can instead run their own no-input
workflow. Avoid passing contradictory modes; choose one explicitly.

Input paths are expanded and resolved to absolute paths before child-process
launch. Relative `--output` paths are resolved against the current working
directory, then created if possible. If no output is supplied, the runner uses
a timestamped directory under the active default `output/` root, except for
skills that explicitly support summary mode without an output directory.

## Output safety and errors

The runner creates missing output directories. It does not overwrite an
existing regular file at the requested output path. That preflight failure has
`success=False`, `exit_code=-1`, and JSON in `stderr`:

```json
{
  "ok": false,
  "stage": "preflight",
  "error_code": "OUTPUT_DIR_NOT_WRITABLE",
  "message": "Output path exists but is not a directory.",
  "fix": "Choose a directory path for --output, or remove/rename the existing file.",
  "details": {"output": "/absolute/path"}
}
```

An existing directory is allowed by the runner, but a child skill may add
suffixes, overwrite known files, or reject its own non-empty destination. For
replay comparisons, use a new empty directory. A timeout returns `success=False`
with `exit_code=-1` and `stderr` such as `Timed out after 300 seconds.`. A
child non-zero exit returns its exit code and captured stdout/stderr.

The runner filters `extra_args` through each registry entry's allowlist. It
silently drops blocked/unknown extra flags, and always drops attempts to
replace `--input`, `--output`, or `--demo`; this is a safety gate, not a way to
repair a malformed command. Use the child skill documentation for allowed
flags.

## Full-profile composition

The virtual skill composes the fixed ordered list:

```text
pharmgx -> nutrigx -> prs -> compare
```

Run it with an existing profile or directly with an input:

```bash
clawbio run full-profile --profile ./profiles/PT001.json --output ./results/full
clawbio run full-profile --input ./data/patient.txt --output ./results/full
```

If only `--input` is given, ClawBio first creates a profile, then runs each
stage sequentially in `<output>/pharmgx/`, `<output>/nutrigx/`,
`<output>/prs/`, and `<output>/compare/`. It writes `<output>/pipeline_summary.json`
with the ordered pipeline, profile path, per-stage success/exit/files, and
completion time. A failed stage does not stop later stages; aggregate success
is false if any stage failed. `full-profile` without `--input` or `--profile`
returns a structured failure saying it requires one of them.

For each successful profile-backed single run, when a child emits
`result.json`, ClawBio attempts to add that envelope under `skill_results` in
the profile. Profile-storage errors are deliberately non-fatal to the main
run, so verify the profile if the accumulated chain state matters.
