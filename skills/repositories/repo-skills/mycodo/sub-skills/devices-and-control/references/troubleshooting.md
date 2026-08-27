# Troubleshooting Devices And Control

Use this reference when a Mycodo control workflow does not behave as expected.
Start with read-only observation: web UI status, Dashboard, Live Measurements,
controller state, daemon log, and configuration values. Stop before hardware,
credentials, network, or service mutation unless the user explicitly approves.

## Quick Triage Order

1. Is the Mycodo daemon running and is the web UI connected to the intended host?
2. Is the controller active? Inputs and Functions do not acquire/control while
   inactive; Input Commands only run while the Input is active.
3. Is recent data in InfluxDB? Check Live Measurements and a graph before
   debugging downstream control.
4. Are IDs and channels correct? Output and Action overrides often need exact
   unique IDs and zero-based channel numbers.
5. Are Max Age values longer than the relevant Period, network latency, Pre
   Output duration, and sensor warm-up time?
6. Are startup/shutdown states and hardware failsafes consistent with the user's
   safety expectation?

## Symptoms And Recovery

| Symptom | Likely causes | Concrete recovery | Stop/ask when |
|---|---|---|---|
| Live Measurements empty | Input inactive, failed sensor init, missing dependency, wrong bus/address/pin, InfluxDB not receiving data | Activate Input; re-save settings; confirm interface fields; use `Acquire Measurements Now`; inspect daemon log; lengthen Period for slow sensors | GPIO/I2C/UART/1-Wire/Bluetooth setup, dependency install, service repair, or wiring changes are needed |
| Widget shows `NO DATA` or `TOO OLD` | No recent InfluxDB point, Widget Max Age too short, controller inactive, measurement ID changed | Confirm measurement in Live Measurements; increase Widget Max Age above Input/Function Period; reselect measurement/channel | Database/service mutation or data deletion is proposed |
| Conditional comparison errors | `self.condition()` returned `None`, Python indentation error, Timeout too low, code branch references wrong ID | Add `if value is None` guard; fix four-space indentation; increase Timeout and Period; verify Condition/Action IDs | Code would actuate hardware, run commands, or use secrets |
| PID does not actuate | PID inactive/paused, measurement older than Max Age, wrong direction, no Output selected, Output min threshold too high, Output not set up | Resume/activate PID; reduce Input Period or increase Max Age; check Raise/Lower mapping; lower min duration/duty/amount for test; inspect daemon log | Activating heater/cooler/pump/motor or changing wiring is required |
| PID oscillates or overshoots | Kp/Ki/Kd too aggressive, Period too short/long, actuator too powerful, sensor lag, no hysteresis/band, output saturation | Return to Kp-only; reduce gains; add Band; increase Period; bound max duration/duty/volume; add Min Off Duration; use Dashboard graph and notes | Process can overheat, flood, overdose, or otherwise become unsafe |
| PID Autotune never finishes | System unstable, noise band/outstep unsuitable, output cannot cross setpoint, disturbances too large | Stop autotune; choose conservative setpoint/noise/outstep; isolate disturbances; tune manually if needed | Repeated perturbation may damage process or device |
| Bang-Bang chatters | Hysteresis too small, measurement noise, Period too short, output min-off not enforced | Increase hysteresis; smooth/average measurement; increase Period; enforce Min Off Duration or Conditional state guard | Mechanical relay/compressor/pump is rapid-cycling |
| Trigger timer missed | Controller inactive, wrong time format/timezone, Start/End span wrong, Period longer than window, Method not selected | Verify active state; use 24-hour `HH:MM`; check timezone; correct Start/End/Period; reselect Method | System clock/timezone/service changes are required |
| Output won't turn on/off | Output inactive/not set up, wrong channel, On State inverted, min-off still active, startup/shutdown restored state, remote state mismatch | Test short supervised duration; verify channel; check On State wiring; wait min-off; inspect Output status and daemon log | Live actuator controls heat, pumps, mains voltage, dosing, movement, or unknown remote devices |
| Output state appears wrong | Wireless/command/MQTT Outputs may track last command, not real state; external remote changed state | Add feedback Input or status measurement; do not trust command-only state; reconcile remote device manually | Physical state affects safety |
| PWM frequency not as entered | Non-hardware PWM rounded to supported list; wrong library; hardware channel shared; unsupported pin | Use supported frequency list; choose hardware-capable pin; avoid shared-channel conflict; verify with meter/scope if safe | Changing GPIO wiring, PWM channel, or load connection is needed |
| PWM causes daemon/Pi instability | NeoPixel/hardware PWM conflict, excessive frequency/load, bad driver wiring | Deactivate conflicting Outputs; move NeoPixel or PWM to separate safe library/channel; use external driver | System becomes unresponsive or needs power cycling |
| Pump dispenses wrong volume | Air in tubing, Fastest Rate inaccurate, switching AC side delay, worn tube, minimum run too low, backpressure | Prime/purge; recalibrate ml/min; switch DC side when appropriate; increase minimum on; collect test dose | Chemicals, reservoir level, or process safety is uncertain |
| pH/EC regulation behaves badly | Probe uncalibrated, stale temp compensation, mixing delay too short, overlapping corrections, pump rate wrong | Calibrate probes; increase Max Age discipline; add mixing delay; dose smaller; add notes/log/e-mail | Independent meter disagrees, reservoir state unknown, or dosing could harm organisms/process |
| Pre Output sample wrong | Purge duration too short/long, Pre Output perturbs sensor, power cycle warm-up missing | Adjust Pre Output Duration; toggle During Measurement; discard/wait after power cycling; increase Period/Max Age | Pump/fan/valve wiring or load behavior is unverified |
| Command Output unsafe/failing | Wrong execute-as user, missing environment/path, command string lacks `((duty_cycle))`, untrusted input, secret leakage | Replace command with harmless echo/log; add full paths; include `((duty_cycle))` for PWM; remove secrets; review permissions | Command can modify files/services, reveal secrets, or run external input |
| MQTT/TTN data missing | Broker/API credentials, topic/payload mismatch, TTN decoder variable names wrong, network/API outage, retained message surprise | Verify credentials with user; inspect topic/payload shape; align variable names; increase Max Age; add status notes | Credentials must be revealed or network/firewall changes are needed |
| Camera capture fails | Camera not configured, unsupported library, permissions, no device, IP camera URL/auth, OpenCV/libcamera missing | Verify camera page settings; test with harmless still capture; check daemon log; choose correct library | Enabling camera interfaces, installing packages, changing USB/IP credentials, or system permissions is needed |
| Energy report inaccurate | Output amps unset, voltage/cost wrong, PWM load used with duration method, missing amp measurements, Period too slow | Set current draw; verify settings; use amp-measurement method for PWM; shorten measurement Period; document assumptions | Electrical measurements or current-transformer wiring are needed |
| Notes absent from graph | No tag selected, time range mismatch, custom date/time wrong, graph tag display not enabled | Ensure note has tag; select tag on graph; check time range/timezone | Attachments contain private data or need deletion |

## PID-Specific Checks

- `Max Age` should be greater than the Input Period plus communication and Pre
  Output delays, but low enough to prevent stale actuation.
- If a measurement is missing within Max Age, PID should not actuate. Do not
  bypass this with an overlarge Max Age unless a stale measurement is safe.
- `Direction` must match physics: `Raise` if the Output increases the measured
  value, `Lower` if it decreases it, `Both` if separate raise/lower actuators
  exist.
- For On/Off duration Outputs, check Min/Max On Duration and Min Off Duration.
- For PWM Outputs, check Min/Max Duty Cycle and `Always Min`.
- For volume/value Outputs, check Min/Max Amount and process safety.
- Use `Pause` for temporary no-actuation tuning and `Hold` only when continuing
  current output behavior is intentional.

## Conditional And Trigger Checks

- Confirm each Condition and Action ID from the live controller section, not the
  target Input/Output/PID ID.
- Every numeric comparison must handle `None`.
- `Period` must exceed worst-case code runtime; `Timeout` must exceed code
  runtime and network calls if any.
- Avoid nested actions that can recursively trigger conflicting controller
  changes.
- For Trigger Output duration events, distinguish `On (any duration)` from exact
  On duration matching.
- For Run PWM Method, confirm the Method is a Duration Method and the Output is a
  PWM Output.

## Optional Dependencies And Hardware Interfaces

Many modules declare optional Python packages, system packages, or vendor
libraries. Symptoms include import errors in the daemon log, setup failures, or
missing module choices. Recovery depends on the installation mode and belongs to
installation operations if packages or services need mutation.

Hardware interface reminders:

- I2C: enable bus, avoid address conflicts, choose correct bus, verify pull-ups.
- UART/FTDI: confirm device path, permissions, baud rate, and exclusive access.
- 1-Wire: confirm kernel interface and sensor serial path.
- GPIO: use BCM numbering unless a module says otherwise; avoid pins reserved by
  other functions; handle relay active-low/high behavior.
- Bluetooth: pair/connect and choose adapter; expect intermittent radio issues.
- Camera: library and device support vary across Raspberry Pi, USB, IP, and URL
  sources.

Stop before changing kernel interfaces, system groups, udev rules, service
files, nginx, InfluxDB, Docker, or installer state.

## Logs And Observation

- Use web UI logs, especially the daemon log, to identify setup, import,
  measurement, and controller errors.
- Add a Dashboard graph for every measurement and actuator variable involved in
  a controller.
- Add notes at each calibration/tuning change. When behavior changes later,
  graph notes make root-cause analysis much faster.
- If an issue only appears after reboot, inspect startup/shutdown Output states,
  Trigger at Startup, controller active flags, and service readiness.

## Verification Limits

This sub-skill was verified through CPU/source and documentation inspection only.
No Raspberry Pi GPIO/I2C/UART/1-Wire/Bluetooth/camera hardware, systemd/nginx,
InfluxDB service, Docker stack, backup/restore, or full installer execution was
run. Require live-system confirmation before treating hardware/service recovery
as proven.
