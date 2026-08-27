# Artifact previews and presentation

## Web UI presentation

- The Web UI is the gateway-served local control console for chat, sessions,
  approvals, logs, agents, usage, and settings.
- Chat sessions render streaming assistant output, tool cards, reasoning and
  status detail, a conversation sidebar, deliverables, and artifact cards.
- Artifact cards can show thumbnails and preview metadata when the artifact is
  previewable.
- HTML artifact previews can run in full-network or offline mode.
- Remote Web UI sessions are forced offline.
- Ordinary web links still open in a separate browser tab with
  `noopener,noreferrer`.

## Desktop preview surface

- The Desktop preview is browser-like, not a privileged Electron webview.
- Each open preview gets its own temporary session partition.
- The preview surface does not receive Node, preload, IPC, host filesystem, or
  OpenSquilla identity access.
- `contextIsolation: true`, `nodeIntegration: false`, `sandbox: true`, and
  `webSecurity: true` are part of the contract.
- The preview keeps the active OpenSquilla Gateway out of the isolated surface.
- `open-external` is the supported escape hatch for ordinary HTTP(S) links.

## Native Workbench kinds

- `artifact-preview` carries a launch URL, expected origin, scope id, and
  preview mode.
- `url-preview` carries a plain HTTP(S) URL for the isolated browser surface.
- The preview modes are `full` and `offline`.
- `OPENSQUILLA_PREVIEW_FORCE_OFFLINE=1` forces offline previews when you need a
  security override.

## Recovery posture

- If a preview is blank, blocked, or missing resources, check whether the
  surface is offline, whether the resource exists, and whether the browser is
  being asked to load a privileged gateway URL.
- If a link should leave the preview, use the explicit external-open action or
  the system browser instead of trying to tunnel through the preview surface.
