# Auto-Parallel and Offload Notes

ColossalAI includes experimental auto-parallel and activation-checkpointing demos as well as offload and NVMe-related memory features. Treat these as advanced routes.

## Auto-parallel

Auto-parallel examples search for sharding/checkpoint strategies from model graphs and memory budgets. They may require solver dependencies and specific PyTorch/Transformers versions.

Use auto-parallel guidance when the user asks for automatic sharding strategy search, activation checkpoint solver behavior, memory budget vs step-time tradeoffs, or ResNet/GPT-style auto-checkpoint examples.

Do not present auto-parallel as guaranteed for every current ColossalAI version. Ask for the target model, PyTorch version, solver availability, and GPU memory budget.

## NVMe/offload

NVMe and async checkpoint paths can require TensorNVMe and system libraries. Use them only when GPU memory or checkpoint IO is a bottleneck and the host storage stack is explicitly prepared.

Safer alternatives before NVMe/offload: reduce batch/microbatch size, enable ZeRO/Gemini placement or CPU offload, use gradient checkpointing, reduce bucket sizes or overlap settings, or shard checkpoints synchronously.
