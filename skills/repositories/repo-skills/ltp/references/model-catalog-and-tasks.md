# Model Catalog, Tasks, and Output Shapes

## When to read

Read this before choosing an LTP model, task list, output accessor, or label interpretation. For concrete Python calls, continue to `sub-skills/python-pipeline/`.

## Model families

| Model id/path | Implementation | Tasks | Main trade-off |
| --- | --- | --- | --- |
| `LTP/tiny` | Neural PyTorch model | `cws`, `pos`, `ner`, `srl`, `dep`, `sdp`, `sdpg` when supported by the model config | Smallest neural model; fastest neural option but lower accuracy. |
| `LTP/small` | Neural PyTorch model | Full neural task family | Default high-level model; balanced speed/quality. |
| `LTP/base`, `LTP/base1`, `LTP/base2` | Neural PyTorch model | Full neural task family | Higher reported quality with more compute/model size. |
| `LTP/legacy` | Rust-backed averaged/perceptron-style legacy model | `cws`, `pos`, `ner` | Very fast CWS/POS/NER; no SRL/DEP/SDP/SDPG. |
| Local path | Neural or legacy based on `config.json` | Determined by the model config | Best for offline or private models; the path must contain `config.json` and the expected weight/model files. |

Model ids may include a revision suffix with `@`, such as `LTP/small@main`. Use `local_files_only=True` when a task must not touch the network.

## Pipeline task names

| Task | Meaning | Input dependency | Typical output |
| --- | --- | --- | --- |
| `cws` | Chinese word segmentation | Raw sentence text | list of words |
| `pos` | POS tagging | Words from `cws`, or pre-tokenized words when `cws` is omitted | list of POS tags |
| `ner` | Named entity recognition | Words; legacy NER also needs POS | list of entity tuples after post-processing |
| `srl` | Semantic role labeling | Words and neural model support | list of predicates with argument spans |
| `dep` | Dependency parsing | Words and neural model support | dict with `head` and `label`; heads are 1-based with root at 0 |
| `sdp` | Semantic dependency parsing tree | Words and neural model support | dict with `head` and `label`; root convention is like dependency parsing |
| `sdpg` | Semantic dependency parsing graph | Words and neural model support | list of `(source, target, label)` graph arcs |

If `tasks` is omitted, neural models attempt all seven tasks and legacy models attempt `cws`, `pos`, `ner`.

## `LTPOutput` access patterns

The high-level pipeline returns `LTPOutput` by default.

```python
output = ltp.pipeline(["他叫汤姆去拿外衣。"], tasks=["cws", "pos", "ner"])
print(output.cws)
print(output["pos"])
print(output[0])
print(output.to_tuple())
```

Set `return_dict=False` or call `.to_tuple()` when a caller wants tuple unpacking. Avoid unpacking `LTPOutput` directly.

## Pretokenized input rule

When `cws` is **not** in the task list, pass pre-tokenized words:

```python
result = ltp.pipeline([["他", "叫", "汤姆", "去", "拿", "外衣", "。"]], tasks=["pos", "ner", "dep"])
```

When `cws` **is** in the task list, pass raw strings:

```python
result = ltp.pipeline(["他叫汤姆去拿外衣。"], tasks=["cws", "pos", "ner"])
```

A common bug is asking for `pos`/`ner` on raw strings while omitting `cws`; tokenization will be interpreted as pre-tokenized words and results will be wrong or fail.

## Label/tag quick reference

- POS uses the 863 tag set; common tags include `n` noun, `v` verb, `a` adjective, `r` pronoun, `m` number, `wp` punctuation, `nh` person name, `ni` organization, `ns` location, `nt` temporal noun, and `ws` foreign words.
- NER recognizes `Nh` person, `Ni` organization, and `Ns` location in documented LTP examples.
- SRL argument tags include `ARG0`, `ARG1`, `ARG2`, `ARG3`, `ARG4`, `ADV`, `TMP`, `LOC`, `MNR`, `PRP`, and related semantic-role labels.
- Dependency labels include `SBV`, `VOB`, `IOB`, `FOB`, `DBL`, `ATT`, `ADV`, `CMP`, `COO`, `POB`, `LAD`, `RAD`, `IS`, and `HED`.
- Semantic dependency labels include semantic roles such as `AGT`, `EXP`, `PAT`, `CONT`, `DATV`, `LINK`, `TOOL`, `TIME`, `LOC`, `MEAS`, and event/marker relations.

For production tasks, keep the raw tags alongside interpreted labels so downstream validation can catch model-version differences.

## Backend expectations

- CPU is enough for import checks, sentence splitting, output-shape conversion, small validators, and many legacy workflows.
- CUDA is optional acceleration for neural models. Verify `torch.cuda.is_available()` and a tiny allocation before moving an LTP model with `ltp.to("cuda")`.
- Model loading can require network access unless a local model path or populated cache is supplied.
- Training uses a broader dependency set than inference; do not assume `pip install ltp` proves train/eval entry points are ready.
