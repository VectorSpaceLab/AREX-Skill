# Service Authoring Workflows

## Create A Minimal Importable Service

1. Create `service.py` in the project root.
2. Import `bentoml` and optional schema libraries.
3. Define `@bentoml.service` on a class.
4. Add one or more `@bentoml.api` methods with explicit type hints.
5. Run `python path/to/validate_service_target.py --target service:ClassName --working-dir .`.
6. If validation passes, route serving/building to the appropriate sub-skill.

A safe starter is available:

```bash
python skills/bentoml/sub-skills/service-authoring/scripts/create_minimal_service.py --output service.py --class-name TextTools --service-name text-tools --path-prefix /v1 --force
```

## Add Batching

Use batching when throughput improves by processing requests together.

```python
@bentoml.api(batchable=True, max_batch_size=16, max_latency_ms=500)
def embed(self, texts: list[str]) -> list[list[float]]:
    return self.encoder.encode(texts).tolist()
```

If input and output are arrays, decide the stacking and splitting axis:

```python
@bentoml.api(batchable=True, batch_dim=(0, 0))
def classify(self, inputs: np.ndarray) -> np.ndarray:
    return self.model.predict(inputs)
```

For multiple logical fields, batch a single composite object:

```python
class Request(BaseModel):
    image: Path
    threshold: float

@bentoml.api(batchable=True)
def predict(self, inputs: list[Request]) -> list[str]:
    ...
```

## Add Async Tasks

Use `@bentoml.task` for fire-and-forget work with later status/result retrieval. Keep the function implementation like a normal API, but do not yield streams.

```python
@bentoml.task(name="render")
def render(self, prompt: str) -> str:
    return self.pipeline(prompt)
```

Task clients call `client.render.submit(...)`; direct HTTP task endpoints include submit/status/get/cancel/retry behavior. Do not use task endpoints for low-latency request/response paths.

## Compose Services

Use one service when multiple models share lifecycle and hardware. Split into services when components need independent hardware, workers, or scaling.

```python
@bentoml.service(resources={"cpu": "1"})
class Preprocess:
    @bentoml.api
    def clean(self, text: str) -> str:
        return text.strip()

@bentoml.service(resources={"gpu": 1})
class Inference:
    prep = bentoml.depends(Preprocess)

    @bentoml.api
    async def predict(self, text: str) -> str:
        cleaned = await self.prep.to_async.clean(text)
        return cleaned.upper()
```

Use `.to_async` when calling a sync dependency from an async API to avoid blocking the event loop.

## Mount ASGI Or WebSocket Routes

```python
from fastapi import FastAPI, WebSocket
import bentoml

app = FastAPI()

@bentoml.service(path_prefix="/v1")
@bentoml.asgi_app(app, path="/chat")
class ChatService:
    @bentoml.api
    def ping(self) -> str:
        return "pong"

    @app.websocket("/ws")
    async def websocket_endpoint(self, websocket: WebSocket):
        await websocket.accept()
        message = await websocket.receive_text()
        await websocket.send_text(f"Echo: {message}")
```

The API route becomes `/v1/ping`; the WebSocket route becomes `/v1/chat/ws`.

## Add A Gradio UI

```python
import gradio as gr
import bentoml


def call_service(text: str) -> str:
    service = bentoml.get_current_service()
    return service.echo(text)

ui = gr.Interface(fn=call_service, inputs="text", outputs="text")

@bentoml.service(image=bentoml.images.Image().python_packages("gradio", "fastapi"))
@bentoml.gradio.mount_gradio_app(ui, path="/ui")
class Echo:
    @bentoml.api
    def echo(self, text: str) -> str:
        return text
```

## Stream Results

```python
from typing import AsyncGenerator

@bentoml.api
async def generate(self, prompt: str) -> AsyncGenerator[str, None]:
    async for token in self.engine.stream(prompt):
        yield token
```

If a stream needs custom HTTP behavior, prefer ASGI routes or explicit output specs. Never mark a streaming method with `@bentoml.task`.

## Load And Test Without Starting A Server

For quick checks:

```python
from service import TextTools

svc = TextTools()
assert svc.echo("hi") == "hi"
```

For HTTP behavior without binding a port:

```python
from starlette.testclient import TestClient
from service import TextTools

with TestClient(TextTools.to_asgi()) as client:
    response = client.post("/echo", json={"text": "hi"})
    assert response.status_code == 200
```

Use `validate_service_target.py` first when debugging import targets because it reports module import, service object discovery, routes, tasks, dependencies, and mounted apps without starting a network server.
