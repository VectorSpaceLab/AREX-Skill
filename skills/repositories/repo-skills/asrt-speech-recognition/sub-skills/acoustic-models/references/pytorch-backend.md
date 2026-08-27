# Experimental PyTorch acoustic backend

ASRT includes an experimental PyTorch implementation for the `SpeechModel251BN` acoustic architecture. Treat it as a separate route from the primary TensorFlow/Keras workflow.

## Available PyTorch pieces

`model_zoo/speech_model/pytorch_backend.py` defines:

```python
SpeechModel251BN(input_shape=(1600, 200, 1), output_size=1428)
```

Key facts:

- `input_shape` default is `(1600, 200, 1)`.
- `_pool_size = 8`.
- `_model_name = 'SpeechModel251bn'`.
- `output_shape = (input_shape[0] // 8, output_size)`, so default `(200, 1428)`.
- The model uses Conv2d + BatchNorm2d blocks, `bfloat16` layer dtypes, `log_softmax`, and `nn.CTCLoss(blank=0)`.
- `forward(x)` returns `(batch, time, classes)` log probabilities.
- `compute_loss(y_pred, labels, input_length, label_length)` permutes to `(time, batch, classes)` and computes CTC loss.
- `get_model()` returns `self`; `get_model_name()` returns `SpeechModel251bn`.

`torch_speech_model.py` defines a PyTorch-side `SpeechDataset` and `ModelSpeech` wrapper:

- `SpeechDataset` adapts ASRT `DataLoader` samples into padded `bfloat16` feature tensors, labels, input lengths, and label lengths.
- `ModelSpeech.train(data_loader, epochs, batch_size, optimizer, device='cpu')` wraps PyTorch training.
- `save_weight(filename)` saves a state dict.
- `load_weight(filepath)` loads a state dict.

## Route selection

Use the Keras route for ASRT's documented and verified acoustic workflows. Consider the PyTorch route only when the task explicitly asks for PyTorch experimentation or conversion, because:

- The README and default train/evaluate/predict scripts describe TensorFlow/Keras operation.
- The provided PyTorch code covers training-related operations but does not provide a single-file recognition wrapper equivalent to Keras `recognize_speech_from_file`.
- The source `train_speech_model_pytorch.py` was not part of this sub-skill's evidence brief, so no runtime claim is made from it here.

## Device and dtype caveats

The PyTorch implementation uses `torch.bfloat16` for convolution and dense layers and for padded feature tensors. That can be problematic on CPUs or GPUs without efficient bfloat16 support. Before long training:

```python
import torch
print(torch.__version__)
print(torch.cuda.is_available())
```

Then run a tiny forward/loss smoke in the target environment. Do not assume CPU can substitute for CUDA, or CUDA can run this code efficiently, until the target hardware and PyTorch build have been checked.

## Save path caveat

The PyTorch `save_weight` method builds:

```python
save_filename = os.path.join('save_models_torch', filename + '.pth')
torch.save(self.speech_model.state_dict(), save_filename)
```

If the caller passes a filename that already includes directories or `.pth`, the final path may be surprising. Create `save_models_torch` first and pass a simple prefix unless you have tested the exact behavior.

## Label and CTC caveats

The PyTorch `SpeechDataset` adds `+1` to labels before training, while the CTCLoss blank index is `0`. This differs from Keras code paths that use ASRT's label indexes directly with Keras CTC handling. Keep label-index assumptions explicit when comparing Keras and PyTorch results.

No accuracy, parity, or weight-conversion claim is made for the PyTorch backend by this skill.
