#!/bin/bash
set -e

# Find the Python executable
PYTHON_CMD=$(which python3 2>/dev/null || which python 2>/dev/null)
if [ -z "$PYTHON_CMD" ]; then
    echo "Python executable not found! Please install Python."
    exit 1
fi

echo "Using Python executable: $PYTHON_CMD"

$PYTHON_CMD -m llm server \
     --model llama-2-7b-chat.Q3_K_M.gguf \
     --served-model-name llama-llm-2-7b-Q3-K-M \
     --n_ctx 1024 \
     --n_threads 4 \
     --api-key paos2025 \
     --port 8002 \
     --mlock

