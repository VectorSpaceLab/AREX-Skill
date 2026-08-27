# API reference

This page records the SketchCode inference APIs relevant to conversion, compiler debugging, and BLEU flag routing. It is a distilled reference; use it instead of opening implementation files to rediscover signatures.

## `Sampler`

`Sampler` orchestrates model loading, image preprocessing, GUI token generation, HTML compilation, and optional BLEU printing.

### Construction

```python
sampler = Sampler(model_json_path=MODEL_JSON, model_weights_path=MODEL_WEIGHTS)
```

Construction behavior:

- Loads the tokenizer and vocabulary through `Dataset.load_vocab()`.
- Opens the model JSON, builds the Keras model with `model_from_json`, then loads weights from the HDF5 weights file.
- Prints `Loaded model from disk` after loading succeeds.

### `convert_single_image`

```python
sampler.convert_single_image(
    output_folder,
    png_path=PNG_PATH,
    print_generated_output=1,
    get_sentence_bleu=0,
    original_gui_filepath=None,
    style="default",
)
```

Behavior:

- Requires the PNG filename to contain `.png`; otherwise raises `ValueError("Image is not a png!")`.
- Derives `sample_id` from the PNG basename before `.png`.
- Calls `generate_gui` and writes `<sample_id>.gui`.
- Calls `generate_html`; writes `<sample_id>.html` only if compilation succeeds.
- If `get_sentence_bleu == 1` and an original GUI path is supplied, prints a sentence BLEU score through `Evaluator`.

### `convert_batch_of_images`

```python
sampler.convert_batch_of_images(
    output_folder,
    pngs_path=PNGS_FOLDER,
    get_corpus_bleu=0,
    original_guis_filepath=None,
    style="default",
)
```

Behavior:

- Sorts all filenames in `pngs_path`.
- Processes filenames containing `.png`.
- Calls `convert_single_image` for each PNG with `print_generated_output=0` and per-image BLEU disabled.
- Catches broad per-image exceptions, prints the exception class/info, and continues.
- Prints the total generated count.
- If `get_corpus_bleu == 1` and an original GUI folder is supplied, prints corpus BLEU through `Evaluator`.

### GUI generation internals

- `MAX_LENGTH = 48` is used for padding decoder sequences.
- Generation starts with `'<START> '` and predicts up to `150` tokens.
- Generation stops when the predicted word is `None` or `<END>`.
- The emitted token list is joined with spaces and written to `<sample_id>.gui`.

## `Compiler`

### Construction and style mapping

```python
compiler = Compiler(style)
```

- `get_stylesheet(style)` supports only `default`, `facebook`, and `airbnb`.
- Each style mapping supplies `opening-tag`, `closing-tag`, `body`, and all known DSL token templates.
- The root node is initialized as `Node("body", None, content_holder)`.

### Compilation

```python
html = compiler.compile(generated_gui)
```

Behavior:

1. Drops the first and last tokens: `generated_gui[1:-1]`.
2. Joins tokens, rewrites braces into parse markers, removes spaces, then splits into parse chunks.
3. Creates `Node` instances for containers and leaves.
4. Renders from the root mapping.
5. Returns HTML on success or the literal `HTML Parsing Error` if rendering returns `None`.

The compiler does not perform friendly style validation and does not provide detailed parse diagnostics. Use `scripts/compile_tiny_dsl.py` for safer preflight debugging.

## `Node`

`Node` represents one DSL key and child list.

Important behavior:

- `Node.render(mapping, rendering_function=None)` renders all children first, then looks up the current node key in the style mapping.
- If any child render returns `None`, the parent returns `None`.
- If the current key is missing from the mapping, render returns `None`.
- If a node has children, its rendered child HTML replaces the mapping's content holder (`opening-tag + closing-tag`, normally `{}`).
- `Node.rendering_function` fills `[]` placeholders for button/title/text keys.

## `SamplerUtils`

`SamplerUtils.get_random_text(length_text=10, space_number=1, with_upper_case=True)` returns pseudo-random filler text for generated HTML placeholders.

Known callers:

- Buttons: default random text.
- Titles: length `5`, no spaces.
- Paragraph text: length `56`, `7` spaces, lowercase.

## `Evaluator` touchpoints during conversion

Conversion can call `Evaluator` only when optional BLEU flags are enabled:

- Single conversion: `Evaluator.get_sentence_bleu(original_gui_filepath, generated_gui_filepath)`.
- Batch conversion: `Evaluator.get_corpus_bleu(original_guis_filepath, output_folder)`.

BLEU normalization, file pairing, and interpretation belong to the `evaluation` sub-skill. For conversion operations, just verify that original `.gui` paths are supplied when the corresponding `--print_bleu_score 1` flag is used.

## Source script handling

The public conversion CLIs are reference-only in this generated skill because they require the live legacy model runtime, user-supplied model artifacts, and project-specific imports. The bundled reusable runtime code here is limited to safe compiler validation in `scripts/compile_tiny_dsl.py`.
