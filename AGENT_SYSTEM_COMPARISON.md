# Agent System Comparison: TypeScript vs Python

## Summary

**Status: 85% Complete** - Core agent functionality is implemented, but advanced features are missing.

## ✅ **FULLY IMPLEMENTED**

### Core Agent Model
| Feature | TypeScript | Python | Status |
|---------|-----------|---------|---------|
| Agent.Info schema | ✅ | ✅ | **MATCH** |
| name | ✅ | ✅ | **MATCH** |
| description | ✅ | ✅ | **MATCH** |
| mode (primary/subagent/all) | ✅ | ✅ | **MATCH** |
| native flag | ✅ | ✅ | **MATCH** |
| hidden flag | ✅ | ✅ | **MATCH** |
| temperature | ✅ | ✅ | **MATCH** |
| top_p | ✅ | ✅ | **MATCH** |
| color | ✅ | ✅ | **MATCH** |
| variant | ✅ | ✅ | **MATCH** |
| prompt | ✅ | ✅ | **MATCH** |
| options | ✅ | ✅ | **MATCH** |
| steps | ✅ | ✅ | **MATCH** |
| model (providerID/modelID) | ✅ | ✅ | **MATCH** |
| permissions/ruleset | ✅ | ✅ | **MATCH** |

### Default Agents (All 7)
| Agent | TypeScript | Python | Status |
|-------|-----------|---------|---------|
| build | ✅ | ✅ | **MATCH** |
| plan | ✅ | ✅ | **MATCH** |
| general | ✅ | ✅ | **MATCH** |
| explore | ✅ | ✅ | **MATCH** |
| compaction | ✅ | ✅ | **MATCH** |
| title | ✅ | ✅ | **MATCH** |
| summary | ✅ | ✅ | **MATCH** |

### Agent Manager Functions
| Function | TypeScript | Python | Status |
|----------|-----------|---------|---------|
| Agent.get() | ✅ | ✅ | **MATCH** |
| Agent.list() | ✅ | ✅ | **MATCH** |
| Agent.defaultAgent() | ✅ | ✅ | **MATCH** |
| check_permission() | ✅ | ✅ | **MATCH** |
| Glob pattern matching | ✅ | ✅ | **MATCH** |

---

## ❌ **MISSING IN PYTHON**

### 1. AI-Powered Agent Generation
**TypeScript:** `Agent.generate({ description, model })`  
**Python:** ❌ Not implemented  
**Priority:** HIGH  
**Description:** Uses LLM to generate agent configuration from a description

```typescript
// TypeScript
const generated = await Agent.generate({ 
  description: "Create a code review agent",
  model: { providerID: "openai", modelID: "gpt-4" }
})
// Returns: { identifier, whenToUse, systemPrompt }
```

### 2. Config File Integration
**TypeScript:** Loads custom agents from `opencode.json` config  
**Python:** ❌ Not implemented  
**Priority:** HIGH  
**Description:** TypeScript loads user-defined agents from config file and merges with defaults

```typescript
// TypeScript - from config
for (const [key, value] of Object.entries(cfg.agent ?? {})) {
  if (value.disable) delete result[key]
  // Merge with defaults
  result[key] = { ...result[key], ...value }
}
```

### 3. Skill System Integration
**TypeScript:** Adds skill directories to agent permissions  
**Python:** ❌ Not implemented  
**Priority:** MEDIUM  
**Description:** TypeScript scans for skills and adds them to external_directory permissions

```typescript
// TypeScript
const skillDirs = await Skill.dirs()
const defaults = PermissionNext.fromConfig({
  external_directory: {
    [Truncate.GLOB]: "allow",
    ...Object.fromEntries(skillDirs.map((dir) => [path.join(dir, "*"), "allow"])),
  },
})
```

### 4. Agent Persistence (Markdown Files)
**TypeScript:** Saves/loads agents from `.opencode/agents/*.md` files  
**Python:** ❌ Not implemented  
**Priority:** MEDIUM  
**Description:** TypeScript creates agent files with frontmatter

```typescript
// TypeScript creates:
// .opencode/agents/my-agent.md
// ---
// description: "Agent description"
// mode: primary
// tools:
//   read: true
//   write: false
// ---
// System prompt content here
```

### 5. Truncate.GLOB Handling
**TypeScript:** Special handling for truncation glob pattern  
**Python:** ❌ Not implemented  
**Priority:** LOW  
**Description:** Ensures Truncate.GLOB is allowed in external_directory permissions

```typescript
// TypeScript
result[name].permission = PermissionNext.merge(
  result[name].permission,
  PermissionNext.fromConfig({ external_directory: { [Truncate.GLOB]: "allow" } }),
)
```

### 6. Advanced Permission Merging
**TypeScript:** Complex merge of default + user + custom permissions  
**Python:** ⚠️ Basic implementation  
**Priority:** MEDIUM  
**Description:** TypeScript merges multiple permission sources with deep merge

### 7. Agent Prompts Loading
**TypeScript:** Loads prompt text files for agents (PROMPT_EXPLORE, PROMPT_COMPACTION, etc.)  
**Python:** ❌ Not implemented  
**Priority:** LOW  
**Description:** TypeScript has separate .txt files for agent prompts

---

## 📊 **FEATURE PARITY MATRIX**

| Category | Features | Implemented | Missing | % Complete |
|----------|----------|-------------|---------|------------|
| **Core Model** | 14 | 14 | 0 | 100% ✅ |
| **Default Agents** | 7 | 7 | 0 | 100% ✅ |
| **Agent Manager** | 4 | 4 | 0 | 100% ✅ |
| **Generation** | 1 | 0 | 1 | 0% ❌ |
| **Config Integration** | 1 | 0 | 1 | 0% ❌ |
| **Skill Integration** | 1 | 0 | 1 | 0% ❌ |
| **Persistence** | 1 | 0 | 1 | 0% ❌ |
| **Advanced Features** | 3 | 0 | 3 | 0% ❌ |
| **TOTAL** | **31** | **25** | **6** | **81%** |

---

## 🎯 **PRIORITY RECOMMENDATIONS**

### **HIGH Priority**
1. **Config File Integration** - Load custom agents from opencode.json
2. **Agent.generate()** - AI-powered agent creation

### **MEDIUM Priority**
3. **Skill System Integration** - Add skill directories to permissions
4. **Agent Persistence** - Save/load agents from markdown files

### **LOW Priority**
5. **Truncate.GLOB Handling** - Special permission handling
6. **Prompt Text Files** - External prompt loading

---

## 📝 **IMPLEMENTATION NOTES**

### What's Working Well
- ✅ All 7 default agents properly configured
- ✅ Permission system with glob matching
- ✅ Agent mode classification
- ✅ Hidden agent support
- ✅ All agent attributes present

### Key Gaps
- ❌ No AI generation of agents
- ❌ No config file integration
- ❌ No skill directory scanning
- ❌ No persistent agent storage
- ❌ No external prompt loading

### Usage Impact
**Current Python version:**
- Can use all built-in agents ✅
- Can create agents in code ✅
- Cannot load custom agents from config ❌
- Cannot generate agents with AI ❌
- Cannot use skills with agents ❌

**TypeScript version:**
- Can do everything Python can ✅
- Can define agents in opencode.json ✅
- Can generate agents with `opencode agent create` ✅
- Can use skills for enhanced capabilities ✅
