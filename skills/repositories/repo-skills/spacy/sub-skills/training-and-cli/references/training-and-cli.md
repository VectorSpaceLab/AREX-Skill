# training-and-cli command map

This sub-skill covers config-driven training workflows, safe conversion helpers, and CLI-based debugging for spaCy. The default posture is CPU-first, no downloads, and no full training unless the caller explicitly asks for it.

## Recommended order

1. Create or generate a config with `init config`.
2. Complete any partial config with `init fill-config`.
3. Validate the config with `debug config`.
4. Convert or prepare data with `convert`.
5. Validate train/dev data with `debug data`.
6. Train with explicit path overrides only after the config and data pass.
7. Evaluate, package, and validate the resulting pipeline.

## Command map

| Command | Use it for | Key flags and notes |
| --- | --- | --- |
| `init config` | Create a starter training config with recommended settings. | `--lang`, `--pipeline`, `--optimize`, `--gpu`, `--pretraining`, `--force`. Safe because it only writes config. |
| `init fill-config` | Complete a partial config so there are no hidden defaults. | `--code`, `--pretraining`, `--diff`. Use this before training. |
| `debug config` | Validate config structure, registered functions, and resolved variables. | `--code`, `--show-functions`, `--show-variables`, plus config overrides such as `--paths.train`. |
| `debug data` | Load the configured corpora and inspect label, annotation, and corpus issues. | `--code`, `--ignore-warnings`, `--verbose`, `--no-format`, plus path overrides. |
| `convert` | Convert IOB, CoNLL, CoNLLU, or legacy JSON data to `.spacy` DocBin files. | `--converter`, `--file-type`, `--n-sents`, `--seg-sents`, `--base/--model`, `--morphology`, `--merge-subtokens`, `--ner-map`, `--lang`, `--concatenate`. |
| `train` | Train or update a pipeline from a complete config. | `--output`, `--code`, `--verbose`, `--gpu-id`, and overrides like `--paths.train` / `--paths.dev` / `--training.max_steps`. |
| `evaluate` / `benchmark accuracy` | Score a trained pipeline on `.spacy` evaluation data. | `--output`, `--code`, `--gold-preproc`, `--gpu-id`, `--displacy-path`, `--displacy-limit`, `--per-component`, `--spans-key`. `evaluate` is the alias. |
| `package` | Build an installable Python package from a saved pipeline directory. | `--code`, `--meta-path`, `--create-meta`, `--name`, `--version`, `--build`, `--force`, `--require-parent/--no-require-parent`. |
| `validate` | Check installed model packages against the current spaCy version. | No training data required. Run after upgrading spaCy or installed models. |
| `find-function` | Locate the module and line number for a registered function. | `--registry` is optional when the registry can be inferred. Useful for missing custom code. |
| `find-threshold` | Sweep thresholds for components that use thresholded scores. | `--n_trials`, `--code`, `--gpu-id`, `--gold-preproc`, `--verbose`. Only useful for thresholded components like multilabel textcat or span categorization. |
| `assemble` | Build a pipeline from config without running training. | `--code`, `--verbose`, and overrides. Use for config-only serialization and initialization checks. |
| `apply` | Apply a pipeline to `.spacy`, `.jsonl`, or plain-text inputs and save a `.spacy` DocBin. | `--text-key`, `--force`, `--gpu-id`, `--batch-size`, `--n-process`. |
| `pretrain` | Pretrain tok2vec weights from raw text with the `[pretraining]` block. | `--code`, `--resume-path`, `--epoch-resume`, `--gpu-id`, `--skip-last`, plus config overrides. |

## Safe workflow examples

```bash
python -m spacy init config config.cfg --lang en --pipeline tagger,parser,ner --optimize efficiency
python -m spacy init fill-config base.cfg config.cfg
python -m spacy debug config config.cfg --show-functions --show-variables
python -m spacy convert ./train.conll ./corpus --converter conll --file-type spacy
python -m spacy debug data config.cfg --paths.train ./train.spacy --paths.dev ./dev.spacy
python -m spacy train config.cfg --paths.train ./train.spacy --paths.dev ./dev.spacy --output ./output --training.max_steps 200
python -m spacy benchmark accuracy ./output/model-best ./dev.spacy --gold-preproc
python -m spacy package ./output/model-best ./dist --name my_model --version 0.1.0
python -m spacy validate
```

## Override rules

- Config overrides use dotted keys like `--paths.train`, `--paths.dev`, `--training.max_steps`, and `--system.seed`.
- Overrides can also be provided through `SPACY_CONFIG_OVERRIDES` with the same syntax.
- Only existing config keys can be overwritten.
- `--code` and `--code-path` load custom registry functions before config resolution.

## Practical guardrails

- Use `debug config` before `debug data` when the failure source is unclear.
- Use `debug data` before `train` when the corpora may have invalid offsets, missing labels, or empty splits.
- Keep training smoke runs tiny and explicit. Prefer a blank pipeline or a very small `--training.max_steps` value when you only need proof of wiring.
- Do not treat optional GPU, transformer, or accelerator settings as verified unless the local environment proves them.
