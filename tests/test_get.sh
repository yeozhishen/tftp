#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/.."
SERVER_LOG="/tmp/tftp_server.log"

TFTP_HOST="127.0.0.1"
TFTP_PORT=69
TFTP_DIR="/tmp/tftp"
JUNK_DIR="/tmp/tftp_junk"
LOG_DIR="/tmp/tftp_test_logs"
SERVER_CMD="python $PROJECT_ROOT/run.py --file-directory $TFTP_DIR --port $TFTP_PORT --single-port"
FILES=("small_file" "medium_file" "large_file")
SIZES=("20M" "50M" "80M")

cleanup_server() {
    echo "[*] Stopping TFTP server..."
    if [[ -n "${SERVER_PID:-}" ]]; then
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
    fi
}

on_success() {
    echo "[✓] All tests passed. Cleaning up..."
    rm -rf "$TFTP_DIR" "$JUNK_DIR" "$LOG_DIR"
    cleanup_server
}

trap 'echo "[✗] Tests failed. Logs kept in $LOG_DIR and server log $SERVER_LOG"; cleanup_server' ERR INT

echo "[*] Setting up test directories..."
mkdir -p "$TFTP_DIR" "$JUNK_DIR" "$LOG_DIR"

echo "[*] Starting TFTP server..."
$SERVER_CMD > "$SERVER_LOG" 2>&1 &
SERVER_PID=$!
sleep 2  # Give server time to start
# Check if server started successfully
if ! ps -p "$SERVER_PID" > /dev/null; then
    echo "[✗] Failed to start TFTP server. Check $SERVER_LOG for details."
    exit 1
fi

echo "[*] Creating test files..."
for i in "${!FILES[@]}"; do
    dd if=/dev/urandom of="$TFTP_DIR/${FILES[$i]}" bs=1M count="${SIZES[$i]//[!0-9]/}" status=none
done

echo "[*] Performing individual GET tests..."
for file in "${FILES[@]}"; do
    tftp "$TFTP_HOST" "$TFTP_PORT" <<EOF &> "$LOG_DIR/get_$file.log"
get $file $JUNK_DIR/downloaded_$file
quit
EOF

    if ! diff "$TFTP_DIR/$file" "$JUNK_DIR/downloaded_$file" &> "$LOG_DIR/diff_$file.log"; then
        echo "[FAIL] Mismatch in GET $file. See $LOG_DIR/diff_$file.log"
        exit 1
    else
        echo "[PASS] GET $file matched original."
    fi
done

echo "[*] Testing 10 concurrent GETs on medium_file..."

concurrent_get() {
    i=$1
    local output="$JUNK_DIR/medium_file_dl_$i"
    local log="$LOG_DIR/get_medium_$i.log"
    local diffout="$LOG_DIR/diff_medium_$i.log"

    tftp "$TFTP_HOST" "$TFTP_PORT" <<EOF &> "$log"
get medium_file $output
quit
EOF

    if ! diff "$TFTP_DIR/medium_file" "$output" &> "$diffout"; then
        echo "[FAIL] Concurrent GET mismatch #$i"
        return 1
    else
        echo "[PASS] Concurrent GET #$i matched original."
        return 0
    fi
}
export -f concurrent_get
export TFTP_HOST TFTP_PORT TFTP_DIR JUNK_DIR LOG_DIR

FAIL_COUNT=0
for i in {1..10}; do
    concurrent_get "$i" &
done

for job in $(jobs -p); do
    if [[ "$job" != "$SERVER_PID" ]]; then
        if ! wait "$job"; then
            ((FAIL_COUNT++))
        fi
    fi
done


if [[ "$FAIL_COUNT" -gt 0 ]]; then
    echo "[✗] $FAIL_COUNT concurrent GET(s) failed."
    cleanup_server
    exit 1
fi

echo "[*] Sending invalid UDP garbage to $TFTP_HOST:$TFTP_PORT..."
echo "NOT_TFTP_PACKET" | nc -u -w1 "$TFTP_HOST" "$TFTP_PORT" || true

echo "[✓] All tests completed successfully."
on_success
exit 0
