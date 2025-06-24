# Configuration Schema

Smart-tiling uses YAML configuration files to define context-aware rules.

## Schema Structure

```yaml
rules:
  - name: "rule_identifier"           # Unique name for the rule
    parent:
      app_id: ["app1", "app2"]       # List of app_ids to match (Wayland)
      class: ["Class1", "Class2"]    # List of window classes (X11)
      title_pattern: ["*pattern*"]   # Glob patterns for window title
    child:
      app_id: ["child_app"]          # Apps that trigger this rule
    actions:
      - set_mode: v after            # Mode and positioning
      - place: below                 # Explicit placement
      - size_ratio: 0.333           # Size ratio (0.0-1.0)
      - inherit_cwd: true           # Inherit working directory
      - preserve_column: true       # Keep column width in splits
```

## Primary Use Case Example

```yaml
# ~/.config/smart-tiling/rules.yaml
rules:
  - name: "neovim_terminal"
    parent:
      app_id: ["kitty"]
      title_pattern: ["*nvim*", "*NVIM*", "*neovim*"]
    child:
      app_id: ["kitty"]
    actions:
      - set_mode: v after
      - place: below
      - size_ratio: 0.333
      - inherit_cwd: true
      - preserve_column: true
```

## Action Types

- `set_mode`: Change Scroll's mode (h/v) with modifiers
- `place`: Explicit placement (below, right, above, left)
- `size_ratio`: Portion of space for new window (0.333 = 1/3)
- `inherit_cwd`: Extract and reuse parent's working directory
- `preserve_column`: Maintain column structure in splits
