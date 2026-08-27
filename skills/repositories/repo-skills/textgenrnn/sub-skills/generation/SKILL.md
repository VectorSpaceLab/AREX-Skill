---
name: generation
description: "Guides agents through textgenrnn generate, generate_samples,
  generate_to_file, save/load, prefix, temperature, interactive, and synthesize
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# textgenrnn generation sub-skill

Use this sub-skill when the user wants to run, inspect, or troubleshoot
text generation with `textgenrnn` models. It covers default bundled weights,
custom weight/vocabulary/config triplets, sampling controls, interactive
next-token selection, writing generated text to files, weight save/load, and
multi-model synthesis.

Do not reopen the source repository or notebooks for these tasks. Use this
router plus the bundled references and helper script.

## Trigger tasks

Activate this sub-skill for requests that mention any of the following with
`textgenrnn`:

- instantiate `textgenrnn()` or load pretrained/default weights;
- call `generate`, `generate_samples`, or `generate_to_file`;
- choose `prefix`, `temperature`, temperature cycles, or `max_gen_length`;
- use `interactive=True`, `top_n`, or terminal next-character controls;
- save or reload HDF5 weights with `save` or `load`;
- load custom `weights_path`, `vocab_path`, and `config_path` files;
- combine several trained models with `synthesize` or `synthesize_to_file`;
- smoke-test generation or create a small generated text file.

## Boundaries and routing

Stay in this sub-skill for generation-time behavior only.

- For model training, fine-tuning, context labels, word-level training,
  `train_on_texts`, `train_new_model`, `train_from_file`, or
  `train_from_largetext_file`, route to [training](../training/SKILL.md).
- For `encode_text_vectors`, PCA/t-SNE vectors, and `similarity`, route to
  [embedding-analysis](../embedding-analysis/SKILL.md).
- For import failures, TensorFlow/Keras compatibility, or `pkg_resources`
  problems, consult the root
  [installation and compatibility guide](../../references/installation-and-compatibility.md).
- For architecture and config background, consult the root
  [model overview](../../references/model-overview.md).

## Runtime assumptions

- Public import: `from textgenrnn import textgenrnn`.
- Public distribution: `textgenrnn==2.0.0`.
- Use a pre-Keras-3 TensorFlow stack, such as TensorFlow/Keras 2.15.x, and
  ensure `pkg_resources` is available through a compatible setuptools install.
- CPU generation is valid. CUDA/GPU is optional acceleration for training, not a
  requirement for generation covered here.
- The repository provides no CLI; use Python APIs or the bundled helper script.
- Notebook examples have already been distilled into this skill. Do not ask a
  future agent to open notebooks for normal generation work.

## Primary references

- [API reference](references/api-reference.md) lists verified signatures,
  defaults, return values, and parameter caveats.
- [Workflows](references/workflows.md) gives copy-ready recipes for common
  generation tasks.
- [Troubleshooting](references/troubleshooting.md) maps symptoms to fixes.
- [smoke_generate.py](scripts/smoke_generate.py) is a safe argparse helper for
  short generation checks and output-file validation.

## Standard generation workflow

1. Confirm whether the user wants the bundled default model or a custom model.
2. If using a custom model trained from scratch, require the matching triplet:
   weights HDF5, vocabulary JSON, and config JSON.
3. Instantiate the model with `textgenrnn(...)`.
4. For programmatic use, call `generate(..., return_as_list=True)` so generated
   strings are returned instead of only printed.
5. For a file artifact, use either `generate_to_file(destination_path, ...)` or
   `scripts/smoke_generate.py --output-file ...`.
6. Keep `max_gen_length` small for smoke tests and increase it only when the
   user asks for longer outputs.
7. If generation fails before sampling, check import/runtime compatibility and
   matching model files before changing sampling parameters.

Minimal API example:

```python
from textgenrnn import textgenrnn

textgen = textgenrnn()
texts = textgen.generate(n=3, return_as_list=True, max_gen_length=80,
                         progress=False)
```

Custom model example:

```python
from textgenrnn import textgenrnn

textgen = textgenrnn(weights_path="my_model_weights.hdf5",
                     vocab_path="my_model_vocab.json",
                     config_path="my_model_config.json",
                     name="my_model")
texts = textgen.generate(n=2, prefix="Once", temperature=[0.2, 1.0],
                         max_gen_length=120, return_as_list=True,
                         progress=False)
```

## Sampling controls

- `temperature` may be one float or a list of floats. A list cycles across
  generated tokens, which can mix conservative and creative sampling.
- Lower temperatures are more repetitive and stable; higher temperatures are
  more varied and can become incoherent.
- `prefix` seeds the generated text. Characters or words not in the model
  vocabulary may be encoded as unknowns, so a prefix cannot guarantee quality.
- `max_gen_length` limits generated token length, not training context length;
  model context length comes from the config `max_length`.
- Set `progress=False` for automation to avoid progress bars.

## Interactive generation

Use `generate(interactive=True, top_n=N)` only in a real terminal with stdin.
The model prints the top `N` next character/word choices and accepts:

- a number selecting an offered option;
- `s` to stop;
- `x` to backspace;
- `o` to type a custom token.

Do not use interactive mode in unattended scripts, CI jobs, notebooks without
stdin, or background agent runs.

## File and weight behavior

- `generate_to_file(destination_path, **kwargs)` overwrites the destination and
  writes one generated text per line.
- `save(weights_path="textgenrnn_weights_saved.hdf5")` saves weights only.
- `load(weights_path)` reloads weights into the current architecture and current
  vocabulary/config. For custom architectures, instantiate with the correct
  `config_path` and `vocab_path` before loading weights.
- Training workflows may create weights, vocab, and config files; route training
  questions to [training](../training/SKILL.md).

## Synthesis behavior

Import synthesis helpers from `textgenrnn.utils`:

```python
from textgenrnn.utils import synthesize, synthesize_to_file
```

Pass a list of instantiated `textgenrnn` objects. Synthesis shuffles model order
for each generated text and switches models at stop tokens by default. Use
`stop_tokens=[]` to switch after every character for character-level models.

## Use the bundled helper script

From the generated skill directory or any other working directory with a compatible installed `textgenrnn` environment:

```bash
python sub-skills/generation/scripts/smoke_generate.py \
  --n 2 --prefix "Once" --temperature 0.2,1.0 --max-gen-length 80 \
  --output-file generated.txt
```

Use `--weights-path`, `--vocab-path`, and `--config-path` together for a custom
scratch-trained model. Add `--quiet` when only the output file matters.
