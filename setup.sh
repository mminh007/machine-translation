#!/bin/bash

ENV_NAME="translator"
YAML_FILE="environment.yaml"

echo "🔧 Creating conda environment '$ENV_NAME' from $YAML_FILE ..."
conda env create -f "$YAML_FILE"

echo "✅ Environment '$ENV_NAME' created."
echo "👉 To activate, run:"
echo "    conda activate $ENV_NAME"
