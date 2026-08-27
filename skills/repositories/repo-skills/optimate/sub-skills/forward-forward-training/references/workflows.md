# Forward-Forward Workflows

## Progressive workflow

1. Choose `model_type="progressive"`.
2. Let the MNIST loader build train and test dataloaders.
3. Set `n_layers`, `hidden_size`, `epochs`, `batch_size`, `theta`, and `device`.
4. Train on label-injected image batches.
5. Read the logged test accuracy at the end of training.

## Recurrent workflow

1. Choose `model_type="recurrent"`.
2. Use the same MNIST loader as the progressive branch.
3. Train with one-hot labels and recurrent goodness updates.
4. Inspect the epoch-by-epoch goodness ratio and test accuracy.

## NLP workflow

1. Choose `model_type="nlp"`.
2. Provide `predicted_tokens` in `kwargs`.
3. Let the Aesop Fables loader build tokenized train/test splits.
4. Train on one-hot token sequences and evaluate perplexity after training.

## Practical notes

- `device` defaults to CPU, but the branch can run on GPU when available.
- The trainer chooses its own local model/data operations; the caller only selects the public entry point and top-level arguments.
- The bundled probe script is for import and signature inspection only; it does not download MNIST or Aesop fables.
