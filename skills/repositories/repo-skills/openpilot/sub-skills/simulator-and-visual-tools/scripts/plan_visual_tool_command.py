#!/usr/bin/env python3
"""Print a safe command plan for openpilot replay/visual/debug tools."""
from __future__ import annotations

import argparse


TOOLS = {
  "replay": "Route replay and message inspection",
  "cabana": "Raw CAN/DBC viewer",
  "plotjuggler": "Time-series plotting and route visualization",
  "sim": "MetaDrive simulator bridge",
  "joystick": "Keyboard/joystick debug control",
}


def main() -> int:
  parser = argparse.ArgumentParser(description="Plan a finite openpilot visual-tool command with prerequisite notes")
  parser.add_argument("tool", choices=sorted(TOOLS))
  parser.add_argument("--route", help="route or segment identifier")
  parser.add_argument("--demo", action="store_true", help="use the demo route when supported")
  parser.add_argument("--stream", action="store_true")
  parser.add_argument("--layout", help="PlotJuggler layout path or name")
  parser.add_argument("--dbc", help="DBC name or path")
  parser.add_argument("--joystick", action="store_true")
  parser.add_argument("--high-quality", action="store_true")
  parser.add_argument("--dual-camera", action="store_true")
  args = parser.parse_args()

  prereqs = []
  if args.tool in {"replay", "cabana", "plotjuggler"}:
    prereqs.append("route/log access or a demo route")
  if args.tool == "plotjuggler":
    prereqs.append("PlotJuggler binary and GUI/display for real launch")
  if args.tool == "sim":
    prereqs.append("optional metadrive package and simulator display/runtime")
  if args.tool == "joystick":
    prereqs.append("offroad/device-safe debug state and, for network use, a bridge process")
  if args.tool == "cabana":
    prereqs.append("CAN/DBC input or a route with CAN messages")

  print(f"tool: {args.tool} — {TOOLS[args.tool]}")
  if prereqs:
    print("prerequisites:")
    for item in prereqs:
      print(f"- {item}")
  if args.tool == "replay":
    route = args.route or ("--demo" if args.demo else "<route>")
    print(f"example: openpilot/tools/replay/replay {route}")
  elif args.tool == "cabana":
    route = args.route or ("--demo" if args.demo else "<route>")
    extra = f" --dbc {args.dbc}" if args.dbc else ""
    print(f"example: openpilot/tools/cabana/cabana {route}{extra}")
  elif args.tool == "plotjuggler":
    route = args.route or ("--demo" if args.demo else "<route>")
    extra = []
    if args.layout:
      extra += ["--layout", args.layout]
    if args.dbc:
      extra += ["--dbc", args.dbc]
    if args.stream:
      extra.append("--stream")
    print("example: openpilot/tools/plotjuggler/juggle.py " + " ".join(extra + [route]))
  elif args.tool == "sim":
    flags = []
    if args.joystick:
      flags.append("--joystick")
    if args.high_quality:
      flags.append("--high_quality")
    if args.dual_camera:
      flags.append("--dual_camera")
    print("example: openpilot/tools/sim/run_bridge.py " + " ".join(flags))
  else:
    print("example: openpilot/tools/joystick/joystick_control.py --keyboard")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
