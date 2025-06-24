# System Architecture

## Overview

Smart-tiling extends autotiling by intercepting window creation events and applying context-aware placement rules. The system operates as a daemon that subscribes to Scroll IPC events and makes intelligent decisions based on application context.

## Core Architecture Principles

1. **Event-Driven State Machine**: React to IPC events, maintain state across event sequences
2. **Non-Invasive Extension**: Preserve original autotiling behavior, activate smart features only when rules match
3. **Fail-Safe Design**: Always fall back to geometry-based tiling on any error
4. **Modular Structure**: Clear separation between detection, state, rules, and execution

## System Components

### Entry Point (`main.py`)
- Minimal modifications to original autotiling
- Adds configuration loading for smart rules
- Injects smart placement logic before geometry-based decisions

### Core Modules

#### `core/geometry.py` (Preserved from Original)
- Original autotiling logic, refactored but functionally identical
- Calculates split direction based on window dimensions
- Handles resize operations
- **Must remain backward compatible**

#### `core/context.py` (New)
- Detects application type from container properties
- Extracts app_id (Wayland) and window class (X11)
- Identifies Neovim running inside Kitty terminals
- Provides window title pattern matching

#### `core/process.py` (New)
- Process tree traversal and analysis
- Extracts working directory from `/proc/{pid}/cwd`
- Finds child processes (e.g., Neovim inside Kitty)
- Handles process hierarchy navigation

#### `core/state.py` (New)
- Tracks relationships between windows
- Stores pending rule applications
- Manages time-based state expiration
- Thread-safe state operations

#### `core/rules.py` (New)
- Rule matching engine
- Action execution framework
- Priority and conflict resolution
- Configuration validation

### Scroll Integration

#### `scroll/ipc.py`
- Extends i3ipc with Scroll-specific events
- Handles IPC_EVENT_SCROLLER for mode tracking
- Manages mark-based window tracking
- Subscribes to window creation events

#### `scroll/layout.py`
- Mode manipulation (h/v with modifiers)
- Size adjustment commands
- Column preservation logic
- Layout type detection

#### `scroll/commands.py`
- Command builders for Scroll operations
- Batches commands for atomic execution
- Handles command sequencing
- Error recovery strategies

### Configuration

#### `config/parser.py`
- YAML/TOML configuration loading
- Hot-reload support
- Configuration file discovery
- Environment variable expansion

#### `config/schema.py`
- Rule schema definitions
- Validation logic
- Default values
- Type checking

## Data Flow

### Window Creation Flow

```
1. User Action (Mod4+Return)
    ↓
2. Scroll creates terminal process
    ↓
3. IPC Event: window::new
    ↓
4. Smart-Tiling Handler
    ├─→ Context Detection (app_id, title)
    ├─→ State Lookup (pending rules)
    ├─→ Rule Matching
    └─→ Decision Point
         ├─→ [Match] Smart Placement
         └─→ [No Match] Geometry Tiling
```

### Smart Placement Sequence

```
1. Focus Event (Neovim detected)
    ├─→ Extract context (PID, cwd)
    ├─→ Store in state manager
    └─→ Set pending rule
    
2. Window Creation Event
    ├─→ Check pending rules
    ├─→ Verify child matches
    ├─→ Execute actions:
    │   ├─→ set_mode v after
    │   ├─→ Apply size ratio
    │   ├─→ Preserve column
    │   └─→ Restore mode
    └─→ Clean up state
```

## State Management

### Window Relationships
```python
{
    "relationships": {
        "<child_container_id>": {
            "parent_id": "<parent_container_id>",
            "rule_name": "neovim_terminal",
            "created_at": 1234567890.123,
            "parent_context": {
                "app_id": "kitty",
                "title": "nvim ~/project/file.py",
                "cwd": "/home/user/project"
            }
        }
    }
}
```

### Pending Rules
```python
{
    "pending_rules": {
        "<workspace_name>": {
            "rule": <Rule object>,
            "parent_id": "<container_id>",
            "context": <Context dict>,
            "expires_at": 1234567890.123
        }
    }
}
```

## Event Subscriptions

### From i3ipc
- `Event.WINDOW` - Window focus changes, creation, close
- `Event.BINDING` - Keybinding events (optional)

### Scroll Extensions
- `IPC_EVENT_SCROLLER` - Mode and modifier changes
- Custom events via modified i3ipc connection

## Integration Points

### With Original Autotiling
```python
def switch_splitting(i3, e, debug, ...):
    # INJECTION POINT: Before geometry decision
    if smart_rules_enabled:
        result = smart_tiling.handle_event(i3, e)
        if result.handled:
            return
    
    # Original geometry-based logic continues
    new_layout = "splitv" if height > width else "splith"
    # ...
```

### With User Configuration
```yaml
# ~/.config/smart-tiling/rules.yaml
rules:
  - name: "neovim_terminal"
    parent:
      app_id: ["kitty"]
      title_pattern: ["*nvim*"]
    child:
      app_id: ["kitty"]
    actions:
      - set_mode: v after
      - size_ratio: 0.333
      - inherit_cwd: true
```

### With Scroll Config
```bash
# ~/.config/scroll/config
exec_always smart-tiling --config ~/.config/smart-tiling/rules.yaml
```

## Performance Considerations

### Caching Strategy
- Process information cached with 5-second TTL
- Window tree queries minimized
- Rule compilation on config load
- Lazy evaluation of expensive operations

### Event Debouncing
- Rapid window creation events batched
- State cleanup on 10-second timer
- Mark cleanup on window close

## Error Handling Strategy

### Fail-Safe Layers
1. **Rule Execution**: Errors logged, fall back to next rule
2. **Context Detection**: Missing data uses defaults
3. **State Corruption**: State reset, continue with fresh state
4. **IPC Failures**: Reconnect with exponential backoff
5. **Ultimate Fallback**: Geometry-based tiling always available

### Logging Hierarchy
- ERROR: Unrecoverable failures requiring user intervention
- WARNING: Recoverable failures, degraded functionality
- INFO: Rule matches, state changes
- DEBUG: All IPC commands, state transitions

## Security Considerations

- No arbitrary command execution
- Process information access limited to reading
- Configuration files require appropriate permissions
- No network access required

## Future Extension Points

The architecture supports future enhancements without breaking changes:

1. **Additional Context Sources**: Window manager hints, desktop files
2. **More Action Types**: Focus management, workspace assignment
3. **Rule Learning**: Track user corrections, suggest rules
4. **External Integrations**: D-Bus notifications, status bar integration

## Testing Strategy

### Unit Testing
- Mock IPC connections for each module
- Fixture-based testing with real event data
- State machine property testing

### Integration Testing
- End-to-end scenarios with mock Scroll
- Performance benchmarks for event handling
- Memory leak detection for long-running daemon
