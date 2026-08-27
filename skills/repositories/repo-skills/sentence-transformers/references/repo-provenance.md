# Repo Provenance

schema: `disco.repo-provenance.v1`

## Source Snapshot

- repository_name: `sentence-transformers`
- package_name: `sentence-transformers`
- package_version: `5.7.0.dev0`
- source_commit: `28e79467c49b5bedff9b1492950504af04d0b74b`
- source_branch: `main`
- exact_tag: none
- dirty_state_at_generation: dirty after generated skill and review artifacts were created; source evidence files were clean before generation
- remote_url: public `https://github.com/huggingface/sentence-transformers.git`

## Evidence Paths

- `pyproject.toml`
- `README.md`
- `index.rst`
- `docs/installation.md`
- `docs/quickstart.rst`
- `docs/sentence_transformer/`
- `docs/cross_encoder/`
- `docs/sparse_encoder/`
- `docs/package_reference/`
- `sentence_transformers/`
- `examples/sentence_transformer/`
- `examples/cross_encoder/`
- `examples/sparse_encoder/`
- `tests/`
- `skills/train-sentence-transformers/`

## Installed-Package Facts Used

- Public imports verified during creation: `sentence_transformers`, `sentence_transformers.cross_encoder`, `sentence_transformers.sparse_encoder`, `sentence_transformers.util`, `sentence_transformers.backend`, and trainer modules.
- Public APIs inspected: `SentenceTransformer.__init__`, `SentenceTransformer.encode`, `CrossEncoder.__init__`, `CrossEncoder.predict`, `CrossEncoder.rank`, `SparseEncoder.__init__`, `SparseEncoder.encode`, `util.semantic_search`, `util.cos_sim`, `util.mine_hard_negatives`, and backend export helpers.
- Inspection used a minimal CPU package environment and intentionally skipped broad optional extras unless the generated skill documents them as user-selected prerequisites.

## Refresh Guidance

Refresh this skill when any of these change materially:

- Package version, public constructor or method signatures, optional extras, backend support, trainer/loss/evaluator names, or utility function arguments.
- Documentation routes for dense embeddings, CrossEncoder, SparseEncoder, training/evaluation, retrieval utilities, ONNX, or OpenVINO.
- Existing repo-local training skill templates or safety contracts.
- Native tests/examples that alter expected API behavior, evaluator metrics, sparse active-dimension guidance, or backend export file naming.
