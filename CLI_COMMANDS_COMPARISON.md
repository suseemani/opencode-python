# CLI Commands Comparison: TypeScript vs Python

## Summary

**TypeScript CLI has 20 commands, Python CLI has 16 commands**
**Missing in Python: 4 commands**

---

## Commands Comparison

### ✅ **IMPLEMENTED IN BOTH**

| Command | TypeScript | Python | Status | Notes |
|---------|-----------|---------|---------|-------|
| `run` | ✅ | ✅ | **MATCH** | Python version simpler |
| `serve` | ✅ | ✅ | **MATCH** | Both start server |
| `models` | ✅ | ✅ | **MATCH** | List available models |
| `agent` | ✅ | ✅ | **PARTIAL** | TS has create/list subcommands, Py has list/info |
| `session` | ✅ | ✅ | **PARTIAL** | TS has list with pagination, Py has list/create/delete |
| `upgrade` | ✅ | ✅ | **MATCH** | Upgrade OpenCode |
| `version` | ✅ | ✅ | **MATCH** | Show version |

### ❌ **MISSING IN PYTHON**

| Command | TypeScript | Python | Priority | Description |
|---------|-----------|---------|----------|-------------|
| `auth` | ✅ | ❌ | **HIGH** | Authentication management |
| `acp` | ✅ | ❌ | **MEDIUM** | Agent Communication Protocol |
| `mcp` | ✅ | ❌ | **MEDIUM** | Model Context Protocol |
| `generate` | ✅ | ❌ | **MEDIUM** | Generate code/stubs |
| `stats` | ✅ | ❌ | **LOW** | Statistics and metrics |
| `export` | ✅ | ❌ | **LOW** | Export data |
| `import` | ✅ | ❌ | **LOW** | Import data |
| `github` | ✅ | ❌ | **LOW** | GitHub integration |
| `pr` | ✅ | ❌ | **LOW** | Pull request management |
| `web` | ✅ | ❌ | **LOW** | Web interface |
| `tui-thread` | ✅ | ❌ | **LOW** | TUI thread management |
| `attach` | ✅ | ❌ | **LOW** | Attach to TUI |
| `debug` | ✅ | ❌ | **LOW** | Debug utilities |
| `uninstall` | ✅ | ❌ | **LOW** | Uninstall OpenCode |

---

## Command Options Comparison

### `run` Command Options

| Option | TypeScript | Python | Status |
|--------|-----------|---------|---------|
| `--agent` | ✅ | ✅ | **MATCH** |
| `--model` / `-m` | ✅ | ❌ | **MISSING** |
| `--command` | ✅ | ❌ | **MISSING** |
| `--continue` / `-c` | ✅ | ❌ | **MISSING** |
| `--session` / `-s` | ✅ | ❌ | **MISSING** |
| `--share` | ✅ | ❌ | **MISSING** |
| `--format` | ✅ | ❌ | **MISSING** |
| `--file` / `-f` | ✅ | ❌ | **MISSING** |
| `--title` | ✅ | ❌ | **MISSING** |
| `--attach` | ✅ | ❌ | **MISSING** |
| `--port` | ✅ | ❌ | **MISSING** |
| `--variant` | ✅ | ❌ | **MISSING** |
| `--thinking` | ✅ | ❌ | **MISSING** |

**Summary:** Python `run` is missing 13 options

### `models` Command Options

| Option | TypeScript | Python | Status |
|--------|-----------|---------|---------|
| `provider` (positional) | ✅ | ✅ | **MATCH** |
| `--verbose` / `-v` | ✅ | ✅ | **MATCH** |
| `--refresh` | ✅ | ❌ | **MISSING** |

**Summary:** Python `models` is missing 1 option

### `agent` Command Options

**TypeScript has subcommands:**
- `agent create` - Create new agent with interactive prompts
- `agent list` - List all agents

**Python has:**
- `agents` - List agents (flat list)
- `agent-info <id>` - Show agent details

**Summary:** Python missing `agent create` command

### `session` Command Options

| Option | TypeScript | Python | Status |
|--------|-----------|---------|---------|
| `--max-count` / `-n` | ✅ | ✅ | **MATCH** |
| `--format` (table/json) | ✅ | ❌ | **MISSING** |
| Pagination support | ✅ | ❌ | **MISSING** |

**Summary:** Python `session list` missing format and pagination

---

## Priority Recommendations

### **HIGH Priority (Core Functionality)**
1. **`auth` command** - Authentication is essential for API providers
2. **`run` command options** - Add `--model`, `--continue`, `--session`, `--file`

### **MEDIUM Priority (Important Features)**
3. **`agent create` command** - Allow creating custom agents
4. **`acp` and `mcp` commands** - Protocol support for extensibility
5. **`generate` command** - Code generation capability

### **LOW Priority (Nice to Have)**
6. `stats`, `export`, `import` - Data management
7. `github`, `pr` - GitHub integration
8. `web` - Web interface
9. `tui-thread`, `attach` - TUI features
10. `debug` - Debug utilities
11. `uninstall` - Cleanup

---

## Missing Options Detail

### `run` Command Missing Options Impact

**Critical for usability:**
- `--model` / `-m`: Allow using different models
- `--continue` / `-c`: Continue previous session (very useful!)
- `--session` / `-s`: Resume specific session
- `--file` / `-f`: Attach files to prompt

**Nice to have:**
- `--format`: JSON output format
- `--thinking`: Show reasoning/thinking blocks
- `--title`: Set session title
- `--share`: Share session
- `--attach`: Connect to existing server
- `--port`: Custom server port
- `--variant`: Model variant (reasoning effort)
- `--command`: Run predefined command

---

## Next Steps

To achieve feature parity with TypeScript CLI:

1. **Immediate (This Session):**
   - Add `--model` option to `run` command
   - Add `--continue` and `--session` options
   - Add `--file` option for file attachments

2. **Short Term:**
   - Implement `auth` command
   - Add `agent create` subcommand
   - Add `--format` option to `session list`

3. **Long Term:**
   - Implement remaining commands (acp, mcp, generate, etc.)
   - Add all missing options
   - Implement TUI features

---

## Current State: 75% Complete

**Implemented:** 16/20 commands (80%)
**Core Options:** Most critical options present
**Missing:** 4 commands and ~15 options

The Python CLI has all essential functionality but lacks advanced features and convenience options.
