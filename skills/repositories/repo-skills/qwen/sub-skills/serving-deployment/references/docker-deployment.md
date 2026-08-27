# Docker Deployment

## Images and prerequisites

The repository documents `qwenllm/qwen` images including `cu117` (recommended historically), `cu114`, `cu121`, and `latest`. Docker workflows require:

- Docker daemon.
- NVIDIA driver compatible with the chosen CUDA image.
- NVIDIA Container Toolkit configured for `--gpus all`.
- A local checkpoint directory with `config.json`, tokenizer assets, and model shards.

Do not pull images or run containers during a dry-run plan. Use the command builder:

```bash
python scripts/qwen_docker_command_builder.py --mode openai-api --checkpoint /models/Qwen-7B-Chat --port 8000
python scripts/qwen_docker_command_builder.py --mode web --checkpoint /models/Qwen-7B-Chat --image qwenllm/qwen:cu117 --port 8901
python scripts/qwen_docker_command_builder.py --mode cli --checkpoint /models/Qwen-7B-Chat
```

## CLI container pattern

```bash
docker run --gpus all --rm --name qwen \
  --mount type=bind,source=/path/to/Qwen-Chat,target=/data/shared/Qwen/Qwen-Chat \
  -it qwenllm/qwen:cu117 \
  python cli_demo.py -c /data/shared/Qwen/Qwen-Chat/
```

## Web/API container patterns

The web and API scripts run daemon containers, publish a host port, mount the checkpoint, and print log/cleanup instructions:

```bash
docker run --gpus all -d --restart always --name qwen \
  -p 8901:80 \
  --mount type=bind,source=/path/to/Qwen-Chat,target=/data/shared/Qwen/Qwen-Chat \
  -it qwenllm/qwen:cu117 \
  python web_demo.py --server-port 80 --server-name 0.0.0.0 -c /data/shared/Qwen/Qwen-Chat/
```

```bash
docker run --gpus all -d --restart always --name qwen \
  -p 8000:80 \
  --mount type=bind,source=/path/to/Qwen-Chat,target=/data/shared/Qwen/Qwen-Chat \
  -it qwenllm/qwen:cu117 \
  python openai_api.py --server-port 80 --server-name 0.0.0.0 -c /data/shared/Qwen/Qwen-Chat/
```

## Validation and cleanup

- If `config.json` is absent at the host checkpoint path, fix the path before running Docker.
- Use `docker logs qwen` to inspect service status.
- Use `docker rm -f qwen` to stop and remove the daemon container.
- Avoid mounting Docker socket or broad host paths unless the user has a concrete reason and accepts the security impact.
