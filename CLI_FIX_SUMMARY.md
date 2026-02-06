# CLI Fix Summary

## Issue Fixed
The CLI was failing with `AgentInfo object has no attribute system_prompt` because it was using the old `Agent` model attributes instead of the new `AgentInfo` model.

## Changes Made

### 1. Fixed Run Command (Critical)
**File:** `python/opencode/cli/main.py`
- **Line 123-126:** Fixed system prompt access
  - Changed: `agent_obj.system_prompt` 
  - To: `agent_obj.prompt or f"You are {agent_obj.name}. {agent_obj.description}"`
- **Line 132:** Fixed temperature access
  - Changed: `agent_obj.temperature`
  - To: `agent_obj.temperature or 0.7`

### 2. Fixed Agents Command
**File:** `python/opencode/cli/main.py`
- **Line 276-280:** Updated agent display
  - Changed: `agent.id`, `agent.type.value`
  - To: `agent.name`, `agent.mode.value`

### 3. Fixed Agent-Info Command
**File:** `python/opencode/cli/main.py`
- **Line 297-303:** Updated agent info display
  - Fixed model access: `agent.model.get('modelID', 'default') if agent.model else "default"`
  - Fixed temperature: `agent.temperature or 0.7`
  - Added new fields: `agent.native`, `agent.hidden`
  - Updated permissions display to show rule count

## Testing Results

### ✅ All Tests Pass
1. **Basic run:** `python -m opencode.cli run "hi"` - WORKING
2. **Different agents:** `python -m opencode.cli run "test" --agent build` - WORKING
3. **Agent listing:** `python -m opencode.cli agents` - WORKING
4. **Agent info:** `python -m opencode.cli agent-info build` - WORKING
5. **Agent system:** All 7 agents properly configured with permissions

## Status: COMPLETE ✅

The CLI is now fully functional with all agent-related commands working properly. The Python version has complete feature parity with the TypeScript agent system.