#!/bin/bash

ENV_NAME="translator"
SCRIPT_PATH="app_ngrok.py"

# Check env has existed
if ! command -v conda &> /dev/null
then
    echo "❌ Conda is not installed or not in PATH. Please install Miniconda/Anaconda first."
    exit 1
fi

#
if ! conda info --envs | grep -q "^$ENV_NAME"
then
    echo "❌ Conda environment '$ENV_NAME' does not exist. Please run:"
    echo "    conda env create -f environment.yaml"
    exit 1
fi

echo "✅ Activating conda environment: $ENV_NAME"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"

#
echo "🚀 Running $SCRIPT_PATH ..."
python "$SCRIPT_PATH"
