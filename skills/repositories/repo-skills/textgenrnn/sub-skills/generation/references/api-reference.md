# Generation API reference

This reference describes the verified generation-facing API for
`textgenrnn==2.0.0`. Use it with the root
[installation and compatibility guide](../../../references/installation-and-compatibility.md)
when imports or TensorFlow/Keras versions fail.

## Imports

```python
from textgenrnn import textgenrnn
from textgenrnn.utils import synthesize, synthesize_to_file
```

## Verified signatures

| API | Signature | Notes |
| --- | --- | --- |
| Constructor | `textgenrnn(weights_path=None, vocab_path=None, config_path=None, name="textgenrnn", allow_growth=None)` | Loads bundled default weights/vocab when paths are omitted. Supply matching weights, vocab, and config for scratch-trained/custom architectures. |
| Generate | `generate(n=1, return_as_list=False, prefix=None, temperature=[1.0, 0.5, 0.2, 0.2], max_gen_length=300, interactive=False, top_n=3, progress=True)` | Prints texts by default. Set `return_as_list=True` for programmatic use. |
| Sample temperatures | `generate_samples(n=3, temperatures=[0.2, 0.5, 1.0], **kwargs)` | Loops over `temperatures`, prints a heading, then calls `generate(..., progress=False, **kwargs)`. |
| Generate file | `generate_to_file(destination_path, **kwargs)` | Calls `generate(return_as_list=True, **kwargs)` and writes one generated text per line as UTF-8. Overwrites the destination. |
| Save weights | `save(weights_path="textgenrnn_weights_saved.hdf5")` | Saves model weights only. It does not save config or vocab JSON. |
| Load weights | `load(weights_path)` | Rebuilds the current architecture with the current config/vocab and loads the given weights. |
| Synthesize | `synthesize(textgens, n=1, return_as_list=False, prefix='', temperature=[0.5, 0.2, 0.2], max_gen_length=300, progress=True, stop_tokens=[' ', '\n'])` | Generates from a list of instantiated models. Shuffles model order for each text. |
| Synthesize file | `synthesize_to_file(textgens, destination_path, **kwargs)` | Calls `synthesize(return_as_list=True, **kwargs)` and writes one text per line. |

## Constructor behavior

- `weights_path=None` loads the package's bundled pretrained HDF5 weights.
- `vocab_path=None` loads the package's bundled vocabulary JSON.
- `config_path=None` uses the class default config:
  - `rnn_layers=2`
  - `rnn_size=128`
  - `rnn_bidirectional=False`
  - `max_length=40`
  - `max_words=10000`
  - `dim_embeddings=100`
  - `word_level=False`
  - `single_text=False`
- `name` is copied into `config['name']` and is used by training/save callbacks
  as the filename stem for generated artifacts.
- `allow_growth` enables TensorFlow v1-style GPU memory growth when not `None`.
  Generation does not require a GPU.

For custom models created with `new_model=True`, load all three matching files:

```python
textgen = textgenrnn(weights_path="model_weights.hdf5",
                     vocab_path="model_vocab.json",
                     config_path="model_config.json",
                     name="model")
```

Using custom weights with the wrong vocab or config usually causes weight shape
errors or poor/OOV output.

## `generate` parameters

| Parameter | Meaning and caveats |
| --- | --- |
| `n` | Number of texts to generate. Use small values for smoke tests. |
| `return_as_list` | `False` prints each text and returns `None`; `True` returns `list[str]` and suppresses printing. |
| `prefix` | Optional starting text. Character-level models split it into characters; word-level models tokenize/lowercase and add punctuation spacing. OOV tokens map to index 0. |
| `temperature` | Float or list of floats. Lists cycle token-by-token. `0.0` or `None` triggers greedy argmax sampling in the low-level sampler. |
| `max_gen_length` | Upper bound on generated token sequence length. It is separate from config `max_length`, the model's lookback window. |
| `interactive` | If `True`, prompts on stdin for each next token. Do not use in unattended jobs. |
| `top_n` | Number of next-token choices shown in interactive mode. |
| `progress` | Enables a tqdm progress bar when `n > 1`. Set `False` for scripts and clean logs. |

## Interactive controls

When `interactive=True`, the generator prints the top `top_n` options and asks
for input. Controls are:

- an integer choice from the displayed options;
- `s` to stop generation;
- `x` to delete the previous generated token;
- `o` to type a custom token.

Interactive mode is terminal-oriented and blocks until input is provided.

## `generate_samples`

Use `generate_samples()` for quick qualitative temperature comparison. It prints
separator headings and generated texts; it is not designed for programmatic
capture. If the caller needs the strings, loop over temperatures and call
`generate(return_as_list=True)` directly.

## `generate_to_file`

`generate_to_file(destination_path, **kwargs)` is the shortest built-in path for
file output:

```python
textgen.generate_to_file("generated.txt", n=5, prefix="AI",
                         temperature=[0.2, 1.0], max_gen_length=100,
                         progress=False)
```

The destination is overwritten. Each generated string receives a trailing
newline.

## Save and load weights

Use `save()` when the current in-memory model state should be reused later:

```python
textgen.save("my_weights.hdf5")
```

Use `load()` only when the current `textgenrnn` instance already has the correct
architecture and vocabulary:

```python
textgen = textgenrnn(vocab_path="my_vocab.json", config_path="my_config.json")
textgen.load("my_weights.hdf5")
```

For one-shot custom loading, prefer passing paths in the constructor.

## Synthesis parameters

`synthesize` accepts most generation controls used by `generate` plus
`stop_tokens`:

- `textgens`: list of instantiated `textgenrnn` objects.
- `prefix`: starting text shared by the synthesis loop.
- `temperature`: float/list of floats cycled by the low-level generator.
- `stop_tokens`: for character-level models, switch to the next model after one
  of these tokens is generated. Default switches at spaces or newlines.
- `stop_tokens=[]`: switch after every generated character; output can become
  more experimental.

Because model order is shuffled for each generated text, synthesis is not
naturally deterministic unless the caller controls Python's random state and the
NumPy/TensorFlow sampling state.
