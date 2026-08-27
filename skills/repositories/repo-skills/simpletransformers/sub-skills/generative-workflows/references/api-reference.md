# Generative Workflows API Reference

## Public imports and constructors

```python
from simpletransformers.language_modeling import LanguageModelingArgs, LanguageModelingModel, GenerationArgs
from simpletransformers.language_generation import LanguageGenerationArgs, LanguageGenerationModel
from simpletransformers.seq2seq import Seq2SeqArgs, Seq2SeqModel
from simpletransformers.t5 import T5Args, T5Model
from simpletransformers.conv_ai import ConvAIArgs, ConvAIModel
```

```python
LanguageModelingModel(model_type, model_name, generator_name=None, discriminator_name=None, train_files=None, args=None, use_cuda=True, retrieval_model=None, adapter_name=None, cuda_device=-1, **kwargs)
LanguageGenerationModel(model_type, model_name, args=None, use_cuda=True, cuda_device=-1, **kwargs)
Seq2SeqModel(encoder_type=None, encoder_name=None, decoder_name=None, encoder_decoder_type=None, encoder_decoder_name=None, additional_special_tokens_encoder=None, additional_special_tokens_decoder=None, index_name=None, knowledge_dataset=None, index_path=None, dpr_ctx_encoder_model_name=None, rag_question_encoder_model_name=None, config=None, args=None, use_cuda=True, cuda_device=-1, **kwargs)
T5Model(model_type, model_name, args=None, tokenizer=None, use_cuda=True, cuda_device=-1, **kwargs)
ConvAIModel(model_type, model_name, args=None, use_cuda=True, cuda_device=-1, **kwargs)
```

## Main methods

| Model | Main methods | Notes |
|---|---|---|
| `LanguageModelingModel` | `train_model`, `eval_model`, `predict`, `train_tokenizer` | Supports pretrained fine-tuning and from-scratch workflows. |
| `LanguageGenerationModel` | `generate` | Generation-only wrapper around causal/XL-style model families. |
| `Seq2SeqModel` | `train_model`, `eval_model`, `predict` | BART/Marian/encoder-decoder or separate encoder/decoder. |
| `T5Model` | `train_model`, `eval_model`, `predict`, `rerank` | Prefix-driven text-to-text and monoT5-style reranking. |
| `ConvAIModel` | `train_model`, `eval_model`, `interact`, `interact_single` | Starts interactive generation; avoid in automated tests. |

## High-value args

- Generation: `max_length`, `max_new_tokens`, `do_sample`, `num_beams`, `temperature`, `top_k`, `top_p`, `num_return_sequences`, `repetition_penalty`, `stop_token`.
- LM: `block_size`, `data_format`, `vocab_size`, `mlm`, `mlm_probability`, `train_files`, `generator_config`, `discriminator_config`, `sliding_window`, `special_tokens`, `peft`, `qlora`, `stream_hf_datasets`.
- T5/Seq2Seq: `max_length`, `num_beams`, `do_sample`, `evaluate_generated_text`, `preprocess_inputs`, `dataset_class`, `use_multiprocessed_decoding`.
- ConvAI: `max_history`, `num_candidates`, `personality_permutations`, `temperature`, `top_k`, `top_p`, `lm_coef`, `mc_coef`.

## Compatibility notes

Modern Transformers versions may remove APIs used by Simple Transformers 0.70.8. During inspection, latest Transformers broke `TransfoXLConfig` and top-level `cached_path`; Transformers 4.31.0 satisfied metadata but still required compatibility handling for some shared custom-model aliases. If generation or ConvAI imports fail, handle package compatibility before data debugging.
