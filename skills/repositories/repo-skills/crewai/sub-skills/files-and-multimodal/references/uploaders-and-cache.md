# Uploaders and Cache

CrewAI can deliver file content as inline base64, raw bytes, URL references, or provider file references. Upload behavior is useful for large files and provider APIs that support file handles, but it is side-effectful and can require credentials, SDKs, network access, cloud storage, and cleanup.

## Resolution Flow

`FileResolver.resolve(file, provider)` follows this high-level order:

1. Load provider constraints with `get_constraints_for_provider(provider)`.
2. If the source is `FileUrl` and the provider supports URL references, return a `UrlReference` for non-Bedrock/non-AWS providers.
3. Otherwise read file content, compute size, content hash, and content type.
4. Decide whether to upload based on `prefer_upload`, type-specific inline limits, and provider upload threshold.
5. If upload succeeds, return `FileReference` and cache it when a cache is attached.
6. Fall back to inline content: `InlineBytes` for Bedrock when `use_bytes_for_bedrock=True`, otherwise `InlineBase64`.

The default `FileResolverConfig` is:

```python
FileResolverConfig(
    prefer_upload=False,
    upload_threshold_bytes=None,
    use_bytes_for_bedrock=True,
)
```

`create_resolver(provider=None, prefer_upload=False, upload_threshold_bytes=None, enable_cache=True)` attaches an `UploadCache` by default. `format_multimodal_content` uses the shared default upload cache from `get_upload_cache()`.

## Delivery Types

| Type | Meaning | Common providers |
| --- | --- | --- |
| `InlineBase64` | Base64-encoded file data embedded in the request block. | OpenAI, Anthropic, Gemini. |
| `InlineBytes` | Raw bytes embedded in a provider-specific request block. | Bedrock by default. |
| `UrlReference` | URL passed to provider without local fetch. | OpenAI, Anthropic, Gemini, Azure for supported HTTP(S) URL sources. |
| `FileReference` | Provider upload result with `file_id` and optional `file_uri`/expiry. | OpenAI, Anthropic, Gemini, Bedrock S3. |

## Upload Thresholds

Provider constraints include upload support and default thresholds:

- OpenAI completions and OpenAI Responses: upload support, threshold `5_242_880` bytes.
- Anthropic: upload support, threshold `5_242_880` bytes.
- Gemini: upload support, threshold `20_971_520` bytes.
- Bedrock: no generic file upload flag in constraints, but a Bedrock S3 uploader exists when configured.
- Azure constraints do not enable generic upload support.

A file can upload below threshold when `prefer_upload=True`. Without upload support or a configured uploader, the resolver falls back to inline formatting.

## Uploader Requirements

`get_uploader(provider, **kwargs)` maps providers to uploader classes:

| Provider | Uploader | Typical requirements |
| --- | --- | --- |
| `openai`, `gpt`, `azure` | `OpenAIFileUploader` | `openai` SDK and API credentials/client. |
| `anthropic`, `claude` | `AnthropicFileUploader` | `anthropic` SDK and API credentials/client. |
| `gemini`, `google` | `GeminiFileUploader` | `google-genai` SDK and API credentials/client. |
| `bedrock`, `aws` | `BedrockFileUploader` | `boto3`, AWS credentials/client, and `CREWAI_BEDROCK_S3_BUCKET` or explicit bucket args. |

Do not run uploaders in a dry-run validation script unless the user explicitly approved network and credential use. Prefer inspecting resolution decisions without forcing upload.

## Bedrock S3 Notes

`format_multimodal_content` sets Bedrock `prefer_upload=True` by default only when `CREWAI_BEDROCK_S3_BUCKET` is present, unless the caller overrides `prefer_upload`. `CREWAI_BEDROCK_S3_BUCKET_OWNER` can be used by the formatter to include the S3 bucket owner in the Bedrock content block. Without S3 upload, Bedrock defaults to raw bytes.

Ordinary HTTP(S) `FileUrl` values are not sent directly to Bedrock as URL references; Bedrock direct references are S3-style file locations produced through upload/reference handling.

## Upload Cache

`UploadCache` stores cached upload records by SHA-256 file hash and provider. It uses `aiocache` with pickle serialization and defaults to an in-memory backend.

Default cache behavior:

- Namespace: `crewai_uploads`.
- TTL: `86_400` seconds.
- Max tracked entries: `1000`.
- Expired uploads are ignored and removed from cache on lookup.
- Upload entries include `file_id`, provider, optional `file_uri`, content type, upload timestamp, and optional `expires_at`.
- The shared default cache is process-local unless configured with a backend such as Redis.

Useful public helpers:

```python
from crewai_files import get_upload_cache, reset_upload_cache
from crewai_files.cache.cleanup import cleanup_expired_files, cleanup_uploaded_files

cache = get_upload_cache()
# Inspect cache metadata without printing file content.
print(cache.get_providers(), len(cache))
# Clear local metadata only.
reset_upload_cache()
```

## Cleanup Semantics

`cleanup_uploaded_files(cache, delete_from_provider=True, providers=None)` attempts to delete cached provider uploads through each provider uploader, then clears the cache. This can call provider APIs. Use only when credentials and deletion side effects are approved.

`cleanup_expired_files(cache, delete_from_provider=False)` clears expired cache entries locally by default. Setting `delete_from_provider=True` may call provider APIs for expired entries.

`cleanup_provider_files(provider, cache=None, delete_all_from_provider=False)` is provider-specific and can delete files from the provider. `delete_all_from_provider=True` is broad and should be treated as a destructive provider operation.

## Safe Inspection Pattern

Use this when you need to explain how a file would be delivered without uploading:

```python
from crewai_files import FileResolver, FileResolverConfig, ImageFile

resolver = FileResolver(
    config=FileResolverConfig(prefer_upload=False, use_bytes_for_bedrock=True),
    upload_cache=None,
)
resolved = resolver.resolve(ImageFile(source="chart.png"), "openai")
print(type(resolved).__name__, resolved.content_type)
```

For a URL source, this pattern is safe only when the provider supports URL references and will not fetch the URL. Avoid running it for Bedrock or unknown providers with remote URLs in no-network contexts.

## Logging and Security

- Never log full base64 data, raw bytes, provider file IDs from production uploads, signed URLs, or bucket names from user environments.
- Summarize with MIME type, source kind, local filename, byte size, provider name, and resolved type.
- Treat upload retries as network operations. The resolver retries upload attempts up to three times with exponential backoff.
- Do not assume cached provider uploads are permanent; respect `expires_at`, provider retention rules, and user cleanup requirements.
