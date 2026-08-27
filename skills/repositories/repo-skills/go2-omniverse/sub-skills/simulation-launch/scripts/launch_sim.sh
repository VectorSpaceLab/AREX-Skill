#!/usr/bin/env bash
set -euo pipefail

# Self-contained launcher adapter for the go2_omniverse runtime.
# It replaces the repository's launcher wiring without depending on the
# adapter's own directory. It never sources host ROS; it requires an explicit
# project root and accepts the normal Isaac AppLauncher arguments after its
# adapter options.

PROJECT_ROOT=""
ISAAC_VENV="${ISAAC_VENV:-}"
ISAACLAB_PATH="${ISAACLAB_PATH:-}"
ROS_DISTRO="${ROS_DISTRO:-jazzy}"
ROBOT="go2"
ROBOT_AMOUNT="1"
TERRAIN="flat"
TWINBOT=0
QUALITY=0
PASSTHROUGH=()

while (($#)); do
  case "$1" in
    --project-root) PROJECT_ROOT="$2"; shift 2;;
    --isaac-venv) ISAAC_VENV="$2"; shift 2;;
    --isaaclab-path) ISAACLAB_PATH="$2"; shift 2;;
    --ros-distro) ROS_DISTRO="$2"; shift 2;;
    --robot) ROBOT="$2"; shift 2;;
    --robot-amount) ROBOT_AMOUNT="$2"; shift 2;;
    --terrain) TERRAIN="$2"; shift 2;;
    --twinbot) TWINBOT=1; shift;;
    --quality) QUALITY=1; shift;;
    --) shift; PASSTHROUGH+=("$@"); break;;
    *) PASSTHROUGH+=("$1"); shift;;
  esac
done

if [[ -z "$PROJECT_ROOT" ]]; then
  echo "error: --project-root is required (the checkout containing main.py)" >&2
  exit 2
fi
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"
[[ -f "$PROJECT_ROOT/main.py" ]] || { echo "error: main.py not found under --project-root" >&2; exit 2; }
[[ -n "$ISAAC_VENV" ]] || { echo "error: pass --isaac-venv or set ISAAC_VENV" >&2; exit 2; }
[[ -x "$ISAAC_VENV/bin/python" ]] || { echo "error: Isaac Python not found under --isaac-venv" >&2; exit 2; }

export OMNI_KIT_ACCEPT_EULA="${OMNI_KIT_ACCEPT_EULA:-YES}"
export ROS_DISTRO
export RMW_IMPLEMENTATION="${RMW_IMPLEMENTATION:-rmw_fastrtps_cpp}"
[[ -n "$ISAACLAB_PATH" ]] && export ISAACLAB_PATH

PYTHON="$ISAAC_VENV/bin/python"
ISAAC_ROS2_EXT="$(ROS_DISTRO="$ROS_DISTRO" "$PYTHON" -c 'import isaacsim, os; base=os.path.dirname(isaacsim.__file__); distro=os.environ["ROS_DISTRO"]; candidates=("isaacsim.ros2.core", "isaacsim.ros2.bridge"); print(next((os.path.join(base,"exts",name) for name in candidates if os.path.isdir(os.path.join(base,"exts",name,distro,"lib"))), ""))')"
[[ -n "$ISAAC_ROS2_EXT" ]] || { echo "error: bundled ROS $ROS_DISTRO extension not found" >&2; exit 1; }
BUNDLED_LIB="$ISAAC_ROS2_EXT/$ROS_DISTRO/lib"
BUNDLED_RCLPY="$ISAAC_ROS2_EXT/$ROS_DISTRO/rclpy"
[[ -d "$BUNDLED_LIB" ]] || { echo "error: bundled ROS library directory missing: $BUNDLED_LIB" >&2; exit 1; }
export PYTHONPATH="$BUNDLED_RCLPY${PYTHONPATH:+:$PYTHONPATH}"
export LD_LIBRARY_PATH="$BUNDLED_LIB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

ARGS=(--robot_amount "$ROBOT_AMOUNT" --robot "$ROBOT" --terrain "$TERRAIN")
(( TWINBOT )) && ARGS+=(--twinbot)
(( QUALITY )) && ARGS+=(--rendering_mode quality)
cd "$PROJECT_ROOT"
exec "$PYTHON" -u main.py "${ARGS[@]}" "${PASSTHROUGH[@]}"
