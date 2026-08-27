# Hardware And Control Recipes

Use these recipes to turn Mycodo concepts into safe environmental-control plans.
They are patterns, not permission to mutate a live system. Ask before changing
hardware, credentials, Outputs, services, or system state.

## General Preflight For Any Recipe

1. Identify the controlled variable, acceptable range, failure state, and maximum
   safe actuation.
2. Confirm the Input measurement, units, Period, calibration status, and Max Age.
3. Confirm the Output channel, type, electrical interface, load rating, startup
   state, shutdown state, and manual override/failsafe.
4. Create Live Measurements and a Dashboard graph before enabling closed-loop
   control.
5. Test the Output with a short supervised command and the real load disconnected
   or in a harmless state when possible.
6. Activate the controller at conservative limits and watch at least one full
   response cycle.
7. Add notes for wiring changes, calibration values, PID gains, Method edits,
   and manual interventions.

## Recipe: Temperature Chamber With Heater And Cooler

**Goal**: hold air temperature near a setpoint with separate heat and cooling
Outputs.

**Components**:

- Input: a temperature sensor with reliable sampling Period and units.
- Outputs: one On/Off heater relay and one On/Off cooler relay, or PWM-capable
  devices if proportional modulation is required.
- Function: PID with direction `Both` or Bang-Bang On/Off with direction `Both`.
- Dashboard: graph temperature, PID setpoint, setpoint band, Output duration or
  duty cycle, and heater/cooler state.

**PID path**:

1. Add and activate the temperature Input; confirm InfluxDB data.
2. Add heater and cooler Outputs. Set heater/cooler safe startup and shutdown to
   Off unless hardware failsafe demands otherwise.
3. Add PID. Select the temperature measurement, `Direction = Both`, conservative
   Period, and Max Age slightly longer than the Input Period plus expected delay.
4. Set Setpoint and optional Band. Start with Kp-only, then tune Ki and Kd after
   observing stable response.
5. Assign Raise Output to heater and Lower Output to cooler.
6. Configure Min Off Duration for compressors, fridges, pumps, or anything that
   must not rapid-cycle.
7. Use Dashboard and notes to record changes. If oscillation grows or output
   saturates, deactivate and retune.

**When to choose Bang-Bang instead**: use Bang-Bang if the system tolerates a
hysteresis band and device protection is more important than tight regulation.

## Recipe: Humidity Sampling With Purge Fan Or Pump

**Goal**: sample a sensor only after air has been drawn across it.

**Components**:

- Input: humidity/temperature sensor.
- Output: fan or pump used as `Pre Output`.
- Optional Output: sensor power switch as `Power Output` for recovery.

**Configuration**:

1. Add the fan/pump Output. Test a short duration and verify flow direction.
2. Add the sensor Input. Configure normal interface and units.
3. Set `Pre Output` to the fan/pump Output and `Pre Output Duration` long enough
   to purge the measurement chamber.
4. Decide whether `Pre Output During Measurement` should stay on. If flow heats
   or cools the sensor, turn it off before acquisition.
5. If the sensor occasionally locks up, wire a low-current sensor power switch
   and assign it as `Power Output`. Confirm warm-up time and avoid switching
   high-current devices from sensor-power logic.
6. Set Function/Widget Max Age to account for Period plus purge duration.

**Failure guard**: if repeated acquisition errors trigger power cycling, first
samples after power-up may be invalid. Require observation before using this
measurement in PID.

## Recipe: Fan Speed Or Light Dimming With PWM

**Goal**: drive a fan, dimmer, LED, or similar load with duty cycle.

**Components**:

- Output: PWM GPIO, PCA9685, MQTT PWM, shell/Python PWM, or vendor-specific PWM.
- Function: PID PWM output, Bang-Bang PWM, Output PWM Action, PID Controller
  Widget, or PWM Slider Widget.

**Configuration**:

1. Confirm whether the load expects low-frequency switching, kHz PWM, hardware
   PWM, or an external PWM driver.
2. For non-hardware GPIO PWM, use one of Mycodo's supported frequencies:
   40000, 20000, 10000, 8000, 5000, 4000, 2500, 2000, 1600, 1250, 1000, 800,
   500, 400, 250, 200, 100, or 50 Hz. Other values are rounded to the nearest
   supported frequency.
3. For hardware PWM, choose a hardware-capable BCM pin and account for shared PWM
   channels. Pins on the same channel share the latest frequency/duty settings.
4. Avoid NeoPixel/hardware-PWM conflicts. NeoPixel WS2812 control can use
   hardware PWM0 and can conflict with other hardware PWM outputs.
5. Configure `Startup State`, `Startup Value`, `Shutdown State`, and `Shutdown
   Value`. Fans often need a nonzero minimum duty to start; lights may need 0%
   at shutdown.
6. Use a Dashboard PWM Slider for supervised manual testing, then bound PID or
   Bang-Bang duty cycle limits.

**Energy caveat**: Mycodo duration-based energy estimates do not include PWM
Outputs. Use an amp-measuring Input/Function for energy reporting if PWM loads
matter.

## Recipe: Peristaltic Pump Dosing

**Goal**: dispense a known volume of liquid for nutrients, pH adjustment, EC
control, or irrigation.

**Components**:

- Output: generic pump, Atlas Scientific pump, motor-driver pump, or expander
  pump module.
- Input/Function: pH, EC, flow, reservoir level, or other safeguard.
- Function: Conditional, Bang-Bang, pH/EC regulation Function, or PID volume
  Output depending on process requirements.

**Configuration**:

1. Purge air from tubing and prime the pump.
2. Run a known duration into a measuring cylinder. Calculate `Fastest Rate
   (ml/min)` and enter it.
3. If using `Specify Flow Rate`, set Desired Flow Rate and Minimum On time.
4. Set conservative maximum volume per actuation and require long mixing delays
   before re-measuring pH/EC.
5. Use Max Age on pH/EC measurements; never dose from missing or stale readings.
6. Add notes for reagent concentration, tube changes, calibration, and pump
   rate changes.

**Stop conditions**: stop for manual review if pH/EC readings disagree with a
reference meter, the reservoir level is unknown, a pump runs dry, a valve leaks,
or network/API credentials would be needed for actuation.

## Recipe: pH And Electrical Conductivity Regulation

**Goal**: regulate pH and EC using measurements and dosing pumps.

**Pattern**:

- Use pH and EC Inputs with temperature compensation when available.
- Use calibrated pump Outputs for pH up/down, nutrient, dilution, or water.
- Use Mycodo's pH/EC regulation Function or explicit Conditional logic.
- Set danger ranges, Max Age values, e-mail timers, and mixing delays.
- Include Actions for notes/logs/e-mails rather than silent dosing.

**Safety guidance**:

- Dose in small volumes with enough time to mix and re-measure.
- Use independent reservoir-level protection.
- Avoid overlapping pH and EC corrections unless the chemical process is known.
- Do not rely on uncalibrated probes or stale temperature compensation.

## Recipe: TTN Or MQTT Measurement Ingestion

**Goal**: ingest remote measurements for Dashboard and control.

**TTN**:

1. Enable Data Storage integration in the TTN application.
2. Decode payload into variable names that match Mycodo channel `Variable Name`.
3. Configure Application ID, API key, Device ID, number of measurements, and
   measurement units.
4. On first activation, expect Mycodo to download stored history; later runs
   continue from the latest known timestamp.

**MQTT**:

1. Choose value payload or JSON payload Input based on broker topic format.
2. Record topic, payload path/key, units, and expected update interval.
3. Set Max Age and Dashboard Widget age longer than expected network jitter.
4. Treat MQTT credentials and broker URLs as secrets.

**Control warning**: do not close a fast feedback loop over unreliable network
measurements unless stale-data behavior is explicitly safe.

## Recipe: Output-MQTT Or Remote Mycodo Actuation

**Goal**: control another system from Mycodo.

- MQTT Publish Outputs can represent On/Off, PWM, or Value outputs.
- Remote Mycodo Outputs bridge to another Mycodo instance.
- Retained MQTT messages and remote startup state can surprise downstream
  devices; design topics and retain flags intentionally.
- Confirm feedback: an Output state in Mycodo may represent the last command,
  not the true remote device state.
- Add a Dashboard indicator backed by a measurement or status Input when actual
  remote state matters.

## Recipe: Camera Capture With Actions And Widgets

**Goal**: capture stills, stream video, or attach photos to notifications.

- Configure the camera under `More -> Camera` first.
- Supported acquisition libraries include Raspberry Pi camera libraries,
  fswebcam, OpenCV, urllib, and requests depending on camera type.
- Add a Camera Widget to Dashboard for visibility.
- Use Camera Actions to capture photos, e-mail photos, or pause/resume
  time-lapse from Conditional/Trigger logic.
- Stop before changing camera device permissions, kernel modules, libcamera,
  rpicam, USB, or network camera credentials.

## Recipe: Energy Reporting

**Duration-based method**:

1. Configure `Current Draw (amps)` on each relevant Output.
2. Ensure voltage/cost settings are correct in the system settings.
3. Use energy pages/reports for approximate kWh/cost from on-duration.
4. Remember PWM Outputs are not included in this method.

**Measured-amps method**:

1. Add an Input or Function that measures amps, such as an ADC attached to a
   current transformer.
2. Configure conversion range and units so measurements are in amps.
3. Select the amp measurement on the Energy Usage page.
4. Use a Period fast enough for expected load changes; missing intervals reduce
   accuracy.

## Recipe: Notes For Tuning And Traceability

Use notes whenever a human changes the system:

- Create tags such as `calibration`, `pid`, `wiring`, `pump-rate`, `sensor-swap`,
  `outage`, and `manual-dose`.
- Use custom date/time for historical events.
- Attach calibration files, photos, or logs only when safe for storage.
- Display note tags on graphs to correlate behavior changes with interventions.

## Dry-Run Strategy

- Replace a dangerous Output with a harmless indicator Output, low-voltage LED,
  test relay, or MQTT/log Action while developing Conditional/PID/Trigger logic.
- Use Dashboard Widgets and notes to confirm state transitions.
- For PID, use conservative limits and a short observation period before
  increasing authority.
- For pumps, collect into a container before connecting process tubing.
- For command Outputs, echo to a log file first and only then substitute the real
  command after review.

## When To Stop And Ask

Stop and ask before:

- Activating heaters, pumps, dosing, motors, mains relays, solenoids, RF relays,
  or unknown remote Outputs.
- Changing GPIO/I2C/UART/SPI/1-Wire/Bluetooth/camera configuration or wiring.
- Installing optional dependencies, enabling kernel interfaces, or changing
  system services.
- Using credentials for TTN, MQTT, e-mail, webhook, remote Mycodo, or IP cameras.
- Running system restart/shutdown Actions or command Outputs with destructive
  shell/Python code.
