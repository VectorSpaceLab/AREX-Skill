# Dependencies and runtime assets

## Practical dependency set
The system-pipeline import surface is broader than the single-op CV surface because these modules are imported when `paddlecv` loads:
- `paddlenlp`
- `paddlespeech`
- `aistudio-sdk`
- `setuptools` with `pkg_resources`

## Asset locations
- Configs and model downloads resolve through `paddlecv://` URLs.
- Runtime caches live under `~/.cache/paddlecv/models`, `~/.cache/paddlecv/configs`, `~/.cache/paddlecv/dicts`, and `~/.cache/paddlecv/fonts`.

## Special assets
- OCR and structure workflows may need font files and label dictionaries.
- TTS and NLP workflows may pull transitive assets through the speech/NLP stack.
- ShiTu-style workflows may need a compatible `faiss` wheel for your Python version.

## Version sensitivity
If imports fail, check the dependency versions before assuming the pipeline YAML is broken. The most common failures are `aistudio-sdk` compatibility, `pkg_resources` availability, and `urllib3` or `NumPy` wheel conflicts.
