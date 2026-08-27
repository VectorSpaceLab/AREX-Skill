# Command wrapper workflows

## Translate shell commands to dispatcher calls

Rule of thumb: remove the executable name, keep the subcommand as the dispatcher attribute, and pass every remaining shell token as a separate string argument.

| Shell command | Python call |
| --- | --- |
| `samtools view -h reads.bam` | `pysam.samtools.view("-h", "reads.bam")` |
| `samtools sort -o sorted.bam reads.bam` | `pysam.samtools.sort("-o", "sorted.bam", "reads.bam", catch_stdout=False)` |
| `samtools index sorted.bam` | `pysam.samtools.index("sorted.bam")` |
| `samtools idxstats sorted.bam` | `pysam.samtools.idxstats("sorted.bam", split_lines=True)` |
| `samtools cram-size sample.cram` | `pysam.samtools.cram_size("sample.cram")` |
| `samtools import input.fq` | `pysam.samtools.fqimport("input.fq")` |
| `bcftools view -H variants.vcf.gz` | `pysam.bcftools.view("-H", "variants.vcf.gz")` |
| `bcftools query -f '%CHROM\t%POS\n' variants.vcf.gz` | `pysam.bcftools.query("-f", "%CHROM\t%POS\n", "variants.vcf.gz")` |
| `bcftools index --csi variants.vcf.gz` | `pysam.bcftools.index("--csi", "variants.vcf.gz")` |

Do not include shell-only redirection tokens in dispatcher calls. Replace `>` with captured return values, `save_stdout`, or command-native output options.

## Capture text output in memory

Use the default `catch_stdout=True` for small text output that the Python code needs to parse.

```python
import pysam

stats_text = pysam.samtools.flagstat("reads.bam")
for line in stats_text.splitlines():
    if "mapped" in line:
        print(line)

idxstats_lines = pysam.samtools.idxstats("reads.bam", split_lines=True)
rows = [line.split("\t") for line in idxstats_lines if line]
```

For top-level samtools aliases, the equivalent calls are `pysam.flagstat(...)` and `pysam.idxstats(...)`.

## Save stdout to a file

Use `save_stdout` when a command naturally writes useful stdout and the output should go to a file.

```python
import pysam

pysam.samtools.mpileup("reads.bam", save_stdout="reads.pileup")
pysam.bcftools.query("-f", "%CHROM\t%POS\t%REF\t%ALT\n", "variants.vcf.gz", save_stdout="sites.tsv")
```

The call returns `None` when stdout is saved this way. Inspect `get_messages()` afterwards for warnings.

## Let the command own its output file

Use command-native output flags with `catch_stdout=False` when the wrapped tool writes a file itself, especially for BAM/CRAM/BCF or compressed output.

```python
import pysam

pysam.samtools.sort("-o", "sorted.bam", "reads.bam", catch_stdout=False)
pysam.samtools.index("sorted.bam")
pysam.bcftools.view("-O", "z", "-o", "filtered.vcf.gz", "input.vcf", catch_stdout=False)
pysam.bcftools.index("--tbi", "filtered.vcf.gz")
```

This prevents pysam’s stdout capture from conflicting with the tool’s own output handling.

## Build commands safely from Python data

Assemble a token list and splat it into the dispatcher. Keep values as separate tokens even when they came from user input or configuration.

```python
from pathlib import Path
import pysam

input_bam = Path("reads.bam")
output_bam = Path("mapped.bam")
min_mapq = 20

args = ["-b", "-q", str(min_mapq), "-o", str(output_bam), str(input_bam)]
pysam.samtools.view(*args, catch_stdout=False)
```

Avoid `pysam.samtools.view(f"-b -q {min_mapq} -o {output_bam} {input_bam}")`; that passes one argument containing spaces, not five command tokens.

## Check usage and errors before retrying

`usage()` is a cheap way to confirm required options and the correct command spelling. Catch `pysam.SamtoolsError` around inputs that may be missing, malformed, or incompatible.

```python
import pysam

try:
    pysam.samtools.sort("reads.bam")
except pysam.SamtoolsError as error:
    print("sort failed:", error)
    print("usage excerpt:", pysam.samtools.sort.usage().splitlines()[0])
    print("stderr:", pysam.samtools.sort.get_messages())
```

Call `get_messages()` on the dispatcher that was invoked, not on the module.

## Convert common pipelines

Pysam dispatchers do not implement shell pipes. Split a pipeline into staged files or use Python parsing for small text output.

Shell:

```bash
samtools view -h reads.bam | samtools sort -o sorted.bam
```

Python with explicit staging:

```python
import os
import tempfile
import pysam

with tempfile.TemporaryDirectory() as workdir:
    staged_sam = os.path.join(workdir, "reads.sam")
    pysam.samtools.view("-h", "reads.bam", save_stdout=staged_sam)
    pysam.samtools.sort("-o", "sorted.bam", staged_sam, catch_stdout=False)
```

For large alignment or variant transformations, prefer command-native output files or object-level APIs in sibling sub-skills rather than capturing large data in memory.

## Work with bcftools output formats

When `bcftools view`, `bcftools norm`, or related commands write compressed VCF/BCF, use `-O`/`-o` and disable capture.

```python
import pysam

pysam.bcftools.view(
    "-O", "b",
    "-o", "subset.bcf",
    "-s", "sampleA,sampleB",
    "input.vcf.gz",
    catch_stdout=False,
)
pysam.bcftools.index("subset.bcf")
```

For small textual reports, keep default capture:

```python
report = pysam.bcftools.stats("variants.vcf.gz")
summary = [line for line in report.splitlines() if line.startswith("SN")]
```

## Route producers and consumers

Use this sub-skill only for invoking bundled commands. If a workflow needs to create a BAM/CRAM object before running `samtools index`, route the object creation to the alignment I/O sub-skill, then return here for the command wrapper call. If a workflow needs to edit VCF records before running `bcftools index`, route record manipulation to the variant I/O sub-skill, then return here for the command wrapper call.
