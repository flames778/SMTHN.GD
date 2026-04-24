#!/usr/bin/env bash
set -euo pipefail
# Create a conda env with Python 3.11 and install PyTorch + deps for Jarvis
ENV_NAME=${1:-jarvis}
PYTHON_VERSION=${2:-3.11}

echo "Creating conda env '$ENV_NAME' with Python $PYTHON_VERSION..."
conda create -n "$ENV_NAME" python="$PYTHON_VERSION" -y
echo "Installing PyTorch and torchaudio (conda-forge / pytorch channels)..."
conda install -n "$ENV_NAME" -c pytorch -c conda-forge pytorch torchaudio torchvision -y

echo "Upgrading pip and installing Python packages into the env..."
conda run -n "$ENV_NAME" pip install --upgrade pip setuptools wheel
conda run -n "$ENV_NAME" pip install transformers safetensors huggingface_hub sounddevice soundfile openai-whisper boto3

echo "Done. To use the env: conda activate $ENV_NAME"
