# CLaMP Workflows

CLaMP is the Muzic branch for cross-modal symbolic music information retrieval. It aligns natural-language text and score-oriented symbolic music in ABC/MusicXML form, enabling semantic search, zero-shot classification, and similar-score retrieval.

## Model names and limits

The CLI accepts two model names:

| Model | Music sequence limit | Text sequence limit | Notes |
|---|---:|---:|---|
| `sander-wood/clamp-small-512` | 512 music patches | 128 text tokens | Smaller default model. |
| `sander-wood/clamp-small-1024` | 1024 music patches | 128 text tokens | Longer symbolic music context. |

Both variants use a 6-layer music encoder and 6-layer text encoder with hidden size 768. Music is patchilized as ABC-like bars with patch length 64 and 98 patch features.

## First-run download and cache caveats

The original CLaMP script loads models at startup. On first run it may:

- create a local directory named after the Hugging Face model path;
- download `config.json` and `pytorch_model.bin` for the selected CLaMP model;
- download tokenizer/model assets for `distilroberta-base` through Transformers;
- write key-feature cache files under `inference/cache/`.

Plan for network access, disk space, and retry behavior before running model inference. Use `scripts/validate_clamp_inputs.py` when the task only needs layout checks.

## Inference layout

Run the original CLaMP CLI from the CLaMP working directory so its hard-coded `inference/` paths resolve.

```text
inference/
  music_query.mxl          # required when query_modal=music
  text_query.txt           # required when query_modal=text
  music_keys/              # required when key_modal=music
    *.mxl                  # one or more MusicXML/MXL scores, recursively accepted by the script
  text_keys.txt            # required when key_modal=text; one key per non-empty line
  cache/                   # optional; source script creates and updates feature caches
  xml2abc.py               # used by the source script for MusicXML-to-ABC conversion
```

The CLI expects compressed MusicXML files with `.mxl` extension for music queries and music keys. Text keys are stored as lines in a single UTF-8 text file.

## CLI contract

```bash
python clamp.py \
  -clamp_model_name sander-wood/clamp-small-512 \
  -query_modal text \
  -key_modal music \
  -top_n 5
```

| Flag | Allowed values | Meaning |
|---|---|---|
| `-clamp_model_name` | `sander-wood/clamp-small-512`, `sander-wood/clamp-small-1024` | CLaMP checkpoint/model variant. |
| `-query_modal` | `music`, `text` | Which query file to load from `inference/`. |
| `-key_modal` | `music`, `text` | Which key collection to load from `inference/`. |
| `-top_n` | integer; `0` means all in source script | Number of highest-scoring keys printed. |

## Modal recipes

### Text-to-music semantic search

Use this for queries like “a joyful waltz in a bright major key” against a folder of scores.

```text
inference/text_query.txt       # one free-form natural-language query
inference/music_keys/*.mxl     # candidate symbolic scores
```

```bash
python clamp.py -clamp_model_name sander-wood/clamp-small-512 -query_modal text -key_modal music -top_n 5
```

Expected output: top score filenames with probability-like softmax percentage and cosine similarity, followed by the query text.

### Music-to-text zero-shot classification

Use this to pick the best natural-language label, composer prompt, genre prompt, or descriptor for one symbolic score.

```text
inference/music_query.mxl      # target score
inference/text_keys.txt        # one candidate label/prompt per line
```

```bash
python clamp.py -clamp_model_name sander-wood/clamp-small-1024 -query_modal music -key_modal text -top_n 3
```

Example text keys:

```text
This piece of music is composed by Chopin.
This piece of music is composed by Mozart.
This piece of music is a jazz standard.
```

Expected output: top text lines with softmax percentage and cosine similarity.

### Music-to-music similar-score retrieval

Use this to retrieve similar symbolic scores from a `.mxl` folder.

```text
inference/music_query.mxl
inference/music_keys/*.mxl
```

```bash
python clamp.py -clamp_model_name sander-wood/clamp-small-1024 -query_modal music -key_modal music -top_n 10
```

Expected output: top `.mxl` paths from the key folder.

### Text-to-text sanity check

This exercises text encoder and key parsing without MusicXML conversion. It still loads CLaMP and text model assets, so use the bundled validator for no-network checks.

```text
inference/text_query.txt
inference/text_keys.txt
```

```bash
python clamp.py -clamp_model_name sander-wood/clamp-small-512 -query_modal text -key_modal text -top_n 5
```

## Input validation helper

Use the bundled helper before invoking the source CLI:

```bash
python scripts/validate_clamp_inputs.py \
  --inference-dir inference \
  --model-name sander-wood/clamp-small-512 \
  --query-modal text \
  --key-modal music \
  --top-n 5
```

What it checks:

- model name is one of the two CLaMP variants;
- query/key modal values are valid;
- required query file exists and is non-empty;
- text keys contain non-empty lines when `key_modal=text`;
- music keys contain `.mxl` files when `key_modal=music`;
- `.mxl` files are readable and, by default, valid zip containers;
- `top_n` does not exceed key count unless `top_n=0`.

The helper does not run `xml2abc.py`, load Torch/Transformers, download models, or write feature caches.

## Result interpretation

The source CLI computes two related values:

- normalized feature cosine similarity;
- softmax over scaled query-key logits, printed as `Prob: ...%`.

Softmax probability is relative to the supplied candidate set, not an absolute confidence score. If key sets change, the displayed probabilities can change even when cosine similarities remain comparable.

## Cache behavior

For key features, the source script reads and writes:

```text
inference/cache/music_key_cache_512.pth
inference/cache/music_key_cache_1024.pth
inference/cache/text_key_cache_512.pth
inference/cache/text_key_cache_1024.pth
```

When keys are removed, the script drops missing cached entries. When new keys are added, it encodes only uncached keys and merges them with cached features. Delete the relevant cache file if you suspect stale feature tensors, changed model versions, or corrupted cache state.

## Known source portability issue

The inspected MusicXML loader shells out through a Windows-style command string before running `inference/xml2abc.py`. On non-Windows systems this may fail before any model work begins. If a future run on Linux/macOS fails during MusicXML conversion, verify whether the command wrapper needs a local portability patch or pre-convert MusicXML to acceptable ABC text through an equivalent converter.
