# Web UI Basics

## What it is

The OpenSquilla Web UI is the local control console served by the gateway.
Use it for setup, chat sessions, approvals, channels, logs, agents, usage, and health views.

## How to open it

Start the gateway, then visit:

```text
http://127.0.0.1:18791/control/
```

If the gateway is not running, the Web UI will not load.

## What the user should expect

The Web UI is the same surface the gateway serves locally, so it inherits the gateway bind and port.
A healthy first run usually means:

- the setup sections are visible
- the Health view reports readiness
- the Control UI can start a chat session
- the logs and approvals panes load without errors

## Release vs source behavior

Official release wheels, desktop installers, and container images already include the built Vue console.
They do not require Node.js or npm on the user's machine.

A Git checkout contains the Web UI source instead of a committed build tree.
Source installs therefore need the console build step:

```sh
cd opensquilla-webui
npm ci
npm run build
```

If a source checkout has a missing or stale console artifact, rebuild it before starting the gateway or building a wheel.
If the user only wants the normal release experience, reinstall from the official release wheel instead of debugging the checkout build.

## Safe access notes

The Web UI is local by default because the gateway binds to loopback.
If the gateway is intentionally exposed beyond localhost, protect the gateway first; the Web UI is only as safe as the gateway behind it.
