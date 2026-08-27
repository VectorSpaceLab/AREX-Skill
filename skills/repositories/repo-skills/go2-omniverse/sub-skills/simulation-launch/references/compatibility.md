# Version and compatibility matrix

| Route | Python | Isaac stack | ROS runtime | Status |
|---|---:|---|---|---|
| Modern launcher | 3.11 | Isaac Sim 5.0.0.0 + IsaacLab 0.54.3 | bundled Jazzy + Fast DDS | documented primary; IsaacLab package unavailable during creation |
| Humble launcher | 3.12 per source comments | Isaac Sim 6.0 + IsaacLab 4.5.22 | bundled Humble + Fast DDS | documented optional; not prepared or boot-verified |
| Legacy upstream track | repository docs describe Ubuntu 22.04, Isaac Sim 2023.1.1, Orbit 0.3.0, ROS 2 Humble | legacy Orbit/Isaac installation | system/legacy setup | compatibility documentation only |

The modern route deliberately avoids sourcing system Jazzy because system
Python and Isaac's Python ABI differ. The launcher also avoids enabling the
ROS bridge extension in-process when direct `rclpy` publishing is used, because
duplicate typesupport loading was observed in the source project's port.

A successful `torch.cuda.is_available()` check only proves framework/device
availability. It does not prove IsaacLab task registration, extension loading,
checkpoint compatibility, or stable simulation.
