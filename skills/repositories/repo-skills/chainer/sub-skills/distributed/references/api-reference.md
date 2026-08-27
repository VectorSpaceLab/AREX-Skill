# ChainerMN API Reference

## Communicator creation

`chainermn.create_communicator(communicator_name='pure_nccl', mpi_comm=None, **kwargs)` creates the process communicator.
If `mpi_comm` is omitted, ChainerMN imports `mpi4py.MPI` and uses `MPI.COMM_WORLD`.

Communicator names:

| Name | CPU | GPU | NCCL | Typical use |
| --- | --- | --- | --- | --- |
| `pure_nccl` | no | yes | required | recommended GPU communicator when NCCL2 is available |
| `flat` | no | yes | no | legacy GPU communicator |
| `non_cuda_aware` | no | yes | no | GPU path when MPI is not CUDA-aware |
| `naive` | yes | yes | no | CPU testing and simple debugging |
| `dummy` | environment-dependent | environment-dependent | no | focused tests and debugging |

Useful communicator properties:

- `comm.rank`
- `comm.size`
- `comm.intra_rank`
- `comm.intra_size`
- `comm.inter_rank`
- `comm.inter_size`
- `comm.mpi_comm`

## Optimizers and evaluators

- `chainermn.create_multi_node_optimizer(actual_optimizer, communicator, double_buffering=False, zero_fill=True)`
- `chainermn.create_multi_node_evaluator(evaluator, communicator)`
- `chainermn.create_multi_node_checkpointer(name, comm, cp_interval=5, gc_interval=5, path=None)`

A multi-node optimizer wraps a normal Chainer optimizer and inserts gradient communication before parameter updates.
A multi-node evaluator wraps a normal evaluator and aggregates validation observations across workers.

## Dataset and iterator helpers

- `chainermn.scatter_dataset(dataset, communicator)`
- `chainermn.scatter_index(index, communicator)`
- `chainermn.datasets.create_empty_dataset()`
- `chainermn.iterators.create_multi_node_iterator(...)`
- `chainermn.iterators.create_synchronized_iterator(...)`

Use dataset scattering when rank 0 loads the dataset and workers need equal shards.

## Links and model-parallel helpers

- `chainermn.links.MultiNodeChainList`
- `chainermn.links.create_mnbn_model(...)`
- `chainermn.links.MultiNodeBatchNormalization`
- `chainermn.links.create_multi_node_n_step_rnn(...)`

`MultiNodeChainList` lets different ranks own different links in a model-parallel graph.

## Communication functions

- `chainermn.functions.send(...)`
- `chainermn.functions.recv(...)`
- `chainermn.functions.bcast(...)`
- `chainermn.functions.gather(...)`
- `chainermn.functions.scatter(...)`
- `chainermn.functions.alltoall(...)`
- `chainermn.functions.allgather(...)`
- `chainermn.functions.pseudo_connect(...)`

These are lower-level building blocks for custom distributed models.

## Runtime prerequisite checks

Before trying a launch, verify:

- `mpi4py` imports successfully
- `mpiexec` and `mpicc` are in `PATH`
- CuPy is installed when using GPU workflows
- NCCL is enabled for `pure_nccl`
- MPI is CUDA-aware for high-performance GPU communication
