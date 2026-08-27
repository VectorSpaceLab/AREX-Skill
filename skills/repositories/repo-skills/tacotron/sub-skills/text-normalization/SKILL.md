---
name: text-normalization
description: "Guides Tacotron text cleaning, number expansion, symbol IDs,
  ARPAbet pronunciation syntax, and CMUDict integration for training and
  synthesis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Text normalization

Use this route when the task asks how Tacotron converts text into model input,
why pronunciation differs, how numbers or abbreviations are expanded, or how to
select cleaners for English and non-English text.

## Workflow

1. Choose the cleaner pipeline before changing data: `english_cleaners` expands
   numbers/abbreviations and transliterates; `transliteration_cleaners` only
   transliterates/lowercases/collapses whitespace; `basic_cleaners` preserves
   non-ASCII characters but requires a matching symbol vocabulary.
2. Convert with `text.text_to_sequence(text, cleaner_names)`. It appends the
   `~` EOS id and accepts ARPAbet tokens in braces, for example
   `Turn left on {HH AW1 S S T AH0 N} Street.`.
3. Keep the cleaner names and symbol set consistent between preprocessing,
   training, evaluation, and serving. Use
   `scripts/text_pipeline_check.py` for a safe local check.
4. If `use_cmudict=True`, provide the expected CMUDict file beside the
   preprocessed metadata and understand that training randomly substitutes
   pronunciations; see the references for ambiguity behavior.
## Command roots and boundary

Use the generated helper from the skill root, and use the source checkout as
cwd for the real cleaner. These paths exist in the target checkout; replace
the assignments when using a different copy.

```bash
SKILL_ROOT=/path/to/tacotron-skill
CHECKOUT_ROOT=/path/to/tacotron-checkout
cd "$SKILL_ROOT" && python sub-skills/text-normalization/scripts/text_pipeline_check.py
cd "$CHECKOUT_ROOT" && python -c "from text import text_to_sequence; print(text_to_sequence('A test.', ['english_cleaners']))"
```

The first command checks routing syntax only; it does not import the checkout,
prove the repository cleaners, download CMUDict, or synthesize audio. The
checkout command requires the legacy `Unidecode`/`inflect` dependencies.

Read [`references/api-reference.md`](references/api-reference.md) for exact
functions and symbol contracts, [`references/workflows.md`](references/workflows.md)
for language/pronunciation recipes, and [`references/troubleshooting.md`](references/troubleshooting.md)
for invalid cleaners, dropped symbols, and CMUDict failures. The bundled
[`scripts/text_pipeline_check.py`](scripts/text_pipeline_check.py) is a safe
smoke helper; it does not train or synthesize audio.
