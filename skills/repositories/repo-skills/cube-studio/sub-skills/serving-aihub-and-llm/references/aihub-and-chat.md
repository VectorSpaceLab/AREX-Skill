# AIHub and chat

CubeStudio's AIHub and chat features sit on top of the serving layer.

## AIHub catalog shape

`Aihub` records a card-like catalog entry with fields such as:

- `uuid`, `status`, `doc`, `name`, `field`, `scenes`, `type`, `label`, `describe`, `source`, `pic`
- `images`, `dataset`, `notebook`, `job_template`, `pipeline`, `pre_train_model`, `inference`, `service`
- `version`, `hot`, `price`, `expand`

The AIHub view groups cards by field and exposes category-specific routes for visual, voice, language, multimodal, and large-model content.

## Chat model shape

`Chat` records a reusable chat scenario with:

- `name`, `icon`, `label`, `doc`
- `session_num`, `chat_type`, `hello`, `tips`, `knowledge`, `prompt`
- `service_type`, `service_config`, `owner`, `expand`

`ChatLog` stores the query, answer, feedback, answer status, answer cost, and error message.

## Service configuration contract

The chat service config may describe either:

1. an OpenAI-compatible service, with URL, headers, data, stream behavior, and before/after transforms
2. an AIHub-style service, with a request URL, prompt-shaped data payload, output type, request count, and streaming flag

The knowledge config may point to a file or API-based knowledge source and optionally include upload and recall URLs.

## User-visible behavior

- AIHub cards can be visually grouped by domain such as computer vision, audio, language, multimodal, and large models.
- A paid / commercial card may show reduced actions in the UI.
- The chat view can clone an existing chat scenario and preserve the original prompt/service setup.
- Chat histories are meant for inspection and prompt iteration rather than a raw model-backend API.

## Native evidence

- `view_aihub.py` defines the category routes and card rendering behavior.
- `model_aihub.py` defines the AIHub record schema.
- `view_chat.py` defines the chat view, prompt templates, service config shape, and request helpers.
- `model_chat.py` defines the persistent chat/chat-log schema.
- `init-aihub.json` and `init-chat.json` seed the catalog and chat examples.
