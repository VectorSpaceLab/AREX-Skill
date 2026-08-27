# Data preparation troubleshooting

## Install and import

- **`ModuleNotFoundError: pointllm`**: run commands from an installed PointLLM
environment or install the package in editable form in the intended environment.
The validator itself needs only Python and NumPy; use it to separate a data
schema issue from a package import issue.
- **Transformer import or tokenizer errors while constructing a tokenized
dataset**: the inspected environment used Python 3.10, torch 2.0.1+cu117,
CUDA on an A100 40GB (capability 8.0), transformers 4.28.0.dev0 at the project
pinned commit, and tokenizers 0.12.1. Keep the package's compatible dependency
set together; do not fix a data error by mixing arbitrary transformer and
 tokenizer versions.
- **YAML/config import failure**: ModelNet uses the repository's YAML loader
and EasyDict-style attribute access. Verify the YAML is readable and has the
keys in `ModelNet40.yaml`; a path typo is more likely than a malformed point
file.

## Dependencies and backends

- **ModelNet cannot open the `.dat` file**: `DATA_PATH` is resolved from the YAML
as written, commonly relative to the process working directory. Check that the
split-specific `modelnet40_<split>_<npoints>pts_fps.dat` exists under that path,
and that `split` is exactly `train` or `test`.
- **CUDA errors during data loading**: dataset validation and NumPy checks do
not require CUDA. Confirm data on CPU first; pass tensors to a GPU only in the
inference/training sibling route. The inspected A100 environment is evidence
for available CUDA, not a requirement of this validator.
- **Open3D or flash-attn installation failure**: neither is needed to validate
NPY/JSON contracts. Avoid adding optional backend packages for this route.

## Data and configuration

- **`expected (8192, 6), got ...`**: inspect `shape`, not just file size. The
loader uses the count embedded in the filename and `pointnum`; either rename
only when the data really has that count or pass a deliberately matching custom
count. For released model inputs, keep 8192.
- **RGB range error**: PointLLM expects normalized RGB `[0, 1]`. Convert a
known 0--255 source once, record that conversion outside the validator, and
rerun it. Do not clip values silently because clipping can hide a bad exporter.
- **non-finite values or zero-radius geometry**: repair the source export or
reject the sample. The source normalization divides by the maximum centered
radius without an epsilon; a constant/empty cloud can yield NaN or Inf.
- **missing annotation reference**: ensure the exact `<object_id>_<pointnum>.npy`
file exists in `data_path`. Annotation filtering does not check file existence.
The validator reports missing files before dataset construction.
- **empty dataset**: inspect `conversation_types`, the two known color-corrupt
ID filters, and `data_debug_num`. Missing `conversation_type` means
`simple_description`, not a custom type.
- **unexpected train/val membership**: `data_debug_num > 0` wins over splitting;
otherwise the dataset uses a contiguous 90/10-style boundary from
`int(split_ratio * len(records))`, not a randomized split. Validate the ratio
and the record order before comparing counts.
- **ModelNet label mismatch**: use the 40 names in the package's modified shape
name file in their existing order. Names with spaces are intentional.

## API and CLI misuse

- **`ObjectPointCloudDataset` constructor fails on `data_args`**: passing
`data_args` is optional for direct point-only use, but factory/training use
expects the attributes documented in `api-reference.md`. Provide a small
namespace with explicit values in a fixture rather than relying on missing
training defaults.
- **`tokenizer=None` returns no text fields**: this is intentional and is the
safe point-only mode. A tokenized call additionally requires a compatible
conversation template, tokenizer, and `point_backbone_config` for replacing
`<point>`.
- **`use_color` confusion**: Objaverse `False` returns XYZ only; `True` retains
RGB. ModelNet `True` appends zero-valued compatibility features, not source
colors. Check tensor width before passing it downstream.
- **collator returns a list instead of a batch tensor**: at least one point
cloud shape differs. Normalize/sample all examples to the same count before
collation if the point encoder requires a rectangular batch.
- **`farthest_point_sample` gives duplicates or random results**: it starts from
a random point and only guarantees the requested loop count, not unique indices
when `npoint > N`. Sample only with `npoint <= N` unless repeated rows are
explicitly intended.

## Workflow failures and boundaries

- **A validator tries to download data**: stop. The bundled validator is
strictly local and read-only; acquire datasets through an approved data source,
then rerun it on the local directory.
- **large archive extraction or full dataset scan is too slow**: first create
a tiny fixture and use `--max-files`/`--max-records`. The released Objaverse
clouds require roughly 77 GB according to the README; never use that scale to
diagnose a shape or annotation typo.
- **dataset works but model rejects features**: compare the model's configured
color expectation with `use_color` and the post-normalization width. Route model
configuration and launch questions to training or inference; this route only
establishes the input contract.
- **evaluation ground truth is mistaken for training data**: keep validation
IDs/GT files under the annotation directory but route generation and scoring to
evaluation. This sub-skill does not call OpenAI/GPT or modify result files.
- **complex instruction provenance is being treated as executable input**: the
bundled GPT-4 system prompt documents how one family of annotations was
produced. It is not a loader schema replacement and must not trigger external
API calls.
