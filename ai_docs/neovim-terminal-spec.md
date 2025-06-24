# Neovim + Terminal Specification

## User Story
As a developer using Neovim in Scroll,
When I press Mod4+Return,
I want a terminal to open below my editor with the same working directory,
So I can run commands without breaking my flow.

## Technical Requirements

### Detection
- Identify Neovim by `app_id`: "nvim"
- Also check window title for "NVIM" pattern
- Handle both Wayland and XWayland variants

### Working Directory
1. Get Neovim's PID from container
2. Read `/proc/{pid}/cwd` symlink
3. Fall back to `$HOME` if unavailable
4. Pass to terminal via:
   - `kitty --directory <path>`
   - `alacritty --working-directory <path>`
   - `foot --working-directory <path>`

### Layout Manipulation
```python
# Pseudocode for the flow
if focused_window.is_neovim():
    # Save current mode
    original_mode = get_current_mode()
    
    # Set vertical mode with "after" placement
    i3.command('set_mode v after')
    
    # Mark parent for tracking
    mark = f'_smart_parent_{timestamp}'
    i3.command(f'mark --add {mark}')
    
    # Terminal will be created by user's keybinding
    # We detect it in window::new event
    
    # After terminal appears:
    i3.command('set_size v 0.333')  # Terminal 1/3
    # Parent automatically becomes 2/3
    
    # Restore mode
    i3.command(f'set_mode {original_mode}')
```

### Edge Cases
1. Multiple Neovim instances - use focused one
2. Neovim in split - preserve column width
3. Neovim closes - terminal remains, state cleaned
4. Workspace changes - rules follow workspace
```

