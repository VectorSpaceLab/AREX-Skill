# NLP runtime setup

## Packages
The verified construction environment imported `transformers==4.38.2`, `keras-preprocessing==1.1.2`, TensorFlow 2.15.x, NLTK, TextBlob, and the root pandas compatibility shim. Use the root environment reference for the full stack.

## NLTK corpora
Libra's `client.__init__` calls:
- `nltk.download('punkt')`
- `nltk.download('averaged_perceptron_tagger')`
- `nltk.download('stopwords')`

Newer NLTK/TextBlob usage can also need:
- `averaged_perceptron_tagger_eng`
- `punkt_tab`
- `wordnet`
- `omw-1.4`

Check current availability without downloads:

```bash
python skills/disco/libra/sub-skills/nlp-and-generation/scripts/prepare_nltk_corpora.py --check
```

Download only when network policy allows it:

```bash
python skills/disco/libra/sub-skills/nlp-and-generation/scripts/prepare_nltk_corpora.py --download
```

## HuggingFace and model caches
Summarization, GPT-2 text generation, NER, and image captioning may load pretrained weights. Before running them:
- confirm network/cache policy
- set any desired HuggingFace/TensorFlow cache directories
- use small `epochs`, `max_text_length`, and `return_sequences` values for smoke checks

## CPU/GPU
The construction environment saw no TensorFlow GPU even though host GPUs were visible. Treat CPU as the verified baseline. Do not set `gpu=True` unless TensorFlow in the active environment reports a GPU.
