# Scroll IPC Extensions

## Key Differences from i3/Sway

### Events
- `IPC_EVENT_SCROLLER` - Mode and modifier state
- `IPC_EVENT_TRAILS` - Trail/mark tracking

### Commands
- `set_mode [h|v] [after|before|end|beg] [focus|nofocus]`
- `mark --add --toggle <name>`
- `set_size [h|v] <ratio>`
- `fit_size [h|v] [active|visible|all]`

### Mode System
```python
# Example: Place window below with 1/3 height
i3.command('set_mode v after')
# ... window creates ...
i3.command('set_size v 0.333')
# ... restore original mode ...
```

### Layout Types
- Horizontal: columns of windows
- Vertical: rows of windows
- Query with: `container.parent.layout`

### Marks for Tracking
```python
# Mark parent window
i3.command(f'[con_id={container_id}] mark --add _smart_parent_{uuid}')
# Find it later
parents = i3.get_tree().find_marked(f'_smart_parent_{uuid}')
```

## Event Flow for Window Creation
1. User presses key → `binding` event (optional)
2. Terminal launches → `window::new` event
3. Window maps → `window::focus` event
4. Layout updates → `workspace` event

## Critical Timing
- Mode must be set BEFORE window creation
- Size adjustment happens AFTER window exists
- Mark cleanup on window close
```



---
# Sway Window Manager Split Commands and Scroll Fork Implementation

## Sway's Split Commands

Sway window manager provides several commands for controlling how windows are split and arranged within containers. The primary split commands are `splith`, `splitv`, and their variations[1][2].

### Core Split Commands

**`splitv` (Split Vertical)**
- Equivalent to `split vertical`[2]
- Creates a vertical split in the current container[1]
- When executed, it turns the focused window into a container with vertical orientation[3]
- New windows opened after this command will be arranged vertically within that container[4]

**`splith` (Split Horizontal)**  
- Equivalent to `split horizontal`[2]
- Creates a horizontal split in the current container[1]
- Turns the focused window into a container with horizontal orientation[3]
- Subsequent windows will be arranged horizontally[4]

**`splitt` (Split Toggle)**
- Equivalent to `split toggle`[2]
- Toggles between horizontal and vertical splitting modes[1]
- When specified, the current container is split opposite to the parent container's layout[1]

### Split Command Limitations

Sway currently only supports `splith` and `splitv` commands, but users have requested additional split commands for tabbed and stacking layouts[4]. The proposed `split tabbed` and `split stacking` commands would work similarly to the existing split commands but create tabbed or stacked containers instead[4]. However, these can be achieved through command chaining, such as `splitv; layout tabbed`[4].

## Dawsers/Scroll Fork Analysis

Scroll is a Wayland compositor forked from Sway that implements a fundamentally different approach to window management[7]. The main difference is that Scroll only supports one layout: a scrolling layout similar to PaperWM, niri, or hyprscroller[7].

### Split Command Implementation in Scroll

**Traditional Split Commands Removed**
Scroll has removed the original Sway/i3 layouts, including the traditional split functionality[7][8]. The fork focuses exclusively on a scrolling layout paradigm rather than the tile-based splitting system used in Sway[7].

**Alternative Layout Management**
Instead of `splith` and `splitv` commands, Scroll implements a different set of layout commands:

- **Mode-based Operation**: Scroll works with "horizontal" and "vertical" modes that can be changed with `set_mode `[7]
- **Layout Types**: Per-output layout types can be set as "horizontal" or "vertical" using `layout_type horizontal|vertical`[7]
- **Dynamic Layout Control**: The `layout_transpose` command allows switching between layout orientations at runtime[7]

### Window Arrangement in Scroll

Scroll's approach to window arrangement differs significantly from Sway's split commands[7]:

- **Horizontal Mode**: Creates new columns per new window in horizontal layouts, or adds windows to current row in vertical layouts[7]
- **Vertical Mode**: Adds new windows to active column in horizontal layouts, or creates new rows in vertical layouts[7]
- **Scrolling Navigation**: Windows are arranged in a scrolling fashion that can be navigated with trackpad gestures or mouse dragging[7]
