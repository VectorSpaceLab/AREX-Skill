# Runtime operations

## Experiments and checkpoints

Training creates `experiments/<General.name>/` and writes logs, a symbol JSON,
and checkpoint parameters under the configured model prefix. Evaluation reads
`TestParam.model.prefix` and `epoch`; speed inference writes an inference symbol
next to that prefix. Keep `data`, `pretrain_model`, `experiments`, and logs on
storage with enough space, but do not put them inside the generated skill.

A checkpoint prefix normally has a symbol JSON plus parameter files named with a
four-digit epoch, for example `<prefix>-0006.params`. Before fine-tuning or
class-count changes, inspect parameter names and remove incompatible class-aware
bbox/mask heads rather than setting `allow_missing` indiscriminately.

## TensorBoard

The documented pattern is to install `mxboard` and `tensorboard`, construct a
`SummaryWriter`, pass it as `summary=` to metrics, then run TensorBoard against
the configured log directory. This is optional and must not be required for
training. Avoid starting a long-running server as an environment smoke check.

## Distributed prerequisites

The source documentation expects:

- a compatible Singularity/container or equivalent CUDA runtime on every node;
- a launcher placed outside the SimpleDet checkout;
- passwordless SSH and a hostfile;
- shared or deliberately symlinked `data`, `pretrain_model`, and `experiments`;
- consistent config, MXNet, CUDA, NCCL, and network-interface settings;
- a tested single-node/single-GPU command before multi-node execution.

The source launch helpers also contain private mount paths, host probing, and
process termination. Treat them as evidence only. Adapt their arguments and
review every side effect before using any cluster launcher.

## Safe escalation

Start with environment diagnostic → config import/inspection → one-GPU speed
smoke with a tiny shape/model if weights are already present → short training
or evaluation → multi-GPU local kvstore → NCCL/distributed. If a step fails,
reduce scope before changing several backend variables at once.
