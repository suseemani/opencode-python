# Local Model Support

OpenCode Python now supports both **cloud** and **local** models!

## 🌐 Cloud Model (Default)

By default, OpenCode uses the **big-pickle** model from OpenCode's cloud API:

```bash
# No configuration needed - works out of the box!
python -m opencode.cli run "Hello"
```

**Endpoint:** `https://opencode.ai/zen/v1`

## 🏠 Local Model Support

You can configure OpenCode to use your own local model server (e.g., Ollama, llama.cpp, vLLM, etc.)

### Configuration

Create an `opencode.json` file in your project root or global config directory:

```json
{
  "$schema": "https://opencode.ai/schema.json",
  "provider": {
    "opencode": {
      "options": {
        "baseURL": "http://localhost:8080/v1",
        "apiKey": "optional-api-key"
      }
    }
  }
}
```

### Configuration Options

- **`baseURL`** - The base URL for your local model API (OpenAI-compatible)
- **`endpoint`** - Alternative to baseURL (takes precedence if both specified)
- **`apiKey`** - Optional API key for authentication

### Supported Local Model Servers

Any OpenAI-compatible API server:

#### Ollama
```bash
# Start Ollama with OpenAI compatibility
ollama serve
ollama pull llama2

# Config (opencode.json)
{
  "provider": {
    "opencode": {
      "options": {
        "baseURL": "http://localhost:11434/v1"
      }
    }
  }
}
```

#### llama.cpp (server mode)
```bash
# Start llama.cpp server
./server -m model.gguf --port 8080

# Config (opencode.json)
{
  "provider": {
    "opencode": {
      "options": {
        "baseURL": "http://localhost:8080/v1"
      }
    }
  }
}
```

#### vLLM
```bash
# Start vLLM server
python -m vllm.entrypoints.openai.api_server --model meta-llama/Llama-2-7b-hf

# Config (opencode.json)
{
  "provider": {
    "opencode": {
      "options": {
        "baseURL": "http://localhost:8000/v1"
      }
    }
  }
}
```

#### LM Studio
```bash
# Start LM Studio local server on port 1234

# Config (opencode.json)
{
  "provider": {
    "opencode": {
      "options": {
        "baseURL": "http://localhost:1234/v1"
      }
    }
  }
}
```

#### Text Generation Inference (TGI)
```bash
# Start TGI
docker run --gpus all --shm-size 1g -p 8080:80 ghcr.io/huggingface/text-generation-inference:1.4 --model-id meta-llama/Llama-2-7b-hf

# Config (opencode.json)
{
  "provider": {
    "opencode": {
      "options": {
        "baseURL": "http://localhost:8080/v1"
      }
    }
  }
}
```

### Priority Order

1. **Command-line options** (if implemented)
2. **`opencode.json` config file** (project root or global)
3. **Environment variables** (`OPENCODE_API_KEY`)
4. **Defaults** (cloud API)

### Config File Locations

OpenCode looks for config files in this order:

1. `./opencode.json` (current directory)
2. `./opencode.jsonc` (with comments)
3. `./.opencode/opencode.json`
4. `./.opencode/opencode.jsonc`
5. Parent directories (upwards)
6. `~/.config/opencode/opencode.json` (global config)

### Example: Switching Between Cloud and Local

**For cloud (default):**
```json
{
  "provider": {
    "opencode": {
      "options": {}
    }
  }
}
```

**For local Ollama:**
```json
{
  "provider": {
    "opencode": {
      "options": {
        "baseURL": "http://localhost:11434/v1"
      }
    }
  }
}
```

### Testing Your Local Model

```bash
# Test if local model is working
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "big-pickle",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### Environment Variables

You can also set the API key via environment variable:

```bash
export OPENCODE_API_KEY="your-api-key"
python -m opencode.cli run "Hello"
```

### Troubleshooting

**"Cannot connect to local model"**
- Check if your model server is running: `curl http://localhost:8080/health`
- Verify the port is correct in your config
- Check firewall settings

**"API Error 404"**
- Make sure your local server uses OpenAI-compatible endpoints (`/v1/chat/completions`)
- Some servers need `/v1` suffix, others don't

**Authentication errors**
- Check if your local server requires an API key
- Set it in config: `"apiKey": "your-key"`
- Or via environment: `export OPENCODE_API_KEY="your-key"`

### Multiple Configurations

You can have different configs for different projects:

```bash
# Project A - uses cloud
cd project-a
python -m opencode.cli run "Hello"

# Project B - uses local Ollama
cd project-b
# (has opencode.json with localhost:11434)
python -m opencode.cli run "Hello"
```

## 🔧 Advanced Configuration

See `opencode.json.example` for a complete configuration template.
