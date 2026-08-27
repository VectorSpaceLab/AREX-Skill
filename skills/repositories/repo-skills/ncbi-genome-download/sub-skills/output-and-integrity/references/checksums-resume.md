# Checksums, reruns, and recovery

Start with the [output-and-integrity skill](../SKILL.md), then use
[output-layout](output-layout.md) to identify the canonical file. This page
covers the implementation's integrity decisions, not a general MD5 tutorial.

## Where `MD5SUMS` comes from

For each candidate, ngd converts the entry's FTP path to HTTPS and requests
`md5checksums.txt`. A failed checksum request is attempted twice immediately
by `grab_checksums_file`; if both responses are not OK, that candidate produces
no jobs. This immediate two-request behavior is independent of CLI
`--retries`, which retries the broader invocation only after a return code `75`.

- Nested output: if `OUT/SECTION/DOMAIN/ACCESSION/MD5SUMS` is absent or older
  than `md5_cache_days` days, the fetched text is written there. Otherwise the
  existing file is read and no checksum-manifest request is needed.
- Flat output: checksum text is fetched for the candidate and parsed, but no
  persistent `MD5SUMS` is written by `create_downloadjob`.
- `--no-cache` concerns assembly summaries, not these per-assembly manifests.
  See [metadata and concurrency](metadata-and-concurrency.md#summary-cache-versus-checksum-cache)
  for the distinction.

The parser accepts lines that split into exactly two whitespace-separated
fields (MD5 and filename), removes a leading `./`, skips blanks, and logs
malformed lines only at debug level. Standard NCBI lines therefore look like:

```text
0123456789abcdef0123456789abcdef  ./assembly_genomic.gbff.gz
```

Do not hand-edit a checksum to bless a bad file. If a manifest is truncated,
ambiguous, or from the wrong assembly, remove it in a disposable fixture (or
let its age expire) and obtain a fresh approved manifest.

## Filename matching gotchas

`get_name_and_checksum(checksums, ending)` returns the first checksum entry
whose filename ends with the requested format ending. It deliberately rejects
CDS and RNA-from-genomic names when looking for ordinary genomic FASTA:

- `fasta` means `_genomic.fna.gz`, but must **not** select
  `_cds_from_genomic.fna.gz` or `_rna_from_genomic.fna.gz`; broad matching on
  the shared `genomic.fna.gz` tail is unsafe.
- `cds-fasta` means `_cds_from_genomic.fna.gz`.
- `rna-fasta` means `_rna_from_genomic.fna.gz`.
- `rna-fna` means `_rna.fna.gz`.

Long assembly names do not change the rule: match the exact configured suffix,
not a substring or a hand-shortened accession. A requested format absent from
the manifest raises `ValueError`, is logged by `create_downloadjob`, and is
skipped. If all requested formats are absent, that entry returns an empty job
list; the overall command can still return `0` because there was a candidate.

A robust fixture should include all of these lines and assert the selected
filename for each:

```text
11111111111111111111111111111111  ./X_cds_from_genomic.fna.gz
22222222222222222222222222222222  ./X_genomic.fna.gz
33333333333333333333333333333333  ./X_rna_from_genomic.fna.gz
44444444444444444444444444444444  ./X_rna.fna.gz
```

The checksum values above are labels for a parser fixture, not valid digests
for arbitrary content. For an end-to-end fixture, compute them with
`ncbi_genome_download.core.md5sum` after writing the tiny file.

## Reuse, re-download, and interruption

For each selected format, `has_file_changed(directory, checksums, format)`:

1. selects the manifest filename and expected MD5;
2. returns true when the canonical file is absent;
3. otherwise computes the actual MD5 in 4096-byte chunks and returns true on a
   mismatch or false on an exact match.

A false result means the file is reused; there is no HTTP range request,
temporary-part resume, or size-only shortcut. A partial file is just a
mismatch and is downloaded from the beginning on the next run.

`save_and_check(response, local_file, expected_checksum)` opens the destination
with `wb`, writes every `iter_content(4096)` chunk, then computes MD5. It does
not write to a temporary name and rename atomically. On mismatch, the bad
content remains at `local_file`, the worker returns `False`, and no symlink is
created for that job. A later run detects that mismatch and overwrites it.
Therefore, after interruption or a mismatch:

1. stop using the affected file;
2. retain the manifest for diagnosis, but verify it matches the same entry;
3. rerun with the same destination and formats, or delete only the bad file;
4. inspect MD5 and link targets before consuming data.

A caught connection/chunked-transfer exception yields `75`; `--retries N`
means up to N additional complete `args_download` attempts after the initial
attempt. It is not N retries per file, does not retry checksum mismatches, and
is not a resume. A worker-level false result is currently not collected by
`config_download`, so a log warning and code `0` can coexist; treat file-level
verification as mandatory.

## Safe mocked checksum smoke

This is a network-free check that can be run from an installed environment
with a temporary directory. It uses a tiny fake response object and exercises
the same lower-level objects used by the CLI; it does not contact NCBI:

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from ncbi_genome_download import core

class Response:
    def __init__(self, payload):
        self.payload = payload
    def iter_content(self, size):
        yield self.payload[:1]
        yield self.payload[1:]

with TemporaryDirectory() as d:
    root = Path(d)
    target = root / "fixture_genomic.gbff.gz"
    payload = b"tiny fixture\n"
    expected = __import__("hashlib").md5(payload).hexdigest()
    checksums = core.parse_checksums(
        f"{expected}  ./fixture_genomic.gbff.gz\nmalformed\n"
    )
    assert checksums == [{"checksum": expected,
                          "file": "fixture_genomic.gbff.gz"}]
    assert core.save_and_check(Response(payload), str(target), expected)
    assert core.md5sum(str(target)) == expected
    assert not core.has_file_changed(str(root), checksums, "genbank")
```

For the difficult suffix case, add four tiny files with the names in the
fixture above and call `get_name_and_checksum` with `NgdConfig.get_fileending`
for `fasta`, `cds-fasta`, `rna-fasta`, and `rna-fna`. This validates that the
ordinary FASTA file is not accidentally replaced by CDS/RNA data.

## What integrity does not cover

MD5 verifies bytes against the selected NCBI manifest; it does not prove the
summary was fresh, the assembly is biologically appropriate, or that a flat
filename came from the intended accession. Candidate semantics belong to
[download-and-filter](../../download-and-filter/SKILL.md), and taxonomy expansion
belongs to [taxonomy-helper](../../taxonomy-helper/SKILL.md). Keep those
questions separate from file-integrity checks.
