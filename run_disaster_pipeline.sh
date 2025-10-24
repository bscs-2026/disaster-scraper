#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit
PYTHON_PATH="/usr/local/bin/python3"
LOG_FILE="$SCRIPT_DIR/logs/pipeline_cron.log"

mkdir -p "$SCRIPT_DIR/logs"

echo "[$(date)] Starting Disaster Pipeline..."
echo "[$(date)] Starting Disaster Pipeline..." >> "$LOG_FILE" 2>&1

"$PYTHON_PATH" "$SCRIPT_DIR/src/run_full_pipeline.py" --auto 2>&1 | tee -a "$LOG_FILE"

echo "[$(date)] Pipeline finished."
echo "[$(date)] Pipeline finished." >> "$LOG_FILE" 2>&1
