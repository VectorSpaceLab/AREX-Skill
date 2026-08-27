# Workflow Authoring Patterns

Use these patterns to create or refactor Snakefiles without relying on external examples.

## Pattern: Convert an Ad Hoc Script Chain

Start by listing concrete file boundaries. Durable files become rule outputs; consumed files become rule inputs; transient files can become `temp()` outputs.

```python
SAMPLES = ["A", "B"]

rule all:
    input:
        expand("results/{sample}.summary.txt", sample=SAMPLES)

rule clean:
    input:
        raw="raw/{sample}.csv"
    output:
        cleaned=temp("cleaned/{sample}.csv")
    log:
        "logs/clean/{sample}.log"
    shell:
        "python scripts/clean.py {input.raw:q} {output.cleaned:q} 2> {log:q}"

rule summarize:
    input:
        cleaned="cleaned/{sample}.csv"
    output:
        summary="results/{sample}.summary.txt"
    log:
        "logs/summarize/{sample}.log"
    script:
        "scripts/summarize.py"
```

Checklist:

- Put target files in `rule all`.
- Use named IO/logs before commands grow complex.
- Put logs under `logs/<rule>/...` with the same wildcards as outputs.
- Move Python longer than a few lines into `script:`.
- Validate with `snakemake --cores 1 --dry-run --printshellcmds` before a real run.

## Pattern: Named IO for Maintainable Commands

Avoid index-heavy commands:

```python
shell: "tool {input[0]} {input[1]} {output[0]}"
```

Prefer names:

```python
rule compare:
    input:
        case="data/{sample}.case.tsv",
        control="data/{sample}.control.tsv"
    output:
        report="reports/{sample}.txt"
    shell:
        "tool --case {input.case:q} --control {input.control:q} --out {output.report:q}"
```

Named IO is especially useful for scripts, wrappers, module overrides, and handoffs between agents.

## Pattern: Known Targets vs Existing-File Discovery

If sample names are known from a small constant or configuration value, build targets directly:

```python
SAMPLES = ["s1", "s2", "s3"]

rule all:
    input:
        expand("plots/{sample}.svg", sample=SAMPLES)
```

If sample names are encoded in files that already exist before the workflow starts:

```python
SAMPLES, = glob_wildcards("reads/{sample}.fastq.gz")
```

If sample names or chunks are produced by upstream jobs, use a checkpoint input function instead of top-level `glob_wildcards()`.

## Pattern: Reduce Wildcard Ambiguity

Symptoms include `AmbiguousRuleException`, unexpected wildcard values, or input functions receiving values with extra dots/slashes.

Prefer structural separation:

```python
output: "results/{sample}/groups/{group}.txt"
```

If flat filenames are required, constrain the wildcards:

```python
rule write_group:
    output:
        r"results/{sample,[A-Za-z0-9_-]+}.{group,case|control}.txt"
    shell:
        "make-group {wildcards.sample:q} {wildcards.group:q} > {output:q}"
```

If two rules intentionally overlap, use `ruleorder` as a last-mile tie-breaker:

```python
ruleorder: write_specific > write_generic
```

Still prefer distinct output directories or suffixes where possible.

## Pattern: Input Function for Wildcard-Dependent Files

Use input functions when the mapping from wildcard to input file is non-patterned:

```python
READS_BY_SAMPLE = {
    "tumor": ["reads/tumor_R1.fq.gz", "reads/tumor_R2.fq.gz"],
    "normal": ["reads/normal_R1.fq.gz", "reads/normal_R2.fq.gz"],
}

def reads_for_sample(wildcards):
    try:
        return READS_BY_SAMPLE[wildcards.sample]
    except KeyError as error:
        raise ValueError(f"Unknown sample {wildcards.sample!r}") from error

rule align:
    input:
        reads=reads_for_sample
    output:
        bam="mapped/{sample}.bam"
    shell:
        "aligner {input.reads:q} > {output.bam:q}"
```

Robustness checklist:

- Pass the function object, not its result.
- Raise a clear exception for unsupported wildcard values.
- Avoid side effects in input functions.
- Add constraints if the output pattern can match unintended sample values.

## Pattern: Extract Python into `script:`

Snakefile:

```python
rule summarize:
    input:
        table="tables/{sample}.tsv"
    output:
        summary="results/{sample}.txt"
    params:
        min_count=10
    log:
        "logs/summarize/{sample}.log"
    script:
        "scripts/summarize.py"
```

Script body pattern:

```python
from pathlib import Path

out = Path(snakemake.output.summary)
out.parent.mkdir(parents=True, exist_ok=True)
with open(snakemake.input.table) as src, out.open("w") as dst:
    for line in src:
        dst.write(line)
```

If the script may also be run directly, add an explicit CLI fallback. Do not assume the `snakemake` object exists outside `script:`.

## Pattern: Reusable Rule Files with `include:`

Layout:

```text
workflow/
  Snakefile
  rules/
    qc.smk
    transform.smk
  scripts/
    summarize.py
```

Main Snakefile:

```python
SAMPLES = ["A", "B"]

rule all:
    input:
        expand("results/{sample}.txt", sample=SAMPLES)

include: "rules/qc.smk"
include: "rules/transform.smk"
```

Included files share namespace and config. Keep each include focused; avoid hidden default targets in included files unless the import order makes that intentional.

## Pattern: Reusable Workflows with Modules

Use modules when you need namespace isolation or selective rule import.

```python
module qc:
    snakefile:
        "modules/qc/Snakefile"
    config:
        {"samples": ["A", "B"]}
    prefix:
        "module_outputs/qc"

use rule * from qc as qc_*
```

Override a specific imported rule with the original rule name:

```python
use rule summarize from qc as qc_summarize with:
    output:
        "results/qc/{sample}.txt"
```

Module surprises to prevent:

- Do not name a module `workflow`.
- Remember that module helpers live under the module namespace.
- `prefix:` relocates relative module IO; check paths in dry-run before execution.
- When `use rule * ... as prefix_*` has already imported a rule, a second override must refer to the original module rule name.
- Dynamic module imports need variable-to-variable aliasing, not literal alias transformations.

## Pattern: Checkpoint-Generated Fan-Out

Use checkpoints for unknown downstream files created by an upstream job.

```python
import os

SAMPLES = ["A", "B"]

rule all:
    input:
        expand("aggregated/{sample}.txt", sample=SAMPLES)

checkpoint split:
    input:
        "data/{sample}.txt"
    output:
        directory("chunks/{sample}")
    shell:
        "mkdir -p {output}; awk '{{print > \"{output}/chunk_\" NR \".txt\"}}' {input:q}"


def chunk_inputs(wildcards):
    chunk_dir = checkpoints.split.get(sample=wildcards.sample).output[0]
    chunks, = glob_wildcards(os.path.join(chunk_dir, "{chunk}.txt"))
    return expand(os.path.join(chunk_dir, "{chunk}.txt"), chunk=chunks)

rule aggregate:
    input:
        chunk_inputs
    output:
        "aggregated/{sample}.txt"
    shell:
        "cat {input:q} > {output:q}"
```

Key rule: call `checkpoints.split.get(...)` inside the input function. Top-level `glob_wildcards("chunks/{sample}/{chunk}.txt")` runs too early and will miss files generated by the checkpoint.

## Pattern: Output Flag Selection

Use flags to express lifecycle, not as decoration:

```python
rule temporary_sort:
    output:
        temp("tmp/{sample}.sorted.tsv")
    shell:
        "sort raw/{wildcards.sample:q}.tsv > {output:q}"

rule final_index:
    output:
        protected("indexes/{sample}.idx")
    shell:
        "indexer {wildcards.sample:q} > {output:q}"

rule validate:
    output:
        ensure("results/{sample}.txt", non_empty=True)
    shell:
        "generate {wildcards.sample:q} > {output:q}"
```

Use `directory()` for directory outputs, `touch()` for marker outputs, and `ancient()` for inputs that should never trigger rebuilds due to timestamps.

## Pattern: Wrapper, Notebook, and CWL Hooks

Keep authoring concise and explicit:

```python
rule run_wrapper:
    input:
        reads="reads/{sample}.fq.gz"
    output:
        report="qc/{sample}.html"
    params:
        extra="--quiet"
    wrapper:
        "v1.0.0/bio/tool"
```

```python
rule notebook_report:
    input:
        table="tables/{sample}.tsv"
    output:
        html="reports/{sample}.html"
    notebook:
        "notebooks/report.py.ipynb"
```

```python
rule cwl_tool:
    input:
        reads="reads/{sample}.fq.gz"
    output:
        out="results/{sample}.txt"
    cwl:
        "tools/process.cwl"
```

Pin wrapper/tool identifiers where possible and route environment/container setup to deployment-storage.

## Refactor Validation Loop

After each structural change:

```bash
snakemake --snakefile Snakefile --cores 1 --dry-run --printshellcmds
snakemake --snakefile Snakefile --cores 1 --dry-run --dag > dag.dot
snakemake --snakefile Snakefile --cores 1 --dry-run specific/target.txt
```

If a copied command mentions `--reason`, remove it for Snakemake 9.23.1.
