# Command wrapper reference

## Mental model

Pysam exposes many bundled `samtools` and `bcftools` subcommands as `PysamDispatcher` objects. Calling a dispatcher emulates the corresponding command-line tool without starting a shell. Each command-line token becomes one Python string argument:

```python
import pysam
import pysam.samtools
import pysam.bcftools

text = pysam.samtools.view("-h", "reads.bam")
pysam.samtools.sort("-o", "sorted.bam", "reads.bam", catch_stdout=False)
pysam.bcftools.index("--csi", "variants.vcf.gz")
```

The same samtools dispatchers are also imported into the top-level `pysam` namespace for backward-compatible calls such as `pysam.view(...)`, `pysam.sort(...)`, `pysam.index(...)`, `pysam.idxstats(...)`, and `pysam.faidx(...)`. Prefer `pysam.samtools.<command>` in new examples when clarity matters, but recognize top-level aliases in existing code.

## Dispatcher call contract

For each available command, the effective signature is:

```python
pysam.samtools.command(*args, catch_stdout=True, save_stdout=None, split_lines=False)
pysam.bcftools.command(*args, catch_stdout=True, save_stdout=None, split_lines=False)
```

Useful keywords:

- `catch_stdout=True`: capture command stdout and return it as the call result.
- `catch_stdout=False`: do not capture stdout; the function returns `None` unless another parser applies. Use this with command-native output options such as `-o output.bam`.
- `save_stdout="path"`: write stdout to the named file and return `None`.
- `split_lines=True`: split captured stdout into `list[str]`; captured stderr returned by `get_messages()` also follows the split setting for that invocation.
- `raw=True`: bypass any parser associated with the dispatcher and return raw stdout.

The command’s stderr is always captured. After a command returns, call the same dispatcher’s `get_messages()` to retrieve stderr from the most recent invocation. If the underlying command exits with a non-zero status, pysam raises `pysam.SamtoolsError` and includes the command collection, return code, stdout, and stderr in the exception text.

Use `dispatcher.usage()` for a command’s help or usage text. Some commands write usage to stderr internally; `usage()` normalizes this by returning the message as a string.

## Return types

- Text output normally returns `str`.
- `split_lines=True` returns `list[str]` for captured text output.
- Commands that produce binary output can return `bytes`; avoid accidental in-memory binary capture by using command output options or `save_stdout` when the output may be large.
- `catch_stdout=False` or `save_stdout=...` returns `None` for stdout-driven commands.
- `get_messages()` returns the captured stderr as `str`, `bytes`, or a split list depending on command behavior and `split_lines`.

## Safe command construction

Build commands as lists or tuples of tokens and splat them into the dispatcher. Do not pass shell metacharacters such as `>`, `|`, or quoted compound strings unless the command itself expects that exact token.

```python
args = ["-f", "2", "-o", "mapped.bam", "input.bam"]
pysam.samtools.view(*args, catch_stdout=False)
```

For user inputs, validate file paths and option choices before passing them to a dispatcher. Do not concatenate user text into a single command string; dispatchers do not run through a shell, and tokenized calls avoid shell injection mistakes.

## samtools inventory

`pysam.samtools` defines these dispatchers:

- `addreplacerg`, `ampliconclip`, `ampliconstats`, `bam2fq`, `bamshuf`, `bedcov`, `calmd`, `cat`, `checksum`, `collate`, `consensus`, `coverage`
- `cram_size` for command `cram-size`
- `depad`, `depth`, `dict`, `faidx`, `fasta`, `fastq`, `fixmate`, `flags`, `flagstat`, `fqidx`
- `fqimport` for command `import`
- `head`, `idxstats`, `index`, `markdup`, `merge`, `mpileup`, `pad2unpad`, `phase`, `quickcheck`, `reference`, `reheader`, `reset`, `rmdup`, `samples`, `sort`, `split`, `stats`, `targetcut`, `tview`, `version`, `view`

Top-level `pysam` imports these samtools names, so `pysam.sort(...)` and `pysam.samtools.sort(...)` refer to the same command wrapper family.

## bcftools inventory

`pysam.bcftools` defines these dispatchers:

- `annotate`, `call`, `cnv`, `concat`, `consensus`, `convert`, `csq`, `filter`, `gtcheck`, `head`, `index`, `isec`, `merge`, `mpileup`, `norm`, `plugin`, `query`, `reheader`, `roh`, `sort`, `stats`, `view`

`bcftools` dispatchers are not imported into top-level `pysam`; access them through `pysam.bcftools.<command>`.

## Version context

The pysam package version covered by this skill is `0.24.0`, wrapping `htslib 1.23.1`, `samtools 1.23.1`, and `bcftools 1.23.1`. Prefer `pysam.__samtools_version__`, `pysam.__bcftools_version__` when available, and `pysam.samtools.version.usage()` or `pysam.bcftools.view.usage()` for command-level help in live environments.

## Confirmed behavior checkpoints

- `PysamDispatcher` stores the command collection and dispatch name, calls the bundled command dispatcher, captures stdout/stderr, raises `SamtoolsError` on non-zero return codes, and exposes `get_messages()` plus `usage()`.
- Public pysam behavior includes tokenized calls, top-level samtools aliases, `cram_size`/`fqimport`, `catch_stdout`, `save_stdout`, `split_lines`, stderr capture, and `SamtoolsError`.
- Command wrapper behavior is expected to match the bundled samtools/bcftools tools for supported subcommands while using Python return values or explicit output files instead of shell redirection.
- `split_lines=True` and `split_lines=False` are both supported for text-producing commands such as `idxstats` and `bedcov`.
