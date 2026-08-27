# ASRT data and configuration

This reference covers ASRT's repository-evidenced data configuration, dictionary, datalist, label-list, and loader behavior as self-contained operating guidance.

## `asrt_config.json` shape

ASRT uses one JSON object with these top-level keys:

- `dict_filename`: path to the pinyin dictionary file. In the repository default this is `dict.txt`.
- `dataset`: object keyed by split. The repository default defines `train`, `dev`, and `test`.

Each split value is a list of dataset descriptors. Every descriptor has:

| key | meaning |
| --- | --- |
| `name` | Human-readable dataset partition name such as `thchs30_train` or `stcmds_train`. |
| `data_list` | Text file containing sample ids and relative WAV paths. |
| `data_path` | Base directory joined with each relative WAV path. The default config points many datasets at `/data/speech_data`, with MagicData under `/data/speech_data/magicdata`. |
| `label_list` | Text file containing sample ids and pinyin syllable labels. |

Repository defaults list six datasets per split: THCHS30, ST-CMDS, Primewords, AIShell-1, Aidatatang200, and MagicData. Only THCHS30 and ST-CMDS list files were present in the inspected repository tree; the others are configured as expected user-provided/downloaded corpora and datalists.

Minimal custom config example:

```json
{
  "dict_filename": "dict.txt",
  "dataset": {
    "train": [
      {
        "name": "my_train",
        "data_list": "datalist/my/train.wav.lst",
        "data_path": "/data/speech_data",
        "label_list": "datalist/my/train.syllable.txt"
      }
    ],
    "dev": [],
    "test": []
  }
}
```

For ASRT's `DataLoader`, the config filename is fixed by `utils.config.DEFAULT_CONFIG_FILENAME` as `asrt_config.json`; stock `DataLoader` does not take a config path argument.

## Dictionary format and pinyin indexes

`dict.txt` is UTF-8 text with one pinyin syllable per line:

```text
<pinyin-with-tone-number>\t<characters-associated-with-that-pinyin>
```

Examples from the repository dictionary include:

```text
a1	阿啊呵腌吖锕
a2	啊呵嗄
ai1	哀挨埃唉哎捱锿诶
```

Important operating facts:

- The inspected dictionary has 1427 non-empty rows. One pinyin token, `heng5`, appears twice; ASRT appends both rows to `pinyin_list` and maps `pinyin_dict['heng5']` to the later row index because assignment overwrites the earlier mapping.
- `utils.config.load_pinyin_dict()` reads each non-empty row, splits on a tab, appends the first token to `pinyin_list`, and maps that pinyin token to its zero-based row index in `pinyin_dict`.
- Labels used by `DataLoader.get_data()` are converted from pinyin strings to integer ids by this dictionary. Any label token missing from `dict.txt` raises a lookup error in stock ASRT.
- The installed verification fact `['ni3', 'hao3', 'ya5']` decodes in ASRT's language-model path, but this sub-skill owns only dictionary membership and numeric label mapping, not Chinese-text decoding details.
- Acoustic model output classes include one extra CTC blank over the dictionary size; a default downstream fact is `SpeechModel251BN` output shape `(200, 1428)` for 1427 dictionary entries plus blank. Model architecture details route to `acoustic-models`.

## Datalist line schemas

ASRT uses two parallel text files per dataset descriptor.

### WAV list (`data_list`)

Each non-empty line has exactly two whitespace-separated fields:

```text
<sample_id> <relative_wav_path>
```

Examples:

```text
A11_0 data_thchs30/train/A11_0.wav
20170001P00001A0001 ST-CMDS-20170001_1-OS/20170001P00001A0001.wav
```

`DataLoader` stores `sample_id` in order, then resolves the audio path as:

```text
os.path.join(data_path, relative_wav_path)
```

The default `/data/speech_data` base means a THCHS30 sample above resolves to `/data/speech_data/data_thchs30/train/A11_0.wav`.

### Syllable label list (`label_list`)

Each non-empty line starts with the same `sample_id`, followed by zero or more pinyin syllables with tone numbers:

```text
<sample_id> <pinyin1> <pinyin2> ... <pinyinN>
```

Examples:

```text
A11_0 lv4 shi4 yang2 chun1 yan1 jing3 da4 kuai4 wen2 zhang1 de5 ...
20170001P00001A0001 er4 mao2 ni3 jin1 tian1 mei2 ke4 ma5 hai2 he2 li3 xia2 liao2 tian1
```

The THCHS30 label files may contain trailing spaces. Stock ASRT skips empty label tokens in `DataLoader.get_data()`.

## `DataLoader` behavior

`data_loader.DataLoader(dataset_type)` accepts `dataset_type` values expected to match keys in the config, usually `train`, `dev`, or `test`.

During initialization it:

1. Loads `asrt_config.json` through `utils.config.load_config_file()`.
2. Loads the pinyin dictionary through `load_pinyin_dict(config['dict_filename'])`.
3. Iterates every dataset descriptor under `config['dataset'][dataset_type]`.
4. Reads the `data_list`; for each non-empty line, splits on a single space, appends the first token to `data_list`, and stores the joined absolute/relative WAV path in `wav_dict[sample_id]`.
5. Reads the `label_list`; for each non-empty line, splits on a single space and stores all tokens after the first in `label_dict[sample_id]`.

Runtime accessors:

- `get_data_count()` returns the number of sample ids from all selected dataset descriptors.
- `get_data(index)` reads the WAV for `data_list[index]`, maps label pinyins to dictionary ids, and returns `(wav_signal, sample_rate, data_label)`.
- `shuffle()` randomly shuffles the ordered `data_list`; the dictionaries remain keyed by sample id.

Practical validation implications:

- Duplicate sample ids are risky: `data_list` can contain duplicates while `wav_dict` and `label_dict` keep only the last value for that id. Duplicate dictionary pinyins also overwrite the pinyin-to-index mapping while leaving duplicate rows in `pinyin_list`.
- A WAV-list id missing from the label list fails later when `get_data()` indexes `label_dict[mark]`.
- A label token absent from `dict.txt` fails during numeric label conversion.
- `DataLoader` does not verify that WAV files exist until `get_data()` reads a sample.
- `DataLoader` does not enforce 16 kHz; feature extraction/model code does.

Use `scripts/validate_asrt_config.py` to catch these cases before invoking stock ASRT.

## `utils.config` global cache behavior

`utils.config` stores module-level caches:

- `_config_dict`
- `_pinyin_dict`
- `_pinyin_list`

Once `load_config_file()` has loaded a config, later calls return the cached dict and ignore changes to the file path or file contents in the same Python process. Once `load_pinyin_dict()` has loaded a dictionary, later calls return the cached list/dict and ignore new dictionary paths or edits.

For agents debugging changing configs or dictionaries:

- Restart the Python process between validations that use stock ASRT utilities.
- Or explicitly clear the module globals in a controlled debugging session before reloading.
- Prefer the bundled validator for static checks; it does not reuse ASRT's global cache.