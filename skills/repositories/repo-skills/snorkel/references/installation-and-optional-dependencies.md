# Installation and optional dependencies

## Base package

Snorkel is a Python package for programmatic training-data creation, weak supervision, labeling functions, label models, classification utilities, data transforms, and slicing.

Base requirements from package metadata:

- Python `>=3.11`
- `munkres`, `numpy`, `scipy`, `pandas`, `tqdm`, `scikit-learn`, `torch`, `tensorboard`, `protobuf`, and `networkx`

Typical installs:

```bash
pip install snorkel
```

or:

```bash
conda install snorkel -c conda-forge
```

For an editable local checkout, install with:

```bash
python -m pip install -e .
```

Run the root smoke check after installation:

```bash
python scripts/check_snorkel_install.py
```

## Optional Dask support

Dask paths are used by:

- `snorkel.labeling.apply.dask.DaskLFApplier`
- `snorkel.labeling.apply.dask.PandasParallelLFApplier`
- `snorkel.slicing.apply.dask.DaskSFApplier`
- `snorkel.slicing.apply.dask.PandasParallelSFApplier`

Install the optional stack when a task needs Dask or parallel Pandas application:

```bash
python -m pip install "dask[dataframe]" distributed
```

Use `PandasLFApplier` or `PandasSFApplier` when a single-process Pandas path is enough.

## Optional spaCy NLP support

spaCy paths are used by:

- `snorkel.preprocess.nlp.SpacyPreprocessor`
- `snorkel.labeling.lf.nlp.NLPLabelingFunction`
- `snorkel.labeling.lf.nlp.nlp_labeling_function`
- `snorkel.slicing.sf.nlp.NLPSlicingFunction`
- `snorkel.slicing.sf.nlp.nlp_slicing_function`

The Snorkel helpers default to `language="en_core_web_sm"`. Install spaCy and a compatible model before constructing those helpers:

```bash
python -m pip install spacy
python -m spacy download en_core_web_sm
```

If another model is already installed, pass it with the `language` argument instead of downloading the default model.

## Optional local Spark support

Spark paths are used by:

- `snorkel.labeling.apply.spark.SparkLFApplier`
- `snorkel.labeling.lf.nlp_spark.SparkNLPLabelingFunction`
- `snorkel.labeling.lf.nlp_spark.spark_nlp_labeling_function`
- `snorkel.map.spark.make_spark_mapper`
- `snorkel.preprocess.spark.make_spark_preprocessor`
- `snorkel.slicing.apply.spark.SparkSFApplier`

The repository pins local PySpark verification to:

```bash
python -m pip install pyspark==3.4.1
```

A Java runtime is also required. In local containers or CI, Spark hostname resolution can fail; set:

```bash
export SPARK_LOCAL_HOSTNAME=localhost
```

Use the root smoke script for an optional local Spark probe:

```bash
python scripts/check_snorkel_install.py --check-spark
```

This only verifies local Spark startup. It does not validate cluster, EMR, storage, executor memory, or production distributed configuration.

## No Snorkel CLI entry points

The package metadata exposes Python APIs rather than console entry points. Prefer small Python scripts or notebooks that import public Snorkel modules.

## Smoke-check scripts by workflow

- Root install and optional backend imports: `scripts/check_snorkel_install.py`
- Weak supervision and label model: `sub-skills/labeling/scripts/labeling_smoke.py`
- Optional local Spark LF applier: `sub-skills/labeling/scripts/labeling_spark_smoke.py`
- Mapper/preprocessor/augmentation/synthetic helper: `sub-skills/data-transforms/scripts/data_transform_smoke.py`
- Classification/trainer/evaluation helper: `sub-skills/classification/scripts/classification_smoke.py`
- Slicing and slice-aware labels helper: `sub-skills/slicing/scripts/slicing_smoke.py`
