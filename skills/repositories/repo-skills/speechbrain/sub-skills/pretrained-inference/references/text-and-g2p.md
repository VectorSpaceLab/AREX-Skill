# Text and grapheme-to-phoneme inference

SpeechBrain includes text-oriented pretrained interfaces, most notably `GraphemeToPhoneme`. The original repository also contains a convenience G2P command script; this skill distills the safe API pattern instead of depending on that source script.

## G2P interface

```python
from speechbrain.inference.text import GraphemeToPhoneme

g2p = GraphemeToPhoneme.from_hparams(
    source="path-or-huggingface-model",
    savedir="pretrained_models/g2p",
    run_opts={"device": "cpu"},
)
print(g2p.g2p("English is tough"))
print(g2p(["first sentence", "second sentence"]))
```

Verified call signature: `GraphemeToPhoneme.g2p(self, text)`. The input can be one string or a list of strings; single-string inputs return one phoneme sequence and batched inputs return a list.

## Batch file pattern

For a text file with one sample per line:

```python
from pathlib import Path
from speechbrain.inference.text import GraphemeToPhoneme

g2p = GraphemeToPhoneme.from_hparams(source="path-or-model", savedir="pretrained_models/g2p")
lines = Path("input.txt").read_text(encoding="utf-8").splitlines()
phoneme_lines = [" ".join(seq) for seq in g2p(lines)]
Path("phonemes.txt").write_text("\n".join(phoneme_lines) + "\n", encoding="utf-8")
```

For very large files, process chunks to avoid building one huge batch.

## Response generation classes

`ResponseGenerator`, `GPTResponseGenerator`, and `Llama2ResponseGenerator` exist in `speechbrain.inference.text`, but they are model-specific and depend on the hparams/custom model object. Before using them, inspect the model's `hyperparams.yaml` and custom class trust boundary.

## Failure modes

- If the model load complains about missing tokenizer/phoneme resources, verify the model folder contains every file referenced by the hparams `pretrainer` and dependency pretrainer.
- If input text is too long, chunk the file or sentence list; available sequence length depends on the model.
- If a Hugging Face model requires custom code, use only trusted sources and consider a local copy plus `FetchConfig(allow_network=False)` for reproducibility.
- If generated phonemes include placeholders such as `<spc>` or `<eos>`, confirm whether they are expected by the downstream TTS/acoustic model before stripping them.
