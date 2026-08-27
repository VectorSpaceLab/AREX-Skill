---
name: tagging-and-annotations
description: "Routes Flair annotation, tokenization, splitting, prediction-label
  inspection, serialization, regex tagging, and HTML visualization tasks for
  CPU-first package workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Tagging and Annotations

Use this sub-skill when a task is about creating or inspecting Flair `Sentence` objects, token/span/relation labels, pretrained prediction outputs, tokenization, sentence splitting, regex tagging, serialization, or simple HTML visualization in a pip-installed `flair` workflow.

## Route here for

- Building `Sentence`, `Token`, `Span`, `Relation`, `Label`, or `DataPair` objects and attaching labels to the correct layer.
- Running pretrained inference with `Classifier.load(...)`, `SequenceTagger.load(...)`, or `TextClassifier.load(...)`, then reading predictions from `get_labels(...)`, `get_spans(...)`, or `get_relations(...)`.
- Choosing `SegtokTokenizer`, `SpaceTokenizer`, `NoTokenizer`, `SpacyTokenizer`, `SciSpacyTokenizer`, `JapaneseTokenizer`, `StaccatoTokenizer`, or sentence splitters.
- Using `RegexpTagger` for no-download rule-based span labels.
- Round-tripping annotations with `Sentence.to_dict()` / `Sentence.from_dict()` or rendering NER-style HTML with `render_ner_html(...)`.

Use the training-and-datasets sub-skill instead for corpus readers, label dictionaries for training, `ModelTrainer`, fine-tuning, TARS, or multi-GPU launch. Use the embeddings-and-optimization sub-skill for embedding selection, vector shapes, ONNX/provider runtimes, TorchScript, or cache-heavy embedding optimization. Use the biomedical-nlp sub-skill for HunFlair/HunFlair2 entity linking, SciSpaCy-heavy biomedical workflows, abbreviations, or pyab3p-specific behavior.

## Start safely

1. Treat CPU as the verified baseline. If device placement matters, set `FLAIR_DEVICE=cpu` before importing `flair`.
2. Do not load pretrained model names unless downloads are allowed or the model is already cached. `Classifier.load("ner")`, `SequenceTagger.load("ner")`, and `TextClassifier.load("sentiment")` may download public resources.
3. If downloads are allowed, set a deliberate cache root before importing `flair` (for example a project-local cache) so future agents know where models went.
4. Keep CUDA, ONNX/provider runtimes, SciSpaCy, Japanese tokenizer backends, pyab3p, and model downloads marked optional/unverified unless the active environment proves them.
5. For no-download validation of the annotation stack, run the bundled smoke script from this sub-skill directory:

```bash
python scripts/annotation_smoke.py --json
```

The script uses only local in-memory sentences, manual labels, rule-based tagging, tokenizers, splitters, serialization, and HTML rendering.

## Core workflow

1. **Create sentences with an explicit tokenization choice.** Use `Sentence(text)` for the default SegTok route, `Sentence(text, use_tokenizer=False)` for whitespace tokenization, `Sentence(text, use_tokenizer=Tokenizer())` for a custom tokenizer, or `Sentence(["pre", "tokenized"])` when token boundaries are already decided.
2. **Attach or predict labels into named layers.** The first argument to `add_label` / `set_label` is the layer name such as `"ner"`, `"pos"`, `"sentiment"`, or `"relation"`; the second argument is the class value such as `"PER"` or `"POSITIVE"`.
3. **Extract labels by layer.** Use `sentence.get_labels("ner")` for `Label` objects, `sentence.get_spans("ner")` for span data points, and `sentence.get_relations("relation")` for relation data points. Calling `get_labels()` with no argument returns all layers and is a common source of mixed output.
4. **Preserve offsets deliberately.** Token and span offsets are relative to `sentence.text`; `sentence.start_position` records the sentence offset in a larger document.
5. **Serialize only what can be reconstructed.** `Sentence.from_dict(sentence.to_dict())` preserves sentence/span/relation labels and tokenizer configuration when the tokenizer class and optional dependencies are available.

## Read these references

- [Annotation workflows](references/annotation-workflows.md): concrete APIs for labels, layers, pretrained predictions, `RegexpTagger`, relations, `DataPair`, serialization, and HTML visualization.
- [Tokenization and splitting](references/tokenization-and-splitting.md): tokenizer/splitter decision rules, offset behavior, retokenization caveats, optional dependency routes, and serializer implications.
- [Troubleshooting](references/troubleshooting.md): fixes for tokenization drift, model downloads/cache, label-layer confusion, offsets/serialization, optional tokenizer dependencies, and visualization issues.

## Practical rules for future agents

- Prefer `Classifier.load(model_id)` in examples because it dispatches to the appropriate Flair classifier class. Use `SequenceTagger.load(...)` or `TextClassifier.load(...)` only when the task specifically needs that concrete class.
- Pass `label_name="new_layer"` to prediction methods when preserving an existing layer matters; prediction normally removes existing labels in the target layer before adding new ones.
- For sequence taggers, span-predicting models put predictions on `Span` objects by default; use `force_token_predictions=True` only when token-level outputs are required.
- For `RegexpTagger`, regex match spans must align exactly with token boundaries. If a match cuts through a token, adjust tokenization or the regex before treating the output as valid.
- Use `render_ner_html(..., label_name="layer")` only for non-overlapping span-style labels that should be shown in one visual layer.
- Keep generated guidance self-contained: future use should require only a public pip-installed `flair` package plus explicitly permitted optional resources, not the original source checkout.
