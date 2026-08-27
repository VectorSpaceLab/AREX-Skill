# Client workflows

These are safe, placeholder-driven workflows for the Xinference Python client and OpenAI-compatible APIs.

## Before you start

- Use the **Xinference endpoint** (`http://HOST:PORT`) with `Client` / `AsyncClient`.
- Use the **OpenAI-compatible base URL** (`http://HOST:PORT/v1`) with OpenAI-style SDK calls.
- Replace `MODEL_UID` with the UID of a model that has already been launched.
- If you need the launch recipe, get it from the sibling serving or backend skill; do not guess model parameters here.

## Sync Python client

```python
from xinference.client import Client

client = Client("http://127.0.0.1:9997", api_key="YOUR_API_KEY")
try:
    print(client.list_models())
    model = client.get_model("MODEL_UID")
    try:
        response = model.chat(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Write a one-sentence reply."},
            ],
            generate_config={"max_tokens": 64},
        )
        print(response)
    finally:
        model.close()
finally:
    client.close()
```

Typical flow:
1. Connect to the endpoint root.
2. Confirm the launched model is visible.
3. Resolve a handle with `get_model(MODEL_UID)`.
4. Call the handle method that matches the model type.
5. Close both handle and client.

### Streaming with the sync client

```python
stream = model.generate(
    prompt="Write a short story starter.",
    generate_config={"stream": True, "max_tokens": 64},
)
for chunk in stream:
    print(chunk)
```

## Async Python client

```python
import asyncio
from xinference.client import AsyncClient


async def main():
    client = AsyncClient("http://127.0.0.1:9997", api_key="YOUR_API_KEY")
    try:
        model = await client.get_model("MODEL_UID")
        try:
            response = await model.create_embedding("A sentence to embed.")
            print(response)
        finally:
            await model.close()
    finally:
        await client.close()


asyncio.run(main())
```

### Async streaming

```python
stream = await model.chat(
    messages=[{"role": "user", "content": "Count to three."}],
    generate_config={"stream": True, "max_tokens": 32},
)
async for chunk in stream:
    print(chunk)
```

## OpenAI-compatible SDK workflow

```python
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:9997/v1", api_key="YOUR_API_KEY")
response = client.chat.completions.create(
    model="MODEL_UID",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello."},
    ],
)
print(response)
```

Use this path when you want OpenAI-compatible tooling, not Xinference-specific helpers.

## Raw HTTP workflow

Use raw HTTP when you want direct control over the request body or when a helper is not available.

```bash
curl -X POST "http://127.0.0.1:9997/v1/embeddings" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "MODEL_UID",
    "input": ["A sentence to embed."]
  }'
```

## Launching from the client

If you already know the launch parameters, the sync client can start a model:

```python
model_uid = client.launch_model(
    model_name="MODEL_NAME",
    model_type="LLM",
    model_engine="MODEL_ENGINE",
    model_format="MODEL_FORMAT",
    model_size_in_billions=MODEL_SIZE,
)
```

Keep the launch parameters sourced from the serving or backend workflow. Do not invent a model engine, format, or quantization setting here.

## Common handle calls

- Chat / generate: `model.chat(...)`, `model.generate(...)`
- Embedding: `model.create_embedding(...)`
- Rerank: `model.rerank(...)`
- Image: `model.text_to_image(...)`, `model.image_to_image(...)`, `model.image_edit(...)`, `model.inpainting(...)`, `model.ocr(...)`
- Audio: `model.transcriptions(...)`, `model.translations(...)`, `model.speech(...)`
- Video: `model.text_to_video(...)`, `model.image_to_video(...)`, `model.flf_to_video(...)`
- Flexible: `model.infer(...)`

## Close-out checklist

- Close the model handle.
- Close the client.
- If auth is enabled, make sure the token or API key is valid before retrying.
- If the request fails, inspect the model description and the request shape before changing the endpoint.
