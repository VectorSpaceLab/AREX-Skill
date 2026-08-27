# ROSA troubleshooting

## GPU and extension assumptions

Symptoms:

- `cuda` is hard-coded in the script
- `torch.utils.cpp_extension.load` tries to compile a CUDA op
- the script mentions `HEAD_SIZE`, `CHUNK_LEN`, or `wkv7_cuda`

Likely causes:

- the script is a research prototype rather than a portable helper
- `nvcc` or `CUDA_HOME` is missing
- the checkpoint or custom op does not match the script's fixed dimensions

Recovery:

- start with the CPU-safe suffix-automaton demo
- only run the original script after checking the environment and checkpoint
- do not treat a successful PyTorch CUDA import as proof that the custom op will
  compile

## Checkpoint confusion

Symptoms:

- script points to a maintainer-local `.pth`
- a run script expects a file name like `251016_rosa_1bit_run.pth`
- the checkpoint does not match the demo's parameter count

Recovery:

- identify whether the script is a trainer or a runner
- check that the `.pth` file is from the same toy family and layer count
- keep checkpoint paths as user-supplied input in the generated skill

## Reverse-digit mismatch

Symptoms:

- the reverse task uses a different `DIGIT_MAX`, `T`, or saved checkpoint name
- accuracy no longer matches the comments in the source script

Recovery:

- match the task length to the checkpoint family
- preserve the exact digit range and prompt format when reproducing the demo
- do not generalize the result to a different length without retraining

## Too-slow or memory-heavy toy training

Symptoms:

- a comment says the backward pass is extremely slow
- the script allocates large batches or long sequences
- the script is unsuitable for a smoke test even if the algorithm is simple

Recovery:

- treat the script as an experimental reference only
- use the CPU-safe helper for algorithm inspection
- if the user wants a full reproduction, warn them that the run is not a quick
  validation and may need a GPU and a long time budget
