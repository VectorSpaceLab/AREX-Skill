# Encrypted DistilBERT Model Notes

The Nesa demo uses an encrypted DistilBERT sentiment model to demonstrate EE in a
small, local, inspectable setting.

## Public behavior

- Task family: English sentiment classification.
- Framework: Hugging Face Transformers with PyTorch.
- Inputs: plaintext strings on the client side.
- Client output before server inference: encrypted token IDs.
- Model output: logits/probabilities for the sequence-classification labels.
- Client-side interpretation: label names from the model config.

## Demo model limitations

The community model card states that the public encrypted DistilBERT model is an
approximation of a higher-fidelity enterprise version. It says the public version
is expected to reproduce the original model's result about 92% of the time, with
small confidence-score changes.

When comparing encrypted and plaintext models:

- choose a fixed prompt set;
- log both predicted labels and probabilities;
- keep model ids and revisions fixed;
- separate latency, fidelity, and privacy claims; and
- report uncertainty instead of generalizing from a few prompts.

## Model directory validation

Use the bundled validator before running the demo. A directory with only a
README or only weights is not enough. The tokenizer and config are part of the
client-controlled encryption/decryption story, so a missing or mismatched
tokenizer changes the result.

## Common model ids

The source documentation names Nesa encrypted DistilBERT variants. If a model id
is unavailable, do not replace it with `distilbert-base-uncased-finetuned-sst-2`
without telling the user; that would remove the encrypted-token behavior the Nesa
demo is meant to exercise.

## Interpreting encrypted token IDs

Encrypted token IDs are numeric IDs produced by the tokenizer. In the demo, they
are printed to show what the server would see. Do not try to decode them with a
plain DistilBERT tokenizer and call that decryption. The mapping belongs to the
Nesa tokenizer/model pair.
