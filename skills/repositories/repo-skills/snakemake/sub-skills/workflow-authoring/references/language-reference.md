# Snakemake 9.23.1 Snakefile Language Reference

This reference covers authoring-time Snakefile semantics. It does not cover execution profiles, deployment environments, storage backends, config-schema design, reports, or Python API orchestration.

## Mental Model

Snakemake authoring has three useful phases:

1. **Initialization**: Snakefiles are parsed, top-level Python runs, `include:` files are loaded, modules are registered, and rules/checkpoints are defined.
2. **DAG construction**: requested targets are matched to rule outputs, wildcard values are inferred, input/params/resources functions are evaluated, and checkpoint-aware dependencies are resolved.
3. **Execution**: selected jobs run with scheduling, resources, environments, and backends handled by execution/deployment concerns.

Author with this distinction in mind: use `expand()` and top-level Python for values known during initialization; use input/params/resources functions for values known only after wildcard inference; use checkpoints for values discovered only after an upstream job has run.

## Minimal Rule Anatomy

```python
SAMPLES = ["A", "B"]

rule all:
    input:
        expand("results/{sample}.txt", sample=SAMPLES)

rule summarize:
    input:
        table="data/{sample}.tsv"
    output:
        summary="results/{sample}.txt"
    log:
        stderr="logs/summarize/{sample}.err"
    params:
        label=lambda wildcards: f"sample-{wildcards.sample}"
    threads: 1
    resources:
        mem_mb=512
    shell:
        "python scripts/summarize.py --label {params.label:q} {input.table:q} > {output.summary:q} 2> {log.stderr:q}"
```

Rules should normally have one execution directive: `shell:`, `run:`, `script:`, `notebook:`, `wrapper:`, or `cwl:`. Prefer named `input`, `output`, and `log` entries once a rule has more than one file.

## Targets and Rule Ordering

The first rule without wildcards is the default target unless another rule is marked with `default_target: True`. Target rules should collect concrete file paths, usually via `expand()`.

```python
rule all:
    input:
        expand("plots/{sample}.svg", sample=SAMPLES)
```

Use `ruleorder` only to break intentional overlap between producer rules:

```python
ruleorder: specific_converter > generic_converter
```

Do not use `ruleorder` as a substitute for clear output namespaces or wildcard constraints.

## Wildcards and Constraints

Wildcards are inferred from output patterns. The inferred values propagate to input files, logs, params, and commands.

```python
rule convert:
    input:
        "raw/{sample}.dat"
    output:
        "results/{sample}.txt"
    shell:
        "cat {input:q} > {output:q}"
```

All output, log, and benchmark files for a rule must use compatible wildcard sets so each job maps to unique paths. Multiple wildcards in flat filenames can be ambiguous:

```python
# Ambiguous for results/101.normal.txt: where does dataset end?
output: "results/{dataset}.{group}.txt"
```

Constrain wildcards in one of three places:

```python
# Inline constraint.
output: r"results/{dataset,\d+}.{group,case|control}.txt"

# Rule-local constraint.
wildcard_constraints:
    sample="[A-Za-z0-9_-]+"

# Global constraint.
wildcard_constraints:
    sample="[A-Za-z0-9_-]+"
```

Prefer directory structure over clever regular expressions when possible:

```python
output: r"results/{dataset,\d+}/groups/{group,case|control}.txt"
```

## `expand()`, `collect()`, `glob_wildcards()`, and `multiext()`

`snakemake.io.expand(*args, **wildcard_values)` creates concrete paths from patterns. By default, it uses Cartesian product:

```python
expand("qc/{sample}.{metric}.txt", sample=["A", "B"], metric=["depth", "gc"])
```

Pass a combinator such as `zip` as the second positional argument for paired values:

```python
expand("pairs/{sample}.{read}.fq", zip, sample=["A", "B"], read=["R1", "R2"])
```

Mask a wildcard with doubled braces when it must remain unresolved in the generated pattern:

```python
expand("chunks/{{sample}}/{chunk}.txt", chunk=[1, 2, 3])
```

`collect()` is an alias-style helper for `expand()` when gathering outputs. `snakemake.io.glob_wildcards(pattern, files=None, followlinks=False)` discovers wildcard values from files that exist before DAG construction:

```python
SAMPLES, = glob_wildcards("reads/{sample}.fastq.gz")
```

Do not use top-level `glob_wildcards()` for files that upstream rules will create. Put that discovery behind a checkpoint input function.

`snakemake.io.multiext(prefix, *extensions, **named_extensions)` defines a consistent set of same-prefix files:

```python
output:
    multiext("plots/{sample}", ".pdf", ".svg", ".png")
```

Use either all positional extensions or all named extensions, not a mixture. Treat `multiext()` as positional output before additional named outputs.

## Input Functions and Deferred Values

Input functions run during DAG construction after wildcard values are known.

```python
READS = {"A": "reads/A.fastq.gz", "B": "reads/B.fastq.gz"}

def reads_for_sample(wildcards):
    try:
        return READS[wildcards.sample]
    except KeyError as error:
        raise ValueError(f"No reads configured for sample {wildcards.sample!r}") from error

rule align:
    input:
        reads=reads_for_sample
    output:
        bam="mapped/{sample}.bam"
    shell:
        "aligner {input.reads:q} > {output.bam:q}"
```

Rules for input functions:

- Pass the function object (`reads_for_sample`), not a call (`reads_for_sample()`).
- The first argument must represent `wildcards`.
- A function may return a string, a list of strings, or a dict when used with `unpack()`.
- An optional second argument named exactly `groupid` is supported for group-local behavior.
- Handle every wildcard value that the output pattern can match, or tighten the wildcard constraints.

For named returns:

```python
def paired_reads(wildcards):
    return {
        "r1": f"reads/{wildcards.sample}_R1.fastq.gz",
        "r2": f"reads/{wildcards.sample}_R2.fastq.gz",
    }

rule align_paired:
    input:
        unpack(paired_reads)
    output:
        "mapped/{sample}.bam"
    shell:
        "aligner -1 {input.r1:q} -2 {input.r2:q} > {output:q}"
```

Exceptions raised by input functions surface as `InputFunctionException` with the rule and wildcard values.

## `params`, `resources`, `threads`, and `log`

`params` is for non-file command values. `params` functions may accept `wildcards` first and optionally `input`, `output`, `threads`, and `resources`.

```python
rule call:
    input:
        bam="mapped/{sample}.bam"
    output:
        vcf="calls/{sample}.vcf"
    params:
        prior=lambda wildcards: "0.001" if wildcards.sample.startswith("A") else "0.0001"
    threads: 4
    resources:
        mem_mb=lambda wildcards, threads: threads * 1024
    log:
        stderr="logs/call/{sample}.err"
    shell:
        "caller --prior {params.prior} --threads {threads} {input.bam:q} > {output.vcf:q} 2> {log.stderr:q}"
```

Resource functions may accept `wildcards` and optional context such as `input`, `threads`, and `attempt`. Keep execution-policy choices with the execution-cli sub-skill.

Log files should contain the same wildcards as outputs to avoid collisions between jobs.

## Shell Formatting

Snakemake formats shell strings with fields such as `{input}`, `{output}`, `{params.name}`, `{threads}`, and `{wildcards.sample}`. Use `:q` to quote paths safely:

```python
shell:
    "tool --in {input.table:q} --out {output.result:q} > {log:q} 2>&1"
```

Escape literal braces by doubling them:

```python
shell:
    "awk '{{print $1}}' {input:q} > {output:q}"
```

Shell commands use Bash strict mode by default. If a pipeline can legitimately produce a non-zero status in an early segment, handle that explicitly rather than assuming shell leniency.

## Output and Input Flags

Installed helper signatures include:

- `protected(value)` marks outputs read-only after successful creation.
- `temp(value, group_jobs=False)` marks intermediate outputs for cleanup; `group_jobs=True` hints that producer and consumer should be grouped when useful.
- `directory(value)` marks directory outputs for safe tracking.
- `ancient(value)` marks inputs as always older than outputs.
- `touch(value)` creates/updates marker outputs after success.
- `ensure(value, non_empty=False, sha256=None, md5=None, sha1=None)` validates output non-emptiness or checksum.

Examples:

```python
rule index:
    input: "reference/genome.fa"
    output: protected("reference/genome.fa.idx")
    shell: "indexer {input:q} {output:q}"

rule intermediate:
    output: temp("tmp/{sample}.txt")
    shell: "make-tmp {wildcards.sample:q} > {output:q}"

rule done:
    output: touch("done/{sample}.ok")
    shell: "validate {wildcards.sample:q}"
```

Use `directory()` only when the directory itself is the meaningful output; normal files are easier to reason about.

## Includes and Pathvars

`include:` inserts another Snakefile into the same namespace:

```python
include: "rules/qc.smk"
include: "rules/transform.smk"
```

Included files share global Python variables, config, and rule namespace with the including Snakefile.

Pathvars let reusable workflows parameterize path components before wildcard resolution:

```python
pathvars:
    results="results",
    per="{sample}"

rule report:
    output: "<results>/<per>/report.txt"
    shell: "make-report > {output:q}"
```

Pathvars are resolved when rules are parsed; values can contain wildcards.

## Modules and Rule Imports

Modules isolate another workflow namespace and selectively import rules:

```python
module qc_workflow:
    snakefile:
        "workflow/modules/qc/Snakefile"
    config:
        {"samples": ["A", "B"]}
    prefix:
        "module_outputs/qc"

use rule * from qc_workflow as qc_*
```

Important semantics:

- A module cannot be named `workflow`.
- Non-rule Python in the module stays in the module namespace; access helpers as `qc_workflow.helper()`.
- `prefix:` relocates relative input/output files of the module.
- A module-level `config:` overrides module configfile statements; `skip_validation: True` can skip validation inside an imported module.
- When overriding imported rules, use the original rule name from the module, not the already-prefixed imported name.

```python
use rule align from qc_workflow as qc_align with:
    output:
        "custom/qc/{sample}.bam"
```

Snakemake 9 supports dynamic module names through `name:` in the module definition. When importing dynamic modules inside a loop, keep aliases one-to-one with variables; literal transformations such as `as module_*` are not allowed for dynamic module variables.

## Checkpoints

Checkpoints are rules whose output influences later DAG construction. Use them when downstream file names or branches are not knowable until the checkpoint output exists.

```python
checkpoint split:
    output:
        directory("chunks/{sample}")
    shell:
        "mkdir -p {output}; printf 'a\nb\n' | while read c; do echo $c > {output}/$c.txt; done"


def aggregate_inputs(wildcards):
    checkpoint_output = checkpoints.split.get(sample=wildcards.sample).output[0]
    chunk_ids, = glob_wildcards(os.path.join(checkpoint_output, "{chunk}.txt"))
    return expand(os.path.join(checkpoint_output, "{chunk}.txt"), chunk=chunk_ids)

rule aggregate:
    input:
        aggregate_inputs
    output:
        "aggregated/{sample}.txt"
    shell:
        "cat {input:q} > {output:q}"
```

Rules:

- Call `checkpoints.name.get(**wildcards)` inside an input function, not at top level.
- Read or glob checkpoint outputs only after `get()` has made Snakemake schedule and complete the checkpoint.
- Use `directory()` for checkpoint outputs that contain an unknown set of files.
- Do not precompute checkpoint-dependent `glob_wildcards()` during initialization.

## Scripts, Notebooks, Wrappers, and CWL

`script:` runs an external script with a global `snakemake` object exposing `input`, `output`, `params`, `wildcards`, `log`, `threads`, `resources`, and `config`.

```python
rule filter_table:
    input: table="tables/{sample}.tsv"
    output: filtered="filtered/{sample}.tsv"
    log: "logs/filter/{sample}.log"
    script: "scripts/filter_table.py"
```

A Python script can optionally support standalone execution, but when called via `script:` it should use the injected `snakemake` object and create missing parent directories as needed.

`notebook:` behaves similarly but requires notebook/Jupyter dependencies and usually an `.ipynb` path or language-indicating notebook source. Route dependency installation to deployment-storage.

`wrapper:` and `cwl:` delegate implementation to reusable wrappers or CWL tools. Pin identifiers/URLs and match expected named `input`, `output`, `params`, `threads`, and `resources`. Environment/container troubleshooting belongs to deployment-storage; report preservation and deep debugging belong to debugging-reporting.

## Authoring Smoke Commands

Use these current commands while authoring:

```bash
snakemake --snakefile Snakefile --cores 1 --dry-run --printshellcmds
snakemake --snakefile Snakefile --cores 1 --dry-run target/file.txt
snakemake --snakefile Snakefile --cores 1 --dry-run --dag > dag.dot
python -m snakemake --help
```

Do not use `--reason` with Snakemake 9.23.1. Reasons appear in dry-run output without that legacy flag.
