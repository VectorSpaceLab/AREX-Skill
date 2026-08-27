# Repo provenance

- Repository: `Palashio/libra`
- Remote: `https://github.com/Palashio/libra.git`
- Local source commit used for this skill: `4767c9d079d65ebf8afb162fc08f0c261d8e1c60`
- Branch observed: `master`
- Dirty state during construction: clean (`git status --short` produced no output before generated skill files were written)
- Package metadata: `setup.py` declares `name="libra"`, `version="1.2.1"`, `python_requires=">=3.6"`
- Primary import surface: `libra/__init__.py` exports `client` from `libra/queries.py`

## Evidence paths inspected

- `README.md`
- `requirements.txt`
- `setup.py`
- `setup.cfg`
- `tests/tests.py`
- `tests/README.md`
- `docs/README.md`
- `docs/html/started.html`
- `docs/html/modeling.html`
- `docs/html/nlp.html`
- `docs/html/utility.html`
- `tools/examples/Classification/Libra Example-SVM Query.py`
- `tools/materials/common_problems.txt`
- `tools/materials/Example Projects.md`
- `tools/materials/Reference Manual.md`
- `libra/__init__.py`
- `libra/queries.py`
- `libra/datasets.py`
- `libra/query/classification_models.py`
- `libra/query/feedforward_nn.py`
- `libra/query/generative_models.py`
- `libra/query/nlp_queries.py`
- `libra/query/recommender_systems.py`
- `libra/query/supplementaries.py`
- `libra/query/dimensionality_red_queries.py`
- `libra/modeling/prediction_model_creation.py`
- `libra/modeling/tuner.py`
- `libra/preprocessing/data_reader.py`
- `libra/preprocessing/data_preprocessor.py`
- `libra/preprocessing/NLP_preprocessing.py`
- `libra/preprocessing/image_preprocessor.py`
- `libra/preprocessing/image_caption_helpers.py`
- `libra/plotting/generate_plots.py`
- `libra/dashboard/auto_eda.py`
- `libra/dashboard/LibEDA.py`
- `libra/data_generation/dataset_labelmatcher.py`
- `libra/data_generation/grammartree.py`

Generated runtime files intentionally avoid absolute links to the construction checkout. When a future task uses a different checkout or an installed package, compare its commit/version against this provenance before trusting API details.
