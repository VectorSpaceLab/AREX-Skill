# Translation Workflows

## Purpose

Use this reference for concrete translation tasks after the `argostranslate` package is installed. If model packages are not installed, use the package-management sub-skill first.

## Workflow 1: list installed languages

```python
from argostranslate import translate

languages = translate.get_installed_languages()
for lang in languages:
    print(lang.code, lang.name)
```

Expected signal: the list includes each language that has at least one installed `type == "translate"` package. English is sorted first when available.

If the list is empty, no translation packages are installed in the active package directory.

## Workflow 2: translate with the direct helper

```python
from argostranslate import translate

translated = translate.translate("Hello world", "en", "es")
print(translated)
```

Prerequisites:

- `translate.get_language_from_code("en")` returns a language.
- `translate.get_language_from_code("es")` returns a language.
- `translate.get_translation_from_codes("en", "es")` returns a translation object, either direct or pivoted.

If any prerequisite is false, install the missing language-pair package(s) with `argospm` or `package.install_from_path()`.

## Workflow 3: inspect and choose translation objects

Use this when you need to debug a missing direct pair, pivoting behavior, or object class.

```python
from argostranslate import translate

languages = translate.get_installed_languages()
for lang in languages:
    print("from", lang.code, lang.name)
    for candidate in lang.translations_from:
        print("  to", candidate.to_lang.code, type(candidate).__name__)
```

Argos adds identity translations and can add `CompositeTranslation` paths through intermediate languages. A composite path can translate between languages that do not have a direct package, but quality may be lower because the text is translated through a pivot language.

## Workflow 4: object-level translation

```python
from argostranslate import translate

languages = {lang.code: lang for lang in translate.get_installed_languages()}
from_lang = languages["en"]
to_lang = languages["es"]
translation = from_lang.get_translation(to_lang)
if translation is None:
    raise RuntimeError("No translation path from en to es")
print(translation.translate("Hello world"))
```

Use `.hypotheses(text, num_hypotheses=N)` when you need multiple candidate outputs from a translation object. Some remote providers only return one unique hypothesis and repeat it.

## Workflow 5: translate from CLI

```bash
argos-translate --from-lang en --to-lang es "Hello world"
```

Read stdin when the positional text argument is omitted:

```bash
echo "Text to translate" | argos-translate -f en -t es
```

If both language flags are missing, a positional text argument is returned unchanged through identity translation. Always provide both language flags for actual translation.

## Workflow 6: install a missing pair then translate

```bash
argospm update
argospm search -f en -t es
argospm install translate-en_es
argos-translate -f en -t es "Hello world"
```

For a local archive:

```python
from pathlib import Path
from argostranslate import package, translate

package.install_from_path(Path("translate-en_es.argosmodel"))
print(translate.translate("Hello world", "en", "es"))
```

Validate unknown archives with `sub-skills/package-management/scripts/check_argosmodel.py` before installing.

## Workflow 7: configure runtime before import

Set environment variables before importing translation modules:

```bash
export ARGOS_DEVICE_TYPE=cpu
export ARGOS_CHUNK_TYPE=MINISBD
python - <<'PY'
from argostranslate import translate
print([(lang.code, lang.name) for lang in translate.get_installed_languages()])
PY
```

Common switches:

- `ARGOS_DEVICE_TYPE=cpu` for CPU inference.
- `ARGOS_DEVICE_TYPE=cuda` only when CTranslate2/CUDA is verified in the target environment.
- `ARGOS_COMPUTE_TYPE=int8` for lower memory/faster CPU/GPU inference with possible quality tradeoff.
- `ARGOS_CHUNK_TYPE=MINISBD` to force MiniSBD.
- `ARGOS_CHUNK_TYPE=STANZA` only after installing the `stanza` extra and verifying resources.

## Workflow 8: tag-preserving translation utility

For simple tag-tree content, `argostranslate.tags` can translate text while attempting to keep non-translatable subtrees in place.

```python
from argostranslate import tags, translate

languages = {lang.code: lang for lang in translate.get_installed_languages()}
translation = languages["en"].get_translation(languages["es"])
tag_tree = tags.Tag(["I went to ", tags.Tag(["Paris"]), " last summer."])
translated = tags.translate_tags(translation, tag_tree)
print(translated.text())
```

This is an API utility, not an HTML/XML parser. For complex documents, use a library that parses the document format and passes only text segments to Argos Translate.

## Workflow 9: remote provider adapters

The default model provider is local OpenNMT/CTranslate2 via installed packages. The source also includes LibreTranslate and OpenAI-backed provider paths.

Use these only when the user explicitly wants networked translation:

```python
from argostranslate.apis import LibreTranslateAPI

api = LibreTranslateAPI("https://translate.argosopentech.com/")
print(api.translate("Hello", "en", "es"))
```

Remote providers may need endpoints, network access, and credentials. Do not route default offline translation through them.
