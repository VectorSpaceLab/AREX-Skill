# Data and Compatibility

## Dataset behavior

- The progressive and recurrent branches use MNIST.
- `MNISTDataLoaderOperation` downloads MNIST into a local `data` directory through `torchvision.datasets.MNIST`.
- The NLP branch uses Aesop fables text, fetches it from a public source, filters the text, tokenizes it, and keeps 100-token sequences.
- The NLP vocabulary is fixed to 30 symbols: space, punctuation, and lowercase letters.

## Shape conventions

- Progressive training injects labels into the image representation before learning.
- Recurrent training one-hot encodes labels.
- NLP training one-hot encodes token ids and reshapes the sequence to `token_num * sequence_len` before evaluation.

## Compatibility note

- The source-era code is sensitive to Python 3.10 because it imports `Generator` from `collections`.
- Python 3.9 is the safe baseline for this sub-skill unless the import path is patched to `collections.abc.Generator`.

## Use this when

You need to explain which dataset branch the model type uses, why a token-based run needs `predicted_tokens`, or why a Python 3.10 environment fails before the model ever trains.
