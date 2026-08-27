# Data Preparation Troubleshooting

## Purpose

Use this guide for predictable failures around spaCy/torchtext preprocessing,
legacy pickle inspection, WMT downloads, and the experimental BPE route.

## Missing spaCy language models

**Symptoms**

- `OSError` or `IOError` from `spacy.load("en")` or `spacy.load("de")`.
- The preprocessing command fails before torchtext downloads Multi30k.

**Likely cause**

The default non-BPE flow loads short spaCy language aliases. These aliases match
older spaCy 2-era installs but may not exist in modern spaCy environments.

**Recovery**

1. Prefer the verified legacy stack when reproducing repository behavior:
   spaCy 2.3.x with compatible English and German model packages.
2. Try the documented commands first:

   ```bash
   python -m spacy download en
   python -m spacy download de
   ```

3. If the short aliases are rejected, install spaCy-2-compatible model packages
   and create aliases expected by `spacy.load("en")` and `spacy.load("de")`, or
   patch the preprocessing call locally to load the installed model names.
4. Re-run the pickle inspector after preprocessing to verify that source and
   target fields contain the expected special tokens.

## Torchtext legacy API mismatch

**Symptoms**

- `AttributeError: module 'torchtext.data' has no attribute 'Field'`.
- Import errors around `torchtext.datasets.Multi30k`, `TranslationDataset`,
  `Dataset`, or `BucketIterator`.
- Pickle inspection fails with `ModuleNotFoundError` or class lookup errors for
  torchtext legacy modules.

**Likely cause**

The repository uses the torchtext 0.6-style legacy API. Modern torchtext releases
removed or moved these classes, and old pickles need compatible class paths when
unpickled.

**Recovery**

1. Use a legacy-compatible environment for preprocessing and pickle inspection;
   torchtext 0.6.0 is the verified version for this skill.
2. Do not regenerate pickles with a modern torchtext data pipeline unless you
   also adapt `train.py` and `translate.py` to the new schema.
3. If the inspector cannot load a pickle because torchtext is missing, install a
   compatible torchtext version in the inspection environment and rerun:

   ```bash
   python sub-skills/data-preparation/scripts/inspect_preprocessed_pickle.py --pickle artifact.pkl --trust-pickle
   ```

## Custom `-data_src` / `-data_trg` rejected

**Symptoms**

- `AssertionError: Custom data input is not support now.`
- A command that supplies only one of `-data_src` or `-data_trg` fails.

**Likely cause**

The parser exposes custom data flags, but the default non-BPE implementation
asserts that neither flag is set. The custom text packing branch is not
implemented.

**Recovery**

- For repository-compatible non-BPE preprocessing, use the default Multi30k
  download route with German/English language codes.
- If a task truly requires local custom parallel text, create a separate
  conversion path that produces the non-BPE pickle schema in
  [data-formats.md](data-formats.md#non-bpe-multi30k-pickle), then validate it
  with the bundled inspector. Do not claim the stock command supports this.

## Network dataset downloads

**Symptoms**

- torchtext fails to download Multi30k.
- WMT BPE preprocessing fails during archive download or extraction.
- HTTP errors, DNS errors, timeout errors, or missing extracted files.

**Likely cause**

Both documented preprocessing routes can require external datasets. The non-BPE
path relies on torchtext's Multi30k dataset helper; the BPE path downloads WMT
train/dev/test archives when expected raw files are absent.

**Recovery**

1. Confirm network access and whether the original dataset URLs are still live.
2. Prefer a scratch working directory for BPE downloads. The BPE downloader uses
   archive filenames and extraction directories in ways that can be surprising;
   keeping the run isolated avoids overwriting unrelated files.
3. If the data is already available, stage it so the preprocessing search logic
   can find the exact expected filenames.
4. If downloads are disallowed by the task budget or environment, do not run the
   full preprocessing command. Use the tiny BPE demo for local BPE logic and
   keep the real preprocessing step as a blocked external-data requirement.

## BPE path is WIP / not fully tested

**Symptoms**

- Confusion about why the README says to switch from `main_wo_bpe` to `main`.
- BPE training needs extra `-train_path` and `-val_path` flags.
- BPE translation is unavailable or produces undecoded subword text.

**Likely cause**

The repository marks BPE as work in progress. The default preprocessing entry
point is non-BPE, while the BPE route has a separate command shape, external
WMT downloads, sidecar encoded files, and a different pickle schema.

**Recovery**

- Treat BPE support as an experimental training-data route only.
- Use [scripts/bpe_tiny_demo.py](../scripts/bpe_tiny_demo.py) from the
  data-preparation sub-skill to validate merge and encoding behavior without
  downloading WMT.
- Use the BPE pickle plus encoded train/validation prefixes for training.
- Do not use the non-BPE translation command with a BPE shared-field pickle.

## Pickle schema mismatch

**Symptoms**

- `TypeError` or `KeyError` around `data["vocab"]["src"]` or
  `data["vocab"]["trg"]`.
- `KeyError: 'test'` when translating.
- Training works in non-BPE mode but fails when `-train_path`/`-val_path` are
  mixed with a non-BPE pickle, or vice versa.

**Likely cause**

The non-BPE and BPE pickles are intentionally different. Non-BPE stores source
and target fields plus embedded examples. BPE stores a single shared field and
requires external encoded text files.

**Recovery**

1. Inspect the artifact:

   ```bash
   python sub-skills/data-preparation/scripts/inspect_preprocessed_pickle.py --pickle artifact.pkl --trust-pickle --strict
   ```

2. If it is `non_bpe_multi30k`, train with `-data_pkl` only and translate with
   the same pickle.
3. If it is `bpe_shared_field`, train with `-data_pkl`, `-train_path`,
   `-val_path`, and `-embs_share_weight`; do not use it for stock translation.
4. If classification is `unknown`, regenerate the artifact or adapt the consumer
   code intentionally.

## `max_len`, `min_word_count`, and `share_vocab` gotchas

**`max_len`** filters examples before vocabulary building. Very small values can
remove most examples and create tiny or missing vocabularies. The default is
`100`.

**`min_word_count`** controls vocabulary inclusion for non-BPE fields. Raising it
can increase `<unk>` rates and harm translation quality. The default is `3`.

**`share_vocab`** is important when training with source/target embedding
sharing. If training uses shared embeddings, the non-BPE loader asserts that the
source and target `stoi` tables are identical. Use `-share_vocab` during
preprocessing or disable embedding sharing during training.

For BPE training, the loader requires shared embeddings because the BPE pickle
contains a single shared field.

## Encoded BPE files overwritten despite skip message

**Symptoms**

- The BPE preprocessing log says encoded files were found and it will skip
  encoding, but output files still change.

**Likely cause**

The encoder checks whether both output files exist and prints a skip message,
but the implementation still calls the encoding functions afterward.

**Recovery**

- Keep BPE experiments in a scratch `data_dir`.
- Do not rely on existing encoded files being preserved by the stock BPE path.
- Copy important encoded files elsewhere before rerunning BPE preprocessing.
