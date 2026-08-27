# Text-normalization troubleshooting

Start with the smallest failing surface: bundled punctuation helper, optional full ITN/TN imports, grammar/cache generation, then language-specific behavior.

## `ModuleNotFoundError: pynini`

Meaning: the full finite-state ITN/TN stack is not installed. The bundled punctuation helper still works because it is pure Python.

Recover:

1. If the user only needs punctuation spacing, do not install Pynini. Use `scripts/post_process_punct.py align` instead.
2. If the user needs semantic ITN/TN, install a compatible Pynini build for the active Python environment. A known package target used by this code line is `pynini==2.1.5`; conda-forge is often the most reliable route on macOS, while Linux environments may use either conda-forge or a wheel when available.
3. Re-run:

   ```bash
   python scripts/post_process_punct.py check-full-stack --strict
   ```

4. If Pynini imports but grammar creation fails, move to the cache section below.

## Missing tokenizer or NLP helper

Symptoms:

- Full TN with `punct_post_process=True` prints that NeMo NLP or Moses de-tokenization is unavailable.
- Punctuation post-processing in the full TN path is skipped even though the core normalizer runs.

Recover:

1. Treat the NLP helper as optional unless the user specifically needs full TN detokenization behavior.
2. For pure punctuation alignment, run the bundled helper after the full TN output:

   ```bash
   python scripts/post_process_punct.py align --input "$ORIGINAL" --normalized "$TN_OUTPUT" --unicode-punct
   ```

3. If the user requires the full TN detokenizer path, install the package that provides `nemo.collections.common.tokenizers.moses_tokenizers` in the same environment as FunASR and verify with `check-full-stack`.

## Missing `regex`, `joblib`, or `tqdm`

Meaning: the optional full TN module cannot import all helper packages. The standalone punctuation script does not need them.

Recover:

```bash
python scripts/post_process_punct.py check-full-stack --strict
```

Install only the missing package(s) in the active environment. Do not install broad training, serving, or vLLM extras just to use text normalization.

## Unexpected spacing around quotes or punctuation

Symptoms:

- `test 'example` should become `test' example`.
- `你好 ， 世界 ！` should become `你好，世界！`.
- Nested quotes or repeated spaces still look odd after a detokenizer.

Recover:

1. Use `align` mode when you have both the original text and a normalized candidate.
2. Add `--unicode-punct` for non-ASCII punctuation.
3. Use `simple` mode only when there is no original string to align against; it normalizes common quote characters and tightens common punctuation spacing but cannot infer the intended original layout.
4. If the punctuation counts differ between input and candidate, inspect manually. The helper aligns matching punctuation marks but does not invent missing punctuation.
5. For nested quotes, process one line at a time and compare before/after around each quote; repeated spaces are collapsed after alignment.

## Cache or grammar install path problems

Symptoms:

- Permission errors while creating `.far` grammar files.
- Stale grammar behavior after switching language or package versions.
- Cache creation works in one shell but fails in another.

Recover:

1. Choose an explicit, user-writable cache directory for the full ITN/TN run, such as a project-local temporary cache or a user cache directory.
2. Keep separate cache directories for TN vs ITN and for different languages when debugging.
3. Use the full stack's overwrite option only when stale grammar files are likely; do not delete unrelated cache trees.
4. Confirm the same Python environment is used for FunASR, Pynini, and the grammar modules.
5. If grammar compilation still fails after Pynini imports, capture the first missing module or file named in the traceback; that is usually more useful than retrying the install script.

## Full stack is unavailable but the user asked for ITN/TN

Be explicit:

- Say that punctuation cleanup is available now via the bundled helper.
- Say that semantic ITN/TN is blocked by the missing optional package or build step reported by `check-full-stack`.
- Do not claim that ASR transcription, serving, training, or vLLM setup will fix a Pynini/grammar failure; route those workflows to their sibling sub-skills only when the user's task actually changes.
