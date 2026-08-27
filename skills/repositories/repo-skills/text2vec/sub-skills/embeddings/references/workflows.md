# Embedding workflows

Use these workflows from any working directory as long as `text2vec` and the needed optional dependencies are installed. Paths shown for bundled scripts are relative to this sub-skill directory.

## 1. Local HF-compatible model to normalized CPU CSV, no network

Use this when a user has already downloaded or trained a Transformers-compatible model directory and needs deterministic batch embeddings.

1. Prepare an input file with one non-empty sentence per line. Duplicate lines are preserved by the bundled helper.
2. Run the helper with a local model directory and CPU device:

```bash
python scripts/encode_texts.py \
  --input-file input.txt \
  --output-file embeddings.csv \
  --model-type sentencemodel \
  --model-name /path/to/local-hf-model \
  --encoder-type MEAN \
  --device cpu \
  --batch-size 32 \
  --max-seq-length 256 \
  --chunk-size 1000 \
  --normalize-embeddings
```

Output behavior:

- `.csv` outputs columns `sentence` and `embedding`; `embedding` is a JSON array string inside one CSV cell.
- `.jsonl` or `.ndjson` writes one object per line: `{"sentence": ..., "embedding": [...]}`.
- The helper validates that the number of rows written equals the number of non-empty input lines it read.
- No network is needed when `--model-name` points to a complete local HF-compatible directory.

If the user needs vectors for search after this step, route to the similarity-search sub-skill.

## 2. Use the public text2vec CLI safely

The package console command supports the following shape:

```bash
text2vec \
  --input_file input.txt \
  --output_file out.csv \
  --model_type sentencemodel \
  --model_name shibing624/text2vec-base-chinese \
  --encoder_type MEAN \
  --batch_size 128 \
  --max_seq_length 256 \
  --chunk_size 1000 \
  --device cpu \
  --show_progress_bar True \
  --normalize_embeddings False \
  --multi_gpu False
```

Cautions:

- The package CLI de-duplicates input by collecting lines into a set, so output row count and order may differ from the input file.
- The package CLI parses boolean options with Python's `bool()` conversion. Values such as the string `False` can be surprising. Use the bundled helper when exact row preservation or predictable booleans matter.

## 3. SentenceModel multi-process lifecycle

Use this for large embedding jobs, especially when multiple CUDA devices are available. Do not use it for Word2Vec.

```python
from text2vec import SentenceModel

sentences = ["text %d" % i for i in range(10000)]
model = SentenceModel(
    model_name_or_path="/path/to/local-hf-model",
    encoder_type="MEAN",
    max_seq_length=256,
    device="cpu",  # construction device; workers receive their own target devices
)

pool = model.start_multi_process_pool(["cuda:0", "cuda:1"])  # or omit for auto CUDA/CPU fallback
try:
    embeddings = model.encode_multi_process(
        sentences,
        pool,
        batch_size=64,
        normalize_embeddings=True,
        chunk_size=1000,
    )
finally:
    model.stop_multi_process_pool(pool)
```

Notes:

- With no explicit device list, text2vec uses all visible CUDA devices; if CUDA is unavailable, it starts four CPU workers.
- `chunk_size` controls how many sentences are sent to each worker job. Lower it when memory is tight.
- Keep `stop_multi_process_pool(pool)` in `finally` so processes and queues are cleaned up even if encoding fails.

The bundled helper exposes this path with `--multi-gpu` for SentenceModel:

```bash
python scripts/encode_texts.py \
  --input-file input.txt \
  --output-file embeddings.jsonl \
  --model-type sentencemodel \
  --model-name /path/to/local-hf-model \
  --multi-gpu \
  --batch-size 64 \
  --chunk-size 1000 \
  --normalize-embeddings
```

## 4. Word2Vec from a local file with no network

Generate a deterministic tiny word2vec-format fixture:

```bash
python scripts/make_tiny_word2vec_fixture.py --output-file tiny_word2vec.txt
```

Then encode with the bundled helper:

```bash
python scripts/encode_texts.py \
  --input-file input.txt \
  --output-file w2v_embeddings.jsonl \
  --model-type word2vec \
  --model-name tiny_word2vec.txt \
  --chunk-size 1000
```

For a local binary word2vec file, either name it with a `.bin` suffix or pass `--word2vec-binary` to the helper. In direct API code, use:

```python
from text2vec.word2vec import Word2Vec

model = Word2Vec("/path/to/local_vectors.bin", w2v_kwargs={"binary": True})
vectors = model.encode(["银行卡", "花呗更改绑定银行卡"])
```

For the built-in Tencent lightweight vectors, use `Word2Vec("w2v-light-tencent-chinese")` or `--model-name w2v-light-tencent-chinese`; expect a model cache/download unless the file is already present.

## 5. Word2Vec stopwords

Use custom stopwords when literal tokens should not contribute to the average vector:

```python
from text2vec.word2vec import Word2Vec, load_stopwords

stopwords = load_stopwords("stopwords.txt")
model = Word2Vec("/path/to/local_vectors.txt", stopwords=list(stopwords))
vec = model.encode("我去银行开卡")
```

If `stopwords` is omitted, text2vec loads its packaged default stopwords.

## 6. Why `--multi_gpu` with Word2Vec fails

Word2Vec is a CPU-style KeyedVectors averaging path and the package CLI explicitly rejects `--multi_gpu` for `--model_type word2vec`.

Route like this:

| User intent | Correct route |
|---|---|
| Use word vectors from Tencent or a local word2vec file | Drop `--multi_gpu`; run Word2Vec on CPU/local file. |
| Parallelize large transformer embedding batches | Use `--model_type sentencemodel --multi_gpu` or the direct `start_multi_process_pool` lifecycle. |
| Need nearest-neighbor search after Word2Vec embeddings | Generate vectors here, then route to similarity-search for retrieval logic. |

## 7. Direct Transformers or sentence-transformers fallback

Use a fallback only when the user explicitly needs external-library control.

- Transformers fallback: load `AutoTokenizer` and `AutoModel`, tokenize with padding/truncation, and apply the same mean-pooling formula used by SentenceModel for `MEAN`.
- sentence-transformers fallback: load a `SentenceTransformer` model when the model is already managed by that library. Do not mix this with text2vec-specific `EncoderType` values unless you reimplement pooling yourself.
- When possible, prefer `SentenceModel(model_name_or_path=local_dir, encoder_type="MEAN")` so device handling and return shapes match text2vec.
