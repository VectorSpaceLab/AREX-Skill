# Available functions

This page summarizes the helper API exposed by the AirSim sample wrapper.

## Wrapper methods

| Method | Purpose | Notes |
| --- | --- | --- |
| `takeoff()` | Command the drone to take off | Joins the asynchronous AirSim call |
| `land()` | Command the drone to land | Joins the asynchronous AirSim call |
| `get_drone_position()` | Return the drone's current XYZ position | Uses the simulator pose directly |
| `fly_to(point)` | Fly to a target XYZ position | The wrapper flips positive human-facing Z values into the AirSim coordinate convention before calling AirSim |
| `fly_path(points)` | Fly a list of XYZ waypoints | Each point is converted into an AirSim vector before path execution |
| `set_yaw(yaw)` | Set the drone yaw in degrees | Joins the AirSim rotation command |
| `get_yaw()` | Return the drone yaw in degrees | Reads the simulator pose orientation |
| `get_position(object_name)` | Return a named object's XYZ position | Uses a built-in object-name map and resolves the first matching scene object |

## Object names from the sample prompt contract

The sample prompt contract names a fixed object set in the scene and expects those names to be used exactly. The scene names in the repository evidence are:

- `turbine1`
- `turbine2`
- `solarpanels`
- `car`
- `crowd`
- `tower1`
- `tower2`
- `tower3`

## Coordinate conventions

The human-facing prompt contract explains motion in the following terms:

- forward means positive X
- right means positive Y
- up means positive Z

The wrapper then converts the human-facing Z sign into the AirSim movement convention. When you describe the motion to a user, keep the human-facing convention explicit; when you reason about the wrapper internals, remember the conversion exists.

## Why this matters

- The prompt should never invent helper functions that are not in the wrapper.
- The prompt should ask for clarification when the user names a duplicated object type.
- A future agent should know when a user-facing description is about motion in the prompt and when it is about the wrapper's internal coordinate conversion.

## When to read this file

Read this file when a user asks what the drone can do, how a movement command is interpreted, or why a particular object reference or coordinate sign is required.
