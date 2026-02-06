# Using the OpenCode CLI Run Command

## 🚀 Quick Start

The `run` command sends a prompt to an AI and streams the response back.

### Prerequisites

You need an API key from either OpenAI or Anthropic:

**Option 1: OpenAI (Recommended)**
```bash
# Get your API key from: https://platform.openai.com/api-keys
export OPENAI_API_KEY='sk-...'
```

**Option 2: Anthropic**
```bash
# Get your API key from: https://console.anthropic.com/
export ANTHROPIC_API_KEY='sk-ant-...'
```

**Windows:**
```cmd
set OPENAI_API_KEY=sk-...
```

## 💬 Basic Usage

### Simple prompt
```bash
python -m opencode.cli run "Hello, how are you?"
```

### With specific agent
```bash
python -m opencode.cli run "Fix this bug" --agent build
python -m opencode.cli run "Explain this code" --agent explore
python -m opencode.cli run "Design a system" --agent plan
```

### With specific model
```bash
# OpenAI models
python -m opencode.cli run "Hello" --model gpt-4o
python -m opencode.cli run "Hello" --model gpt-4o-mini

# Anthropic models
python -m opencode.cli run "Hello" --model claude-3-5-sonnet-20241022
python -m opencode.cli run "Hello" --model claude-3-opus-20240229
```

### With specific provider
```bash
python -m opencode.cli run "Hello" --provider openai
python -m opencode.cli run "Hello" --provider anthropic
```

## 📝 Examples

### Code Review
```bash
python -m opencode.cli run "Review this Python function for bugs: def add(a, b): return a + b" --agent build
```

### Code Explanation
```bash
python -m opencode.cli run "Explain what this code does: [paste code here]" --agent explore
```

### Architecture Planning
```bash
python -m opencode.cli run "Design a microservice for user authentication" --agent plan
```

### File Analysis
```bash
python -m opencode.cli run "Read this file and tell me what it does" --agent explore < main.py
```

## 🔧 How It Works

1. **Creates a session** - Your conversation is saved for later reference
2. **Sends to AI** - The prompt goes to OpenAI or Anthropic API
3. **Streams response** - You see the AI's response as it's generated
4. **Saves conversation** - Both your prompt and the AI's response are saved

## 📊 Output Format

```
Session: ses_xxx...
Agent: General
Model: gpt-4o
Provider: openai

User: Hello, how are you?

Assistant: I'm doing well, thank you! How can I help you today?

Session saved: ses_xxx...
```

## 🎯 Available Agents

| Agent | Purpose |
|-------|---------|
| `general` | General-purpose coding assistant |
| `build` | Build and compilation specialist |
| `plan` | Architecture and planning specialist |
| `explore` | Code exploration specialist |

## 🤖 Available Models

### OpenAI
- `gpt-4o` - Latest GPT-4 Omni (128K context)
- `gpt-4o-mini` - Smaller, faster version (128K context)
- `gpt-4-turbo` - GPT-4 Turbo (128K context)

### Anthropic
- `claude-3-5-sonnet-20241022` - Claude 3.5 Sonnet (200K context)
- `claude-3-opus-20240229` - Claude 3 Opus (200K context)

### OpenCode
- `big-pickle` - OpenCode's local model (100K context) - Placeholder only

## 🔍 Troubleshooting

### "No API key found"
Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` environment variable.

### "Agent not found"
Use one of: `general`, `build`, `plan`, `explore`

### "Provider not found"
Use one of: `openai`, `anthropic`

## 💡 Tips

1. **Auto-selection**: If you only have one API key set, it will be used automatically
2. **Model selection**: If you don't specify a model, it picks a good default for your provider
3. **Session history**: All conversations are saved and can be viewed with `session list`
4. **Cost control**: Check your OpenAI/Anthropic dashboard to monitor API usage

## 📝 Example Session

```bash
$ export OPENAI_API_KEY='sk-...'
$ python -m opencode.cli run "Write a Python function to calculate fibonacci numbers"
Using OpenAI (set OPENAI_API_KEY)
Session: ses_c30b3e5f3001a5zP...
Agent: General
Model: gpt-4o
Provider: openai

User: Write a Python function to calculate fibonacci numbers

Assistant: Here's a Python function to calculate Fibonacci numbers:

def fibonacci(n):
    """Calculate the nth Fibonacci number."""
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n-1) + fibonacci(n-2)

# Example usage
for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")

Session saved: ses_c30b3e5f3001a5zP...
```

Happy coding! 🚀
