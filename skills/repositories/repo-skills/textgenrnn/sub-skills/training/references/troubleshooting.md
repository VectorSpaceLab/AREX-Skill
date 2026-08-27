# Training troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Fewer tokens than batch_size.` | The dataset is too small after tokenization, `max_length` is too large, or the batch size is too high. | Lower `batch_size`, shorten `max_length`, or add more training text. For smoke tests, keep the fixture tiny but still large enough to cover the chosen batch size. |
| `context_labels` errors or bad contextual output | The label list length does not match `texts`, or the CSV columns are out of order. | Make sure labels align one-for-one with the texts. For file-backed contextual training, use a two-column CSV with text first and label second. |
| `train_from_file` appears to skip or misread rows | The header setting or file format does not match the parser. | Remember that `header=True` skips the first row. Use `is_csv=True` for a one-column CSV and `context=True` for a two-column context CSV. |
| Validation loss is missing | `validation=False` or `train_size=1.0`. | Set `train_size < 1.0` and keep `validation=True` when you need a held-out validation split. |
| No `config` or `vocab` file was written | The run fine-tuned the current model instead of starting a scratch model, or the `name` prefix changed. | Use `train_new_model` or `new_model=True` when you want scratch artifacts, and verify the current working directory plus the configured model name. |
| Training quality is poor or repetitive | The fixture is too small, the model underfit, or the dataset is too narrow. | Use more texts, train for more epochs, lower `max_length` if the sequences are short, or start from pretrained weights instead of a scratch model. |
| The smoke run passes but the sample text still looks bad | The smoke fixture is intentionally tiny and `gen_epochs=0` does not generate quality samples. | Treat the smoke run as an artifact check only. Use a larger corpus and a normal training recipe when quality matters. |
| `ModuleNotFoundError` for `pkg_resources` or `tensorflow.compat.v1.keras` | The environment stack is incompatible with this repo's training code. | Use the root compatibility guidance in `../../references/installation-and-compatibility.md` and a pre-Keras-3 TensorFlow stack. |
| `multi_gpu=True` has no effect or fails | No GPU devices are visible to TensorFlow, or the backend is CPU-only. | Leave `multi_gpu=False` on CPU and enable it only after the GPU backend is verified. |
| Expected snapshot file is missing | `save_epochs=0` or the run ended on the final epoch, which writes only the final weights file. | Set `save_epochs > 0` for intermediate snapshots and remember that the final `name_weights.hdf5` is always the latest weights file. |

## Recovery pattern

1. Confirm the file format, text count, and batch size first.
2. Re-run with `gen_epochs=0` and `validation=False` when you only need to prove the training path.
3. For real-quality recovery, switch to a larger corpus, use a pretrained starting point, and train for more epochs.
4. If the import stack fails, stop adjusting training parameters and fix the compatibility layer first.
