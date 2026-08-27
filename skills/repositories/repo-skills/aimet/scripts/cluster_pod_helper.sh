#!/usr/bin/env bash
# Self-contained AIMET Argo/Kubernetes pod helper.
# It mirrors the repo's scripts/kube launch/sync/stop patterns without assuming
# those source scripts are present in the runtime skill target.
set -euo pipefail

DEFAULT_NAMESPACE="${NAMESPACE:-aihub}"

usage() {
  cat <<'EOF'
Usage:
  cluster_pod_helper.sh preflight [--namespace NS]
  cluster_pod_helper.sh launch [--namespace NS] [--template NAME] [--name WF] [--labels K=V,...]
                              [--wait-step STEP] [--output pod|workflow] [--docker-image IMG]
                              [-c CPU] [-g GPU] [-m MEM] [-p KEY=VALUE] [--timeout-seconds N]
  cluster_pod_helper.sh sync-once --pod POD [--namespace NS] --local-dir DIR --remote-dir DIR
  cluster_pod_helper.sh exec --pod POD [--namespace NS] [--tty] -- COMMAND...
  cluster_pod_helper.sh list [--namespace NS] [--user USER]
  cluster_pod_helper.sh stop [--namespace NS] [--delete] WORKFLOW...

Safety:
  - launch/stop mutate remote cluster state; run them only when the user asked.
  - sync-once excludes .git, build outputs, virtualenvs, and GenAILab artifacts.
  - no credentials are printed; missing auth is reported by kubectl/argo.
EOF
}

fail() { echo "ERROR: $*" >&2; exit 1; }
need_cmd() { command -v "$1" >/dev/null 2>&1 || fail "required command not found: $1"; }

shq() {
  # shell-quote one string for the remote /bin/sh command.
  printf "'%s'" "$(printf "%s" "$1" | sed "s/'/'\\''/g")"
}

preflight() {
  local ns="$DEFAULT_NAMESPACE"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --namespace) ns="$2"; shift 2 ;;
      -h|--help) usage; exit 0 ;;
      *) fail "unknown preflight option: $1" ;;
    esac
  done
  local missing=0
  for cmd in argo kubectl jq tar; do
    if command -v "$cmd" >/dev/null 2>&1; then
      echo "ok: $cmd -> $(command -v "$cmd")"
    else
      echo "missing: $cmd" >&2
      missing=1
    fi
  done
  if [[ "$missing" -ne 0 ]]; then
    exit 1
  fi
  echo "namespace: $ns"
  kubectl config current-context >/dev/null 2>&1 && echo "kube-context: $(kubectl config current-context)" || true
  if kubectl auth whoami >/dev/null 2>&1; then
    kubectl auth whoami
  else
    echo "warning: kubectl auth whoami failed; trying a permissions probe" >&2
  fi
  kubectl auth can-i get pods -n "$ns"
  argo list -n "$ns" --status Running >/dev/null
  echo "preflight passed"
}

launch() {
  local ns="$DEFAULT_NAMESPACE" template="aihub-interactive" wf_name="" labels="" wait_step="" output="pod"
  local cpu="" gpu="" mem="" image="" timeout=900 poll=5
  local -a params=()
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --namespace) ns="$2"; shift 2 ;;
      --template) template="$2"; shift 2 ;;
      --name) wf_name="$2"; shift 2 ;;
      --labels) labels="$2"; shift 2 ;;
      --wait-step) wait_step="$2"; shift 2 ;;
      --output) output="$2"; shift 2 ;;
      --docker-image) image="$2"; shift 2 ;;
      --timeout-seconds) timeout="$2"; shift 2 ;;
      --poll-seconds) poll="$2"; shift 2 ;;
      -c) cpu="$2"; shift 2 ;;
      -g) gpu="$2"; shift 2 ;;
      -m) mem="$2"; shift 2 ;;
      -p) params+=("$2"); shift 2 ;;
      -h|--help) usage; exit 0 ;;
      *) fail "unknown launch option: $1" ;;
    esac
  done
  [[ "$output" == "pod" || "$output" == "workflow" ]] || fail "--output must be pod or workflow"
  need_cmd argo; need_cmd kubectl; need_cmd jq

  local -a argo_args=(--from "workflowtemplate/$template" -n "$ns")
  [[ -n "$wf_name" ]] && argo_args+=(--name "$wf_name")
  if [[ -n "$labels" ]]; then
    argo_args+=(--labels "$labels")
  else
    local username="${USER:-$(whoami)}"
    argo_args+=(--labels "workflows.argoproj.io/creator-email=${username}.at.qualcomm.com,workflows.argoproj.io/creator-preferred-username=${username}")
  fi
  [[ -n "$cpu" ]] && argo_args+=(-p "cpu-request=$cpu")
  [[ -n "$gpu" ]] && argo_args+=(-p "gpu-request=$gpu")
  [[ -n "$mem" ]] && argo_args+=(-p "memory-request=$mem")
  [[ -n "$image" ]] && argo_args+=(-p "docker-image=$image")
  for param in "${params[@]}"; do argo_args+=(-p "$param"); done
  argo_args+=(-o name)

  echo "submitting workflow template=$template namespace=$ns" >&2
  local submitted_wf
  submitted_wf="$(argo submit "${argo_args[@]}")"
  echo "workflow: $submitted_wf" >&2

  local start now wf_status pod="" step_phase=""
  start="$(date +%s)"
  while true; do
    now="$(date +%s)"
    if (( now - start > timeout )); then
      fail "timed out waiting for workflow/pod after ${timeout}s: $submitted_wf"
    fi
    wf_status="$(argo get "$submitted_wf" -n "$ns" -o json 2>/dev/null | jq -r '.status.phase // empty' || true)"
    case "$wf_status" in Failed|Error) argo get "$submitted_wf" -n "$ns" >&2 || true; fail "workflow $submitted_wf status=$wf_status" ;; esac
    if [[ -n "$wait_step" ]]; then
      step_phase="$(argo get "$submitted_wf" -n "$ns" -o json 2>/dev/null | jq -r --arg step "$wait_step" '[.status.nodes // {} | to_entries[] | select(.value.displayName == $step)] | first | .value.phase // "NotStarted"' || true)"
      if [[ "$step_phase" == "Running" ]]; then
        break
      fi
      case "$step_phase" in Failed|Error) argo get "$submitted_wf" -n "$ns" >&2 || true; fail "step $wait_step status=$step_phase" ;; esac
      echo "waiting: workflow=${wf_status:-unknown} step=$wait_step phase=$step_phase" >&2
    else
      pod="$(kubectl get pods -n "$ns" -l "workflows.argoproj.io/workflow=$submitted_wf" --field-selector=status.phase=Running -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' 2>/dev/null | grep -v 'resolve-user-identity' | head -1 || true)"
      [[ -n "$pod" ]] && break
      echo "waiting: workflow=${wf_status:-unknown} no running pod yet" >&2
    fi
    sleep "$poll"
  done

  if [[ "$output" == "workflow" ]]; then
    echo "$submitted_wf"
  else
    if [[ -z "$pod" ]]; then
      pod="$(kubectl get pods -n "$ns" -l "workflows.argoproj.io/workflow=$submitted_wf" --field-selector=status.phase=Running -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' 2>/dev/null | grep -v 'resolve-user-identity' | head -1 || true)"
    fi
    [[ -n "$pod" ]] || fail "workflow running but pod name could not be resolved"
    echo "$pod"
  fi
}

sync_once() {
  local ns="$DEFAULT_NAMESPACE" pod="" local_dir="" remote_dir="/scratch/aimet"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --namespace) ns="$2"; shift 2 ;;
      --pod) pod="$2"; shift 2 ;;
      --local-dir) local_dir="$2"; shift 2 ;;
      --remote-dir) remote_dir="$2"; shift 2 ;;
      -h|--help) usage; exit 0 ;;
      *) fail "unknown sync-once option: $1" ;;
    esac
  done
  [[ -n "$pod" ]] || fail "--pod is required"
  [[ -n "$local_dir" ]] || fail "--local-dir is required"
  [[ -d "$local_dir" ]] || fail "local dir does not exist: $local_dir"
  need_cmd kubectl; need_cmd tar
  local abs_local remote_q
  abs_local="$(cd "$local_dir" && pwd)"
  remote_q="$(shq "$remote_dir")"
  echo "syncing $abs_local -> $pod:$remote_dir" >&2
  tar \
    --exclude='./.git' \
    --exclude='./build' \
    --exclude='./__pycache__' \
    --exclude='./*.pyc' \
    --exclude='./.venv' \
    --exclude='./GenAILab/artifacts' \
    -C "$abs_local" -cf - . \
    | kubectl exec -i -n "$ns" "$pod" -- sh -lc "mkdir -p $remote_q && tar -C $remote_q -xf -"
  echo "sync complete" >&2
}

exec_pod() {
  local ns="$DEFAULT_NAMESPACE" pod="" tty=false
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --namespace) ns="$2"; shift 2 ;;
      --pod) pod="$2"; shift 2 ;;
      --tty) tty=true; shift ;;
      --) shift; break ;;
      -h|--help) usage; exit 0 ;;
      *) fail "unknown exec option before --: $1" ;;
    esac
  done
  [[ -n "$pod" ]] || fail "--pod is required"
  [[ $# -gt 0 ]] || fail "command after -- is required"
  need_cmd kubectl
  if $tty; then
    kubectl exec -it -n "$ns" "$pod" -- "$@"
  else
    kubectl exec -i -n "$ns" "$pod" -- "$@"
  fi
}

list_workflows() {
  local ns="$DEFAULT_NAMESPACE" user="${USER:-$(whoami)}"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --namespace) ns="$2"; shift 2 ;;
      --user) user="$2"; shift 2 ;;
      -h|--help) usage; exit 0 ;;
      *) fail "unknown list option: $1" ;;
    esac
  done
  need_cmd argo
  argo list -n "$ns" -l "workflows.argoproj.io/creator-preferred-username=$user" --status Running
}

stop_workflows() {
  local ns="$DEFAULT_NAMESPACE" delete=false
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --namespace) ns="$2"; shift 2 ;;
      --delete) delete=true; shift ;;
      -h|--help) usage; exit 0 ;;
      --) shift; break ;;
      *) break ;;
    esac
  done
  [[ $# -gt 0 ]] || fail "at least one workflow name is required"
  need_cmd argo
  local wf
  for wf in "$@"; do
    if $delete; then
      echo "deleting workflow: $wf" >&2
      argo delete "$wf" -n "$ns"
    else
      echo "terminating workflow: $wf" >&2
      argo terminate "$wf" -n "$ns"
    fi
  done
}

main() {
  [[ $# -gt 0 ]] || { usage; exit 1; }
  local cmd="$1"; shift
  case "$cmd" in
    preflight) preflight "$@" ;;
    launch) launch "$@" ;;
    sync-once) sync_once "$@" ;;
    exec) exec_pod "$@" ;;
    list) list_workflows "$@" ;;
    stop) stop_workflows "$@" ;;
    -h|--help|help) usage ;;
    *) fail "unknown subcommand: $cmd" ;;
  esac
}

main "$@"
