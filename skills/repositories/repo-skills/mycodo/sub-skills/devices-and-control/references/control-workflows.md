# Control Workflows

This reference distills how Mycodo pieces fit together for environmental
control. Use it when designing a workflow, reviewing a user's proposed setup, or
explaining which controller type should own a behavior.

## Mental Model

- **Inputs** acquire measurements from sensors, system probes, commands, MQTT,
  weather services, TTN, or other sources. Measurements are stored in InfluxDB.
- **Outputs** actuate devices. An Output can expose one or more channels and one
  or more control types: `on_off`, `pwm`, `volume`, or `value`.
- **Functions** consume Inputs/Function/PID measurements and/or manipulate
  Outputs. Built-in Function families include PID, PID Autotune, Bang-Bang,
  equations, statistics, pH/EC regulation, vapor pressure deficit, displays,
  camera capture, backup, redundancy, and verification.
- **Actions** are attached to Inputs, Conditional, and Trigger controllers to
  run side effects: Output control, PID changes, controller activation, MQTT,
  e-mail, photo, notes, log lines, webhooks, and selected system operations.
- **Widgets** and **Dashboards** display measurements and offer controlled
  manipulation surfaces. Widgets do not replace safe controller configuration;
  they make state visible and provide manual controls.
- **Methods** define time-varying values. PIDs use Methods for Setpoint Tracking;
  Run PWM Method Triggers use Methods for duty cycle over time.
- **Notes** annotate events with timestamps and tags so they can be displayed on
  graphs.

## Measurement And InfluxDB Assumptions

1. A measurement has a measurement name, unit, channel/index, value, and time.
2. Functions and Widgets retrieve measurements from InfluxDB, so a controller
   must be active and writing data before downstream logic can see it.
3. `Max Age` is a safety boundary, not just a display preference. If no recent
   value is within Max Age, Functions and Conditionals should treat the value as
   missing and avoid unsafe actuation.
4. Channel identifiers in source metadata are zero-based. The web UI may show a
   friendly channel label, but automation and Action override examples usually
   expect channel `0`, `1`, etc.
5. When a graph or Widget reports `NO DATA` or `TOO OLD`, first check whether the
   Input/Function is active, whether Period is reasonable, whether InfluxDB has
   data, and whether the Widget's Max Age is long enough for the acquisition
   period.

## Inputs

### Add And Activate

Use `Setup -> Input`. After selecting an Input module:

- Set interface fields such as `Location`, `I2C Address`, `I2C Bus`, `UART
  Device`, `FTDI Device`, `BT Adapter`, `GPIO` BCM pin, `1-Wire` serial, IP
  address, MQTT topic, TTN app/device/API key, or command text.
- Set `Period (seconds)` to match sensor response time and control latency.
- Select measurement units and enabled channels when the module supports them.
- Save, then activate. Input Commands and Input Actions only execute while the
  Input is active.
- Confirm Live Measurements before wiring control Functions to the measurement.

### Input Commands And Actions

Input Commands are functions inside an Input module that can be executed from
the web UI. `Acquire Measurements Now` forces a sample outside the normal Period.
Calibration commands may exist on sensor-specific Inputs. Do not run calibration
or device-reset commands without confirming the sensor and current process state.

After every acquisition Period, Mycodo can execute one or more Actions attached
to the Input. Typical uses are MQTT publish, equation/Python processing, notes,
logs, or notifications. Keep Input Actions short and robust; network or command
failures can delay acquisition.

### Pre Output And Power Output

- `Pre Output` turns on an Output before measurement, waits `Pre Output Duration
  (seconds)`, then takes the sample. Use it for purge pumps, valves, fans, or
  sensor chamber flushing.
- `Pre Output During Measurement` keeps the Pre Output on during acquisition;
  disable it if the device perturbs the measurement.
- `Power Output` selects an Output that powers the sensor. Mycodo can power
  cycle it after consecutive sensor errors. Use only when the circuit was built
  for sensor power switching; relays and transistors can both be appropriate.
- Power cycling a sensor can change warm-up time. Increase Period/Max Age and
  verify first samples after power-up before trusting control decisions.

### TTN, MQTT, Weather, And Command Inputs

TTN Inputs download data from The Things Network Data Storage integration. The
payload decoder must expose variable names that match Mycodo channel `Variable
Name` options. On first activation, the Input can pull stored history; later
runs continue from the latest known timestamp.

MQTT, weather, ping, port, Linux command, and Python-code Inputs have similar
external dependency risks: network, credentials, command safety, and latency.
Never close a fast safety-critical control loop on network data unless stale
and missing values have a safe behavior.

## Outputs

### Output Types

- `on_off`: relay/GPIO/wireless/MQTT/Kasa/shell/Python or other binary control.
  May also support timed on-duration.
- `pwm`: duty cycle from 0-100%, often for fans, dimmers, LEDs, or analog-like
  power control.
- `volume`: pump dispense amount; requires flow-rate calibration and often a
  minimum run duration.
- `value`: arbitrary numeric output such as DAC voltage or MQTT value.

### Startup And Shutdown State

Every actuator should have an explicit startup and shutdown plan:

- `Startup State` can turn an Output on/off, set a user value, restore the last
  duty cycle for PWM, or do nothing depending on module capability.
- `Shutdown State` should drive loads to their safe state unless an external
  failsafe owns safety.
- `Trigger at Startup` can fire Trigger Functions when Mycodo starts and an
  Output's start state is on; use carefully to avoid duplicate actuation after a
  reboot.
- Avoid `Do Nothing` for heaters, pumps, dosing, humidifiers, and motors unless
  hardware interlocks make the state safe.

### On/Off Outputs

On/Off Outputs switch a state. Important options include GPIO pin, On State,
protocol/pulse/bit length for RF devices, command text for command Outputs,
execute-as user, current draw, and startup/shutdown state.

Use `Seconds to turn On` for supervised testing. For devices that dislike rapid
cycling, use PID Min Off Duration, Conditional state checks, or hardware delay
relays.

### PWM Outputs

PWM controls duty cycle at a frequency. Mycodo distinguishes software/any-pin
PWM from hardware PWM:

- Non-hardware PWM accepts a discrete frequency set. Supported frequencies are
  40000, 20000, 10000, 8000, 5000, 4000, 2500, 2000, 1600, 1250, 1000, 800,
  500, 400, 250, 200, 100, and 50 Hz. If another value is entered, the nearest
  supported frequency is used.
- Hardware PWM supports exact frequency selection on hardware-capable pins.
  Common BCM hardware PWM pins are 12/channel 0, 13/channel 1, 18/channel 0,
  and 19/channel 1; compute-module pins 40, 41, 45, 52, and 53 are also listed
  by Mycodo. GPIO sharing the same PWM channel uses the latest frequency and
  duty cycle set on that channel.
- The GPIO PWM module metadata exposes library choices such as `Any Pin, <= 40
  kHz` and `Hardware Pin, <= 30 MHz`.
- NeoPixel WS2812 control can use hardware PWM0; do not combine it with another
  hardware-PWM output on the same channel unless the live system is designed for
  it. A conflict can make the daemon or Raspberry Pi unresponsive.
- PWM duty cycle is not currently used by Mycodo's duration-based energy
  calculation; use measured-amp energy if PWM accuracy matters.

### Volume, Pump, Command, And MQTT Outputs

Volume Outputs dispense liquid or drive pumps:

- Calibrate `Fastest Rate (ml/min)` by purging air, running the pump for a fixed
  duration, measuring collected volume, and entering the result.
- `Specify Flow Rate` uses desired flow rate and may need a `Minimum On` time per
  60-second window.
- Generic pumps usually switch power with GPIO/relay/motor driver. Switch DC
  power rather than AC input when converter latency harms volume accuracy.
- Atlas Scientific EZO-PMP style modules can use I2C/UART commands and can
  dispense specific volume/rate when calibrated.

Command Outputs execute shell or Python code; MQTT Outputs publish topics and
payloads. They are powerful and unsafe by default:

- Never paste secrets into command text, payloads, notes, or logs.
- Confirm the execute-as user and filesystem/network side effects.
- For PWM command Outputs, the command must include `((duty_cycle))` where the
  duty cycle value should be substituted.
- `Force Command` can execute an On command even if Mycodo believes the Output is
  already on; use only when idempotence is proven.
- MQTT remote actuation depends on broker reachability, retained messages,
  topic design, and credentials.

## PID

PID is the main feedback controller for maintaining a measurement setpoint.
Configure it from `Setup -> Function`:

1. Select the measurement being regulated.
2. Choose direction: `Raise`, `Lower`, or `Both`.
3. Set `Period` and `Start Offset`.
4. Set `Max Age` so stale data cannot actuate Outputs.
5. Set `Setpoint` and optional `Band (+/- Setpoint)` hysteresis.
6. Start with conservative Kp/Ki/Kd. A common safe learning pattern is Kp only,
   then gradually add Ki, and only later add Kd.
7. Select Raise/Lower Outputs and output type: duration, PWM, volume, or value.
8. Bound each output with min/max duration, duty cycle, amount, volume, and Min
   Off Duration.
9. Save, activate, and observe graphs over an appropriate time span.

PID output facts:

- Control Variable = P output + I output + D output.
- For duration Outputs, the control variable maps to on-duration within Period.
- For PWM, duty cycle is `(Control Variable / Period) * 100`, then bounded to
  0-100% and the configured Min/Max Duty Cycle.
- `Store Lower as Negative` stores lower-direction output values as negative in
  the measurement database, useful for graphs.
- `Pause` prevents updates and does not actuate Outputs. `Hold` stops updating
  the control variable but continues applying associated Outputs. `Resume`
  restarts from paused/held state.

## PID Autotune And Bang-Bang

PID Autotune is experimental. It perturbs the selected Output and analyzes the
measurement response. Use it only when the live system can be safely driven
above and below the chosen setpoint. Essential options: Measurement, Output,
Period, Setpoint, Noise Band, Outstep, and Direction. Watch Dashboard graphs and
the daemon log; stop if oscillations are unsafe or inconsistent.

Bang-Bang Functions use a setpoint plus hysteresis instead of PID math:

- Raise mode turns output on below `setpoint - hysteresis` and off above
  `setpoint + hysteresis`.
- Lower mode is the inverse.
- Both mode can use raise/lower Outputs or PWM duty cycle choices.
- The PWM variant requires a PWM Output and has duty cycles for increase,
  maintain, decrease, and shutdown.
- Set measurement Max Age for the selected measurement.

## Conditional

Conditional Functions run user Python in the Mycodo environment every Period.
They combine Conditions and Actions:

- Conditions include Measurement (single last), Measurement with timestamp,
  Measurement (single past average/sum), Measurement (multiple past), GPIO
  State, Output State, Output Duration On, and Controller Running.
- Actions attached to the Conditional expose IDs. In code, call
  `self.run_action("ACTION_ID")` or `self.run_all_actions()`.
- Use `self.condition("CONDITION_ID")` for latest scalar values and
  `self.condition_dict("CONDITION_ID")` for multiple past measurements.
- If a measurement is older than Max Age, `None` is returned. Always check for
  `None` before numeric comparisons.
- `Timeout` must exceed the Python code's worst-case runtime. `Period` must be
  longer than runtime to avoid overlapping executions.
- Use `self.logger.info()`, `.warning()`, `.error()`, or `.debug()` for daemon
  log lines. Debug lines require debug logging enabled.
- `self.set_custom_option("key", value)` and `self.get_custom_option("key")`
  persist simple values across runs.

Safe Conditional pattern:

```python
measurement = self.condition("condition_id")
if measurement is None:
    self.logger.warning("measurement missing within Max Age")
elif 20 < measurement < 30:
    self.run_action("action_id")
```

Before activating, review every branch, ensure Python uses four-space indents,
confirm no action conflicts, and dry-run with harmless Outputs or low-risk
settings.

## Trigger

Trigger Functions execute Actions when an event occurs:

- **Output On/Off Trigger**: fires when a selected Output changes to On, Off, or
  On for an exact duration.
- **Output PWM Trigger**: fires when duty cycle is greater than, less than, or
  equal to a configured value.
- **Edge Trigger**: fires on rising, falling, or both GPIO edges.
- **Timer Duration**: fires every Period after activation, with optional Start
  Offset.
- **Daily Time Point**: fires at a specific `HH:MM` daily.
- **Daily Time Span**: fires every Period between `Start Time` and `End Time`.
- **Sunrise/Sunset**: fires at rise/set time with latitude, longitude, zenith,
  date offset, and minute offset.
- **Run PWM Method**: evaluates a Duration Method and applies its duty cycle to a
  selected PWM Output every Period; can Trigger Actions every Period and/or when
  activated.

Use Triggers for events, schedules, and inter-controller glue. Use Conditional
when logic needs multi-measurement Python decisions.

## Methods And Setpoint Tracking

Methods define a value over time:

- `Time/Date`: value across absolute date/time spans.
- `Duration`: stacked durations with start/end setpoints; can repeat for a
  configured duration.
- `Daily (Time-Based)`: repeats every day and should cover only one day.
- `Daily (Sine Wave)`: daily sinusoidal value from amplitude, frequency, angle
  shift, and Y-axis shift.
- `Daily (Bezier Curve)`: daily cubic Bezier curve; useful for natural cycles.
- `Cascade`: averages multiple linked Methods for compound profiles.

PIDs use Methods as Setpoint Tracking. Actions can set a PID Method or raise,
lower, or set PID setpoint directly. Run PWM Method Triggers use Duration
Methods to set a PWM duty cycle profile. Verify clock/timezone, method ordering,
repeat behavior, and what should happen at the end of the Method.

## Actions

Attach Actions to Inputs, Conditional, or Trigger controllers. Built-in Action
families include:

- Output: On/Off/Duration, Duty Cycle, Ramp Duty Cycle, Value, Volume.
- PID: Setpoint set/raise/lower, Pause, Resume, Set Method.
- Controller: Activate or Deactivate Input/Function/PID/Trigger/etc.
- Camera: capture photo, pause/resume time-lapse, e-mail photo.
- MQTT publish, Webhook, Send Email, Create Note, Create daemon log line.
- Display/LED controls, flow-meter total clearing, and selected system restart
  or shutdown operations.

Several Actions accept runtime override dictionaries when executed from code.
Use override values only after validating the target ID and channel on the live
system.

## Widgets, Dashboards, Cameras, Energy, Notes

- `Data -> Live Measurements` shows current Input and Function measurements.
- `Data -> Asynchronous Graphs` loads large time spans in chunks and aggregates
  to around 700 displayed points per view.
- `Data -> Dashboard` can host multiple draggable/resizable Widgets and can be
  locked.
- Useful control Widgets: PID Controller, Output Control (Channel), Output (PWM
  Slider), Activate/Deactivate Controller, Function Status, Indicator,
  Measurement values, Camera, Graph, gauges, Python Code, Spacer.
- Cameras can capture stills, time-lapses, and video streams from Raspberry Pi
  cameras, USB/webcams, IP camera/image URLs, and libraries such as picamera,
  fswebcam, OpenCV, urllib, or requests.
- Energy usage can be estimated from Output on-duration and configured amps, or
  more accurately from an Input/Function measuring amps. PWM Outputs are not
  included in duration-based energy calculation.
- Notes have timestamps, require tags, can attach files, and can be displayed on
  graphs. Use notes to mark calibration, tuning changes, sensor swaps, outages,
  and manual interventions.
