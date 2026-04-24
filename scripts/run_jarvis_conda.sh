#!/usr/bin/env bash
set -euo pipefail
# Wrapper to run Jarvis inside the conda env created by setup_conda_env.sh
ENV_NAME=${1:-jarvis}
shift || true
echo "Activating conda env: $ENV_NAME"
# shellcheck disable=SC1091
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"

echo "Running Jarvis with args: $@"
python jarvis.py "$@"
