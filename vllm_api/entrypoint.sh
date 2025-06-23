#!/bin/bash
set -e

# Find the Python executable
PYTHON_CMD=$(which python3 2>/dev/null || which python 2>/dev/null)
if [ -z "$PYTHON_CMD" ]; then
    echo "Python executable not found! Please install Python."
    exit 1
fi

echo "Using Python executable: $PYTHON_CMD"

$PYTHON_CMD -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3.2-1B-Instruct \
    --served-model-name llama-32-1B-instruct \
    --api-key paos2025 \
    --port 8001 \
    --quantization bitsandbytes \
    --gpu-memory-utilization 0.7 \
    --max-model-len 2048 \
    --dtype half

    