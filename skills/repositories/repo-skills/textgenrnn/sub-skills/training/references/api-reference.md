# textgenrnn training API reference

The signatures below are the verified public training entry points for this sub-skill.
Use them as the source of truth for scratch training, fine-tuning, context labels, and file-backed workflows.

## Constructors and training entry points

| Method | Verified signature | Notes |
| --- | --- | --- |
| `textgenrnn.__init__` | `(__init__(weights_path=None, vocab_path=None, config_path=None, name='textgenrnn', allow_growth=None))` | Loads bundled pretrained weights and vocab by default. If `config_path` is supplied, the config file is loaded first and then `name` is written into the live config. `allow_growth` enables TF GPU memory growth when the backend supports it. |
| `textgenrnn.train_on_texts` | `(texts, context_labels=None, batch_size=128, num_epochs=50, verbose=1, new_model=False, gen_epochs=1, train_size=1.0, max_gen_length=300, validation=True, dropout=0.0, via_new_model=False, save_epochs=0, multi_gpu=False, **kwargs)` | Fine-tunes the current model unless `new_model=True` and `via_new_model=False`, in which case it forwards to `train_new_model`. `context_labels` are binarized automatically when present. `train_size < 1.0` reserves validation sequences when `validation=True`. |
| `textgenrnn.train_new_model` | `(texts, context_labels=None, num_epochs=50, gen_epochs=1, batch_size=128, dropout=0.0, train_size=1.0, validation=True, save_epochs=0, multi_gpu=False, **kwargs)` | Resets to the default config, merges `**kwargs`, creates a fresh tokenizer and model, writes the config/vocab files, then trains. Use this for scratch architectures, word-level models, and new vocabularies. |
| `textgenrnn.train_from_file` | `(file_path, header=True, delim='\n', new_model=False, context=None, is_csv=False, **kwargs)` | Reads texts from a file and routes to `train_on_texts` or `train_new_model`. `context=True` expects a two-column CSV with text in column 1 and label in column 2. `is_csv=True` reads the first column from a one-column CSV. `header=True` skips the first row before parsing. |
| `textgenrnn.train_from_largetext_file` | `(file_path, new_model=True, **kwargs)` | Reads the entire file into one text string and trains with `single_text=True`. This is the right entry point for one-document corpora and long-form text blocks. |
| `textgenrnn.save` | `(weights_path='textgenrnn_weights_saved.hdf5')` | Saves only the current model weights. It does not rewrite the config or vocab files. |
| `textgenrnn.load` | `(weights_path)` | Loads weights into the current model shape defined by the live config and vocab. Use matching scratch-model files or compatible pretrained weights. |
| `textgenrnn.reset` | `()` | Restores the default config and reinitializes the packaged pretrained model state. |

## Scratch-model config keys accepted via `**kwargs`

These keys are the ones most often used for training from scratch or training on large text blocks:

- `word_level`: switches tokenization from characters to words.
- `rnn_layers`: number of stacked recurrent layers.
- `rnn_size`: hidden size for each recurrent layer.
- `rnn_bidirectional`: uses bidirectional recurrent layers when true.
- `max_length`: number of prior tokens used to predict the next token.
- `max_words`: vocabulary cap by frequency for word-level training.
- `dim_embeddings`: embedding dimension for the scratch model.
- `single_text`: internal flag used for one-document training.
- `name`: artifact prefix used in the saved filenames.

## Important behavioral notes

- `train_on_texts(..., new_model=True)` is the same scratch-model route as `train_new_model(...)` unless `via_new_model=True` is already in play.
- `save_epochs > 0` creates intermediate files named `name_weights_epoch_<epoch>.hdf5` and still writes the final `name_weights.hdf5`.
- `multi_gpu=True` multiplies the batch size by the number of visible GPUs and builds the model under `tf.distribute.MirroredStrategy()`.
- Context training compiles a two-output model during training and then keeps the text-only path afterward.
- The training code expects at least `batch_size` usable sequences after tokenization and any `train_size` filtering.
