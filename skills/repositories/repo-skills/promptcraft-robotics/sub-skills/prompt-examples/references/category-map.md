# Example category map

This page helps future agents choose the right example family quickly.

## Aerial robotics

**Representative files**
- `airsim_obstacleavoidance.md`
- `airsim_solarpanel_inspection.md`
- `airsim_turbine_inspection.md`
- `tello_example.md`

**Typical user asks**
- inspect turbines, panels, or other scenes from a drone;
- fly in a lawnmower pattern;
- step around obstacles and reorient toward a goal;
- use a drone or Tello-style prompt with object location and heading.

**Signals**
- drone, yaw, fly_to, fly_path, inspection, obstacle avoidance, solar panels, turbines, Tello, altitude, clearance.

## Embodied agents

**Representative files**
- `airsim_objectnavigation.md`
- `visual_language_navigation_1.md`
- `visual_language_navigation_2.md`

**Typical user asks**
- search for an object with camera perception;
- turn and move toward visible items;
- answer with a command at each step;
- use object detection or a scene list to navigate.

**Signals**
- get_image, detect_objects, forward, turn_left, turn_right, object search, waypoint-like motion, turn/move traces.

## Manipulation

**Representative files**
- `manipulation_zeroshot.md`
- `pick_stack_msft_logo.md`

**Typical user asks**
- pick up a block and place it into a bin;
- stack blocks in a specific order;
- push an object toward a hole;
- build a shape or logo from colored blocks.

**Signals**
- move_to, grab, release, open_gripper, close_gripper, safe heights, top-down placement, block stacking, bin placement.

## Multiple robots

**Representative files**
- `multiple_robots.md`

**Typical user asks**
- reason about an embodied agent, a car, and a drone at the same time;
- choose the correct movement primitive for each robot;
- explain differing coordinate and motion constraints.

**Signals**
- move_forward, turn_left, set_velocity, set_steering_angle, set_height, set_pitch, set_roll, get_position, multi-agent comparison.

## Spatial-temporal reasoning

**Representative files**
- `visual_servoing_basketball.md`

**Typical user asks**
- describe visual servoing from a camera view;
- generate an SVG that depicts where an object appears in the image;
- explain motion as a function of image-space error.

**Signals**
- get_image, get_location, move_by_velocity, move_to_point, orange blob, SVG, image center, tracking, servoing.

## Basic robotics

**Representative files**
- `problems.md`

**Typical user asks**
- solve a generic controller or coordinate-transform problem;
- explain a robot-car, drone, or plate-balancing controller;
- reason about kinematics, transforms, or simple control loops.

**Signals**
- transform matrices, controller design, coordinate conventions, reactive control, proportional control, world/vehicle/camera frames.

## How to use this map

Pick the category that matches the robot, the task family, and the expected function set. If the user request spans multiple categories, choose the most specific family first and then cross-reference the others.
