# Web client reference

Source evidence names: README.md; hugginggpt/README.md; hugginggpt/web/package.json; hugginggpt/web/src/config/index.ts; hugginggpt/web/src/api/hugginggpt.ts; hugginggpt/web/src/api/chatgpt.ts.

The HuggingGPT web client is a Vue 3 + TypeScript + Vite app that talks to the chat API server. It does not start `awesome_chat.py` or the optional local model server by itself.

## NPM scripts

Package scripts in the source web client:

| Script | Command | Use |
|---|---|---|
| `dev` | `vite` | Local development server for the web UI. |
| `build` | `run-p type-check build-only` | Type-check and production build. |
| `preview` | `vite preview --port 4173` | Preview a built Vite app. |
| `build-only` | `vite build` | Production build without type-check wrapper. |
| `type-check` | `vue-tsc --noEmit` | TypeScript/Vue type checking. |
| `e:dev` | build, copy Electron files, install, run Electron dev | Electron-flavored dev path in the source package. |
| `e:build` | build, copy Electron files, install, run Electron build | Electron-flavored build path in the source package. |

Typical UI startup sequence after the chat server is already running:

```bash
cd hugginggpt/web
npm install
npm run dev
```

Future agents should avoid treating web startup as proof that the HuggingGPT API or model execution works. The web app can load while the API base URL is wrong or the backend server is absent.

## Base URLs and constants

Source config constants:

- `HUGGINGGPT_BASE_URL` defaults to `http://localhost:8004`.
- `CHAT_GPT_URL` defaults to `https://api.openai.com`.
- `CHAT_GPT_LLM` defaults to `gpt-3.5-turbo`.
- A source comment says the user can switch to ChatGPT by double-clicking the setting icon.
- A source comment shows a local-development alternative for ChatGPT-compatible endpoints.

When the web browser is on a different machine from the chat server, set `HUGGINGGPT_BASE_URL` to a URL the browser can reach, usually the server machine's LAN host/IP and the `http_listen.port` from the chat config. Do not use the local model-server port for this value; the browser calls the chat API server.

## HuggingGPT API client

The source `hugginggpt(messageList)` function:

- imports `HUGGINGGPT_BASE_URL`;
- posts to `${HUGGINGGPT_BASE_URL}/hugginggpt`;
- sends JSON with `model: "gpt-3.5-turbo"` and `messages: messageList.slice(1)`;
- uses content type `application/json`;
- has a 180-second timeout;
- returns `{status: "success", data: response.data.message}` on success;
- returns `{status: "error", message: error.message}` on failure.

The backend source route ignores the request's `model` field and uses its configured controller model. If a user changes the web model constant and sees no backend change, explain that the chat server config controls HuggingGPT's controller model.

## ChatGPT-only client

The source `chatgpt(messageList, apiKey)` function:

- posts to `${CHAT_GPT_URL}/v1/chat/completions`;
- sends `Authorization: Bearer <apiKey>`;
- sends JSON with `model: CHAT_GPT_LLM` and `messages: messageList`;
- has a 60-second timeout;
- returns the first chat completion message content.

This path is separate from HuggingGPT. It calls a ChatGPT-compatible endpoint directly from the browser flow and does not perform HuggingGPT task planning/model selection/execution.

## CORS and route expectations

The chat API server enables CORS, so browser calls are intended to work when the base URL is reachable. Common mistakes:

- `HUGGINGGPT_BASE_URL` points at the web dev server instead of the chat API server.
- `HUGGINGGPT_BASE_URL` points at the local model-server port instead of `http_listen.port`.
- The chat API server binds to localhost on a remote machine, so another browser cannot reach it even though local curl works.
- A reverse proxy strips POST bodies or blocks CORS preflight.
- The web app is served over HTTPS while the API base URL uses plain HTTP and the browser blocks mixed content.

## Video and ffmpeg note

The source README says video generation requires ffmpeg built with H.264 support. Local `models_server.py` uses an ffmpeg command to transcode generated video to MP4 with `libx264`. If text-to-video returns a path but browser playback fails, distinguish:

- backend model execution failure;
- ffmpeg command missing or built without H.264;
- generated file not under the chat server's static `public/videos` path;
- web base URL pointing to a server that cannot serve the returned `/videos/...` URL.

## Browser-side symptom table

| Symptom | Likely cause | First check |
|---|---|---|
| Web page loads but HuggingGPT replies `Network Error`. | Wrong `HUGGINGGPT_BASE_URL`, backend server not running, CORS/proxy problem, or browser cannot reach host. | Call the same base URL plus `/tasks` from the browser-accessible machine with a tiny JSON payload. |
| Web request times out near 180 seconds. | Backend planning/execution took too long or a model endpoint hung. | Try `/tasks` first, then `/results`, to isolate planning from execution. |
| ChatGPT toggle works but HuggingGPT fails. | Direct ChatGPT route is separate; HuggingGPT API server/config may be broken. | Inspect HuggingGPT config and server logs. |
| HuggingGPT works locally but not from another computer. | Base URL still uses localhost or server bind/firewall prevents access. | Change base URL to reachable host and ensure `http_listen.host` permits remote connections. |
| Returned image/audio/video path gives 404. | Static path belongs to chat server working directory or wrong API host is used to fetch it. | Fetch the path from the same chat API base URL, not from the web dev server. |
