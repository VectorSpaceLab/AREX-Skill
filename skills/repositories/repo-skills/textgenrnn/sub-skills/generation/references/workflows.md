# Generation workflows

These recipes are self-contained and use only the public `textgenrnn` API.
For import or dependency failures, use the root
[installation and compatibility guide](../../../references/installation-and-compatibility.md).
For model configuration context, use the root
[model overview](../../../references/model-overview.md).

## 1. Generate from the bundled default model

```python
from textgenrnn import textgenrnn

textgen = textgenrnn()
texts = textgen.generate(n=3,
                         return_as_list=True,
                         max_gen_length=80,
                         progress=False)
for i, text in enumerate(texts, 1):
    print(f"[{i}] {text}")
```

Use this first when checking that the installation and bundled weights work.
The default model is character-level and can run on CPU.

## 2. Generate with a prefix and one temperature

```python
from textgenrnn import textgenrnn

textgen = textgenrnn()
texts = textgen.generate(n=5,
                         prefix="Project",
                         temperature=0.5,
                         max_gen_length=100,
                         return_as_list=True,
                         progress=False)
```

Lower temperatures usually produce safer, more repetitive samples. Higher
values increase variation and can reduce coherence. Avoid treating a prefix as a
hard quality guarantee: unseen characters/words may map to unknown tokens.

## 3. Cycle temperatures token-by-token

```python
from textgenrnn import textgenrnn

textgen = textgenrnn()
texts = textgen.generate(n=5,
                         prefix="AI",
                         temperature=[0.2, 1.0],
                         max_gen_length=120,
                         return_as_list=True,
                         progress=False)
```

A temperature list cycles through generated tokens. A conservative/creative
cycle can reveal different continuations without using a high temperature for
every token. Repeating values changes the cycle rhythm:

```python
textgen.generate(n=5, temperature=[0.2, 0.2, 1.0, 1.0], progress=False)
```

## 4. Compare temperatures with `generate_samples`

```python
from textgenrnn import textgenrnn

textgen = textgenrnn()
textgen.generate_samples(n=3,
                         temperatures=[0.2, 0.5, 1.0],
                         max_gen_length=80)
```

`generate_samples` prints headings and samples. Use it for qualitative review,
not for structured return values.

## 5. Write generated texts to a file

```python
from textgenrnn import textgenrnn

textgen = textgenrnn()
textgen.generate_to_file("generated_texts.txt",
                         n=10,
                         prefix="Today",
                         temperature=[0.2, 0.8],
                         max_gen_length=100,
                         progress=False)
```

The file is overwritten and receives one generated text per line. Ensure the
parent directory exists if writing outside the current directory.

## 6. Load a custom scratch-trained model triplet

Scratch/new-model training creates weights, vocab, and config files. Load the
matching triplet together:

```python
from textgenrnn import textgenrnn

textgen = textgenrnn(weights_path="custom_weights.hdf5",
                     vocab_path="custom_vocab.json",
                     config_path="custom_config.json",
                     name="custom")
texts = textgen.generate(n=2,
                         prefix="Once",
                         temperature=[0.2, 1.0],
                         max_gen_length=80,
                         return_as_list=True,
                         progress=False)
```

If only weights are available, they must match the current/default architecture
and vocabulary. If the files came from `new_model=True`, do not omit the vocab
and config JSONs.

## 7. Save and reload weights

```python
from textgenrnn import textgenrnn

textgen = textgenrnn()
textgen.save("saved_weights.hdf5")

textgen2 = textgenrnn(weights_path="saved_weights.hdf5")
texts = textgen2.generate(n=3, return_as_list=True, progress=False)
```

`save()` writes weights only. For custom architectures, preserve the original
vocab/config JSON files separately and pass them when creating the next object.

## 8. Use interactive generation in a terminal

```python
from textgenrnn import textgenrnn

textgen = textgenrnn()
textgen.generate(interactive=True, top_n=5, max_gen_length=120)
```

Interactive mode presents next-token choices and waits for input. Controls:
select a number, `s` to stop, `x` to backspace, or `o` to write a custom token.
Do not run this in unattended agent workflows.

## 9. Synthesize from multiple models

```python
from textgenrnn import textgenrnn
from textgenrnn.utils import synthesize, synthesize_to_file

model_a = textgenrnn(weights_path="style_a_weights.hdf5",
                     vocab_path="style_a_vocab.json",
                     config_path="style_a_config.json",
                     name="style_a")
model_b = textgenrnn(weights_path="style_b_weights.hdf5",
                     vocab_path="style_b_vocab.json",
                     config_path="style_b_config.json",
                     name="style_b")
models = [model_a, model_b]

texts = synthesize(models,
                   n=5,
                   prefix="The",
                   temperature=[0.5, 0.2, 0.2],
                   max_gen_length=120,
                   return_as_list=True,
                   progress=False)

synthesize_to_file(models * 3, "synthesized.txt", n=10, progress=False)
```

For character-level models, synthesis switches models after a space or newline
by default. Use `stop_tokens=[]` to switch after every character:

```python
synthesize(models, n=3, stop_tokens=[], progress=False)
```

Duplicating models in the input list weights how often a style is selected.

## 10. Use the bundled smoke script

The helper script is useful when a future agent needs a quick compatibility and
file-output check without writing new code:

```bash
python /path/to/skills/disco/textgenrnn/sub-skills/generation/scripts/smoke_generate.py \
  --n 2 \
  --prefix "Once" \
  --temperature 0.2,1.0 \
  --max-gen-length 80 \
  --output-file generated.txt
```

Custom model smoke:

```bash
python /path/to/skills/disco/textgenrnn/sub-skills/generation/scripts/smoke_generate.py \
  --weights-path custom_weights.hdf5 \
  --vocab-path custom_vocab.json \
  --config-path custom_config.json \
  --name custom \
  --n 1 \
  --prefix "AI" \
  --temperature 0.2,1.0 \
  --max-gen-length 60 \
  --output-file custom_generated.txt
```

If the script reports an import or model-load error, check the compatibility
reference first, then verify that all custom paths point to existing matching
files.
