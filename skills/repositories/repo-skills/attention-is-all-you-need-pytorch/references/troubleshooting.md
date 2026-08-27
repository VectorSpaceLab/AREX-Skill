# Cross-Cutting Troubleshooting

## Import fails because the checkout is not on `PYTHONPATH`

The repository has no packaging metadata in this snapshot. Its scripts import
`transformer` as a top-level package. Run scripts from the checkout root, install
a user-specific editable wrapper if a fork provides one, or set `PYTHONPATH` to
the checkout root for ad hoc scripts. Bundled helper scripts accept `--repo-root`
and add that path explicitly.

## Modern torchtext is incompatible

The source imports `Field`, `Dataset`, `BucketIterator`, and
`TranslationDataset` from legacy torchtext locations. If imports fail, select a
legacy torchtext release compatible with the user's PyTorch/Python version or
adapt the repository to modern torchtext APIs before running workflows.

## Pickle files are unsafe or schema-mismatched

Preprocessing outputs and checkpoints are Python pickles. Load only trusted
files. Use the data-preparation pickle inspector for preprocessing artifacts and
the translation checkpoint inspector for `.chkpt` files before long runs.

## CUDA is selected unexpectedly

Both `train.py` and `translate.py` set `opt.cuda = not opt.no_cuda`. On CPU-only
hosts, include `-no_cuda`. For direct API use, explicitly move the model and all
tensors to the same device.

## spaCy language models are missing

The default preprocessing path calls `spacy.load` with the language code passed
on the CLI. Install compatible spaCy 2.x model packages or adapt the tokenizer
loading in the user's own checkout.

## README and source disagree

Prefer inspected source for this commit when commands disagree. Known example:
the README training command includes `-log`, but `train.py` does not parse it in
this snapshot.

## BPE end-to-end path is incomplete

BPE code learning/encoding exists and BPE training can read encoded file
prefixes, but the README says BPE is not fully tested and translation BPE
decoding is TODO. Treat BPE guidance as experimental unless a user's fork has
completed and verified the path.
