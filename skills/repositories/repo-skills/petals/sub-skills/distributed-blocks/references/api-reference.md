# Distributed Blocks API Reference

- `RemoteSequential(config, *, sequence_manager=None, dht=None, start_block=None, end_block=None, **kwargs)` creates a remote block chain or slice.
- `RemoteSequential.forward(inputs, prompts=None, **kwargs)` expects hidden states `[batch, seq, hidden]` and optionally deep prompts.
- `RemoteSequential.inference_session(max_length=...)` creates an incremental remote-cache session.
- `InferenceSession.step(inputs, prompts=None, hypo_ids=None)` advances an active session.
- `load_pretrained_block(model_name, block_index, *, config=None, torch_dtype="auto", revision=None, token=None, cache_dir=None, max_disk_space=None)` loads one local block's weights for inspection or conversion.
- `QuantType` names are `none`, `int8`, and `nf4`.
- `convert_block(block, block_index, config, tensor_parallel_devices, output_device, quant_type, freeze=True, adapters=None, **kwargs)` wraps a local block for serving.
- `make_tensor_parallel(block, model_config, devices, output_device)` creates the tensor-parallel wrapper.
- `check_device_balance(devices)` warns about uneven CUDA devices.

Relevant routing config fields include `initial_peers`, `dht_prefix`, `allowed_servers`, `blocked_servers`, `request_timeout`, `max_retries`, and `active_adapter`.
