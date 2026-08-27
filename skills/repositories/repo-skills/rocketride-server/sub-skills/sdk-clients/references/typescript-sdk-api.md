# TypeScript / Node SDK API

This reference is self-contained for the RocketRide TypeScript package
`rocketride` 1.3.0. It covers SDK use from Node.js and browser code. It does
not cover `.pipe` schema design or engine deployment.

## Install and import

```bash
npm install rocketride
# or: pnpm add rocketride / yarn add rocketride
```

```typescript
import { RocketRideClient, Question } from 'rocketride';

const client = new RocketRideClient({
  uri: 'https://api.rocketride.ai',
  auth: process.env.ROCKETRIDE_APIKEY,
});

await client.connect();
const { token } = await client.use({ filepath: './pipeline.pipe' });
try {
  const result = await client.send(token, 'Hello', { name: 'input.txt' }, 'text/plain');
  console.log(result);
} finally {
  await client.terminate(token);
  await client.disconnect();
}
```

## Configuration and environment

```typescript
new RocketRideClient(config?: RocketRideClientConfig)
```

Important `RocketRideClientConfig` properties:

| Property | Use |
| --- | --- |
| `uri` | Base RocketRide URI. The SDK converts it to the WebSocket `/task/service` endpoint. |
| `auth` | Initial API key. If omitted, `connect()` / `login()` can use a credential argument or `env.ROCKETRIDE_APIKEY`. |
| `env` | Environment map used for credential defaults and `${ROCKETRIDE_*}` substitution. If provided, it replaces `process.env`; if omitted in Node, string values are copied from `process.env`. |
| `persist` | Enables automatic reconnect. Reconnect backoff grows by 250 ms to a 15 s cap and continues until stopped. |
| `requestTimeout` | Default request timeout in milliseconds. |
| `maxRetryTime` | Accepted for compatibility, currently ignored by persistent reconnect. |
| `wsPath` | Custom WebSocket path; default is `/task/service`. |
| `module`, `clientName`, `clientVersion` | Client identity for logs/auth metadata. |
| `public` | Public unauthenticated mode; only public commands are valid. |
| `onEvent`, `onConnected`, `onDisconnected`, `onConnectError` | Async lifecycle and event callbacks. |
| `onProtocolMessage`, `onDebugMessage`, `onTrace` | Debug/trace hooks. Values are intended to be credential-redacted; still avoid printing secrets. |

Environment behavior differs from Python:

- The TypeScript SDK does **not** load `.env` files by itself. Start Node with an
  env-file option, preload `dotenv`, or pass `env` explicitly.
- `setEnv(env: Record<string, string>): void` replaces the client environment
  map. `use()` and `validate()` use it for `ROCKETRIDE_*` substitution; `login()`
  consults `ROCKETRIDE_APIKEY` when no explicit credential is supplied.
- Ordinary SDK/CLI auth uses `ROCKETRIDE_APIKEY`. `ROCKETRIDE_AUTH` is common in
  MCP/Cloud examples; copy it to `ROCKETRIDE_APIKEY` or pass it as `auth` for
  TypeScript client code.

## URI and auth handling

Relevant static and connection methods:

```typescript
RocketRideClient.normalizeUri(uri: string): string
RocketRideClient.getServerInfo(uri: string, timeout?: number): Promise<ServerInfoResult>
attach(uri?: string, options?: { timeout?: number }): Promise<void>
detach(): Promise<void>
login(credential?: string | { code: string; verifier: string; redirectUri: string }, options?: { uri?: string; timeout?: number }): Promise<ConnectResult>
logout(): Promise<void>
connect(credential?: string | { code: string; verifier: string; redirectUri: string }, options?: { uri?: string; timeout?: number }): Promise<ConnectResult>
disconnect(): Promise<void>
isAttached(): boolean
isAuthenticated(): boolean
isConnected(): boolean
getConnectionInfo(): { connected: boolean; transport: string; uri: string }
getApiKey(): string | undefined
```

Interpretation:

- `connect()` is the ordinary one-shot attach+login method.
- `attach()` opens an anonymous WebSocket for public calls; `login()`
  authenticates it.
- `isConnected()` is a compatibility alias for attached transport state and does
  not prove authentication. Use `isAuthenticated()` when auth state matters.
- `login()` / `connect()` may receive a plain API key or a PKCE-style
  `{ code, verifier, redirectUri }` object.
- Bare hostnames and non-cloud URIs without ports normalize to port `5565`.
- `https://` and `wss://` normalize to secure `wss://.../task/service`; `http://`,
  `ws://`, and bare hosts normalize to plain `ws://.../task/service`. For Cloud,
  always use `https://...` or `wss://...`.

One-off scripts can use automatic cleanup:

```typescript
await RocketRideClient.withConnection(
  { uri: 'https://api.rocketride.ai', auth: process.env.ROCKETRIDE_APIKEY },
  async (client) => {
    const { token } = await client.use({ filepath: './pipeline.pipe' });
    try {
      return await client.getTaskStatus(token);
    } finally {
      await client.terminate(token);
    }
  },
);
```

## Low-level DAP helpers

```typescript
buildRequest(command: string, options?: { token?: string; arguments?: Record<string, unknown>; data?: Uint8Array | string }): DAPMessage
request(request: DAPMessage, timeout?: number): Promise<DAPMessage>
dapRequest(command: string, args?: Record<string, unknown>, token?: string, timeout?: number): Promise<DAPMessage>
didFail(response: DAPMessage): boolean
call<T = any>(command: string, args?: Record<string, unknown>, options?: { token?: string; timeout?: number }): Promise<T>
tool<T = any>(options: { token: string; tool: string; nodeId?: string; input?: Record<string, unknown>; timeout?: number }): Promise<T>
```

Prefer typed wrappers (`use`, `send`, `validate`, etc.) unless the user needs a
custom server command not covered by the SDK.

## Pipeline execution and token lifecycle

```typescript
validate(options: { pipeline: PipelineConfig | Record<string, unknown>; source?: string }): Promise<ValidationResult>
use(options?: {
  token?: string;
  filepath?: string;
  pipeline?: PipelineConfig;
  source?: string;
  threads?: number;
  useExisting?: boolean;
  args?: string[];
  ttl?: number;
  pipelineTraceLevel?: 'none' | 'metadata' | 'summary' | 'full';
  name?: string;
  env?: Record<string, string>;
}): Promise<Record<string, unknown> & { token: string }>
terminate(token: string): Promise<void>
restart(options: { token?: string; projectId: string; source: string; pipeline: Record<string, unknown>; teamId?: string }): Promise<void>
getTaskStatus(token: string, options?: { timeout?: number | false }): Promise<TASK_STATUS>
getTaskToken(options: { projectId: string; source: string; teamId?: string }): Promise<string | undefined>
getTaskPipeline(token: string): Promise<Record<string, unknown> | undefined>
ping(token?: string): Promise<void>
```

Lifecycle:

1. `use({ filepath })` or `use({ pipeline })` starts a task and returns `token`.
2. Use the token with data operations, chat, events, status, and termination.
3. Call `terminate(token)` for finite scripts.
4. `getTaskStatus(token)` defaults to a bounded 15 s request timeout unless you
   pass `{ timeout: false }`.
5. `getTaskPipeline(token)` returns the unresolved stored pipeline; placeholders
   are not substituted, so secrets are not included.

`use()` details:

- `filepath` is Node-only. Browser bundles cannot load local files; pass a
  pipeline object instead.
- `.pipe` files wrapped as `{ "pipeline": { ... } }` are unwrapped when loaded
  from file.
- If passing an object directly, pass the flat pipeline config, not the wrapper.
- The SDK filters its configured environment to `ROCKETRIDE_*` keys, then merges
  per-call `env` overrides, then sends them for server-side substitution.
- `name` controls display name; when omitted and `filepath` is present, the file
  basename is used.

## Data methods and `DataPipe`

```typescript
pipe(token: string, objinfo: Record<string, unknown> = {}, mimeType?: string, provider?: string,
  onSSE?: (type: string, data: Record<string, unknown>) => Promise<void>): Promise<DataPipe>
send(token: string, data: string | Uint8Array, objinfo: Record<string, unknown> = {}, mimetype?: string,
  onSSE?: (type: string, data: Record<string, unknown>) => Promise<void>): Promise<PIPELINE_RESULT | undefined>
sendFiles(files: Array<{ file: File; objinfo?: Record<string, unknown>; mimetype?: string }>,
  token: string, maxConcurrent?: number): Promise<UPLOAD_RESULT[]>
chat(options: { token: string; question: Question; onSSE?: (type: string, data: Record<string, unknown>) => Promise<void> }): Promise<PIPELINE_RESULT>
setEvents(token: string, eventTypes: string[], pipeId?: number): Promise<void>
```

Choose the method by payload:

| Method | Use when | Notes |
| --- | --- | --- |
| `send` | One string or one `Uint8Array`. | Converts strings with `TextEncoder`, opens/writes/closes a temporary pipe, and returns the pipeline result. |
| `sendFiles` | File objects with optional metadata/MIME. | Results preserve input order. `maxConcurrent` defaults to `5` and must be a positive integer. Progress is emitted as `apaevt_status_upload` through `onEvent`. |
| `pipe` | Large/chunked/incremental data or pipe-scoped SSE. | Returns `DataPipe`; call `open()`, one or more `write(Uint8Array)`, then `close()`. |
| `chat` | A `Question` object sent to a chat-capable task. | Uses MIME `application/rocketride-question` internally. |

`DataPipe` members:

```typescript
constructor(client: RocketRideClient, token: string, objinfo: Record<string, unknown> = {},
  mimeType = 'application/octet-stream', provider?: string,
  onSSE?: (type: string, data: Record<string, unknown>) => Promise<void>)
get isOpened(): boolean
get pipeId(): number | undefined
open(): Promise<DataPipe>
write(buffer: Uint8Array): Promise<void>
close(): Promise<PIPELINE_RESULT | undefined>
tool<T = any>(tool: string, nodeId?: string, input?: Record<string, unknown>): Promise<T>
```

Streaming example:

```typescript
const pipe = await client.pipe(
  token,
  { name: 'large.csv' },
  'text/csv',
  undefined,
  async (type, data) => console.log('SSE', type, data),
);

await pipe.open();
try {
  for (const chunk of chunks) {
    await pipe.write(new TextEncoder().encode(chunk));
  }
  const result = await pipe.close();
  console.log(result);
} catch (err) {
  if (pipe.isOpened) await pipe.close().catch(() => undefined);
  throw err;
}
```

## Services, events, dashboard, profiling, and apps

```typescript
getServices(): Promise<ServicesResponse>
getService(service: string): Promise<ServiceDefinition>
addMonitor(key: { token: string } | { teamId?: string; projectId: string; source: string; pipeId?: number }, types: string[]): Promise<void>
removeMonitor(key, types: string[]): Promise<void>
clearAllMonitors(): Promise<void>
identify(clientName: string): Promise<void>
getDashboard(): Promise<DashboardResponse>
listConnections(req?: ListPageRequest): Promise<ListConnectionsResponse>
listTasks(req?: ListPageRequest): Promise<ListTasksResponse>
cprofileStart(target?: string | null, session?: string): Promise<CProfileStatusResponse>
cprofileStop(target?: string | null): Promise<CProfileStopResponse>
cprofileStatus(target?: string | null): Promise<CProfileStatusResponse>
cprofileReport(target?: string | null): Promise<CProfileReportResponse>
appPublish({ appId, version, bundle, message?, moduleId?, name? }): Promise<RailEntry>
appVersions(appId): Promise<RailEntry[]>
appDeploy(appId, registryVersion, target): Promise<{ deployment, rung }>
appWhere(appId): Promise<Pin[]>
```

Keep dashboard/profiling/app-publish details task-focused; route engine
observability or deployment decisions to the runtime/deployment sub-skill.

## File store methods

All SDK file-store paths are relative to the account store root. Use `''` for
root listing. Do not pass leading `/` or `\\` paths to SDK methods.

```typescript
fsOpen(path: string, mode?: 'r' | 'w'): Promise<{ handle: string; size?: number }>
fsRead(handle: string, offset?: number, length?: number): Promise<Uint8Array>
fsWrite(handle: string, data: Uint8Array): Promise<number>
fsClose(handle: string, mode: 'r' | 'w'): Promise<void>
fsDelete(path: string): Promise<void>
fsListDir(path?: string): Promise<{ entries: Array<{ name: string; type: 'file' | 'dir'; size?: number; modified?: number }>; count: number }>
fsMkdir(path: string): Promise<void>
fsRmdir(path: string, recursive?: boolean): Promise<void>
fsStat(path: string): Promise<{ exists: boolean; type?: 'file' | 'dir'; size?: number; modified?: number }>
fsRename(oldPath: string, newPath: string): Promise<void>
fsGetUrl(path: string, expiresIn?: number, downloadName?: string): Promise<string>
fsReadMany(paths: string[]): Promise<Array<{ path: string; ok: boolean; data?: Uint8Array; error?: string }>>
fsReadString(path: string): Promise<string>
fsWriteString(path: string, text: string): Promise<void>
fsReadJson<T = any>(path: string): Promise<T>
fsWriteJson(path: string, obj: any): Promise<void>
```

`fsGetUrl()` returns a time-limited browser-accessible URL. Pass `downloadName`
when a user needs a stable download filename across Cloud object-store URLs.

## Namespaces

```typescript
client.account
client.billing
client.database
client.deploy
client.log
```

High-value namespace calls:

| Namespace | Methods |
| --- | --- |
| `database` | `query`, `beginTransaction`, `commit`, `rollback`, `dialect` |
| `deploy` | `publish`, `deploy`, `list`, `get`, `versions`, `run`, `artifact`, `history`, `disable`, `enable`, `remove`, `setSchedule`, `setSourceConfig`, `pauseSchedule`, `resumeSchedule`, `preview` |
| `log` | `chapters`, `read`, `segment`, `delete` |
| `account` | profile/org/team/member/API-key/environment-key operations |
| `billing` | billing detail, plans, credit balance/packs where enabled |

## Error classes to recognize

- `AuthenticationException` extends `ConnectionException`; auth failures stop
  automatic auth retries.
- `ConnectionException` covers transport and WebSocket failures.
- `LoginAttemptCancelledError` is a plain `Error` with reason `'superseded'`,
  `'logout'`, or `'detached'` when overlapping lifecycle actions cancel each
  other.
- `PipeException` is raised for pipe open/write/close failures.

For long-lived UIs, do not call `disconnect()` inside `onDisconnected` if
`persist: true`; doing so cancels the reconnect behavior you asked for.
