# Workflow Authoring Troubleshooting

Use this guide for errors caused by Snakefile syntax, rule design, wildcard logic, helper functions, modules, scripts, notebooks, wrappers, CWL hooks, and checkpoints.

## Fast Triage Commands

Run from the workflow directory:

```bash
snakemake --snakefile Snakefile --cores 1 --dry-run --printshellcmds
snakemake --snakefile Snakefile --cores 1 --dry-run target/file.txt
snakemake --snakefile Snakefile --cores 1 --dry-run --dag > dag.dot
python -m snakemake --help
```

Snakemake 9.23.1 does not support `--reason`. If older docs or scripts use it, delete that flag; dry-runs still include reason information in normal output.

## Parser or Syntax Errors

Common signals:

- `SyntaxError` near a directive.
- `Expected name or colon after rule or checkpoint keyword`.
- A directive is interpreted as ordinary Python.
- A parser error points one line after the real indentation or colon problem.

Checks:

- Rule declarations use `rule name:` and checkpoint declarations use `checkpoint name:`.
- Rule directives are indented under the rule and end with colons: `input:`, `output:`, `params:`, `log:`, `shell:`, `script:`, `notebook:`, `wrapper:`, `cwl:`.
- Multiline shell code uses triple-quoted strings or adjacent strings.
- Literal braces in shell snippets are doubled, e.g. `awk '{{print $1}}'`.
- A Python variable or function is not placed where a Snakemake keyword is required.

Minimal fix pattern:

```python
rule example:
    input:
        "data.txt"
    output:
        "out.txt"
    shell:
        "cp {input:q} {output:q}"
```

## Wildcard Ambiguity

Signals:

- `AmbiguousRuleException`.
- Wildcards contain more text than expected.
- A flat output pattern unexpectedly matches targets from another rule.

Fix order:

1. Move outputs into distinct directories.
2. Add inline or rule-local `wildcard_constraints`.
3. Use distinct suffixes for different product types.
4. Use `ruleorder` only when overlap is intentional.

Example fix:

```python
rule grouped:
    output:
        r"results/{dataset,\d+}/groups/{group,case|control}.txt"
    shell:
        "make-group {wildcards.dataset:q} {wildcards.group:q} > {output:q}"
```

Validate a representative target:

```bash
snakemake --cores 1 --dry-run --printshellcmds results/101/groups/case.txt
```

## `MissingInputException`

Signals:

- `MissingInputException: Missing input files for rule ...`.
- Dry-run shows a job but cannot find one or more upstream files.

Likely causes:

- The missing path should be a real external input but is absent.
- The missing path should be generated, but no rule output matches it.
- A wildcard value is broader than intended.
- An input function returns the wrong path.
- Checkpoint output was globbed before the checkpoint ran.

Debug steps:

```bash
snakemake --cores 1 --dry-run --printshellcmds requested/target.txt
snakemake --cores 1 --dry-run --summary
```

Fix patterns:

```python
# Add a producer when the file should be generated.
rule make_raw:
    output:
        "raw/{sample}.txt"
    shell:
        "make-raw {wildcards.sample:q} > {output:q}"

# Or tighten wildcard matching.
wildcard_constraints:
    sample="[A-Za-z0-9_-]+"
```

If the file is an external input, keep it as input and route data inventory/config management to configuration-data.

## `WildcardError` from `expand()`

Signals:

- `No values given for wildcard 'x'.`
- `expand()` resolves a placeholder that was meant for a later rule.

Fixes:

```python
# Provide all concrete values.
expand("results/{sample}.{metric}.txt", sample=SAMPLES, metric=["qc", "count"])

# Keep a wildcard unresolved by escaping its braces.
expand("chunks/{{sample}}/{chunk}.txt", chunk=[1, 2, 3])
```

Do not mask or escape a wildcard until you can explain which later rule will resolve it.

## `InputFunctionException`

Signals:

- Snakemake reports `InputFunctionException` with wildcard values.
- A `KeyError`, `IndexError`, or custom exception appears during DAG construction.

Checks:

- The function is passed, not called: `input: reads_for_sample`, not `input: reads_for_sample()`.
- The first argument represents `wildcards`.
- Every possible wildcard value is supported or constrained.
- The function returns file paths, not open handles or side-effect results.
- The optional second argument is named exactly `groupid` only when group-local behavior is intended.

Safer function:

```python
def reads_for_sample(wildcards):
    try:
        return SAMPLE_TO_READS[wildcards.sample]
    except KeyError as error:
        raise ValueError(f"No reads configured for sample {wildcards.sample!r}") from error
```

If the callable needs `input`, `output`, `threads`, or `resources`, it likely belongs under `params:` or `resources:`, not `input:`.

## Checkpoint Misuse

Signals:

- A top-level `glob_wildcards()` returns an empty list for files a checkpoint should create.
- A downstream aggregate rule is scheduled before checkpoint-discovered files exist.
- `IncompleteCheckpointException` or a confusing missing input appears around checkpoint output.

Correct pattern:

```python
def aggregate_inputs(wildcards):
    checkpoint_dir = checkpoints.split.get(sample=wildcards.sample).output[0]
    chunks, = glob_wildcards(os.path.join(checkpoint_dir, "{chunk}.txt"))
    return expand(os.path.join(checkpoint_dir, "{chunk}.txt"), chunk=chunks)
```

Rules:

- Put checkpoint-dependent discovery inside an input function.
- Call `checkpoints.<name>.get(**wildcards)` before reading/globbing checkpoint output.
- Use `directory()` when the checkpoint creates an unknown collection of files.
- Do not call `checkpoints.<name>.get()` at top level.

## Module Import and Prefix Surprises

Signals:

- Imported rule names differ from expected names.
- Module outputs appear under an unexpected prefix.
- An override says the rule is unknown.
- A module helper function is not found in the global namespace.

Checks:

- `use rule * from module_name as prefix_*` renames imported rules.
- Overrides refer to original module rule names, not already-prefixed names.
- `prefix:` relocates relative module input/output paths.
- Non-rule Python in a module is accessed via the module object, e.g. `qc.some_func()`.
- A module cannot be named `workflow`.
- Dynamic modules with `name:` require alias variables when used in loops.

Validation:

```bash
snakemake --cores 1 --dry-run --printshellcmds
```

Inspect the printed jobs and paths before changing imported workflows further.

## Script Directive Problems

Signals:

- `NameError: name 'snakemake' is not defined` when running a script directly.
- A script works directly but fails under `script:` because paths or working directory differ.
- Output directories are missing.
- Optional language support is absent for R, Julia, Bash, Rust, or other script languages.

Rules:

- Under `script:`, use the injected `snakemake` object: `snakemake.input`, `snakemake.output`, `snakemake.params`, `snakemake.log`, `snakemake.threads`, `snakemake.resources`, `snakemake.config`.
- Create parent directories in scripts if the called tool does not do it.
- Add a separate standalone CLI mode only if direct execution is a requirement.
- Route optional language/package installation to deployment-storage.

Python script snippet:

```python
from pathlib import Path

out = Path(snakemake.output[0])
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("ok\n")
```

## Notebook Problems

Signals:

- Notebook execution dependency errors.
- Notebook cannot find `snakemake` inputs or outputs.
- A notebook relies on interactive state.

Authoring fixes:

- Keep notebooks under a predictable workflow-relative directory.
- Access `snakemake.input`, `snakemake.output`, and `snakemake.params` inside the notebook.
- Use `.py.ipynb` or `.r.ipynb` naming when helpful for language clarity.
- Validate with a tiny target before full workflow execution.

Dependency repair belongs to deployment-storage.

## Wrapper or CWL Problems

Signals:

- Wrapper code downloads but fails due to unexpected IO names.
- A wrapper identifier is mutable or unavailable.
- CWL execution fails because `cwltool` or a container runtime is absent.

Authoring checks:

- Match the wrapper/CWL tool's expected named `input`, `output`, `params`, `threads`, and `resources`.
- Pin wrapper identifiers, tags, or URLs where possible.
- Do not mix `wrapper:` or `cwl:` with `shell:`/`script:` in the same rule.
- Validate the DAG and printed commands first; route environment failures to deployment-storage.

## Shell Formatting Problems

Signals:

- Snakemake tries to substitute `{print $1}` or other shell braces.
- Paths with spaces break commands.
- A Bash pipeline fails due to strict mode.

Fixes:

```python
shell:
    "awk '{{print $1}}' {input:q} > {output:q}"
```

```python
shell:
    "tool --input {input.table:q} --output {output.result:q} > {log:q} 2>&1"
```

Move complex shell logic into `script:` when quoting and error handling become hard to audit.

## Legacy `--reason` Commands

Symptom:

```text
snakemake: error: unrecognized arguments: --reason
```

Fix:

```bash
snakemake --snakefile Snakefile --cores 1 --dry-run --printshellcmds
```

Reasons are still shown in Snakemake 9.23.1 dry-run output; the old flag is not needed and is invalid.
