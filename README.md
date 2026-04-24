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

Fetching large assets for team
 - To avoid committing large binary files to git, use the provided script `scripts/fetch_assets.sh`.
 - Example: `scripts/fetch_assets.sh assets` will download the Miniforge installer into `assets/`.
 - You can set `DEEPSEEK_URL` to a tar.gz that contains the `DeepSeek-V4-Pro` checkpoint tree, and `SESAME_PROMPTS_URL` to prompts archive.

Example usage (download Miniforge and DeepSeek archive):
```bash
# export DEEPSEEK_URL="https://example.com/deepseek.tar.gz"
DEEPSEEK_URL="<url-to-deepseek-tar.gz>" scripts/fetch_assets.sh assets
```

Team workflow
 - Clone repository with submodules:
	 - `git clone --recurse-submodules <repo>`
 - Run `scripts/fetch_assets.sh` (or set the environment variables and run) to fetch large installers and model checkpoints into place.
 - This keeps the main git history small and lets team members obtain large assets from an external host.

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
