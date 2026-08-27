# Installation and Model Setup

## Purpose

Read this when installing scispaCy, choosing a supported Python version, or deciding which model package to load. The package itself is a normal Python distribution; the biomedical model packages are installed separately.

## Known-good baseline

- Repository package: `scispacy`.
- Verified package version in this checkout: `0.6.2`.
- Verified runtime stack: Python 3.11, spaCy 3.7.5, `en_core_web_sm` 3.7.1, `en_core_sci_sm` 0.5.4.
- Runtime dependencies pulled in by the package include `spacy`, `scipy`, `requests`, `conllu`, `numpy<2.0`, `joblib`, `nmslib`, `scikit-learn`, and `pysbd`.

## Recommended installation flow

1. Create a fresh Python environment.
2. Install scispaCy.
3. Install one or more spaCy model packages separately.
4. Import the scispaCy modules that register custom factories before adding pipes.

### Minimal package install

```bash
python -m pip install scispacy
```

### Editable local checkout install

Use this when working inside a local clone of the repository itself:

```bash
python -m pip install -e .
```

### Model packages

Install model packages separately from the library. The repo docs and project files show these families:

| Model | Purpose | Notes |
| --- | --- | --- |
| `en_core_web_sm` | General English baseline used by many tests and component smoke checks | Small CPU-friendly model |
| `en_core_sci_sm` | Biomedical English pipeline | Good default for scispaCy component workflows |
| `en_core_sci_md` | Biomedical pipeline with larger vocabulary and vectors | Heavier than `sm` |
| `en_core_sci_lg` | Larger biomedical pipeline | Heavier than `md` |
| `en_core_sci_scibert` | Biomedical pipeline with `allenai/scibert-base` transformer | GPU is helpful but not required |
| `en_ner_bc5cdr_md` | NER model for BC5CDR | Domain-specialized NER |
| `en_ner_craft_md` | NER model for CRAFT | Domain-specialized NER |
| `en_ner_bionlp13cg_md` | NER model for BIONLP13CG | Domain-specialized NER |
| `en_ner_jnlpba_md` | NER model for JNLPBA | Domain-specialized NER |

Example commands:

```bash
python -m spacy download en_core_web_sm
python -m pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_core_sci_sm-0.5.4.tar.gz
```

## Import order that matters

The custom factories are registered when their modules are imported. Before calling `nlp.add_pipe("abbreviation_detector")` or `nlp.add_pipe("hyponym_detector")`, import the corresponding module once in the process:

```python
import scispacy.abbreviation
import scispacy.hyponym_detector
```

## Smoke check

A minimal runtime check after installation is:

```bash
python -I -c "import scispacy, spacy, scispacy.abbreviation, scispacy.hyponym_detector; print(scispacy.__version__)"
```

For a fuller smoke that also covers the whitespace tokenizer and tiny linker path, run the bundled `scripts/smoke_scispacy.py` script.

## Model choice guidance

- Use `en_core_sci_sm` for most biomedical component workflows.
- Use `en_core_web_sm` for tests or examples that only need a small general English model.
- Use `en_core_sci_scibert` only when you need the transformer-backed pipeline; it is heavier and slower on CPU.
- If a model load warns about spaCy version compatibility, prefer a model release that matches the spaCy minor version in your environment.

## Cache and data expectations

The linker utilities may download and cache KB/index artifacts on first use. The package uses the scispaCy cache under the user's home directory unless a different cache root is configured.

If a model or linker workflow fails after installation, check the root troubleshooting reference before retrying a larger download or rebuild.
