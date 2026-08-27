# Compatibility

## Supported runtime

- Python: `>=3.9`
- PyTorch: `>=2.1,<2.3`
- Core package version: `3.5.1`

## Core dependencies

The package metadata requires:

- `torch`
- `configargparse`
- `ctranslate2`
- `tensorboard`
- `flask`
- `waitress`
- `pyonmttok`
- `pyyaml`
- `sacrebleu`
- `rapidfuzz`
- `pyahocorasick`
- `fasttext-wheel`
- `spacy`
- `six`

## Optional dependencies

The optional requirements file adds support for advanced or convenience workflows:

- `sentencepiece`
- `subword-nmt`
- `rapidfuzz`
- `scipy`
- `bitsandbytes>=0.41.2`
- `safetensors`
- `spacy`
- `gradio`
- `pyrouge`

## Backend notes

- Core data prep, train, translate, and server workflows are CPU-capable.
- CUDA is useful for large training and LLM-style fine-tuning workflows, but it is not required for the baseline package to import.
- CTranslate2 can run on CPU or GPU depending on the model and options.
- LoRA/8-bit workflows need `bitsandbytes` and a CUDA-capable environment.

## Known environment pitfall

A CUDA-capable torch build still needs a NumPy 1.x compatible ABI for the compiled modules shipped here. If you see warnings about NumPy 2.x, pin `numpy<2` and recheck imports.
