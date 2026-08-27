# Config reference

spaCy training uses one config as the source of truth. The same file drives config generation, initialization, training, evaluation, packaging, and later runtime loading.

## Lifecycle by section

| Section | Used for | Notes |
| --- | --- | --- |
| `[paths]` | Shared file and resource locations. | Use for train/dev `.spacy` files, vectors, `init_tok2vec`, and raw pretraining text. Override on the CLI with dotted keys like `--paths.train`. |
| `[system]` | Seed and hardware settings. | Typical keys are `seed` and `gpu_allocator`. |
| `[nlp]` | The runtime `Language` object, tokenizer, pipeline order, and callbacks. | At runtime, spaCy uses the `[nlp]` and `[components]` blocks. |
| `[components]` | Pipeline component definitions. | Each block usually needs either `factory` or `source`. Custom code must be imported before config resolution. |
| `[corpora]` | Data readers that yield `Example` objects. | Default readers are `spacy.Corpus.v1` for `train` and `dev`, and `spacy.JsonlCorpus.v1` for `pretrain`. |
| `[training]` | Training and evaluation loop settings. | Holds optimizer, batcher, logger, score weights, max steps, max epochs, patience, and corpus references. |
| `[initialize]` | Resources used only during `nlp.initialize()`. | Use for vectors, `init_tok2vec`, `lookups`, tokenizer arguments, component initialization arguments, and init callbacks. |
| `[pretraining]` | Optional tok2vec pretraining settings. | Only used by `spacy pretrain`. |

## Runtime vs training scope

- Runtime uses `[nlp]` and `[components]`.
- Training uses `[training]`.
- Initialization uses `[initialize]` right before training.
- Pretraining uses `[pretraining]` only when pretraining is requested.

That split is why `init fill-config` matters: training configs should be complete and should not depend on hidden defaults.

## Common override patterns

```bash
python -m spacy train config.cfg --paths.train ./train.spacy --paths.dev ./dev.spacy --training.max_steps 500
python -m spacy debug config config.cfg --paths.train ./train.spacy --paths.dev ./dev.spacy
```

Only existing keys can be overwritten. If you need the same value in several places, set it once in the config and reference it with interpolation.

## Minimal config map

```ini
[paths]
train = null
dev = null
vectors = null
init_tok2vec = null
raw_text = null

[system]
seed = 0
gpu_allocator = null

[nlp]
lang = "en"
pipeline = ["tagger", "parser", "ner"]

[components]
; component blocks go here

[corpora]
; reader blocks go here

[training]
; optimizer, batcher, logger, scores, and limits

[initialize]
; vectors, lookups, tokenizer/component init data

[pretraining]
; optional tok2vec pretraining settings
```

## Custom code and registry lookups

- `--code` or `--code-path` imports a Python file before the config is resolved.
- Use it when the config references custom architectures, schedules, readers, or callbacks.
- `debug config --show-functions` is the quickest way to see which registry entries the config uses.
- `find-function` is the fastest way to locate a registered name in the installed code.

## Pretraining notes

- `init config --pretraining` or `init fill-config --pretraining` adds the pretraining block.
- The pretraining config expects a tok2vec component in the pipeline or a corresponding custom name in the config.
- `spacy pretrain` uses raw text via `JsonlCorpus` and writes weights that can later be referenced by `init_tok2vec`.
