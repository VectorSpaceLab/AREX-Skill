#!/usr/bin/env bash
# Airweave local stack helper bundled with the generated repo skill.
# Safe defaults: explicit repo root, status before mutation, preserve existing containers unless
# restart/recreate/destroy is requested.

set -euo pipefail

SCRIPT_NAME="$(basename "$0")"
ACTION="start"
REPO_ROOT="${AIRWEAVE_REPO:-}"
NONINTERACTIVE="${NONINTERACTIVE:-}"
SKIP_LOCAL_EMBEDDINGS="${SKIP_LOCAL_EMBEDDINGS:-}"
SKIP_FRONTEND="${SKIP_FRONTEND:-}"
SKIP_CONNECT="${SKIP_CONNECT:-}"
ENABLE_DOCLING="${ENABLE_DOCLING:-}"
VERBOSE="${VERBOSE:-}"
QUIET="${QUIET:-}"
YES=""

BOLD=""
RESET=""
COMPOSE=()
CONTAINER=()
RUNTIME=""
ENV_CREATED=""
USE_LOCAL_EMBEDDINGS="true"
USE_FRONTEND="true"
USE_CONNECT="true"
USE_DOCLING="false"

setup_colors() {
    if [[ -t 1 && -z ${NO_COLOR:-} ]]; then
        BOLD=$'\033[1m'
        RESET=$'\033[0m'
    fi
}

log_info() { [[ -z $QUIET ]] && printf "  %s\n" "$1" || true; }
log_note() { [[ -z $QUIET ]] && printf "ℹ️ %s\n" "$1" || true; }
log_success() { [[ -z $QUIET ]] && printf "✅ %s\n" "$1" || true; }
log_warning() { printf "⚠️ %s\n" "$1"; }
log_error() { printf "❌ %s\n" "$1" >&2; }
log_debug() { [[ -n $VERBOSE ]] && printf "   [debug] %s\n" "$1" || true; }
section() { [[ -z $QUIET ]] && printf "\n${BOLD}==> %s${RESET}\n" "$1" || true; }

usage() {
    cat <<EOF
${BOLD}Usage:${RESET} $SCRIPT_NAME --repo-root PATH [start|status|restart|recreate|destroy] [OPTIONS]
       $SCRIPT_NAME PATH [start|status|restart|recreate|destroy] [OPTIONS]

Operate the Airweave local Docker stack from any current working directory.

${BOLD}Actions:${RESET}
  start                     Seed missing env values and start/reuse the stack (default)
  status                    Show non-mutating container, port, and health status
  restart                   Restart existing containers, preserving volumes and data
  recreate                  Remove compose containers/volumes, then start again
  destroy                   Remove compose containers/volumes and exit

${BOLD}Options:${RESET}
  --repo-root PATH          Airweave repository root (required unless PATH positional or AIRWEAVE_REPO)
  --noninteractive          Skip prompts
  --yes                     Confirm destructive destroy in automation
  --skip-local-embeddings   Do not start the local embeddings container
  --skip-frontend           Do not start the frontend UI profile
  --skip-connect            Do not start the connect widget profile
  --enable-docling          Start docling-serve and wire backend containers for local OCR
  -v, --verbose             Show debug output
  -q, --quiet               Minimal output
  -h, --help                Show this help

${BOLD}Environment toggles:${RESET}
  AIRWEAVE_REPO=/path/to/repo, NONINTERACTIVE=1, SKIP_LOCAL_EMBEDDINGS=1,
  SKIP_FRONTEND=1, SKIP_CONNECT=1, ENABLE_DOCLING=1, VERBOSE=1, QUIET=1

${BOLD}Examples:${RESET}
  $SCRIPT_NAME --repo-root /path/to/airweave status
  $SCRIPT_NAME /path/to/airweave start --skip-frontend
  $SCRIPT_NAME --repo-root /path/to/airweave restart
  $SCRIPT_NAME --repo-root /path/to/airweave destroy --yes
EOF
}

have_cmd() { command -v "$1" >/dev/null 2>&1; }

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                usage
                exit 0
                ;;
            --repo-root)
                [[ $# -ge 2 ]] || { log_error "--repo-root requires a path"; exit 2; }
                REPO_ROOT="$2"
                shift 2
                ;;
            --repo-root=*)
                REPO_ROOT="${1#--repo-root=}"
                shift
                ;;
            --noninteractive)
                NONINTERACTIVE=1
                shift
                ;;
            --yes|-y)
                YES=1
                shift
                ;;
            --skip-local-embeddings)
                SKIP_LOCAL_EMBEDDINGS=1
                shift
                ;;
            --skip-frontend)
                SKIP_FRONTEND=1
                shift
                ;;
            --skip-connect)
                SKIP_CONNECT=1
                shift
                ;;
            --enable-docling)
                ENABLE_DOCLING=1
                shift
                ;;
            -v|--verbose)
                VERBOSE=1
                shift
                ;;
            -q|--quiet)
                QUIET=1
                shift
                ;;
            --status)
                ACTION="status"
                shift
                ;;
            --restart)
                ACTION="restart"
                shift
                ;;
            --recreate)
                ACTION="recreate"
                shift
                ;;
            --destroy)
                ACTION="destroy"
                shift
                ;;
            start|status|restart|recreate|destroy)
                ACTION="$1"
                shift
                ;;
            *)
                if [[ -z $REPO_ROOT && -d $1 ]]; then
                    REPO_ROOT="$1"
                    shift
                else
                    log_error "Unknown argument: $1"
                    echo "Run '$SCRIPT_NAME --help' for usage." >&2
                    exit 2
                fi
                ;;
        esac
    done
}

resolve_repo_root() {
    if [[ -z $REPO_ROOT ]]; then
        log_error "Missing repo root. Pass --repo-root PATH, a PATH positional, or AIRWEAVE_REPO."
        exit 2
    fi
    if [[ ! -d $REPO_ROOT ]]; then
        log_error "Repo root does not exist: $REPO_ROOT"
        exit 2
    fi
    REPO_ROOT="$(cd "$REPO_ROOT" && pwd -P)"
    if [[ ! -f "$REPO_ROOT/docker/docker-compose.yml" || ! -f "$REPO_ROOT/.env.example" ]]; then
        log_error "Not an Airweave repo root: $REPO_ROOT"
        log_error "Expected docker/docker-compose.yml and .env.example"
        exit 2
    fi
}

detect_runtime() {
    if have_cmd docker && docker info >/dev/null 2>&1; then
        RUNTIME="docker"
        CONTAINER=(docker)
        if docker compose version >/dev/null 2>&1; then
            COMPOSE=(docker compose)
        elif have_cmd docker-compose; then
            COMPOSE=(docker-compose)
        else
            log_error "Docker Compose not found"
            echo "Install Docker Compose and retry." >&2
            exit 1
        fi
    elif have_cmd podman && podman info >/dev/null 2>&1; then
        RUNTIME="podman"
        CONTAINER=(podman)
        if have_cmd podman-compose; then
            COMPOSE=(podman-compose)
        elif podman compose version >/dev/null 2>&1; then
            COMPOSE=(podman compose)
        else
            log_error "Podman is running but podman-compose was not found"
            echo "Install podman-compose or use Docker Compose." >&2
            exit 1
        fi
    else
        log_error "Docker/Podman daemon not running"
        echo "Start Docker Desktop, Docker Engine, or Podman and retry." >&2
        exit 1
    fi
    log_debug "Runtime: $RUNTIME; compose: ${COMPOSE[*]}"
}

require_host_tools_for_health() {
    if ! have_cmd curl; then
        log_error "curl is required for local health checks"
        exit 1
    fi
}

container_cmd() {
    "${CONTAINER[@]}" "$@"
}

compose_cmd() {
    "${COMPOSE[@]}" "$@"
}

compose_file_cmd() {
    if [[ -f .env ]]; then
        compose_cmd --env-file .env -f docker/docker-compose.yml "$@"
    else
        compose_cmd -f docker/docker-compose.yml "$@"
    fi
}

compose_file_cmd_quiet() {
    compose_file_cmd "$@" 2>/dev/null || true
}

get_env_value() {
    local key=$1
    if [[ ! -f .env ]]; then
        return 0
    fi
    grep -E "^${key}=" .env 2>/dev/null | head -1 | cut -d'=' -f2- | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//" || true
}

set_env_value() {
    local key=$1
    local value=$2
    local tmp_file
    tmp_file="$(mktemp)"
    grep -Ev "^${key}=" .env > "$tmp_file" 2>/dev/null || true
    mv "$tmp_file" .env
    printf '%s="%s"\n' "$key" "$value" >> .env
}

ensure_env_value() {
    local key=$1
    local value=$2
    local current
    current="$(get_env_value "$key")"
    if [[ -z $current ]]; then
        set_env_value "$key" "$value"
        log_success "$key configured"
        return 0
    fi
    log_debug "$key already configured"
    return 1
}

generate_urlsafe_secret() {
    if have_cmd python3; then
        python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
    elif have_cmd openssl; then
        openssl rand -base64 32
    else
        log_error "Need python3 or openssl to generate secrets"
        return 1
    fi
}

generate_base64_secret() {
    if have_cmd openssl; then
        openssl rand -base64 32
    elif have_cmd python3; then
        python3 -c 'import base64, secrets; print(base64.b64encode(secrets.token_bytes(32)).decode())'
    else
        log_error "Need openssl or python3 to generate secrets"
        return 1
    fi
}

is_real_key() {
    local value=$1
    [[ -n $value && $value != "your-api-key-here" && $value != "changeme" ]]
}

prompt_api_key() {
    local key_name=$1
    local description=$2
    local existing
    existing="$(get_env_value "$key_name")"
    if is_real_key "$existing"; then
        log_success "$key_name configured"
        return 0
    fi
    if [[ -n $NONINTERACTIVE ]]; then
        log_info "$key_name not set (noninteractive mode)"
        return 0
    fi
    printf "\n%s\n" "$description"
    read -r -p "Add $key_name now? (y/n): " response
    if [[ $response =~ ^[Yy]$ ]]; then
        read -r -p "Enter $key_name: " key_value
        if [[ -n $key_value ]]; then
            set_env_value "$key_name" "$key_value"
            log_success "$key_name added to .env"
        else
            log_warning "$key_name left empty"
        fi
    else
        log_info "You can add $key_name later in .env"
    fi
}

seed_env() {
    section "Checking environment"
    if [[ ! -f .env ]]; then
        cp .env.example .env
        ENV_CREATED=1
        log_success "Created .env from .env.example"
    else
        ENV_CREATED=""
        log_success ".env file exists"
    fi

    if [[ -z $(get_env_value ENCRYPTION_KEY) ]]; then
        set_env_value ENCRYPTION_KEY "$(generate_base64_secret)"
        log_success "ENCRYPTION_KEY generated"
    else
        log_success "ENCRYPTION_KEY configured"
    fi

    if [[ -z $(get_env_value STATE_SECRET) ]]; then
        set_env_value STATE_SECRET "$(generate_urlsafe_secret)"
        log_success "STATE_SECRET generated"
    else
        log_success "STATE_SECRET configured"
    fi

    if [[ -z $(get_env_value SVIX_JWT_SECRET) ]]; then
        set_env_value SVIX_JWT_SECRET "$(generate_urlsafe_secret)"
        log_success "SVIX_JWT_SECRET generated"
    else
        log_success "SVIX_JWT_SECRET configured"
    fi

    if [[ -z $(get_env_value FIRST_SUPERUSER_PASSWORD) ]]; then
        set_env_value FIRST_SUPERUSER_PASSWORD "$(generate_urlsafe_secret)"
        log_success "FIRST_SUPERUSER_PASSWORD generated"
    else
        log_success "FIRST_SUPERUSER_PASSWORD configured"
    fi

    if [[ -z $(get_env_value POSTGRES_PASSWORD) ]]; then
        set_env_value POSTGRES_PASSWORD "$(generate_urlsafe_secret)"
        log_success "POSTGRES_PASSWORD generated"
    else
        log_success "POSTGRES_PASSWORD configured"
    fi

    ensure_env_value FIRST_SUPERUSER "admin@example.com" || true
    ensure_env_value POSTGRES_USER "airweave" || true
    ensure_env_value SKIP_AZURE_STORAGE "true" || true
    ensure_env_value STORAGE_BACKEND "filesystem" || true
    ensure_env_value STORAGE_PATH "./local_storage" || true
    ensure_env_value SPARSE_EMBEDDER "fastembed_bm25" || true

    prompt_api_key OPENAI_API_KEY "OpenAI API key enables OpenAI embeddings and natural-language search."
    prompt_api_key MISTRAL_API_KEY "Mistral API key enables Mistral embeddings and OCR-related functionality."
}

configure_runtime_profiles() {
    USE_FRONTEND="true"
    USE_CONNECT="true"
    USE_DOCLING="false"
    USE_LOCAL_EMBEDDINGS="true"

    [[ -n $SKIP_FRONTEND ]] && USE_FRONTEND="false"
    [[ -n $SKIP_CONNECT ]] && USE_CONNECT="false"
    [[ -n $ENABLE_DOCLING ]] && USE_DOCLING="true"

    local openai_key mistral_key current_dense current_dim current_sparse docling_url
    openai_key="$(get_env_value OPENAI_API_KEY)"
    mistral_key="$(get_env_value MISTRAL_API_KEY)"
    current_dense="$(get_env_value DENSE_EMBEDDER)"
    current_dim="$(get_env_value EMBEDDING_DIMENSIONS)"
    current_sparse="$(get_env_value SPARSE_EMBEDDER)"
    docling_url="$(get_env_value DOCLING_BASE_URL)"

    if [[ -n $docling_url ]]; then
        USE_DOCLING="true"
    fi
    if [[ $USE_DOCLING == "true" ]]; then
        ensure_env_value DOCLING_BASE_URL "http://localhost:5001" || true
    fi

    if is_real_key "$openai_key"; then
        USE_LOCAL_EMBEDDINGS="false"
        if [[ -z $current_dense || -n $ENV_CREATED ]]; then
            set_env_value DENSE_EMBEDDER "openai_text_embedding_3_small"
            set_env_value EMBEDDING_DIMENSIONS "1536"
            log_success "Using OpenAI embeddings (1536 dimensions)"
        fi
    elif is_real_key "$mistral_key"; then
        USE_LOCAL_EMBEDDINGS="false"
        if [[ -z $current_dense || -n $ENV_CREATED ]]; then
            set_env_value DENSE_EMBEDDER "mistral_embed"
            set_env_value EMBEDDING_DIMENSIONS "1024"
            log_success "Using Mistral embeddings (1024 dimensions)"
        fi
    elif [[ -n $ENV_CREATED && -z $SKIP_LOCAL_EMBEDDINGS ]]; then
        set_env_value DENSE_EMBEDDER "local_minilm"
        set_env_value EMBEDDING_DIMENSIONS "384"
        USE_LOCAL_EMBEDDINGS="true"
        log_success "Using local MiniLM embeddings (384 dimensions)"
    elif [[ -z $current_dense || -z $current_dim ]]; then
        if [[ -n $SKIP_LOCAL_EMBEDDINGS ]]; then
            log_warning "No embedding provider configured and local embeddings are skipped"
            USE_LOCAL_EMBEDDINGS="false"
        else
            set_env_value DENSE_EMBEDDER "local_minilm"
            set_env_value EMBEDDING_DIMENSIONS "384"
            USE_LOCAL_EMBEDDINGS="true"
            log_success "Using local MiniLM embeddings (384 dimensions)"
        fi
    fi

    [[ -z $current_sparse ]] && ensure_env_value SPARSE_EMBEDDER "fastembed_bm25" || true

    current_dense="$(get_env_value DENSE_EMBEDDER)"
    current_dim="$(get_env_value EMBEDDING_DIMENSIONS)"
    if [[ $current_dense == "local_minilm" ]]; then
        if [[ -n $SKIP_LOCAL_EMBEDDINGS ]]; then
            log_warning "DENSE_EMBEDDER=local_minilm requires local embeddings; ignoring skip-local-embeddings"
        fi
        USE_LOCAL_EMBEDDINGS="true"
    elif [[ -n $SKIP_LOCAL_EMBEDDINGS ]]; then
        USE_LOCAL_EMBEDDINGS="false"
    fi

    if [[ $current_dense == openai_* ]]; then
        if ! is_real_key "$openai_key"; then
            log_warning "DENSE_EMBEDDER=$current_dense but OPENAI_API_KEY is not set"
        fi
    fi
    if [[ $current_dense == "mistral_embed" ]]; then
        if ! is_real_key "$mistral_key"; then
            log_warning "DENSE_EMBEDDER=mistral_embed but MISTRAL_API_KEY is not set"
        fi
    fi
    if [[ -z $current_dim ]]; then
        log_warning "EMBEDDING_DIMENSIONS is empty; backend and Vespa may fail"
    fi

    [[ $USE_FRONTEND == "false" ]] && log_note "Frontend profile skipped"
    [[ $USE_CONNECT == "false" ]] && log_note "Connect profile skipped"
    [[ $USE_LOCAL_EMBEDDINGS == "false" ]] && log_note "Local embeddings profile skipped"
    [[ $USE_DOCLING == "true" ]] && log_note "Docling profile enabled"
}

profile_args() {
    [[ $USE_LOCAL_EMBEDDINGS == "true" ]] && printf '%s\0' --profile local-embeddings
    [[ $USE_FRONTEND == "true" ]] && printf '%s\0' --profile frontend
    [[ $USE_CONNECT == "true" ]] && printf '%s\0' --profile connect
    printf '%s\0' --profile vespa
    [[ $USE_DOCLING == "true" ]] && printf '%s\0' --profile docling
}

read_profile_args() {
    PROFILE_ARGS=()
    while IFS= read -r -d '' arg; do
        PROFILE_ARGS+=("$arg")
    done < <(profile_args)
}

compose_container_ids() {
    compose_file_cmd_quiet ps -a -q
}

compose_running_ids() {
    compose_file_cmd_quiet ps -q
}

known_airweave_container_exists() {
    container_cmd ps -a --filter 'name=airweave-' -q 2>/dev/null | grep -q .
}

wait_for() {
    local description=$1
    local max_attempts=$2
    local check_func=$3
    local attempt=0
    local code=1
    while (( attempt < max_attempts )); do
        if "$check_func" >/dev/null 2>&1; then
            printf "\r\033[K"
            log_success "$description"
            return 0
        else
            code=$?
        fi
        if [[ $code -eq 2 ]]; then
            printf "\r\033[K"
            log_error "$description failed permanently"
            return 1
        fi
        attempt=$((attempt + 1))
        [[ -z $QUIET ]] && printf "\r\033[K⏳ %s (%d/%d)..." "$description" "$attempt" "$max_attempts"
        sleep 5
    done
    printf "\r\033[K"
    log_error "$description failed after $max_attempts attempts"
    return 1
}

vespa_check() {
    local init_status init_exit_code doc_status
    init_status="$(container_cmd inspect airweave-vespa-init --format='{{.State.Status}}' 2>/dev/null || echo not_found)"
    init_exit_code="$(container_cmd inspect airweave-vespa-init --format='{{.State.ExitCode}}' 2>/dev/null || echo 1)"
    if [[ $init_status == "exited" && $init_exit_code != "0" ]]; then
        log_error "Vespa init exited with code $init_exit_code"
        log_info "Inspect: ${CONTAINER[*]} logs airweave-vespa-init"
        return 2
    fi
    if [[ $init_status == "exited" && $init_exit_code == "0" ]]; then
        doc_status="$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8081/document/v1/ 2>/dev/null || echo 000)"
        [[ $doc_status != "000" && -n $doc_status ]]
        return $?
    fi
    return 1
}

backend_check() {
    container_cmd exec airweave-backend curl -sf http://localhost:8001/health/ready \
        || container_cmd exec airweave-backend curl -sf http://localhost:8001/health
}

frontend_check() { curl -sf http://localhost:8080 >/dev/null; }
connect_check() { curl -sf http://localhost:8082 >/dev/null; }
docling_check() { curl -sf http://localhost:5001/health >/dev/null; }

wait_for_services() {
    section "Waiting for services"
    wait_for "Vespa ready" 60 vespa_check || {
        echo "Vespa troubleshooting:"
        echo "  ${CONTAINER[*]} logs airweave-vespa"
        echo "  ${CONTAINER[*]} logs airweave-vespa-init"
        echo "  curl http://localhost:8081/state/v1/health"
        return 1
    }
    wait_for "Backend healthy" 30 backend_check || {
        echo "Backend troubleshooting:"
        echo "  ${CONTAINER[*]} logs airweave-backend"
        echo "  ${CONTAINER[*]} logs airweave-db"
        echo "  ${CONTAINER[*]} logs airweave-svix"
        return 1
    }
    if [[ $USE_FRONTEND == "true" ]]; then
        wait_for "Frontend responding" 24 frontend_check || true
    fi
    if [[ $USE_CONNECT == "true" ]]; then
        wait_for "Connect widget responding" 24 connect_check || true
    fi
    if [[ $USE_DOCLING == "true" ]]; then
        wait_for "Docling healthy" 30 docling_check || true
    fi
}

container_state_line() {
    local name=$1
    if ! container_cmd inspect "$name" >/dev/null 2>&1; then
        printf '%-28s %s\n' "$name" "missing"
        return 1
    fi
    local status health
    status="$(container_cmd inspect "$name" --format='{{.State.Status}}' 2>/dev/null || echo unknown)"
    health="$(container_cmd inspect "$name" --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' 2>/dev/null || echo unknown)"
    printf '%-28s %s (%s)\n' "$name" "$status" "$health"
    [[ $status == "running" || $status == "exited" ]]
}

url_status() {
    local label=$1
    local url=$2
    if curl -sf "$url" >/dev/null 2>&1; then
        printf '✅ %-24s %s\n' "$label" "$url"
        return 0
    fi
    printf '❌ %-24s not responding (%s)\n' "$label" "$url"
    return 1
}

optional_url_status() {
    local container=$1
    local label=$2
    local url=$3
    if ! container_cmd inspect "$container" >/dev/null 2>&1; then
        printf 'ℹ️ %-24s skipped/not present\n' "$label"
        return 0
    fi
    local state
    state="$(container_cmd inspect "$container" --format='{{.State.Status}}' 2>/dev/null || echo missing)"
    if [[ $state != "running" ]]; then
        printf '⚠️ %-24s container %s\n' "$label" "$state"
        return 1
    fi
    url_status "$label" "$url"
}

print_status() {
    section "Airweave status"
    local had_container="false"
    local status_ok="true"
    local containers=(
        airweave-db
        airweave-redis
        airweave-svix
        airweave-temporal
        airweave-temporal-init
        airweave-temporal-ui
        airweave-vespa
        airweave-vespa-init
        airweave-backend
        airweave-temporal-worker
        airweave-frontend
        airweave-connect
        airweave-embeddings
        airweave-docling
    )

    printf "Repository: %s\n" "$REPO_ROOT"
    printf "Runtime:    %s (%s)\n" "$RUNTIME" "${COMPOSE[*]}"
    printf "\nContainers:\n"
    for container in "${containers[@]}"; do
        if container_cmd inspect "$container" >/dev/null 2>&1; then
            had_container="true"
        fi
        container_state_line "$container" || true
    done

    if [[ $had_container != "true" ]]; then
        printf "\nNo Airweave containers found.\n"
        return 1
    fi

    printf "\nHealth endpoints:\n"
    url_status "Backend API" "http://localhost:8001/health" || status_ok="false"
    url_status "Backend readiness" "http://localhost:8001/health/ready" || status_ok="false"
    if ! curl -sf http://localhost:8081/state/v1/health >/dev/null 2>&1; then
        printf '❌ %-24s not responding (%s)\n' "Vespa health" "http://localhost:8081/state/v1/health"
        status_ok="false"
    else
        printf '✅ %-24s %s\n' "Vespa health" "http://localhost:8081/state/v1/health"
    fi
    optional_url_status airweave-frontend "Frontend UI" "http://localhost:8080" || status_ok="false"
    optional_url_status airweave-connect "Connect widget" "http://localhost:8082" || status_ok="false"
    optional_url_status airweave-docling "Docling" "http://localhost:5001/health" || status_ok="false"

    local dense
    dense="$(get_env_value DENSE_EMBEDDER)"
    if [[ $dense == "local_minilm" ]]; then
        if ! container_cmd inspect airweave-embeddings >/dev/null 2>&1; then
            printf '❌ %-24s required but container is missing\n' "Local embeddings"
            status_ok="false"
        else
            optional_url_status airweave-embeddings "Local embeddings" "http://localhost:9878/health" || status_ok="false"
        fi
    else
        printf 'ℹ️ %-24s %s\n' "Embeddings" "${dense:-not configured}"
    fi

    printf "\nPorts to expect when enabled: backend 8001, metrics 9090, frontend 8080, connect 8082, Vespa 8081/19071, Temporal 7233/8233/8088, Postgres 5432, Redis 6379, Svix 8071, embeddings 9878, Docling 5001.\n"

    [[ $status_ok == "true" ]]
}

start_stack() {
    local existing running
    existing="$(compose_container_ids)"
    running="$(compose_running_ids)"

    if [[ -n $existing && -n $running ]]; then
        log_success "Airweave containers already exist and at least one is running; preserving state"
        print_status
        return $?
    fi

    seed_env
    configure_runtime_profiles
    read_profile_args

    existing="$(compose_container_ids)"
    section "Starting services"
    if [[ -n $existing ]]; then
        log_note "Existing Airweave containers found; starting them without destructive cleanup"
    fi

    if ! compose_file_cmd "${PROFILE_ARGS[@]}" up -d; then
        log_error "Failed to start Docker services"
        echo "Inspect logs with: ${CONTAINER[*]} logs airweave-backend"
        return 1
    fi
    log_success "Docker services started"
    wait_for_services
    print_status
}

restart_stack() {
    if ! known_airweave_container_exists; then
        log_error "No Airweave containers to restart. Run start first."
        return 1
    fi
    configure_runtime_profiles
    read_profile_args
    section "Restarting services"
    compose_file_cmd "${PROFILE_ARGS[@]}" restart
    log_success "Services restarted"
    wait_for_services
    print_status
}

recreate_stack() {
    seed_env
    configure_runtime_profiles
    read_profile_args
    section "Recreating services"
    log_warning "This removes compose containers and named volumes, then starts again."
    compose_file_cmd down --volumes --remove-orphans 2>/dev/null || true
    compose_file_cmd "${PROFILE_ARGS[@]}" up -d
    log_success "Services recreated"
    wait_for_services
    print_status
}

destroy_stack() {
    section "Destroying services"
    if [[ -z $NONINTERACTIVE && -z $YES ]]; then
        log_warning "This removes Airweave compose containers and named volumes."
        read -r -p "Continue? (y/n): " response
        if [[ ! $response =~ ^[Yy]$ ]]; then
            log_info "Aborted"
            return 0
        fi
    fi
    compose_file_cmd down --volumes --remove-orphans 2>/dev/null || true
    log_success "Airweave compose resources removed"
    echo "To start fresh: $SCRIPT_NAME --repo-root '$REPO_ROOT' start"
}

main() {
    setup_colors
    parse_args "$@"
    resolve_repo_root
    cd "$REPO_ROOT"
    detect_runtime
    require_host_tools_for_health

    case "$ACTION" in
        start) start_stack ;;
        status) print_status ;;
        restart) restart_stack ;;
        recreate) recreate_stack ;;
        destroy) destroy_stack ;;
        *) log_error "Unknown action: $ACTION"; exit 2 ;;
    esac
}

main "$@"
