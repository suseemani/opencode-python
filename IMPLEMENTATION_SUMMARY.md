# Local Model & Context Management Implementation

## ✅ Completed Features

### 1. Local Model Support

The provider now supports **both cloud and local models** through configuration.

**Configuration via `opencode.json`:**
```json
{
  "provider": {
    "opencode": {
      "options": {
        "baseURL": "http://localhost:11434/v1",
        "apiKey": "optional-api-key"
      }
    }
  }
}
```

**Priority Order:**
1. Constructor arguments (highest priority)
2. Config file (`opencode.json` or `opencode.jsonc`)
3. Environment variables (`OPENCODE_API_URL`, `OPENCODE_API_KEY`)
4. Defaults (cloud API)

**Supported Local Model Servers:**
- Ollama (`http://localhost:11434/v1`)
- llama.cpp (`http://localhost:8080/v1`)
- vLLM (`http://localhost:8000/v1`)
- LM Studio (`http://localhost:1234/v1`)
- Text Generation Inference
- Any OpenAI-compatible API

### 2. Context Management & Compaction

Implemented context reduction strategies to handle long conversations:

**Strategies:**

#### A. Pruning (`prune_messages`)
- Removes old messages from the beginning
- Protects recent messages (default: 40K tokens)
- Keeps system message always

#### B. Compaction (`compact_messages`)
- Replaces old messages with a summary
- Keeps system message and last 3 messages
- Adds context summary

#### C. Middle-Out (`middle_out_prune`)
- Keeps beginning (system + initial context)
- Keeps end (recent messages)
- Removes middle section
- Adds placeholder indicating removal

**Usage:**
```python
from opencode.session import ContextManager, check_overflow

# Check context overflow
stats = check_overflow(messages, max_context=200000)
if stats.is_overflow:
    print(f"Overflow: {stats.total_tokens} tokens")

# Optimize with strategy
manager = ContextManager(strategy="middle-out")
optimized = manager.optimize(messages)

# Or use specific strategies
from opencode.session import middle_out_prune, prune_messages

# Middle-out: Keep start and end, remove middle
result = middle_out_prune(messages, keep_start=2, keep_end=4)

# Pruning: Remove old messages
result = prune_messages(messages, protect_recent=40000)
```

## 📁 Files Created/Modified

### New Files:
- `opencode/session/compaction.py` - Context management module
- `opencode.json.example` - Example configuration
- `LOCAL_MODELS.md` - Local model documentation

### Modified Files:
- `opencode/provider/provider.py` - Added config loading and local model support
- `opencode/session/__init__.py` - Exported compaction functions

## 🚀 Usage Examples

### Local Model (Ollama)

1. **Create config file** (`opencode.json`):
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

2. **Start Ollama:**
```bash
ollama serve
ollama pull llama2
```

3. **Run OpenCode:**
```bash
python -m opencode.cli run "Hello"
```

### Context Management

```python
from opencode.session import (
    ContextManager,
    check_overflow,
    middle_out_prune
)

# Long conversation
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Question 1..."},
    {"role": "assistant", "content": "Answer 1..."},
    # ... many more messages
]

# Check overflow
stats = check_overflow(messages, max_context=200000)
print(f"Tokens: {stats.total_tokens}, Overflow: {stats.is_overflow}")

# Apply middle-out strategy
optimized = middle_out_prune(
    messages,
    keep_start=2,      # Keep system + first user
    keep_end=4,        # Keep last 4 messages
    max_tokens=160000
)
```

## 🔧 Configuration Options

### Config File Locations (in order):
1. `./opencode.json`
2. `./opencode.jsonc` (with comments)
3. `./.opencode/opencode.json`
4. `./.opencode/opencode.jsonc`
5. Parent directories (traversing up)
6. `~/.config/opencode/opencode.json` (global)

### Provider Options:
- `baseURL` / `baseUrl` - API endpoint URL
- `endpoint` - Alternative to baseURL (takes precedence)
- `apiKey` / `api_key` - Authentication key

## 📝 Notes

- The provider auto-detects local mode (checks for `localhost`, `127.0.0.1`, or `http://`)
- Config files support JSON with comments (`.jsonc` extension)
- Context management is automatic when enabled in config
- All strategies preserve the system message
