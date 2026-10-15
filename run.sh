
set -euo pipefail

cd "$(dirname "$0")"


if [ -f .venv/bin/activate ]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi

PY=${PYTHON:-python}

MODE="headless"
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --visual|--headed)
            MODE="visual"
            ;;
        --video)
            MODE="video"
            ;;
        --trace)
            MODE="trace"
            ;;
        --report)
            EXTRA_ARGS+=( "--html=test-results/report.html" "--self-contained-html" "--clean-before-session" )
            ;;
        -h|--help)
            sed -n '2,25p' "$0" | sed 's/^#\s\?//'
            exit 0
            ;;
        *)
            EXTRA_ARGS+=( "$1" )
            ;;
    esac
    shift
done

XVFB_PID=""
cleanup() {
    if [[ -n "$XVFB_PID" ]] && kill -0 "$XVFB_PID" 2>/dev/null; then
        kill "$XVFB_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

ensure_display() {
    
    if [[ -n "${DISPLAY:-}" ]] && python_check_display "${DISPLAY}"; then
        echo "[display] menggunakan DISPLAY=$DISPLAY yang sudah aktif"
        return 0
    fi

    if ! command -v Xvfb >/dev/null 2>&1; then
        echo "[display] Xvfb tidak terpasang; fallback ke headless."
        return 1
    fi

   
    local display_num=""
    for n in $(seq 20 99); do
        if [[ ! -e "/tmp/.X11-unix/X$n" ]]; then
            display_num="$n"
            break
        fi
    done
    if [[ -z "$display_num" ]]; then
        echo "[display] tidak ada display number bebas; fallback ke headless."
        return 1
    fi

    echo "[display] memulai Xvfb pada display :$display_num"
    Xvfb ":$display_num" -screen 0 1280x720x24 -ac +extension RANDR -nolisten tcp \
        >/dev/null 2>&1 &
    XVFB_PID=$!
    sleep 2

    if ! python_check_display ":$display_num"; then
        echo "[display] Xvfb gagal start; fallback ke headless."
        kill "$XVFB_PID" 2>/dev/null || true
        XVFB_PID=""
        return 1
    fi
    export DISPLAY=":$display_num"
    echo "[display] siap, DISPLAY=$DISPLAY"
}


python_check_display() {
    local disp="$1"
    disp="${disp#:}"
    "$PY" - "$disp" <<'PYEOF' >/dev/null 2>&1
import socket, sys, os
n = sys.argv[1].split(".")[0]
path = f"/tmp/.X11-unix/X{n}"
if not os.path.exists(path):
    sys.exit(1)
try:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(2)
    s.connect(path)
    s.close()
except OSError:
    sys.exit(1)
sys.exit(0)
PYEOF
}


case "$MODE" in
    visual)
        if ensure_display; then
            echo "[mode] VISUAL - browser window terlihat + video rekaman"
            EXTRA_ARGS+=( "--headed" "--video=on" "--screenshot=on" "--slowmo=400" )
        else
            echo "[mode] visual tidak tersedia, beralih ke VIDEO mode"
            EXTRA_ARGS+=( "--video=on" "--screenshot=on" )
        fi
        ;;
    video)
        echo "[mode] HEADLESS + video rekaman setiap test"
        EXTRA_ARGS+=( "--video=on" "--screenshot=on" )
        ;;
    trace)
        echo "[mode] HEADLESS + Playwright trace recording"
        EXTRA_ARGS+=( "--trace=on" )
        ;;
    *)
        echo "[mode] HEADLESS (default)"
        ;;
esac

echo ""
echo "==================================================================="
echo " Menjalankan: $PY -m pytest ${EXTRA_ARGS[*]:-}"
echo "==================================================================="
echo ""


set +e
$PY -m pytest -p no:cacheprovider --override-ini="addopts=" "${EXTRA_ARGS[@]}"
RC=$?
set -e

echo ""
echo "==================================================================="
echo " Selesai. Exit code: $RC"
echo " Artefak ada di folder: $(pwd)/test-results/"
echo "==================================================================="
exit $RC
