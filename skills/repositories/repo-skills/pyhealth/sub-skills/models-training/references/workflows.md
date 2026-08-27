# Training and inference workflows

## Safe one-batch smoke

Use a synthetic task dataset and a model with no external weights. Confirm:

1. one loader batch has the expected keyword keys;
2. tensors are on the intended device and have compatible dimensions;
3. `output = model(**batch)` contains `loss`;
4. `loss.backward()` and one optimizer step work;
5. `Trainer.inference` returns aligned arrays.

The bundled `pipeline_smoke.py` is a contract checker, not a replacement for a
clinical training run.

## Bounded training

For a real experiment, start with `epochs=1` and `steps_per_epoch=1` on a local
fixture, then increase only after checking loss/labels and memory. Set
`output_path` and `exp_name` to a new run directory. Keep validation and test
patient-disjoint. Set `patience` only when a validation monitor is meaningful.

## External/pretrained models

For `TransformersModel`, text/vision embeddings, EHRMamba variants, and
multimodal models, distinguish local architecture/tokenizer checks from weight
acquisition. Record model identifier, revision, cache, license, and network
policy before loading weights. A successful import or randomly initialized
forward is not a recovered pretrained result.
