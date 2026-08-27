# Training Recipes

Verified training surfaces include `TorchComponent.fit`, `TorchComponent.evaluate`, `TorchComponent.load`, `TransformerTaggingTokenizer.fit`, `MultiTaskLearning.fit`, and `TransformerClassifier.fit`.

Before running any training recipe:

1. Confirm dataset files/constants and licenses.
2. Confirm transformer/model downloads or cache.
3. Choose `save_dir`; training writes model artifacts.
4. Set `seed` when reproducibility matters.
5. Choose CPU/GPU `devices`; GPU is recommended for realistic training.
6. Set `epochs`, `batch_size`, and sequence-length controls deliberately.
7. Run focused import/signature checks first.

Chinese tokenizer recipe pattern:

```python
from hanlp.common.dataset import SortingSamplerBuilder
from hanlp.components.tokenizers.transformer import TransformerTaggingTokenizer

tokenizer = TransformerTaggingTokenizer()
tokenizer.fit(trn_data, dev_data, save_dir, transformer='bert-base-chinese', max_seq_len=300, char_level=True, hard_constraint=True, sampler_builder=SortingSamplerBuilder(batch_size=32), epochs=3, seed=1660853059, devices=0)
tokenizer.evaluate(test_data, save_dir)
```

Install optional extras only when needed: `hanlp[amr]`, `hanlp[tf]`, or `hanlp[full]`. Record package versions, model identifiers, data splits, seed, and backend for reproducibility.
