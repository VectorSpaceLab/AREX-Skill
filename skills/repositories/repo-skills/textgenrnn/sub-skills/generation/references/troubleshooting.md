# Generation troubleshooting

Use this page for generation-specific failures. For broad import, install, and
TensorFlow/Keras dependency issues, also consult the root
[installation and compatibility guide](../../../references/installation-and-compatibility.md).

## Import fails with `tensorflow.compat.v1.keras` missing

**Likely cause:** The environment resolved to a Keras 3 / newer TensorFlow stack
where `tensorflow.compat.v1.keras` is not available.

**Fix:** Use a pre-Keras-3 TensorFlow stack such as TensorFlow/Keras 2.15.x, then
retry the import and a short generation smoke.

## Import fails with `No module named pkg_resources`

**Likely cause:** The installed setuptools variant does not provide
`pkg_resources`, which this package imports.

**Fix:** Install a setuptools release that still provides `pkg_resources` (for
example, pin setuptools below the removed-module range) or otherwise provide the
module in the runtime environment.

## Constructor fails when loading custom weights

**Symptoms:** HDF5 errors, weight shape mismatches, missing layer names, or a
model-building traceback during `textgenrnn(weights_path=...)`.

**Likely causes:**

- The weights were created with a custom architecture but the matching config
  JSON was not supplied.
- The vocab JSON does not match the weights.
- A file path points to the wrong file or an empty/incomplete HDF5 artifact.

**Fix:** Load the complete matching triplet:

```python
textgenrnn(weights_path="model_weights.hdf5",
           vocab_path="model_vocab.json",
           config_path="model_config.json",
           name="model")
```

If the files do not exist yet, route to [training](../../training/SKILL.md) to
create them.

## `load(weights_path)` fails after construction

**Likely cause:** `load()` keeps the current object's config and vocab, then
loads weights into that architecture. The weights do not match the current
instance.

**Fix:** Instantiate with the correct `vocab_path` and `config_path` before
calling `load()`, or pass all paths directly to the constructor.

## Generated texts are empty, very short, or stop immediately

**Likely causes:**

- The model sampled its stop/meta token early.
- `max_gen_length` is too small.
- The prefix or vocab/config is mismatched, causing unknown-token behavior.

**Fix:** Increase `max_gen_length`, try a different `temperature`, and verify
that custom weights/vocab/config files match. Generate multiple samples and
curate; occasional weak samples are expected.

## Prefix does not seem to steer output

**Likely causes:**

- The prefix contains characters or words not present in the model vocabulary.
- A word-level model lowercases/tokenizes the prefix and inserts spaces around
  punctuation.
- The model was not trained on the requested style/content.

**Fix:** Use a prefix that exists in the training vocabulary, try several
samples, and keep the temperature moderate. For style/content changes, route to
[training](../../training/SKILL.md).

## Temperature list is rejected or behaves unexpectedly

**Likely causes:** The caller passed strings instead of floats, an empty list, or
values that are too high for coherent sampling.

**Fix:** Pass a float or list of floats, for example `temperature=[0.2, 1.0]`.
For shell use with the bundled script, pass a comma-list such as
`--temperature 0.2,1.0`.

## Progress bars or printed text pollute logs

**Likely cause:** `generate` prints by default and uses tqdm when `n > 1` and
`progress=True`.

**Fix:** Use:

```python
texts = textgen.generate(n=5, return_as_list=True, progress=False)
```

For helper-script use, add `--quiet` when only the output file is needed.

## Interactive generation hangs

**Likely cause:** `interactive=True` waits for stdin at every generated token.

**Fix:** Only use interactive mode in a real terminal. For automation, remove
`interactive=True` and use `return_as_list=True, progress=False`.

## File output is missing or overwritten

**Likely causes:** The parent directory did not exist, the process lacked write
permission, or `generate_to_file` overwrote an existing file.

**Fix:** Create the parent directory first, choose a writable path, and treat
`generate_to_file` as destructive for existing files. The bundled script creates
parent directories for its `--output-file` path.

## Synthesis output is unstable or style balance is poor

**Likely causes:** `synthesize` shuffles model order for each generated text;
styles are weighted by how many times their model appears in the input list.

**Fix:** Duplicate models in the list to weight a style, lower the temperature,
or adjust `stop_tokens`. For character-level models, default switching occurs at
spaces/newlines; `stop_tokens=[]` switches after every character and can be much
more experimental.

## CUDA warnings appear during generation

**Likely cause:** TensorFlow detected partial or missing GPU libraries. This is
not a generation blocker when CPU works.

**Fix:** Continue on CPU for generation. Only prepare a CUDA stack if the user
specifically needs GPU-accelerated training; route that to
[training](../../training/SKILL.md) and the root compatibility guide.
