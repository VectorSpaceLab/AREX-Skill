# Serving and Export API Reference

## FastAPI serving

- `ludwig.serve.run_server(model_path, host, port, allowed_origins, prediction_timeout=30.0)` starts the server.
- `ludwig.serve.server(model, allowed_origins=None, prediction_timeout=30.0)` builds an app from a loaded model.
- `ludwig.serve_v2.create_app(model_path=None, allowed_origins=None, prediction_timeout=30.0)` creates a modern app with injectable model dependency.
- `ludwig.serve_v2.build_request_schema(config)` and `build_response_schema(config)` generate Pydantic request/response models from config features.

## Deployment shims

- `ludwig.serve_ray_serve.deploy_ludwig_model(model_path, name="ludwig", num_replicas=1, ray_actor_options=None, route_prefix=None)` deploys under Ray Serve when Ray Serve is installed.
- `ludwig.serve_kserve.serve_ludwig_model(model_name, model_path, http_port=8080)` starts the KServe shim when KServe is installed.
- `ludwig.serve_vllm.run_vllm_server(model_path, host="0.0.0.0", port=8000, model_name="ludwig-llm", **kwargs)` is for LLM serving with vLLM-compatible runtime.

## Export/upload APIs

- `ludwig.export.export_model(model_path, output_path, format="safetensors", **kwargs)`.
- `ludwig.export.export_mlflow(model_path, output_path="mlflow", registered_model_name=None, callbacks=None, **kwargs)`.
- `LudwigModel.upload_to_hf_hub(repo_id, model_path, repo_type="model", private=False, commit_message=..., commit_description=None)`.
