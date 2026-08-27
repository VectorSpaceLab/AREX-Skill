# NLP and text workflows

Install the optional NLP group for `rapidfuzz`, `rouge_score`, and `nltk`:

```bash
python -m pip install 'pyhealth[nlp]'
```

The package includes `pyhealth.nlp.metrics` and text processors/models. A
`TextProcessor` converts text according to its current processor contract;
`TupleTimeTextProcessor` handles time/text tuples and must be validated with
its expected tuple shape. Text embedding and Transformer-based classes can
require tokenizer configuration and external weights.

Separate these checks:

1. import the package and optional extras;
2. process a local text fixture with a deterministic tokenizer/processor;
3. compute a local metric (ROUGE-like metrics may need the extra only);
4. only then decide whether to download a pretrained tokenizer/model or corpus.

Clinical text may contain PHI. Use de-identified fixtures, document truncation,
tokenization, vocabulary/revision, and model cache/license. NLTK imports do not
prove that a requested corpus is installed; a missing corpus should be reported
as a resource gate rather than downloaded by a helper.
