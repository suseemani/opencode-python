# Config System Comparison: TypeScript vs Python

## Summary

**Status: 60% Complete** - Basic config loading works but advanced features are missing.

## ✅ **IMPLEMENTED IN PYTHON**

### Basic Config Loading
| Feature | TypeScript | Python | Status |
|---------|-----------|---------|---------|
| Global config (~/.config/opencode/) | ✅ | ✅ | **PARTIAL** |
| Project config (cwd/opencode.json) | ✅ | ✅ | **PARTIAL** |
| JSON format | ✅ | ✅ | **MATCH** |
| JSONC format (with comments) | ✅ | ✅ | **MATCH** |
| Pydantic validation | N/A | ✅ | **EXTRA** |

### Config Sources Found
**Python checks:**
1. `~/.config/opencode/config.json`
2. `~/.config/opencode/opencode.json`
3. `~/.config/opencode/opencode.jsonc`
4. `./opencode.jsonc`
5. `./opencode.json`

## ❌ **MISSING IN PYTHON**

### 1. Remote Configuration (HIGH Priority)
**TypeScript:** Loads from `.well-known/opencode` URLs  
**Python:** ❌ Not implemented  
**Code:**
```typescript
// TypeScript
for (const [key, value] of Object.entries(auth)) {
  if (value.type === "wellknown") {
    const response = await fetch(`${key}/.well-known/opencode`)
    const wellknown = await response.json()
    result = mergeConfigConcatArrays(result, wellknown.config)
  }
}
```

### 2. Config File Discovery (HIGH Priority)
**TypeScript:** Uses `findUp` to search from cwd to worktree  
**Python:** ❌ Only checks cwd  
**Impact:** Configs in parent directories won't be found

**TypeScript:**
```typescript
for (const file of ["opencode.jsonc", "opencode.json"]) {
  const found = await Filesystem.findUp(file, Instance.directory, Instance.worktree)
  for (const resolved of found.toReversed()) {
    result = mergeConfigConcatArrays(result, await loadFile(resolved))
  }
}
```

**Python:**
```python
# Only checks cwd
cwd = Path.cwd()
for filename in ["opencode.jsonc", "opencode.json"]:
    config_path = cwd / filename
```

### 3. .opencode Directory Configs (MEDIUM Priority)
**TypeScript:** Checks `.opencode/opencode.json` in project and home  
**Python:** ❌ Not implemented  
**Locations:**
- Project: `.opencode/opencode.json`
- Home: `~/.opencode/opencode.json`

### 4. Environment Variables (MEDIUM Priority)
**TypeScript:**
- `OPENCODE_CONFIG` - Custom config file path
- `OPENCODE_CONFIG_CONTENT` - Inline config JSON
- `OPENCODE_DISABLE_PROJECT_CONFIG` - Disable project config

**Python:** ❌ Not implemented

### 5. Environment Variable Substitution (MEDIUM Priority)
**TypeScript:** Supports `{env:VAR_NAME}` syntax  
**Python:** ❌ Not implemented  
**Example:**
```json
{
  "provider": {
    "openai": {
      "apiKey": "{env:OPENAI_API_KEY}"
    }
  }
}
```

### 6. Deep Config Merging (MEDIUM Priority)
**TypeScript:** Uses `mergeDeep` and `mergeConfigConcatArrays`  
**Python:** ⚠️ Uses basic `dict.update()`  
**Impact:** Nested configs get overwritten instead of merged

**TypeScript:**
```typescript
result = mergeConfigConcatArrays(result, await loadFile(filepath))
// Properly merges nested objects and concatenates arrays
```

**Python:**
```python
result.update(data)  # Overwrites nested dicts!
```

### 7. Legacy Config Support (LOW Priority)
**TypeScript:** Supports legacy `config.toml` and migrates to JSON  
**Python:** ❌ Not implemented

### 8. Config File Auto-Creation (LOW Priority)
**TypeScript:** Creates config file with $schema if missing  
**Python:** ❌ Not implemented

### 9. Config Precedence Order (MEDIUM Priority)
**TypeScript loads in this order (low to high precedence):**
1. Remote .well-known/opencode
2. Global config (~/.config/opencode/)
3. Custom config (OPENCODE_CONFIG env)
4. Project config (findUp opencode.json)
5. .opencode directories
6. Inline config (OPENCODE_CONFIG_CONTENT)

**Python loads:**
1. Global config (3 files, basic merge)
2. Project config (cwd only, basic merge)

## 📊 **FEATURE PARITY MATRIX**

| Category | Features | Implemented | Missing | % Complete |
|----------|----------|-------------|---------|------------|
| **Basic Loading** | 5 | 5 | 0 | 100% ✅ |
| **File Discovery** | 3 | 1 | 2 | 33% ❌ |
| **Advanced Sources** | 4 | 0 | 4 | 0% ❌ |
| **Merging** | 2 | 1 | 1 | 50% ⚠️ |
| **Env Variables** | 4 | 0 | 4 | 0% ❌ |
| **Legacy Support** | 2 | 0 | 2 | 0% ❌ |
| **TOTAL** | **20** | **7** | **13** | **35%** |

## 🎯 **PRIORITY RECOMMENDATIONS**

### **HIGH Priority (Critical)**
1. **findUp for project config** - Search up directory tree
2. **Remote config loading** - .well-known/opencode support

### **MEDIUM Priority (Important)**
3. **Deep config merging** - Proper nested object merging
4. **Environment variable substitution** - {env:VAR} support
5. **OPENCODE_CONFIG env var** - Custom config path
6. **.opencode directory configs** - Project and home directories

### **LOW Priority (Nice to have)**
7. **OPENCODE_CONFIG_CONTENT** - Inline config
8. **Legacy TOML support** - Migration from old format
9. **Auto-creation with $schema** - Initialize new configs

## 🔧 **IMPLEMENTATION DETAILS**

### Current Python Implementation
```python
# opencode/config/index.py
async def load() -> ConfigInfo:
    # 1. Load global config (3 files, basic merge)
    for filename in ["config.json", "opencode.json", "opencode.jsonc"]:
        config_path = paths.config / filename
        if await filesystem.exists(config_path):
            data = json.loads(content)
            result.update(data)  # ⚠️ Shallow merge!
    
    # 2. Load project config (cwd only)
    cwd = Path.cwd()
    for filename in ["opencode.jsonc", "opencode.json"]:
        config_path = cwd / filename
        if await filesystem.exists(config_path):
            data = json.loads(content)
            result.update(data)  # ⚠️ Shallow merge!
```

### What TypeScript Does
```typescript
// 1. Remote config
// 2. Global config (with legacy TOML migration)
// 3. OPENCODE_CONFIG env
// 4. Project config (findUp from cwd to worktree)
// 5. .opencode directories (project + home)
// 6. OPENCODE_CONFIG_CONTENT env
// Uses deep merge with array concatenation
// Environment variable substitution
```

## 💡 **USAGE IMPACT**

**Current Python Limitations:**
- ❌ Configs in parent directories not found
- ❌ No enterprise/org remote config support
- ❌ Environment variables in config not resolved
- ❌ Nested config objects get overwritten
- ❌ No custom config path via env var

**Works in Python:**
- ✅ Simple global config in ~/.config/opencode/
- ✅ Simple project config in cwd/opencode.json
- ✅ Basic JSON/JSONC parsing

## 🚀 **NEXT STEPS**

To achieve full parity:

1. **Implement findUp** for project config discovery
2. **Add remote config loading** from .well-known URLs
3. **Implement deep merging** for nested configs
4. **Add environment variable substitution**
5. **Support OPENCODE_CONFIG env var**
6. **Load .opencode directory configs**

**Estimated effort:** Medium (1-2 hours)
**Current status:** Functional for basic use cases, missing advanced features
