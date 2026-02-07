# TUI Implementation Plan: TypeScript to Python

## Overview

The TypeScript TUI is a complex terminal interface built on **OpenTUI** (a SolidJS-based TUI framework). Porting this to Python requires significant architectural changes.

## TypeScript TUI Architecture

### Core Components
1. **OpenTUI Framework** - SolidJS-based reactive UI
2. **Worker Thread** - Background processing via Web Workers
3. **RPC System** - Communication between main thread and worker
4. **Event System** - Bus-based event handling
5. **Server Integration** - HTTP server for external access
6. **UI Components** - Text areas, dialogs, spinners, keybindings

### File Structure (TypeScript)
```
cli/cmd/tui/
├── app.ts          # Main TUI application
├── thread.ts       # Thread command entry point
├── attach.ts       # Attach command
├── worker.ts       # Web Worker for background tasks
├── event.ts        # TUI event definitions
├── context/        # Context providers
│   └── sdk.ts
│   └── directory.ts
├── component/      # UI components
│   ├── dialog-agent.tsx
│   ├── dialog-commands.tsx
│   ├── dialog-help.tsx
│   ├── dialog-models.tsx
│   ├── dialog-sessions.tsx
│   ├── dialog-themes.tsx
│   ├── toast.tsx
│   └── textarea-keybindings.ts
├── ui/            # UI utilities
│   └── spinner.ts
└── util/          # Utilities
    ├── clipboard.ts
    ├── editor.ts
    ├── signal.ts
    ├── terminal.ts
    └── transcript.ts
```

## Python Implementation Strategy

### Framework Choice: Textual

**Why Textual?**
- Modern Python TUI framework
- Reactive (similar to SolidJS)
- CSS-like styling
- Rich components (text areas, data tables, etc.)
- Built-in event system
- Async support
- Good documentation

**Alternative:** Rich (simpler, less reactive)

### Architecture Changes

#### 1. Replace Web Workers with Asyncio
- Python doesn't have Web Workers
- Use asyncio for concurrency
- Run background tasks in async functions

#### 2. Replace OpenTUI with Textual
- Convert SolidJS components to Textual widgets
- Use Textual's reactive system
- CSS-like styling with Textual CSS

#### 3. Replace RPC with Direct Calls
- No need for RPC in single-process Python
- Direct method calls between components
- Use asyncio.Queue for communication if needed

#### 4. Keep Server Integration
- Reuse existing Python server
- WebSocket for real-time updates
- HTTP API for control

## Implementation Phases

### Phase 1: Core Framework (Week 1-2)
- [ ] Install and configure Textual
- [ ] Create basic app structure
- [ ] Implement main screen layout
- [ ] Add basic widgets (header, footer, sidebar)

### Phase 2: Essential Components (Week 3-4)
- [ ] Chat/message display area
- [ ] Input text area with keybindings
- [ ] Session sidebar
- [ ] Basic dialogs (help, sessions)

### Phase 3: Advanced Features (Week 5-6)
- [ ] Agent switching
- [ ] Model selection dialog
- [ ] Theme support
- [ ] Command palette

### Phase 4: Integration (Week 7-8)
- [ ] Server integration
- [ ] WebSocket connection
- [ ] Event handling
- [ ] Background processing

### Phase 5: Polish (Week 9-10)
- [ ] Error handling
- [ ] Loading states/spinners
- [ ] Clipboard integration
- [ ] External editor support

## Component Mapping

### TypeScript → Python

| TypeScript | Python (Textual) | Notes |
|------------|------------------|-------|
| SolidJS Components | Textual Widgets | Reactive UI |
| Web Workers | Asyncio Tasks | Background processing |
| OpenTUI CSS | Textual CSS | Styling |
| Event Bus | Textual Messages | Event handling |
| Text Area | Textual TextArea | Input component |
| Dialogs | Textual ModalScreen | Popup dialogs |
| Spinner | Textual LoadingIndicator | Loading states |

## Key Features to Implement

### 1. Main Chat Interface
- Scrollable message history
- User input text area
- Send button / Ctrl+Enter
- Message styling (user vs assistant)

### 2. Sidebar
- Session list
- New session button
- Session management (rename, delete)

### 3. Input Area
- Multi-line text input
- Syntax highlighting (optional)
- Keybindings (Ctrl+Enter to send)
- Agent mention support (@agent)

### 4. Dialogs
- Help dialog (keybindings)
- Sessions dialog
- Models dialog
- Themes dialog
- Commands dialog

### 5. Status Bar
- Current agent
- Current model
- Connection status
- Session info

## Technical Challenges

### 1. Reactivity
**TypeScript:** SolidJS signals
**Python:** Textual reactive attributes

### 2. Performance
**Challenge:** Large message history
**Solution:** Virtual scrolling, pagination

### 3. Keybindings
**Challenge:** Complex key combinations
**Solution:** Textual's keybinding system

### 4. Syntax Highlighting
**Challenge:** Code blocks in chat
**Solution:** Rich syntax highlighting

### 5. External Editor
**Challenge:** Open $EDITOR
**Solution:** Subprocess integration

## Estimated Effort

- **Total Time:** 8-10 weeks
- **Complexity:** Very High
- **Lines of Code:** ~5,000-8,000
- **Files:** ~30-40

## Simplified Alternative

If full TUI is too complex, consider:
1. **Enhanced CLI** - Better prompts, progress bars
2. **Web UI** - Browser-based interface
3. **VS Code Extension** - IDE integration
4. **Simple TUI** - Basic chat interface only

## Recommendation

Given the complexity, I recommend:
1. Start with **Phase 1** (basic framework)
2. Implement **essential chat interface** first
3. Add features incrementally
4. Consider **simplified alternative** if full TUI is too much

## Implementation Priority

### MUST HAVE (Core Experience)
1. Basic chat interface
2. Message history
3. Text input
4. Send/receive messages

### SHOULD HAVE (Good Experience)
5. Session sidebar
6. Agent switching
7. Help dialog
8. Loading indicators

### NICE TO HAVE (Complete Experience)
9. Theme support
10. Model selection
11. Command palette
12. External editor

## Next Steps

Would you like me to:
1. **Start Phase 1** - Implement basic Textual framework?
2. **Create simplified TUI** - Just chat interface?
3. **Focus on enhanced CLI** - Better prompts and progress bars?
4. **Skip TUI for now** - Focus on other missing features?

**Note:** Full TUI implementation is a 2-3 month project. Consider if this is the best use of time vs other missing features (GitHub integration, MCP commands, etc.).
