import os
import sys
try:
    import torch
except Exception:
    torch = None
try:
    import torchaudio
except Exception:
    torchaudio = None
import json
import time
import tempfile
import queue
from datetime import datetime
from argparse import ArgumentParser
try:
    from huggingface_hub import hf_hub_download
except Exception:
    hf_hub_download = None
try:
    from transformers import AutoTokenizer
except Exception:
    AutoTokenizer = None
try:
    from safetensors.torch import load_model
except Exception:
    load_model = None

# Optional realtime audio/ASR
try:
    import sounddevice as sd
    import soundfile as sf
except Exception:
    sd = None
    sf = None

try:
    import whisper
except Exception:
    whisper = None
import glob

# Add paths for both models
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DS_INFERENCE_PATH = os.path.join(BASE_DIR, "DeepSeek-V4-Pro", "inference")
CSM_PATH = os.path.join(BASE_DIR, "csm")

sys.path.insert(0, DS_INFERENCE_PATH)
sys.path.insert(0, CSM_PATH)

# Local imports may require heavy deps; import lazily in Jarvis.__init__
Transformer = None
ModelArgs = None
load_csm_1b = None
Segment = None
encode_messages = None
parse_message_from_completion_text = None

# Set environment variables
os.environ["NO_TORCH_COMPILE"] = "1"

def load_prompt_audio(audio_path: str, target_sample_rate: int) -> torch.Tensor:
    if torchaudio is None:
        raise RuntimeError("torchaudio is required to load audio prompts")
    audio_tensor, sample_rate = torchaudio.load(audio_path)
    audio_tensor = audio_tensor.squeeze(0)
    if audio_tensor.dim() > 1:
        audio_tensor = audio_tensor.mean(dim=0)
    audio_tensor = torchaudio.functional.resample(
        audio_tensor, orig_freq=sample_rate, new_freq=target_sample_rate
    )
    return audio_tensor


def get_preferred_device(requested: str = "auto") -> str:
    """Detect preferred device. Returns one of 'mps', 'cuda', or 'cpu'.

    Pass `requested='cpu'|'mps'|'cuda'` to force selection.
    """
    if requested and requested != "auto":
        return requested
    if torch is None:
        return "cpu"
    try:
        if getattr(torch, "has_mps", False) and getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    try:
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"

def prepare_prompt(text: str, speaker: int, audio_path: str, sample_rate: int) -> Segment:
    audio_tensor = load_prompt_audio(audio_path, sample_rate)
    return Segment(text=text, speaker=speaker, audio=audio_tensor)

class Jarvis:
    def __init__(self, deepseek_ckpt, deepseek_config, device="cuda", dry_run: bool = False):
        self.device = device
        self.dry_run = dry_run
        print(f"Initializing Jarvis on {device}... dry_run={dry_run}")

        # 1. Initialize DeepSeek (The Brain)
        print("Loading DeepSeek-V4-Pro Brain...")
        # detect whether checkpoint files exist to decide whether to import heavy model code
        try:
            ckpt_glob = os.path.join(deepseek_ckpt, 'model*.safetensors')
            models_present = len(glob.glob(ckpt_glob)) > 0
        except Exception:
            models_present = False
        # If dry_run, create lightweight mocks and skip heavy imports
        global Transformer, ModelArgs, load_csm_1b, Segment, encode_messages, parse_message_from_completion_text
        if self.dry_run:
            from dataclasses import dataclass

            @dataclass
            class _Segment:
                speaker: int
                text: str
                audio: object = None

            class _SimpleTokenizer:
                def encode(self, x):
                    return [x]
                def decode(self, toks):
                    if isinstance(toks, list):
                        return toks[0] if toks else ""
                    return str(toks)

            class _MockVoiceGen:
                def __init__(self):
                    self.sample_rate = 24000
                def generate(self, text, speaker, context, max_audio_length_ms=15000):
                    return None

            Transformer = None
            ModelArgs = None
            load_csm_1b = lambda device: _MockVoiceGen()
            Segment = _Segment
            encode_messages = lambda msgs, thinking_mode=None: msgs[-1]["content"] if msgs else ""
            parse_message_from_completion_text = lambda text, thinking_mode=None: {"role": "assistant", "content": text}

            self.brain = None
            self.tokenizer = _SimpleTokenizer()
            self.voice_gen = load_csm_1b(device)
            # setup a default prompt segment
            self.voice_prompt = Segment(speaker=0, text="[dry-run prompt]", audio=None)
        elif models_present:
            # Lazy local imports that depend on torch/torchaudio
            if Transformer is None:
                from model import Transformer, ModelArgs
                from encoding_dsv4 import encode_messages, parse_message_from_completion_text
            if load_csm_1b is None:
                from generator import load_csm_1b, Segment
            with open(deepseek_config) as f:
                ds_args = ModelArgs(**json.load(f))
            ds_args.max_batch_size = 1
            
            if torch is None:
                raise RuntimeError("torch is required to initialize DeepSeek model. Install PyTorch before running Jarvis.")
            with torch.device(device):
                self.brain = Transformer(ds_args)

            if AutoTokenizer is None:
                raise RuntimeError("transformers is required to load tokenizer. Install transformers before running Jarvis.")
            self.tokenizer = AutoTokenizer.from_pretrained(deepseek_ckpt)
            if load_model is None:
                raise RuntimeError("safetensors is required to load model weights. Install safetensors before running Jarvis.")
            load_model(self.brain, os.path.join(deepseek_ckpt, "model0-mp1.safetensors"), strict=False)
        else:
            # No models present and not dry-run: enable fallback generator and skip heavy imports
            self.brain = None
            def _simple_fallback(prompt: str, *args, **kwargs) -> str:
                p = str(prompt).lower()
                if 'hello' in p or 'hi' in p:
                    return 'Hello! I am running in fallback mode. How can I help?'
                if 'joke' in p:
                    return 'Why did the programmer quit his job? Because he didn\'t get arrays.'
                return f"(fallback) I heard: {prompt}. I don't have the full model available right now."
            self._fallback_gen = _simple_fallback
            # provide a lightweight voice generator mock so speak() still works
            class _MockVoiceGenFallback:
                def __init__(self):
                    self.sample_rate = 24000
                def generate(self, text, speaker, context, max_audio_length_ms=15000):
                    return None
            load_csm_1b = lambda device: _MockVoiceGenFallback()
        
        # 2. Initialize Sesame CSM (The Voice)
        print("Loading Sesame CSM Voice Assistant...")
        self.voice_gen = load_csm_1b(device)
        
        if not self.dry_run and models_present:
            # Download default prompts for Sesame when real models/prompts are available
            print("Downloading voice prompts...")
            if hf_hub_download is None:
                raise RuntimeError("huggingface_hub is required to download voice prompts. Install huggingface_hub or provide local prompts.")
            prompt_path = hf_hub_download(repo_id="sesame/csm-1b", filename="prompts/conversational_a.wav")
            self.voice_prompt = prepare_prompt(
                "like revising for an exam I'd have to try and like keep up the momentum because I'd start really early",
                0,
                prompt_path,
                self.voice_gen.sample_rate
            )
        else:
            # fallback prompt segment
            try:
                self.voice_prompt = Segment(speaker=0, text="[fallback prompt]", audio=None)
            except Exception:
                self.voice_prompt = None
        self.messages = []
        self.voice_history = [self.voice_prompt]

    def think(self, user_input):
        self.messages.append({"role": "user", "content": user_input})
        if self.dry_run:
            response = f"(dry-run) Echo: {user_input}"
            parsed_message = {"role": "assistant", "content": response}
            self.messages.append(parsed_message)
            return parsed_message["content"]
        # If DeepSeek not available, use fallback HF generator if present
        if getattr(self, 'brain', None) is None:
            if getattr(self, '_fallback_gen', None) is not None:
                prompt = encode_messages(self.messages, thinking_mode="chat") if encode_messages is not None else user_input
                try:
                    out = self._fallback_gen(prompt, max_new_tokens=150, do_sample=True, temperature=0.7)
                    text = out[0]['generated_text'] if isinstance(out, list) and out else str(out)
                except Exception:
                    text = f"(fallback) I couldn't generate a response right now."
                parsed_message = {"role": "assistant", "content": text}
                self.messages.append(parsed_message)
                return parsed_message["content"]

        prompt_tokens = self.tokenizer.encode(encode_messages(self.messages, thinking_mode="chat"))

        # Generate from DeepSeek
        from generate import generate as ds_generate
        completion_tokens = ds_generate(self.brain, [prompt_tokens], 300, self.tokenizer.eos_token_id, 0.6)
        completion_text = self.tokenizer.decode(completion_tokens[0])

        # Parse response (removing thinking tokens if any)
        parsed_message = parse_message_from_completion_text(completion_text, thinking_mode="chat")
        self.messages.append(parsed_message)
        return parsed_message["content"]

    def speak(self, text):
        print(f"Jarvis: {text}")
        if self.dry_run:
            # In dry-run mode, just append a segment placeholder and skip audio generation
            self.voice_history.append(Segment(text=text, speaker=0, audio=None))
            print("(dry-run) voice skipped, not saving audio")
            return
        # Try to generate audio via voice generator (may be a mock)
        audio_tensor = None
        try:
            if getattr(self, 'voice_gen', None) is not None:
                audio_tensor = self.voice_gen.generate(
                    text=text,
                    speaker=0,
                    context=self.voice_history,
                    max_audio_length_ms=15_000
                )
        except Exception:
            audio_tensor = None

        output_path = "jarvis_response.wav"
        # If we got audio and torchaudio is available, save it
        if audio_tensor is not None and torchaudio is not None:
            try:
                # audio_tensor expected shape [samples] or tensor; ensure 2D for torchaudio
                tensor = audio_tensor
                if hasattr(tensor, 'unsqueeze'):
                    tensor_out = tensor.unsqueeze(0).cpu()
                else:
                    import torch as _torch
                    tensor_out = _torch.tensor(tensor).unsqueeze(0)
                torchaudio.save(output_path, tensor_out, self.voice_gen.sample_rate)
                # play on macOS
                if sys.platform == "darwin":
                    try:
                        os.system(f"afplay {output_path} &")
                    except Exception:
                        pass
                print(f"Voice saved to {output_path}")
            except Exception:
                audio_tensor = None

        # If no generated audio, fall back to platform TTS (macOS `say`) to ensure reply is audible
        if audio_tensor is None:
            try:
                if sys.platform == 'darwin':
                    os.system(f"say {text!r} &")
                else:
                    # Non-darwin fallback: try to print a hint for the user to play audio
                    print("(no audio generated) ->", text)
            except Exception:
                print("(tts fallback failed)")

        # Update voice context (keep small window)
        try:
            self.voice_history.append(Segment(text=text, speaker=0, audio=audio_tensor))
            if len(self.voice_history) > 8:
                # keep prompt + recent history
                self.voice_history = [self.voice_history[0]] + self.voice_history[-7:]
        except Exception:
            pass

def main():
    parser = ArgumentParser()
    parser.add_argument("--ds-ckpt", type=str, default="./DeepSeek-V4-Pro")
    parser.add_argument("--ds-config", type=str, default="./DeepSeek-V4-Pro/inference/config.json")
    parser.add_argument("--enable-wake", action="store_true", help="Enable wake-word listening via microphone (optional deps) ")
    parser.add_argument("--wake-word", type=str, default="jarvis", help="Wake word to listen for (simple ASR-based detection)")
    parser.add_argument("--device", type=str, choices=["auto", "cpu", "mps", "cuda"], default="auto", help="Device to run models on (auto detects mps/cuda/cpu)")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode (no model weights, fast) ")
    parser.add_argument("--once", action="store_true", help="Print greeting and exit (non-interactive)")
    args = parser.parse_args()

    # Choose device (prefer MPS on macOS when available)
    def get_preferred_device(requested: str = "auto") -> str:
        if requested and requested != "auto":
            return requested
        if torch is None:
            return "cpu"
        try:
            if getattr(torch, "has_mps", False) and getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
                return "mps"
        except Exception:
            pass
        try:
            if torch.cuda.is_available():
                return "cuda"
        except Exception:
            pass
        return "cpu"

    device = get_preferred_device(args.device)
    
    jarvis = Jarvis(args.ds_ckpt, args.ds_config, device=device, dry_run=args.dry_run)

    print("\n--- Jarvis is Online ---")

    # Send a time-aware greeting on startup
    def time_greeting() -> str:
        now = datetime.now()
        hour = now.hour
        if 5 <= hour < 12:
            part = "Good morning"
        elif 12 <= hour < 18:
            part = "Good afternoon"
        elif 18 <= hour < 22:
            part = "Good evening"
        else:
            part = "Hello"
        timestr = now.strftime("%I:%M %p").lstrip('0')
        return f"{part}, the time is {timestr}. How can I help you today?"

    greeting = time_greeting()
    print(greeting)
    try:
        jarvis.messages.append({"role": "assistant", "content": greeting})
    except Exception:
        pass
    try:
        jarvis.speak(greeting)
    except Exception:
        print("(greeting playback skipped)")

    if args.once:
        print("Exiting after one greeting (--once).")
        return

    # If wake enabled but ASR deps missing, warn and fall back to keyboard
    use_wake = args.enable_wake and sd is not None and whisper is not None and sf is not None
    if args.enable_wake and not use_wake:
        print("Wake-word requested but optional microphone/ASR dependencies are missing.")
        print("Install `sounddevice soundfile whisper` or run without `--enable-wake` to use keyboard input.")

    # Prepare whisper model lazily
    asr_model = None
    def get_asr_model():
        nonlocal asr_model
        if asr_model is None and whisper is not None:
            try:
                asr_model = whisper.load_model("small")
            except Exception as e:
                print("Failed to load whisper ASR model:", e)
                asr_model = None
        return asr_model

    def record_to_file(duration_s: float, sample_rate: int = 16000) -> str:
        if sd is None or sf is None:
            raise RuntimeError("sounddevice/soundfile not available")
        data = sd.rec(int(duration_s * sample_rate), samplerate=sample_rate, channels=1, dtype="float32")
        sd.wait()
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        sf.write(tmp.name, data, sample_rate)
        return tmp.name

    def transcribe_file(path: str) -> str:
        model = get_asr_model()
        if model is None:
            return ""
        try:
            result = model.transcribe(path)
            return result.get("text", "").strip().lower()
        except Exception:
            return ""

    try:
        while True:
            try:
                if use_wake:
                    # listen in short bursts for wakeword, then record a longer utterance
                    print(f"Listening for wake word '{args.wake_word}' (short snippets)...")
                    snippet_path = record_to_file(2.0)
                    text = transcribe_file(snippet_path)
                    try:
                        os.remove(snippet_path)
                    except Exception:
                        pass
                    print("Heard:", text)
                    if args.wake_word.lower() in text:
                        print("Wake word detected — recording your utterance (speak now)...")
                        # record a shorter utterance to keep responsiveness
                        user_audio = record_to_file(8.0)
                        user_text = transcribe_file(user_audio)
                        try:
                            os.remove(user_audio)
                        except Exception:
                            pass
                        if not user_text:
                            print("Couldn't transcribe speech, please type instead:")
                            user_input = input("You: ")
                        else:
                            user_input = user_text
                        if user_input.lower() in ["exit", "quit", "bye"]:
                            break
                        response_text = jarvis.think(user_input)
                        jarvis.speak(response_text)
                        continue
                    else:
                        # no wake word, continue listening
                        continue
                else:
                    user_input = input("\nYou: ")
                    if user_input.lower() in ["exit", "quit", "bye"]:
                        break
                    response_text = jarvis.think(user_input)
                    jarvis.speak(response_text)
            except KeyboardInterrupt:
                break
    except Exception as e:
        print("Encountered error in main loop:", e)
    print("\nJarvis is going offline. Goodbye.")

if __name__ == "__main__":
    main()
