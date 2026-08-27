# RWKV inference workflows

## GPT-mode demo

The repository's `rwkv_v7_demo.py` is the most direct GPT-style generation
example. It loads a checkpoint, tokenizes an input prompt, runs the model over
the full prefix, and then samples one token at a time. Use this mode when you
want to compare logits, inspect a prompt, or generate text with the least state
machinery.

Typical ingredients:

- a `.pth` checkpoint
- a tokenizer (`rwkv_vocab_v20230424` for RWKV-7 examples)
- `temperature`, `top_p`, and `top_k` controls
- a prompt string or list of tokens

The repository example uses local absolute paths for the model file. Replace
those with a user-provided path or a config value in the generated skill.

## RNN-mode demo

`rwkv_v7_demo_rnn.py` shows the stateful token-by-token path. It is more useful
when a user wants to understand or preserve recurrent state between steps.
The forward function accepts a token id and a persistent state list.

Use RNN-mode when:

- you need to continue generation interactively
- you want to reuse the hidden state across turns
- you are comparing state updates between implementations

## Fast mixed mode

`rwkv_v7_demo_fast.py` combines GPT-like prefill with optimized CUDA inference.
It compiles and loads a custom extension and therefore depends on a matching GPU
stack, compiler toolchain, and checkpoint shape. Treat it as the fastest path,
not the simplest path.

Common compile-time requirements:

- matching torch CUDA wheel and driver
- CUDA toolkit and `nvcc`
- a checkpoint whose layer/head dimensions match the hard-coded demo config

## Safe configuration checklist

Before running any demo:

- verify checkpoint basename and dimensions
- verify tokenizer file and vocabulary size
- record whether the user wants greedy decoding or stochastic sampling
- set a max generation length
- decide whether the run is for qualitative chat or for comparison/debugging

## Minimal command shape

A generated helper should accept a config file or explicit arguments for:

- `checkpoint`
- `tokenizer`
- `mode` (`gpt`, `rnn`, `fast`)
- `prompt`
- `temperature`
- `top_p`
- `top_k`
- `max_new_tokens`
- `seed`

This keeps the workflow reproducible without embedding the repository's local
paths.
