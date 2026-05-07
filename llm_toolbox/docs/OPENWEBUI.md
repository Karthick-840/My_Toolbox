# OpenWebUI Integration

This guide is focused on connecting OpenWebUI to the `llm_toolbox` OpenAI-compatible endpoint.

## Prerequisites

- Python environment with this repository installed
- Optional local Ollama runtime (for local models)
- Docker installed if you want to run OpenWebUI in a container

## 1) Start model backends

If you want local models via Ollama:

```sh
ollama serve
ollama pull gemma3:latest
```

If you want Gemini routing, make sure your key is set:

```sh
export GOOGLE_API_KEY="your-key"
```

## 2) Start the OpenAI-compatible server

From repository root:

```sh
python -m llm_toolbox.chat_serving.run_openai_compat
```

Default endpoint:

```text
http://localhost:8000/v1
```

## 3) Run OpenWebUI

Using Docker (recommended):

```sh
docker run -d \
	-p 3000:8080 \
	--add-host=host.docker.internal:host-gateway \
	-v open-webui:/app/backend/data \
	--name open-webui \
	ghcr.io/open-webui/open-webui:main
```

Then open:

```text
http://localhost:3000
```

## 4) Connect OpenWebUI to llm_toolbox

In OpenWebUI:

1. Go to Admin Settings.
2. Open Connections (or external provider settings).
3. Add an OpenAI-compatible connection.
4. Set Base URL to `http://host.docker.internal:8000/v1` if OpenWebUI runs in Docker.
5. Set API key to any placeholder value (the local endpoint does not require a real OpenAI key).

If OpenWebUI runs on the host (not Docker), use:

```text
http://localhost:8000/v1
```

## 5) Choose models in OpenWebUI

The backend supports routing by model name:

- Model names starting with `gemini` route to Gemini.
- Other model names route to Ollama.

Examples:

- `gemma3:latest`
- `llama3.2:latest`
- `gemini-1.5-flash`

## Troubleshooting

- No models visible:
	- Confirm `python -m llm_toolbox.chat_serving.run_openai_compat` is running.
	- Verify OpenWebUI can reach the endpoint URL.
- Connection works but generations fail:
	- For Ollama models, ensure `ollama serve` is running and model is pulled.
	- For Gemini models, confirm `GOOGLE_API_KEY` is set in the server environment.
- Docker networking issues:
	- Use `host.docker.internal` from OpenWebUI container to access host services.

## Architecture Note

- `llm_toolbox` provides shared adapters and the OpenAI-compatible API.
- `ollama_toolbox` keeps Ollama-local runtime wrappers.
- OpenWebUI remains a UI layer connected through the shared API path.