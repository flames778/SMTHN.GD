Jarvis (DeepSeek + Sesame CSM) Integration

Overview
- This repo integrates DeepSeek-V4-Pro (text generation) with Sesame CSM (voice generation) into a simple assistant called Jarvis.

Quick start (recommended: conda/miniforge on macOS)

1. Install Miniforge and create env

```bash
# Install Miniforge (if not installed) then open a new terminal
conda create -n jarvis python=3.11 -y
conda activate jarvis
```

2. Install PyTorch + torchaudio via conda

```bash
conda install -c pytorch -c conda-forge pytorch torchaudio -y
```

3. Install the rest of the requirements

```bash
pip install --upgrade pip setuptools wheel
# remove or skip torch in requirements if conda installed it
pip install -r requirements.txt --no-deps
pip install openai-whisper sounddevice soundfile
```

4. Place DeepSeek checkpoints

Put your DeepSeek checkpoint directory at `./DeepSeek-V4-Pro` (contains `model0-mp1.safetensors` and friends) and ensure `./DeepSeek-V4-Pro/inference/config.json` exists.

5. (Optional) Set Hugging Face token for downloads

```bash
export HUGGINGFACE_HUB_TOKEN="hf_xxx"
```

Run Jarvis (dry-run, fast)

```bash
# dry-run skips heavy models and simulates behavior
python jarvis.py --dry-run
```

Run full Jarvis (real models)

```bash
python jarvis.py --ds-ckpt ./DeepSeek-V4-Pro --ds-config ./DeepSeek-V4-Pro/inference/config.json
```

Flags
- `--dry-run`: simulate responses without loading model weights (useful for development)
- `--enable-wake`: enable microphone wake-word listening (requires `sounddevice` and `openai-whisper`)
- `--wake-word`: set the wake word (default `jarvis`)
- `--device`: `auto|cpu|mps|cuda` (auto-detects `mps` on macOS)
- `--once`: print greeting and exit

Notes
- On macOS, generated audio is played automatically with `afplay` (non-dry runs).
- CPU-only inference for large models may be slow; prefer machines with GPUs or Apple MPS where available.

If you want, I can help automate environment setup or run a full end-to-end test if you provide model checkpoints and confirm you want me to proceed.
