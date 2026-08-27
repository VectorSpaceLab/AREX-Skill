# Inference and evaluation troubleshooting

## Wrong demo mode

Symptoms:

- user expects continuation, but the run behaves like a prompt-comparison demo
- state appears to reset every token
- the script compiles a CUDA extension when the user only wanted a quick check

Likely causes:

- GPT-mode, RNN-mode, and fast mode were conflated
- the checkpoint family does not match the hard-coded demo dimensions

Recovery:

- choose GPT-mode for full-prefix inspection
- choose RNN-mode for persistent state across tokens
- choose fast mode only when CUDA compilation is feasible
- record the checkpoint dimension assumptions before changing code

## Missing checkpoint or tokenizer

Symptoms:

- `FileNotFoundError`
- `torch.load` fails immediately
- tokenizer encoding fails or unexpected token ids appear

Recovery:

- verify checkpoint basename and suffix separately from output directory
- verify the tokenizer family and vocabulary size
- do not borrow a checkpoint path from the repository examples; replace it with a user path or config entry

## Sampling confusion

Symptoms:

- generations vary wildly or are too deterministic
- top-p logic appears to ignore the user's intent
- prompt length or max output length is not what the user expected

Recovery:

- set `temperature`, `top_p`, `top_k`, `max_new_tokens`, and `seed` explicitly
- confirm whether the task wants greedy, controlled sampling, or comparison output

## MMLU scoring failure

Symptoms:

- `A/B/C/D` labels are multiple tokens
- accuracy looks random because the label mapping is wrong
- the code runs but answers are scored against the wrong gold index

Recovery:

- check tokenizer tokenization of the label strings first
- keep a label-to-choice map in the prompt adapter
- if labels are multi-token, change the benchmark adapter instead of pretending the scoring rule still holds

## CUDA or extension failure

Symptoms:

- `nvcc not found`
- custom extension build fails in `torch.utils.cpp_extension.load`
- the fast demo imports but cannot compile or load its op

Recovery:

- distinguish PyTorch CUDA runtime success from extension build success
- confirm CUDA toolkit, compiler, and checkpoint dimensions
- if the task is only configuration or prompt analysis, use the simpler demo or reference path instead of insisting on the fast path
