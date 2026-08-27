# Model compatibility

## Core rule

Neuron view is not a generic Hugging Face visualization entry point. Use BertViz's vendored modified classes from `bertviz.transformers_neuron_view` so model forward passes expose attention probabilities plus query and key vectors.

The `model_type` string controls tokenization and sentence-pair behavior. It must match the model/tokenizer family and must be one of `bert`, `gpt2`, `xlnet`, or `roberta`.

## Vendored classes to use

| `model_type` | Tokenizer classes | Model/config classes | Local verification status |
| --- | --- | --- | --- |
| `bert` | `BertTokenizer`, `BasicTokenizer`, `WordpieceTokenizer` | `BertConfig`, `BertModel`, `BertForSequenceClassification`, `BertForQuestionAnswering`; additional exported BERT heads include `BertForPreTraining`, `BertForMaskedLM`, `BertForNextSentencePrediction`, `BertForMultipleChoice`, and `BertForTokenClassification` | Toy validator checks `BertModel`, `BertForSequenceClassification`, and `BertForQuestionAnswering` with no network. |
| `gpt2` | `GPT2Tokenizer` | `GPT2Config`, `GPT2Model`, `GPT2LMHeadModel`, `GPT2DoubleHeadsModel` | Public notebook recipe exists; shortcut-based native checks require cached/downloaded GPT-2 files. |
| `roberta` | `RobertaTokenizer` | `RobertaConfig`, `RobertaModel`, `RobertaForMaskedLM`, `RobertaForSequenceClassification` | Public notebook recipe exists; shortcut-based native checks require cached/downloaded RoBERTa files. |
| `xlnet` | `XLNetTokenizer` | `XLNetConfig`, `XLNetModel`, `XLNetLMHeadModel`, `XLNetForSequenceClassification`, `XLNetForQuestionAnswering` | Source API accepts single-sentence XLNet; sentence pairs are not implemented; native shortcut checks require cached/downloaded XLNet files and SentencePiece. |

The package also exports older OpenAI GPT, Transformer-XL, and XLM vendored classes. They are not valid `model_type` values for `bertviz.neuron_view.get_attention`; do not route them to neuron view unless you are writing a custom adapter outside this skill.

## Sentence-pair matrix

| `model_type` | Single sentence | Sentence pair | Pair output filters | Failure mode |
| --- | --- | --- | --- | --- |
| `bert` | Yes | Yes | `all`, `aa`, `ab`, `ba`, `bb` | None for supported vendored classes. |
| `roberta` | Yes | Yes | `all`, `aa`, `ab`, `ba`, `bb` | None for supported vendored classes. |
| `gpt2` | Yes | No | None | `ValueError: Model gpt2 does not support sentence pairs`. |
| `xlnet` | Yes | No | None | `NotImplementedError: Sentence-pair inputs for XLNet not currently supported.` |

Partition details:

- BERT A span: `[CLS] + tokens(sentence_a) + [SEP]`.
- BERT B span: `tokens(sentence_b) + [SEP]`.
- RoBERTa A span: `[CLS] + tokens(sentence_a) + [SEP]`.
- RoBERTa B span: `[SEP] + tokens(sentence_b) + [SEP]`.
- `aa`, `ab`, `ba`, and `bb` are raw slices of `all`; they do not independently sum to one.

## Optional dependency caveats

- `sentencepiece` is required by `XLNetTokenizer`. If it is missing, tokenizer construction fails after a warning or with a missing-name error.
- TensorFlow is optional and only needed for TensorFlow checkpoint conversion paths such as `from_tf=True` or `load_tf_weights_in_*`. Standard PyTorch local directories and cached PyTorch weights do not need TensorFlow.
- NVIDIA `apex` is optional. The vendored BERT/XLNet code falls back to a standard PyTorch layer norm implementation when `apex` is absent; this is a speed caveat, not a correctness requirement for this skill.
- `ftfy` and `spacy` are only relevant for the vendored OpenAI GPT and XLM tokenizer paths. Those paths are not valid neuron-view `model_type` values, so do not install them for normal BERT/GPT-2/RoBERTa/XLNet neuron-view work.
- Jupyter and IPython display support are needed for interactive `show(..., html_action='view')`. Schema validation with `get_attention` does not require notebook widgets.

## CPU backend expectations

- Core BertViz neuron-view validation is CPU-capable. The bundled toy script uses random-weight BERT models and PyTorch CPU tensors.
- `get_attention` creates its input tensors internally on CPU. Keep the vendored model on CPU unless you have written and verified a custom same-device wrapper.
- A GPU may be useful when a user separately computes large model outputs, but it is not required for the selected BertViz neuron-view operating workflows.
- Long inputs and large pretrained models can be slow because neuron view serializes all layers, heads, attention matrices, and query/key vectors. Start with short text and small/default selections.
