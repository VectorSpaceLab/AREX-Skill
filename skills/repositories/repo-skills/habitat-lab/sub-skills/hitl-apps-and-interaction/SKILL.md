---
name: hitl-apps-and-interaction
description: "Reason about Habitat-HITL realtime apps, viewers, interaction
  services, networking, policy integration, and graphics troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Habitat-HITL Apps and Interaction

Use this sub-skill when a task involves Habitat-HITL realtime human interaction applications: desktop viewers, VR or web clients, app/session services, GUI input and drawing, remote-client messages, controller helpers, policy inference inside interactive loops, or graphics/network troubleshooting.

## Start Here

- Read [HITL workflows](references/hitl-workflows.md) to choose between a safe probe, a headed desktop app, a headless service, a web/VR server, or a custom `AppState`.
- Read [API reference](references/api-reference.md) for `hitl_main`, `AppState`, `AppService`, input/drawing/message helpers, controller helpers, and policy boundaries.
- Read [Troubleshooting](references/troubleshooting.md) before launching full apps on headless, remote, containerized, or graphics-constrained systems.
- Run [hitl_config_probe.py](scripts/hitl_config_probe.py) for import/config checks that avoid opening windows, creating Habitat environments, or starting network servers.

## Routing Rules

- Use this sub-skill for `habitat_hitl`, `hitl_main`, GUI window/input/drawer/text/UI helpers, remote-client/websocket services, VR interaction, and HITL app state/session structure.
- Use `tasks-datasets-and-envs` for core Habitat `Env`, task, dataset, simulator, and episode semantics outside realtime HITL app orchestration.
- Use `baselines-training-and-evaluation` for training, evaluation jobs, checkpoints, PPO/DDPPO configuration, and non-HITL policy workflows.
- Use `setup-and-configuration` for installation, package extras, Habitat-Sim build choices, data download basics, and Hydra configuration fundamentals.
- Use `extension-patterns` for general extension authoring patterns that are not specifically HITL app interaction.

## Safe Operating Posture

- Prefer the bundled probe script when the user asks whether HITL is installed, whether a module imports, or whether a config looks like a HITL config.
- Treat full viewers, rearrange apps, VR clients, and websocket servers as side-effectful: they may need a display, OpenGL/EGL support, Habitat-Sim with Bullet, datasets, free ports, and sometimes baseline policy dependencies.
- Do not call `hitl_main` as a diagnostic unless the user explicitly wants to launch a HITL runtime and the environment is prepared for graphics or a deliberate headless service run.
- Keep app-specific launch commands in the user's working project context; this skill provides decision logic and safe probes rather than bundled full viewer or VR launchers.
