# Model Asset Assessment

Date: 2026-07-17

## DeepSeek V4 Pro

Present:

- Tokenizer and model configuration.
- OpenAI-compatible message encoding and parsing helpers.
- Reference conversion, model, kernel, and generation source.

Absent:

- Converted `model*-mp*.safetensors` checkpoint shards.

Runtime implications:

- The model has 1.6T total parameters and 49B activated parameters.
- Reference inference uses CUDA, model parallelism, Torch 2.10+, and Transformers 5+.
- The reference example uses eight model-parallel processes.
- The legacy `jarvis.py` single-process loader must not be treated as a production runtime for these assets.

Decision:

- Keep DeepSeek V4 as an optional M4 provider target.
- Run it in a dedicated process or hosted runtime with its own dependency environment.
- Reuse the encoding contract for tool calling and reasoning modes through a provider adapter.
- Do not add Torch 2.10 or Transformers 5 to the M1 backend environment.

## Sesame CSM

Current state:

- The `csm/` directory contains only its submodule pointer; generator source is unavailable.
- Real CSM speech generation cannot initialize from this checkout.

Decision:

- Preserve text and fallback/mock voice behavior.
- Restore and validate CSM in M10, where TTS has a health-checked adapter and degraded mode.
- Do not block M1 backend work on voice assets.

## M1 Impact

No M1 domain, identity, persistence, or security design changes are required. The only immediate changes are truthful readiness detection and documentation. Model runtime integration remains isolated to M4 and voice integration to M10.