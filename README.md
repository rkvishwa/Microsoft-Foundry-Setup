# Microsoft Foundry Chat

A minimal FastAPI web app that connects to **Microsoft Azure AI Foundry** (or any OpenAI-compatible endpoint) and provides a clean chat UI. It supports both the **Chat Completions** API and the newer **Responses** API.

## Features

- **FastAPI backend** with `/api/chat` endpoint
- **Single-page web UI** — clean, dark-themed, responsive
- **Dual API mode toggle**:
  - *Chat Completions* — classic conversation with message history
  - *Responses* — stateful API using `previous_response_id`
- **Environment-based configuration** via `.env`
- **Auto-normalization** of Foundry base URLs (`*.services.ai.azure.com`)

## Requirements

- Python 3.10+
- An Azure AI Foundry project with a deployed model and API key

## Setup

1. **Install dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment variables**

   Copy the example file and add your API key:

   ```bash
   cp .env.example .env
   ```

   Edit `.env`:

   ```env
   AZURE_AI_API_KEY=your-azure-foundry-api-key
   ```

   Optional overrides:

   ```env
   AZURE_AI_ENDPOINT=https://your-resource.services.ai.azure.com/openai/v1
   AZURE_AI_DEPLOYMENT=Your-Model-Deployment-Name
   ```

   > **Tip:** If you only configure the host (`*.services.ai.azure.com`), the app automatically appends `/openai/v1`.

3. **Run the server**

   ```bash
   uvicorn main:app --reload
   ```

4. **Open in browser**

   Navigate to [http://localhost:8000](http://localhost:8000)

## API Usage

You can also hit the backend directly:

### Chat Completions mode

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "completion",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

### Responses mode

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "response",
    "input": "What is the capital of France?"
  }'
```

## Project Structure

```
.
├── main.py              # FastAPI application
├── static/
│   └── index.html       # Chat UI (vanilla JS + CSS)
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
└── .env                 # Your local secrets (ignored by git)
```

## License

MIT
