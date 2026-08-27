# Data API Reference

The APIs below were checked against the OpenFold source evidence used for this generated skill. Use them for planning and debugging, and prefer local introspection if a future checkout records a different OpenFold version.

## Parser APIs

```python
from openfold.data import parsers, mmcif_parsing

sequences, descriptions = parsers.parse_fasta(fasta_string)
msa = parsers.parse_a3m(a3m_string)
msa = parsers.parse_stockholm(stockholm_string)
hits = parsers.parse_hhr(hhr_string)
result = mmcif_parsing.parse(
    file_id="1abc",
    mmcif_string=mmcif_text,
    catch_all_errors=True,
)
```

Expected signatures and behavior:

- `openfold.data.parsers.parse_fasta(fasta_string: str) -> Tuple[Sequence[str], Sequence[str]]`; returns sequences first, descriptions second.
- `openfold.data.parsers.parse_a3m(a3m_string: str) -> openfold.data.parsers.Msa`; removes lowercase insertion characters from aligned sequences and records deletions.
- `openfold.data.parsers.parse_stockholm(stockholm_string: str) -> openfold.data.parsers.Msa`; treats the first sequence as query and removes query-gap columns.
- `openfold.data.parsers.parse_hhr(hhr_string: str) -> Sequence[openfold.data.parsers.TemplateHit]`; returns template-hit records, not MSA features.
- `openfold.data.parsers.parse_hmmsearch_sto(stockholm_string: str, query_sequence: str) -> Sequence[openfold.data.parsers.TemplateHit]`; used for HMMsearch template hits.
- `openfold.data.mmcif_parsing.parse(*, file_id: str, mmcif_string: str, catch_all_errors: bool = True) -> openfold.data.mmcif_parsing.ParsingResult`; check whether `result.mmcif_object` is `None` before using chain/header fields.

## DataPipeline APIs

```python
from openfold.data.data_pipeline import DataPipeline

pipeline = DataPipeline(template_featurizer=None)
features = pipeline.process_fasta(
    fasta_path="target.fasta",
    alignment_dir="alignments_for_target",
    alignment_index=None,
    seqemb_mode=False,
)
```

Key expectations:

- `DataPipeline.__init__(self, template_featurizer)` accepts an optional template featurizer.
- `DataPipeline.process_fasta(self, fasta_path, alignment_dir, alignment_index=None, seqemb_mode=False)` requires exactly one FASTA record.
- `DataPipeline.process_multiseq_fasta(self, fasta_path, super_alignment_dir, ri_gap=200)` accepts multiple records, strips description whitespace to the first token, expects one subdirectory per token, and stitches sequences with residue-index gaps.
- Without `alignment_index`, `alignment_dir` directly contains alignment/template files.
- With a per-chain `alignment_index`, `alignment_dir` contains the shard named by `alignment_index["db"]`.
- `seqemb_mode=True` creates dummy MSA features and loads `*.pt` sequence-embedding data from the alignment directory.
- Ordinary MSA parsing includes `*.a3m` and `*.sto` except `uniprot_hits.sto` and `hmm_output.sto`.
- Template parsing includes `*.hhr`, plus `hmm_output.sto` in directory-backed mode and `hmmsearch_output.sto` in index-backed mode.

## Multimer Pipeline APIs

```python
from openfold.data.data_pipeline import DataPipeline, DataPipelineMultimer

monomer_pipeline = DataPipeline(template_featurizer=None)
multimer_pipeline = DataPipelineMultimer(monomer_pipeline)
features = multimer_pipeline.process_fasta(
    fasta_path="multimer.fasta",
    alignment_dir="multimer_alignments",
    alignment_index=None,
)
```

Key expectations:

- `DataPipelineMultimer.__init__(self, monomer_data_pipeline)` wraps a monomer `DataPipeline`.
- `DataPipelineMultimer.process_fasta(self, fasta_path, alignment_dir, alignment_index=None)` uses each FASTA description as the chain key.
- Without an index, it expects `alignment_dir/<description>/`.
- With an index, it looks up `alignment_index.get(description)` and uses the shared DB shard directory.
- For heteromers, it loads `uniprot_hits.sto` from the chain directory or chain index entry to build all-sequence MSA pairing features.
- For duplicate sequences in the same multimer, it reuses features from the first matching sequence; still keep alignment and cache IDs explicit so diagnostics are clear.

## FeaturePipeline API

```python
from openfold.data.feature_pipeline import FeaturePipeline

feature_pipeline = FeaturePipeline(config)
processed = feature_pipeline.process_features(
    raw_features,
    mode="train",
    is_multimer=False,
)
```

Use `FeaturePipeline` after raw features have been assembled by data pipelines. If raw data parsing fails, debug FASTA, alignment, index, cache, or cluster layout first rather than changing feature-processing config.

## Alignment Index API Pattern

For a chain key from `alignment_db.index`:

```python
import json
from openfold.data.data_pipeline import DataPipeline

with open("alignment_db.index", "r", encoding="utf-8") as handle:
    index = json.load(handle)

chain_index = index["3lrm_A"]
pipeline = DataPipeline(template_featurizer=None)
features = pipeline.process_fasta(
    fasta_path="3lrm_A.fasta",
    alignment_dir="alignment_dbs",
    alignment_index=chain_index,
)
```

For multimer indexed data, pass the full top-level index to code paths that look up each chain description, or pass the correct per-chain entry when calling monomer `process_fasta` directly.

## Cache API Pattern

Cache generation utilities parse mmCIF and PDB files, then write JSON dictionaries. Important fields during cache generation are:

- `mmcif.header["release_date"]`
- `mmcif.header["resolution"]`
- `mmcif.chain_to_seqres`
- Full chain IDs built as `<file_id>_<chain_id>`
- Optional cluster sizes from a cluster file, keyed case-insensitively by full chain ID

Validate generated JSON with `inspect_mmcif_cache.py` before long training runs.

## Safe Smoke Checks

Use these checks when OpenFold is installed in the active environment:

```bash
python - <<'PY'
from openfold.data import parsers
seqs, descs = parsers.parse_fasta('>x\nACD\n')
assert seqs == ['ACD'] and descs == ['x']
print('parse_fasta ok')
PY
```

```bash
python - <<'PY'
from openfold.data.mmcif_parsing import parse
print(parse)
PY
```

These checks import data modules only. They do not run alignment searches, model inference, or training.

## Environment Caveat

A lightweight inspection environment may successfully import package metadata, configs, and `parse_fasta` while full model or CLI imports fail because the `attn_core_inplace_cuda` extension is not importable. Treat that as an installation/assets or model-runtime issue, not as a data-layout failure. Data validators in this sub-skill avoid heavy OpenFold model imports.
