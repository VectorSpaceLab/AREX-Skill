#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: run_django_demo_check.sh --repo-root PATH [--start]

Safe preflight for the agriculture knowledge graph Django demo.

Options:
  --repo-root PATH   Repository root that contains demo/, README.md, and requirement.txt.
  --start            After all checks pass, start the Django dev server.
  -h, --help         Show this help text.

The script checks required files, compiles the demo Python sources, verifies
core Python dependencies, warns about Neo4j and MongoDB reachability, and runs
`manage.py help` before any optional server launch.
EOF
}

repo_root=""
start=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      repo_root="${2:-}"
      shift 2
      ;;
    --start)
      start=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[error] unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$repo_root" ]]; then
  echo "[error] --repo-root is required" >&2
  usage >&2
  exit 2
fi

if [[ ! -d "$repo_root" ]]; then
  echo "[error] repo root not found: $repo_root" >&2
  exit 1
fi

repo_root="$(cd "$repo_root" && pwd)"
demo_root="$repo_root/demo"

printf '[info] repo root: %s\n' "$repo_root"
printf '[info] demo root: %s\n' "$demo_root"
printf '[info] Neo4j and MongoDB are runtime prerequisites for most pages.\n'

required_files=(
  "README.md"
  "requirement.txt"
  "demo/manage.py"
  "demo/django_server_start.sh"
  "demo/demo/settings.py"
  "demo/demo/urls.py"
  "demo/demo/index_view.py"
  "demo/demo/index_ERform_view.py"
  "demo/demo/relation_view.py"
  "demo/demo/question_answering.py"
  "demo/demo/tagging.py"
  "demo/demo/tagging_data_view.py"
  "demo/demo/tagging_data_writefile_view.py"
  "demo/demo/decisions_making.py"
  "demo/demo/overview_view.py"
  "demo/demo/detail_view.py"
  "demo/demo/_404_view.py"
  "demo/Model/neo_models.py"
  "demo/Model/mongo_model.py"
  "demo/toolkit/pre_load.py"
  "demo/toolkit/NER.py"
  "demo/toolkit/tree_API.py"
  "demo/toolkit/vec_API.py"
  "demo/toolkit/img_match.py"
  "demo/templates/index.html"
  "demo/templates/entity.html"
  "demo/templates/relation.html"
  "demo/templates/overview.html"
  "demo/templates/detail.html"
  "demo/templates/question_answering.html"
  "demo/templates/tagging_data.html"
  "demo/templates/taggingSentences.html"
  "demo/templates/tagging_cache.html"
  "demo/templates/decisions_making.html"
  "demo/templates/404.html"
  "demo/label_data/city_list.txt"
  "demo/label_data/labels.txt"
  "demo/label_data/word_list.txt"
  "demo/toolkit/predict_labels.txt"
  "demo/toolkit/vector_15.txt"
  "demo/toolkit/micropedia_tree.txt"
  "demo/toolkit/leaf_list.txt"
  "demo/toolkit/id2obj.txt"
  "demo/toolkit/relationStaticResult.txt"
)

missing_files=0
for rel in "${required_files[@]}"; do
  if [[ -e "$repo_root/$rel" ]]; then
    printf '[ok] file: %s\n' "$rel"
  else
    printf '[error] missing file: %s\n' "$rel" >&2
    missing_files=1
  fi
done

if (( missing_files )); then
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "[error] python3 not found on PATH" >&2
  exit 1
fi

python_files=(
  "demo/manage.py"
  "demo/demo/settings.py"
  "demo/demo/urls.py"
  "demo/demo/index_view.py"
  "demo/demo/index_ERform_view.py"
  "demo/demo/relation_view.py"
  "demo/demo/question_answering.py"
  "demo/demo/tagging.py"
  "demo/demo/tagging_data_view.py"
  "demo/demo/tagging_data_writefile_view.py"
  "demo/demo/decisions_making.py"
  "demo/demo/overview_view.py"
  "demo/demo/detail_view.py"
  "demo/demo/_404_view.py"
  "demo/Model/neo_models.py"
  "demo/Model/mongo_model.py"
  "demo/toolkit/pre_load.py"
  "demo/toolkit/NER.py"
  "demo/toolkit/tree_API.py"
  "demo/toolkit/vec_API.py"
  "demo/toolkit/img_match.py"
)

printf '[info] compiling core Python sources\n'
python3 - "$repo_root" "${python_files[@]}" <<'PY'
import pathlib
import sys

repo = pathlib.Path(sys.argv[1])
for rel in sys.argv[2:]:
    path = repo / rel
    try:
        source = path.read_text(encoding='utf-8')
        compile(source, str(path), 'exec')
    except Exception as exc:
        print(f"[error] syntax check failed: {path.relative_to(repo)}: {exc}", file=sys.stderr)
        raise SystemExit(1)
    else:
        print(f"[ok] syntax: {path.relative_to(repo)}")
PY

printf '[info] checking Python dependencies\n'
deps_ok=1
if python3 - <<'PY'
import importlib
import sys

modules = ["django", "thulac", "py2neo", "pymongo", "pinyin", "requests"]
missing = []
for name in modules:
    try:
        mod = importlib.import_module(name)
        if name == "django":
            try:
                version = mod.get_version()
            except Exception:
                version = getattr(mod, "__version__", "unknown")
        else:
            version = getattr(mod, "__version__", "available")
        print(f"[ok] {name}: {version}")
    except Exception as exc:
        missing.append(f"{name}: {exc}")

if missing:
    for item in missing:
        print(f"[warn] {item}")
    sys.exit(1)
PY
then
  deps_ok=1
else
  deps_ok=0
fi

probe_service() {
  local name="$1"
  local host="$2"
  local port="$3"

  if python3 - "$host" "$port" <<'PY'
import socket
import sys

host = sys.argv[1]
port = int(sys.argv[2])

sock = socket.socket()
sock.settimeout(0.5)
try:
    ok = sock.connect_ex((host, port)) == 0
finally:
    sock.close()

raise SystemExit(0 if ok else 1)
PY
  then
    printf '[ok] %s reachable on %s:%s\n' "$name" "$host" "$port"
    return 0
  fi

  printf '[warn] %s not reachable on %s:%s\n' "$name" "$host" "$port"
  return 1
}

service_up=1
probe_service "Neo4j" "127.0.0.1" "7474" || service_up=0
probe_service "MongoDB" "127.0.0.1" "27017" || service_up=0

help_ok=1
if (( deps_ok )); then
  help_log="$(mktemp "${TMPDIR:-/tmp}/agri-kg-help.XXXXXX")"
  trap 'rm -f "$help_log"' EXIT

  printf '[info] running manage.py help\n'
  if ! (cd "$demo_root" && python3 manage.py help >"$help_log" 2>&1); then
    echo "[error] manage.py help failed" >&2
    sed 's/^/[help] /' "$help_log" >&2
    help_ok=0
  else
    printf '[ok] manage.py help succeeded\n'
  fi
else
  printf '[warn] skipping manage.py help because required Python packages are missing.\n'
fi

if (( start )); then
  if (( deps_ok == 0 )); then
    echo "[error] refusing to start because required Python packages are missing" >&2
    exit 1
  fi
  if (( help_ok == 0 )); then
    echo "[error] refusing to start because manage.py help failed" >&2
    exit 1
  fi
  if (( service_up == 0 )); then
    echo "[error] refusing to start because Neo4j or MongoDB is not reachable" >&2
    exit 1
  fi
  echo "[info] starting: cd \"$demo_root\" && python3 manage.py runserver 0.0.0.0:8000"
  cd "$demo_root"
  exec python3 manage.py runserver 0.0.0.0:8000
fi

if (( deps_ok == 0 )); then
  echo "[error] required Python packages are missing" >&2
  exit 1
fi

if (( help_ok == 0 )); then
  exit 1
fi

printf '[info] preflight complete; server not started.\n'
